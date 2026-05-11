from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import time

from dream_foundry.agent.core import stream_chat
from dream_foundry.shared_protocol import parse_command, to_dict, Pong

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()

    pending_task: asyncio.Task | None = None

    async def send_event(event: dict):
        try:
            await websocket.send_json(event)
        except Exception:
            pass

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=60)
            except asyncio.TimeoutError:
                await send_event(to_dict(Pong()))
                continue

            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await send_event(to_dict(Pong()))
                continue

            if msg_type == "chat.interrupt":
                if pending_task and not pending_task.done():
                    pending_task.cancel()
                    pending_task = None
                continue

            if msg_type == "chat.message":
                content = data.get("content", "")
                if not content:
                    continue

                if pending_task and not pending_task.done():
                    pending_task.cancel()

                async def run_chat(content=content):
                    await stream_chat(session_id, content, send_event)

                pending_task = asyncio.create_task(run_chat())
                continue

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if pending_task and not pending_task.done():
            pending_task.cancel()
