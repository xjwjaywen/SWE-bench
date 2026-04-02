"""对话管理 API 路由。"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.models.conversation import (
    ConversationCreate,
    ConversationOut,
    ConversationUpdate,
    MessageOut,
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _parse_message(row) -> dict:
    import json
    sources = []
    if row["sources"]:
        try:
            sources = json.loads(row["sources"])
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": row["id"],
        "conversation_id": row["conversation_id"],
        "role": row["role"],
        "content": row["content"],
        "sources": sources,
        "created_at": row["created_at"],
    }


@router.post("", response_model=ConversationOut)
async def create_conversation(data: ConversationCreate):
    db = await get_db()
    try:
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conv_id, data.title, now, now),
        )
        await db.commit()
        return ConversationOut(id=conv_id, title=data.title, created_at=now, updated_at=now)
    finally:
        await db.close()


@router.get("", response_model=list[ConversationOut])
async def list_conversations():
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
        )
        rows = await cursor.fetchall()
        return [ConversationOut(**dict(r)) for r in rows]
    finally:
        await db.close()


@router.get("/{conv_id}")
async def get_conversation(conv_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?",
            (conv_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conv = dict(row)

        cursor = await db.execute(
            "SELECT id, conversation_id, role, content, sources, created_at "
            "FROM messages WHERE conversation_id = ? ORDER BY created_at",
            (conv_id,),
        )
        msg_rows = await cursor.fetchall()
        conv["messages"] = [_parse_message(r) for r in msg_rows]
        return conv
    finally:
        await db.close()


@router.put("/{conv_id}", response_model=ConversationOut)
async def update_conversation(conv_id: str, data: ConversationUpdate):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        cursor = await db.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (data.title, now, conv_id),
        )
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")

        cursor = await db.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?",
            (conv_id,),
        )
        row = await cursor.fetchone()
        return ConversationOut(**dict(row))
    finally:
        await db.close()


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str):
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"detail": "Deleted"}
    finally:
        await db.close()
