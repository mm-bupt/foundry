import asyncio
import json
import time
from typing import Callable, Awaitable

from pydantic_ai.messages import (
    ModelMessage,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
    ThinkingPart,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
    PartStartEvent,
    PartDeltaEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
)
from pydantic_ai.agent import ModelRequestNode, CallToolsNode

from foundry_app.agent.factory import create_agent
from foundry_app.agent.deps import AgentDeps
from foundry_app.model.registry import get_model_info
from foundry_app.session.history import load_history, serialize_msg
from foundry_app.session.compaction import is_overflow, prune as compaction_prune, do_compaction
from foundry_app.db import crud
from foundry_app.db.database import get_db
from foundry_app.config import settings
from foundry_app.logger import get_logger

logger = get_logger("chat.orchestrator")


async def stream_chat(
    session_id: str,
    user_message: str,
    send_event: Callable[[dict], Awaitable[None]],
    model_id_override: str | None = None,
):
    logger.debug("stream_chat start | session=%s msg_len=%d", session_id, len(user_message))
    db = await get_db()
    session = await crud.get_session(db, session_id)
    if not session:
        await send_event(
            {
                "type": "stream.error",
                "error": {
                    "code": "session_not_found",
                    "message": f"Session '{session_id}' not found",
                },
            }
        )
        return

    model_id = model_id_override or session["model_id"]
    logger.debug("resolved model: %s", model_id)
    model_info = get_model_info(model_id)
    if not model_info:
        await send_event(
            {
                "type": "stream.error",
                "error": {
                    "code": "model_not_available",
                    "message": f"Model '{model_id}' not found",
                },
            }
        )
        return

    user_msg = await crud.create_message(db, session_id, "user", user_message)

    messages = await crud.list_messages(db, session_id)
    history = load_history(messages[:-1])

    agent = create_agent(model_id, session.get("system_prompt", ""))
    deps = AgentDeps(
        session_id=session_id,
        model_id=model_id,
        work_dir=str(settings.work_dir),
        send_event=send_event,
    )

    start_time = time.monotonic()
    assistant_id = None
    full_text = ""
    thinking_text = ""
    input_tokens = 0
    output_tokens = 0
    pending_tool_calls: dict[str, dict] = {}

    async def _ensure_assistant_id() -> str:
        nonlocal assistant_id
        if not assistant_id:
            assistant_id = (
                await crud.create_message(
                    db, session_id, "assistant", "", model_id=model_id,
                )
            )["id"]
        return assistant_id

    try:
        async with agent.iter(user_message, message_history=history, deps=deps) as run:
            async for node in run:
                if isinstance(node, ModelRequestNode):
                    async with node.stream(run.ctx) as agent_stream:
                        async for event in agent_stream:
                            if isinstance(event, PartStartEvent):
                                part = event.part
                                if isinstance(part, ThinkingPart):
                                    await send_event(
                                        {
                                            "type": "thinking.start",
                                            "message_id": user_msg["id"],
                                        }
                                    )
                                    if part.content:
                                        thinking_text += part.content
                                        await send_event(
                                            {
                                                "type": "thinking.delta",
                                                "message_id": user_msg["id"],
                                                "text": part.content,
                                        }
                                    )
                                    logger.debug("thinking.start | session=%s", session_id)
                                elif isinstance(part, TextPart):
                                    await _ensure_assistant_id()
                                    logger.debug("text.start | session=%s assistant_id=%s", session_id, assistant_id)
                                    if thinking_text:
                                        await send_event(
                                            {
                                                "type": "thinking.end",
                                                "message_id": user_msg["id"],
                                            }
                                        )
                                    if part.content:
                                        full_text += part.content
                                        await send_event(
                                            {
                                                "type": "stream.delta",
                                                "message_id": user_msg["id"],
                                                "part_id": assistant_id or "",
                                                "text": part.content,
                                            }
                                        )
                                elif isinstance(part, ToolCallPart):
                                    await _ensure_assistant_id()
                                    tc_id = part.tool_call_id or ""
                                    tool_name = part.tool_name
                                    pending_tool_calls[tc_id] = {
                                        "tool_name": tool_name,
                                        "args_json": part.args if isinstance(part.args, str) else "",
                                    }
                            elif isinstance(event, PartDeltaEvent):
                                delta = event.delta
                                if isinstance(delta, TextPartDelta):
                                    full_text += delta.content_delta
                                    await send_event(
                                        {
                                            "type": "stream.delta",
                                            "message_id": user_msg["id"],
                                            "part_id": assistant_id or "",
                                            "text": delta.content_delta,
                                        }
                                    )
                                elif isinstance(delta, ThinkingPartDelta):
                                    if delta.content_delta:
                                        thinking_text += delta.content_delta
                                        await send_event(
                                            {
                                                "type": "thinking.delta",
                                                "message_id": user_msg["id"],
                                                "text": delta.content_delta,
                                            }
                                        )
                                elif isinstance(delta, ToolCallPartDelta):
                                    if delta.tool_call_id and delta.tool_call_id in pending_tool_calls:
                                        pending_tool_calls[delta.tool_call_id]["args_json"] += delta.args_delta or ""

                elif isinstance(node, CallToolsNode):
                    async with node.stream(run.ctx) as stream:
                        async for event in stream:
                            if isinstance(event, FunctionToolCallEvent):
                                tc_part = event.part
                                tc_id = tc_part.tool_call_id or ""
                                tool_name = tc_part.tool_name
                                args = tc_part.args_as_dict() if hasattr(tc_part, "args_as_dict") else {}
                                if tc_id not in pending_tool_calls:
                                    pending_tool_calls[tc_id] = {"tool_name": tool_name}
                                await _ensure_assistant_id()
                                tc_record = await crud.create_tool_call(
                                        db, assistant_id, tool_name,
                                        args_json=json.dumps(args, ensure_ascii=False),
                                    )
                                pending_tool_calls[tc_id]["db_id"] = tc_record["id"]
                                await send_event(
                                    {
                                        "type": "tool.call",
                                        "tool_call_id": tc_id,
                                        "tool_name": tool_name,
                                        "args": args,
                                    }
                                )
                                logger.debug("tool.call | session=%s tool=%s args=%s", session_id, tool_name, json.dumps(args, ensure_ascii=False)[:500])
                            elif isinstance(event, FunctionToolResultEvent):
                                result_part = event.result
                                if isinstance(result_part, ToolReturnPart):
                                    tc_id = result_part.tool_call_id or ""
                                    meta = pending_tool_calls.pop(tc_id, {})
                                    result_text = str(result_part.content)
                                    db_id = meta.get("db_id")
                                    if db_id:
                                        await crud.update_tool_call(
                                            db, db_id,
                                            result=result_text,
                                            status="done",
                                        )
                                    logger.debug("tool.result | session=%s tool=%s result_len=%d preview=%s", session_id, meta.get("tool_name", ""), len(result_text), result_text[:200])
                                    await send_event(
                                        {
                                            "type": "tool.result",
                                            "tool_call_id": tc_id,
                                            "tool_name": meta.get(
                                                "tool_name", ""
                                            ),
                                            "result": result_text,
                                        }
                                    )
                                    logger.debug("tool.result | session=%s tool=%s result_len=%d", session_id, meta.get("tool_name", ""), len(str(result_part.content)))

        result = run.result
        if result:
            if not full_text and result.output:
                full_text = str(result.output)
                if not assistant_id:
                    assistant_id = (
                        await crud.create_message(
                            db,
                            session_id,
                            "assistant",
                            full_text,
                            model_id=model_id,
                        )
                    )["id"]
                else:
                    await crud.update_message(db, assistant_id, content=full_text)

            usage = result.usage
            if usage:
                input_tokens = usage.request_tokens or 0
                output_tokens = usage.response_tokens or 0

            all_msgs = result.all_messages()

            total_tokens_used = input_tokens + output_tokens
            if is_overflow(model_id, total_tokens_used):
                logger.info(
                    "overflow detected | model=%s tokens=%d, triggering compaction",
                    model_id,
                    total_tokens_used,
                )
                await do_compaction(db, session_id, model_id, all_msgs, send_event)

            if assistant_id:
                msgs_to_store = all_msgs
                try:
                    msgs_to_store = await compaction_prune(all_msgs)
                except Exception:
                    logger.exception("prune failed | session=%s", session_id)
                await crud.update_message(
                    db,
                    assistant_id,
                    content=full_text,
                    thinking_content=thinking_text,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ms=int((time.monotonic() - start_time) * 1000),
                    model_messages_json=json.dumps(
                        [serialize_msg(m) for m in msgs_to_store], default=str
                    ),
                )

        duration = int((time.monotonic() - start_time) * 1000)
        logger.debug("stream.done | session=%s duration=%dms tokens=%d+%d text_len=%d", session_id, duration, input_tokens, output_tokens, len(full_text))
        await send_event(
            {
                "type": "stream.done",
                "message_id": user_msg["id"],
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                },
                "duration_ms": duration,
            }
        )

        if (
            session.get("title") == "New Chat"
            and len(messages) <= 1
        ):
            from foundry_app.chat.title import generate_title

            asyncio.create_task(
                generate_title(session_id, model_id, user_message, send_event)
            )

    except asyncio.CancelledError:
        try:
            duration = int((time.monotonic() - start_time) * 1000)
            if full_text and not assistant_id:
                assistant_id = (
                    await crud.create_message(
                        db, session_id, "assistant", full_text,
                        model_id=model_id,
                    )
                )["id"]
            if assistant_id:
                await crud.update_message(
                    db, assistant_id,
                    content=full_text,
                    thinking_content=thinking_text,
                    duration_ms=duration,
                )
            logger.debug("stream cancelled | session=%s text_len=%d duration=%dms", session_id, len(full_text), duration)
            await send_event(
                {
                    "type": "stream.done",
                    "message_id": user_msg["id"],
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                    },
                    "duration_ms": duration,
                }
            )
        except Exception:
            logger.exception("cancelled cleanup failed | session=%s", session_id)
        raise

    except Exception as e:
        logger.exception("stream_chat error | session=%s error=%s", session_id, e)
        await send_event(
            {
                "type": "stream.error",
                "message_id": user_msg["id"],
                "error": {"code": "internal_error", "message": str(e)},
            }
        )
