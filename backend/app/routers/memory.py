"""Memory API 路由。"""

from fastapi import APIRouter, HTTPException

from app.models.memory import MemoryOut
from app.services.memory import delete_memory, get_all_memories

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("", response_model=list[MemoryOut])
async def list_memories():
    rows = await get_all_memories()
    return [MemoryOut(**r) for r in rows]


@router.delete("/{memory_id}")
async def remove_memory(memory_id: str):
    deleted = await delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"detail": "Deleted"}
