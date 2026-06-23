from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

from var_app.chat.orchestrator import stream_chat
from var_app.shared_protocol import parse_command, to_dict, Pong
from var_app.session.history import load_history
from var_app.session.compaction import do_compaction
from var_app.agent import question as question_mod
from var_app.db.database import get_db
from var_app.db import crud
from var_app.config import settings
from var_app.logger import get_logger

logger = get_logger("api.ws")

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.debug("ws connected | session=%s", session_id)

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
            logger.debug("ws recv | session=%s type=%s", session_id, msg_type)

            if msg_type == "ping":
                await send_event(to_dict(Pong()))
                continue

            if msg_type == "chat.interrupt":
                if pending_task and not pending_task.done():
                    pending_task.cancel()
                    pending_task = None
                else:
                    await send_event({"type": "stream.done"})
                continue

            if msg_type == "chat.compact":
                async def do_compact():
                    db_conn = await get_db()
                    msgs = await crud.list_messages(db_conn, session_id)
                    sess = await crud.get_session(db_conn, session_id)
                    model_id = (sess or {}).get("model_id", settings.default_model)
                    history = load_history(msgs)
                    if history:
                        await do_compaction(db_conn, session_id, model_id, history, send_event)
                    else:
                        await send_event({"type": "compaction.done", "session_id": session_id, "summary_message_id": ""})

                asyncio.create_task(do_compact())
                continue

            if msg_type == "question.reply":
                qid = data.get("question_id", "")
                answers = data.get("answers", [])
                if qid and question_mod.resolve(qid, answers):
                    logger.debug("question reply resolved | session=%s id=%s", session_id, qid)
                else:
                    logger.warning("question reply ignored | session=%s id=%s", session_id, qid)
                continue

            if msg_type == "question.reject":
                qid = data.get("question_id", "")
                if qid and question_mod.reject(qid):
                    logger.debug("question rejected | session=%s id=%s", session_id, qid)
                else:
                    logger.warning("question reject ignored | session=%s id=%s", session_id, qid)
                continue

            if msg_type == "chat.message":
                content = data.get("content", "")
                model_id = data.get("model_id") or None
                if not content:
                    continue

                if pending_task and not pending_task.done():
                    pending_task.cancel()

                async def run_chat(content=content, model_id=model_id):
                    await stream_chat(session_id, content, send_event, model_id_override=model_id)

                pending_task = asyncio.create_task(run_chat())
                continue

    except WebSocketDisconnect:
        logger.debug("ws disconnected | session=%s", session_id)
    except Exception:
        pass
    finally:
        if pending_task and not pending_task.done():
            pending_task.cancel()
