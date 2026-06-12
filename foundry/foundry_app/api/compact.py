from fastapi import APIRouter, HTTPException

from foundry_app.db.database import get_db
from foundry_app.db import crud
from foundry_app.session.history import load_history
from foundry_app.session.compaction import do_compaction
from foundry_app.config import settings

router = APIRouter(tags=["compaction"])


@router.post("/api/sessions/{session_id}/compact")
async def compact_session(session_id: str):
    db = await get_db()
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail={"error": {"code": "session_not_found"}})

    messages = await crud.list_messages(db, session_id)
    model_id = session.get("model_id", settings.default_model)
    history = load_history(messages)

    if not history:
        return {"status": "noop", "message": "No messages to compact"}

    async def noop_send(event: dict):
        pass

    await do_compaction(db, session_id, model_id, history, noop_send)

    return {"status": "ok", "session_id": session_id}
