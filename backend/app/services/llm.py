"""LLM 服务：基于检索结果生成回答。"""

import re

from openai import OpenAI

from app.config import (
    MINIMAX_API_KEY,
    MINIMAX_BASE_URL,
    MINIMAX_CHAT_MODEL,
    OPENAI_API_KEY,
    OPENAI_CHAT_MODEL,
    USE_MINIMAX,
)
from app.services.retriever import retrieve

SYSTEM_PROMPT = """你是一个邮件检索助手。用户会问关于历史邮件的问题，你需要根据检索到的邮件内容生成准确的回答。

规则：
1. 只基于提供的邮件内容回答，不要编造信息
2. 回答要简洁明了，直接给出关键信息
3. 如果检索到的邮件中没有相关信息，诚实告知用户
4. 在回答中自然地引用来源（邮件主题、发件人等）
5. 支持中文和英文问答
6. 如果用户只是打招呼或闲聊（如"你好"、"hi"），直接友好回复，不需要引用邮件来源
7. 不要在回答中包含任何XML标签（如<think>等）"""

# 判断是否为闲聊（不需要检索）
CASUAL_PATTERNS = re.compile(
    r"^(你好|hello|hi|hey|嗨|喂|在吗|在不在|谢谢|感谢|ok|好的|明白|再见|bye)[\s!！?？。.]*$",
    re.IGNORECASE,
)


def strip_think_tags(text: str) -> str:
    """移除 MiniMax 等模型输出的 <think>...</think> 标签。"""
    return re.sub(r"<think>[\s\S]*?</think>\s*", "", text).strip()


def build_context(sources: list[dict]) -> str:
    """将检索结果构建为 LLM 上下文。"""
    if not sources:
        return "未找到相关邮件。"

    parts = []
    for i, src in enumerate(sources, 1):
        parts.append(
            f"--- 邮件 {i} ---\n"
            f"主题: {src['subject']}\n"
            f"发件人: {src['from_name']} <{src['from_email']}>\n"
            f"日期: {src['date']}\n"
            f"附件: {src['attachments'] or '无'}\n"
            f"内容:\n{src['document'][:2000]}\n"
        )
    return "\n".join(parts)


def get_llm_client():
    """获取 LLM 客户端，自动选择 MiniMax 或 OpenAI。"""
    if USE_MINIMAX:
        return OpenAI(api_key=MINIMAX_API_KEY, base_url=MINIMAX_BASE_URL)
    return OpenAI(api_key=OPENAI_API_KEY)


def get_chat_model():
    """获取聊天模型名称。"""
    return MINIMAX_CHAT_MODEL if USE_MINIMAX else OPENAI_CHAT_MODEL


def rewrite_query(query: str, conversation_history: list[dict] | None) -> str:
    """结合对话历史改写查询，解析指代词（如"它"、"这个"）。"""
    if not conversation_history:
        return query

    # 检测是否含指代词
    pronouns = ["它", "这个", "那个", "该", "其", "上面", "前面", "刚才"]
    if not any(p in query for p in pronouns):
        return query

    # 用 LLM 改写查询
    try:
        client = get_llm_client()
        model = get_chat_model()

        # 取最近几轮对话作为上下文
        recent = conversation_history[-6:]
        history_text = "\n".join(f"{m['role']}: {m['content'][:200]}" for m in recent)

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": (
                    "你的任务是改写用户的查询，将其中的指代词（如'它'、'这个'）替换为对话历史中提到的具体实体。"
                    "只输出改写后的查询，不要解释。如果不需要改写，原样输出。"
                )},
                {"role": "user", "content": f"对话历史:\n{history_text}\n\n当前查询: {query}\n\n改写后的查询:"},
            ],
            temperature=0,
        )
        rewritten = (resp.choices[0].message.content or "").strip()
        rewritten = strip_think_tags(rewritten)
        if rewritten and len(rewritten) < 200:
            return rewritten
    except Exception:
        pass
    return query


def generate_answer(
    query: str,
    conversation_history: list[dict] | None = None,
    memory_context: str = "",
) -> tuple[str, list[dict]]:
    """生成 RAG 回答。"""
    # 闲聊不走检索
    is_casual = bool(CASUAL_PATTERNS.match(query.strip()))

    # 多轮对话时，改写查询解析指代词
    search_query = query if is_casual else rewrite_query(query, conversation_history)

    sources = [] if is_casual else retrieve(search_query)
    context = build_context(sources)

    system_parts = [SYSTEM_PROMPT]
    if memory_context:
        system_parts.append(f"用户偏好和关注点：\n{memory_context}")
    if not is_casual:
        system_parts.append(f"以下是检索到的相关邮件内容：\n\n{context}")

    messages = [{"role": "system", "content": "\n\n".join(system_parts)}]

    # 添加对话历史
    if conversation_history:
        messages.extend(conversation_history[-10:])

    messages.append({"role": "user", "content": query})

    client = get_llm_client()
    model = get_chat_model()

    # MiniMax 和 OpenAI 的参数略有不同
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
    }
    if not USE_MINIMAX:
        kwargs["max_tokens"] = 1500

    response = client.chat.completions.create(**kwargs)

    answer = response.choices[0].message.content or ""

    # 清理 <think> 标签
    answer = strip_think_tags(answer)

    # 返回简化的来源信息
    simple_sources = []
    for src in sources:
        simple_sources.append({
            "email_id": src["email_id"],
            "subject": src["subject"],
            "from_": src["from_name"],
            "from_email": src["from_email"],
            "date": src["date"],
            "attachments": [a.strip() for a in src["attachments"].split(",") if a.strip()],
            "snippet": src["document"][:200],
        })

    return answer, simple_sources
