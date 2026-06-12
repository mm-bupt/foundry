from fastapi import APIRouter, HTTPException

from foundry_app.db.database import get_db
from foundry_app.db import crud
from foundry_app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
    SessionDetailResponse,
    map_message,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=SessionListResponse)
async def list_sessions():
    db = await get_db()
    sessions = await crud.list_sessions(db)
    return SessionListResponse(sessions=[SessionResponse(**s) for s in sessions])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(body: SessionCreate):
    db = await get_db()
    session = await crud.create_session(db, title=body.title, model_id=body.model_id)
    return SessionResponse(**session)


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str):
    db = await get_db()
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "session_not_found",
                    "message": f"Session '{session_id}' not found",
                }
            },
        )
    messages = await crud.list_messages(db, session_id)
    mapped = []
    for m in messages:
        tc_list = await crud.list_tool_calls(db, m["id"])
        mapped.append(map_message(m, tc_list))
    return SessionDetailResponse(
        **session,
        messages=mapped,
    )


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, body: SessionUpdate):
    db = await get_db()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        session = await crud.get_session(db, session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "session_not_found",
                        "message": f"Session '{session_id}' not found",
                    }
                },
            )
        return SessionResponse(**session)
    session = await crud.update_session(db, session_id, **updates)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "session_not_found",
                    "message": f"Session '{session_id}' not found",
                }
            },
        )
    return SessionResponse(**session)


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str):
    db = await get_db()
    deleted = await crud.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "session_not_found",
                    "message": f"Session '{session_id}' not found",
                }
            },
        )
