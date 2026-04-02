"""Memory 的 Pydantic 模型。"""

from pydantic import BaseModel


class MemoryOut(BaseModel):
    id: str
    content: str
    source_conversation_id: str | None
    created_at: str
