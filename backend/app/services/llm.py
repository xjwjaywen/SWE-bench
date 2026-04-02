"""LLM 服务：基于检索结果生成回答。"""

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_CHAT_MODEL
from app.services.retriever import retrieve

SYSTEM_PROMPT = """你是一个邮件检索助手。用户会问关于历史邮件的问题，你需要根据检索到的邮件内容生成准确的回答。

规则：
1. 只基于提供的邮件内容回答，不要编造信息
2. 回答要简洁明了，直接给出关键信息
3. 如果检索到的邮件中没有相关信息，诚实告知用户
4. 在回答中自然地引用来源（邮件主题、发件人等）
5. 支持中文和英文问答"""


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


def generate_answer(
    query: str,
    conversation_history: list[dict] | None = None,
    memory_context: str = "",
) -> tuple[str, list[dict]]:
    """生成 RAG 回答。

    Args:
        query: 用户问题
        conversation_history: 对话历史 [{"role": "user"/"assistant", "content": "..."}]
        memory_context: 用户 Memory 上下文

    Returns:
        (answer_text, sources_list)
    """
    # 检索相关邮件
    sources = retrieve(query)

    # 构建上下文
    context = build_context(sources)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if memory_context:
        messages.append({
            "role": "system",
            "content": f"用户偏好和关注点：\n{memory_context}",
        })

    messages.append({
        "role": "system",
        "content": f"以下是检索到的相关邮件内容：\n\n{context}",
    })

    # 添加对话历史
    if conversation_history:
        messages.extend(conversation_history[-10:])  # 最近10轮

    messages.append({"role": "user", "content": query})

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_CHAT_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=1500,
    )

    answer = response.choices[0].message.content or ""

    # 返回简化的来源信息（不含完整文档内容）
    simple_sources = []
    for src in sources:
        simple_sources.append({
            "email_id": src["email_id"],
            "subject": src["subject"],
            "from": src["from_name"],
            "from_email": src["from_email"],
            "date": src["date"],
            "attachments": [a.strip() for a in src["attachments"].split(",") if a.strip()],
            "snippet": src["document"][:200],
        })

    return answer, simple_sources
