from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from var_app.db.database import get_db
from var_app.db import crud
from var_app.agent.memory import embed_text

router = APIRouter(prefix="/api/memory", tags=["memory"])


class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 5


@router.get("/{session_id}")
async def list_session_memory(session_id: str):
    db = await get_db()
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "session_not_found"}}
        )
    memories = await crud.list_memory(db, session_id)
    return {"memories": memories}


@router.post("/{session_id}/search")
async def search_session_memory(session_id: str, body: MemorySearchRequest):
    db = await get_db()
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "session_not_found"}}
        )

    try:
        embedding = await embed_text(body.query)
    except Exception:
        return {"memories": []}

    results = await crud.search_memory(db, session_id, embedding, body.limit)
    return {"memories": results}


@router.delete("/{memory_id}", status_code=204)
async def delete_memory_entry(memory_id: str):
    db = await get_db()
    deleted = await crud.delete_memory(db, memory_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "memory_not_found"}}
        )
