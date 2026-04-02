"""Memory 服务：自动从对话中提取用户偏好和关注点。"""

import json
import uuid
from datetime import datetime, timezone

from app.database import get_db

EXTRACT_KEYWORDS = [
    "经常", "总是", "每次", "关注", "重点", "偏好", "习惯",
    "always", "focus", "prefer", "usually", "often",
]


async def extract_memory_from_conversation(
    conversation_id: str,
    user_message: str,
    assistant_response: str,
) -> str | None:
    """从对话中判断是否需要提取 memory。

    简单规则：如果用户多次询问某个主题/项目/人物，记录下来。
    """
    db = await get_db()
    try:
        # 获取该对话的历史消息数量
        cursor = await db.execute(
            "SELECT content FROM messages WHERE conversation_id = ? AND role = 'user'",
            (conversation_id,),
        )
        rows = await cursor.fetchall()
        user_messages = [r[0] for r in rows]

        if len(user_messages) < 2:
            return None

        # 简单提取：检查是否有重复关键词/主题
        # 在真实场景中可用 LLM 提取
        all_text = " ".join(user_messages)

        # 找出出现超过一次的实体词（简单实现）
        words = set()
        repeated = set()
        for msg in user_messages:
            for word in msg.split():
                if len(word) >= 2:
                    if word in words:
                        repeated.add(word)
                    words.add(word)

        if not repeated:
            return None

        memory_content = f"用户在对话中多次提及: {', '.join(list(repeated)[:5])}"

        # 检查是否已有相似的 memory
        cursor = await db.execute(
            "SELECT content FROM memories WHERE source_conversation_id = ?",
            (conversation_id,),
        )
        existing = await cursor.fetchall()
        for row in existing:
            if any(w in row[0] for w in repeated):
                return None  # 已存在相似记录

        memory_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO memories (id, content, source_conversation_id, created_at) VALUES (?, ?, ?, ?)",
            (memory_id, memory_content, conversation_id, now),
        )
        await db.commit()
        return memory_id
    finally:
        await db.close()


async def get_memory_context() -> str:
    """获取所有 memory 拼接为上下文字符串。"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT content FROM memories ORDER BY created_at DESC LIMIT 20"
        )
        rows = await cursor.fetchall()
        if not rows:
            return ""
        return "\n".join(f"- {r[0]}" for r in rows)
    finally:
        await db.close()


async def get_all_memories() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, content, source_conversation_id, created_at FROM memories ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def delete_memory(memory_id: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()
