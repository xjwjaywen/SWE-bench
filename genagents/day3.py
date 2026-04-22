"""
Generative Agents - Day 3
Adds reflection: periodically abstract high-level judgments from recent
observations, store them back into the same memory stream with higher
importance so future retrieval can surface them.

Trigger rule (paper §4.3 simplified):
  each Agent keeps an `importance_buffer` of post-last-reflect observation
  importance; when it crosses REFLECTION_THRESHOLD, we run reflect() and reset.

Output:
  reflections are printed inline ("💭 <name> 反思: ...") so you can see the
  moment abstraction happens during the conversation.

Run:
  export MINIMAX_API_KEY="..."
  python day3.py
"""

import asyncio
import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"   # silence the fork warning

import re
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
from openai import AsyncOpenAI, APIError
from sentence_transformers import SentenceTransformer


MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M2")  # swap without editing
BASE_URL = "https://api.minimaxi.com/v1"

# Reflection hyperparameters
REFLECTION_THRESHOLD = 30.0        # lowered from 50 so short conversations still trigger
N_REFLECTIONS_PER_CYCLE = 3
REFLECTION_IMPORTANCE = 8.0

client = AsyncOpenAI(
    api_key=os.environ.get("MINIMAX_API_KEY", ""),
    base_url=BASE_URL,
    max_retries=3,
    timeout=60.0,
)

print("→ loading embedding model...")
EMBED_MODEL = SentenceTransformer("BAAI/bge-small-zh-v1.5")
print("✓ embedding model ready\n")

THINK_PATTERN = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


def strip_thinking(text: str) -> str:
    return THINK_PATTERN.sub("", text).strip()


def embed(text: str) -> np.ndarray:
    return EMBED_MODEL.encode(text, normalize_embeddings=True)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


# ============ LLM ============

async def _llm_call(prompt: str, temperature: float = 0.8) -> str:
    for attempt in range(5):
        try:
            resp = await client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            return strip_thinking(resp.choices[0].message.content)
        except APIError as e:
            if attempt == 4:
                raise
            wait = 2 ** attempt
            print(f"  ⚠ retry {attempt + 1}/5 after {wait}s ({type(e).__name__})")
            await asyncio.sleep(wait)


async def score_importance(content: str) -> float:
    prompt = f"""请评估以下记忆对当事人的重要性,输出 1-10 的整数。

- 1-3: 日常琐事(喝咖啡、路过公园)
- 4-6: 普通社交(闲聊、打招呼、简单请求)
- 7-8: 重要事件(新认识朋友、得到承诺、收到邀请)
- 9-10: 人生大事(分手、去世、升职、重大决定)

记忆内容: "{content}"

只输出一个 1-10 的整数,不要其他任何文字。"""
    try:
        raw = await _llm_call(prompt, temperature=0.0)
    except APIError:
        # API overloaded after all retries — fall back so the run doesn't crash
        print("  ⚠ importance scoring failed, defaulting to 5.0")
        return 5.0
    m = re.search(r"\b([1-9]|10)\b", raw)
    return float(m.group(1)) if m else 5.0


REFLECTION_PROMPT = """基于 {agent_name} 最近经历的重要记忆,请总结 {n} 条关于对方 / 自己 / 当前情况的**高层判断或模式**。

{agent_name} 最近的重要记忆(按重要性降序):
{memories}

要求:
1. 每条必须是**抽象的陈述句**,不是对某次事件的简单复述
2. 应该能指导 {agent_name} 在未来的决策中如何行动
3. 可以是对某人性格的判断、某类情况的规律、自己的情绪状态等

好的例子(抽象):
- "Maria 对热闹的社交活动态度是回避的"
- "Klaus 是一个对美食很挑剔的人"
- "我最近对 party 话题的追问让 Maria 不太自在"

不好的例子(太具体):
- "Maria 说过'我考虑一下'"
- "Klaus 上周点了拿铁"

输出格式(必须严格遵守):
1. <judgment>
2. <judgment>
3. <judgment>

只输出 {n} 条编号条目,不要任何其他解释或前缀。"""


# ============ data structures ============

@dataclass
class MemoryItem:
    timestamp: datetime
    type: str                  # "observation" | "reflection"
    content: str
    importance: float
    embedding: np.ndarray


@dataclass
class Agent:
    name: str
    identity: str
    memories: list[MemoryItem] = field(default_factory=list)
    importance_buffer: float = 0.0

    async def remember(self, content: str, importance: float | None = None,
                       mem_type: str = "observation"):
        if importance is None:
            importance = await score_importance(content)
        self.memories.append(MemoryItem(
            timestamp=datetime.now(),
            type=mem_type,
            content=content,
            importance=importance,
            embedding=embed(content),
        ))
        # only observations push the reflection buffer (avoid infinite loops)
        if mem_type == "observation":
            self.importance_buffer += importance
            if self.importance_buffer >= REFLECTION_THRESHOLD:
                await self.reflect()
                self.importance_buffer = 0.0

    async def reflect(self):
        """Abstract 3 high-level insights from top-importance recent memories."""
        top = sorted(self.memories, key=lambda m: -m.importance)[:20]
        mem_text = "\n".join(f"- [{m.importance:.0f}] {m.content}" for m in top)
        prompt = REFLECTION_PROMPT.format(
            agent_name=self.name,
            n=N_REFLECTIONS_PER_CYCLE,
            memories=mem_text,
        )
        raw = await _llm_call(prompt, temperature=0.3)

        # parse "1. ... 2. ... 3. ..." format; tolerate minor variations
        reflections = re.findall(r"\d+[\.\)]\s*(.+)", raw)
        reflections = [r.strip() for r in reflections if r.strip()]
        reflections = reflections[:N_REFLECTIONS_PER_CYCLE]

        if not reflections:
            print(f"  ⚠ {self.name} 反思失败(格式未匹配),原始输出: {raw[:200]}")
            return

        print(f"\n  💭 {self.name} 反思:")
        for r in reflections:
            print(f"     - {r}")
            await self.remember(
                content=f"[反思] {r}",
                importance=REFLECTION_IMPORTANCE,
                mem_type="reflection",
            )
        print()

    def retrieve(self, query: str, k: int = 5) -> list[MemoryItem]:
        if not self.memories:
            return []
        q_emb = embed(query)
        now = datetime.now()

        def score(m: MemoryItem) -> float:
            hours_ago = (now - m.timestamp).total_seconds() / 3600 + 1e-3
            recency = 0.99 ** hours_ago
            relevance = cosine(m.embedding, q_emb)
            importance = m.importance / 10.0
            return recency + relevance + importance

        return sorted(self.memories, key=score, reverse=True)[:k]

    def retrieve_as_prompt(self, query: str, k: int = 5) -> str:
        items = self.retrieve(query, k)
        lines = []
        for m in items:
            tag = "💭" if m.type == "reflection" else "·"
            lines.append(f"{tag} [{m.importance:.0f}] {m.content}")
        return "\n".join(lines)


# ============ agent speak ============

async def agent_speak(speaker: Agent, listener: Agent, scene: str) -> str:
    query = f"{scene} 和 {listener.name} 的对话"
    retrieved = speaker.retrieve_as_prompt(query, k=6)

    prompt = f"""你是 {speaker.name}。
【人格】{speaker.identity}

【你检索到的相关记忆(💭 = 你自己的反思判断,· = 具体观察;数字是重要性 1-10)】
{retrieved}

【当前场景】{scene}
你正在和 {listener.name} 说话。

请用一句自然、符合人格的话回应(≤40字)。如果你有反思判断,请让它影响你的回应方式。
直接输出内容,不要任何前缀、引号、解释。"""

    return await _llm_call(prompt, temperature=0.8)


# ============ conversation loop ============

async def conversation(a: Agent, b: Agent, rounds: int, scene: str):
    print(f"━━━ {a.name} × {b.name} ━━━")
    print(f"场景: {scene}\n")
    speaker, listener = a, b

    for _ in range(rounds):
        utt = await agent_speak(speaker, listener, scene)
        print(f"[{speaker.name}] {utt}")

        # Share one importance score across both sides of the same utterance.
        # Cuts LLM calls per turn from 3 -> 2.
        shared_score = await score_importance(f"对话内容: {utt}")

        await speaker.remember(
            f"我对 {listener.name} 说: {utt}",
            importance=shared_score,
        )
        await listener.remember(
            f"{speaker.name} 对我说: {utt}",
            importance=shared_score,
        )

        speaker, listener = listener, speaker

    print(f"\n━━━ 对话结束 ({rounds} 轮) ━━━")


# ============ entry ============

async def build_agents() -> tuple[Agent, Agent]:
    isabella = Agent(
        name="Isabella",
        identity=(
            "32岁,Hobbs Cafe 老板娘,热情外向。"
            "最近在策划 2026 年情人节 party,想邀请常客一起庆祝。"
        ),
    )
    maria = Agent(
        name="Maria",
        identity=(
            "25岁,计算机系大学生,性格内向但对熟人友好,"
            "喜欢下午一个人在 Hobbs Cafe 喝咖啡、写代码。"
        ),
    )
    await isabella.remember(
        "我打算 2026-02-14 在 Hobbs Cafe 办情人节 party,想邀请常客",
        importance=9.0,
    )
    await isabella.remember(
        "Maria 是 Cafe 的常客,经常一个人来学习,我一直想和她多聊聊",
        importance=7.0,
    )
    return isabella, maria


async def main():
    if not os.environ.get("MINIMAX_API_KEY"):
        raise SystemExit("请先 export MINIMAX_API_KEY=...")

    isabella, maria = await build_agents()

    await conversation(
        isabella, maria,
        rounds=10,   # 跑长一点,让反思有机会触发
        scene=(
            "2026年2月10日傍晚的 Hobbs Cafe,"
            "Maria 像往常一样来喝咖啡,Isabella 走过去招呼她"
        ),
    )

    for agent in (isabella, maria):
        print(f"\n═══ {agent.name} 的记忆 ({len(agent.memories)} 条) ═══")
        obs = [m for m in agent.memories if m.type == "observation"]
        refs = [m for m in agent.memories if m.type == "reflection"]
        print(f"  observation: {len(obs)} 条    reflection: {len(refs)} 条")
        print("  --- 按重要性降序 ---")
        for m in sorted(agent.memories, key=lambda x: -x.importance):
            tag = "💭" if m.type == "reflection" else "·"
            print(f"  {tag} [{m.importance:.1f}] {m.content}")


if __name__ == "__main__":
    asyncio.run(main())
