from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

from foundry_app.chat.orchestrator import stream_chat
from foundry_app.db.database import get_db
from foundry_app.db import crud
from foundry_app.shared_protocol import to_dict

router = APIRouter()


@router.get("/api/chat/{session_id}/stream")
async def sse_stream(session_id: str, request: Request):
    event_queue: asyncio.Queue = asyncio.Queue()

    async def enqueue(event: dict):
        await event_queue.put(event)

    async def event_generator():
        yield {"event": "connected", "data": json.dumps({"session_id": session_id})}

        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=15)
                yield {
                    "event": event.get("type", "message"),
                    "data": json.dumps(event),
                }
            except asyncio.TimeoutError:
                yield {"event": "keepalive", "data": ""}

    return EventSourceResponse(event_generator())


async def handle_sse_chat(session_id: str, content: str, event_queue: asyncio.Queue):
    async def send_event(event: dict):
        await event_queue.put(event)

    await stream_chat(session_id, content, send_event)
