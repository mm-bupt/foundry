import json
import time
from typing import Callable, Awaitable
from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from dream_foundry.agent.registry import get_provider_prefix, get_model_info
from dream_foundry.agent.context import trim_and_summarize
from dream_foundry.db import crud
from dream_foundry.db.database import get_db
from dream_foundry.config import settings


SYSTEM_PROMPT = """You are Dream Foundry AI, a helpful coding assistant.

You have access to long-term memory. Use `recall_memory` before responding \
to check for relevant user preferences and past context. Use `store_memory` \
when the user shares important information worth remembering (preferences, \
project details, decisions made).

Be concise, direct, and helpful. Format code with markdown code blocks.
Respond in the same language the user uses."""


@dataclass
class AgentDeps:
    session_id: str
    model_id: str
    send_event: Callable[[dict], Awaitable[None]] | None = None


def create_agent(model_id: str, system_prompt: str = "") -> Agent:
    model_info = get_model_info(model_id)
    model_string = get_provider_prefix(model_id)

    if model_info and model_info.api_base:
        api_key = model_info.api_key or _resolve_api_key(model_info.provider)
        model_obj = _create_model_client(
            model_string, model_info.provider, api_key, model_info.api_base
        )
        agent = Agent(
            model_obj,
            instructions=system_prompt or SYSTEM_PROMPT,
            deps_type=AgentDeps,
            history_processors=[trim_and_summarize],
        )
    else:
        agent = Agent(
            model_string,
            instructions=system_prompt or SYSTEM_PROMPT,
            deps_type=AgentDeps,
            history_processors=[trim_and_summarize],
        )
    _register_tools(agent)
    return agent


def _resolve_api_key(provider: str) -> str:
    if provider == "openai":
        return settings.openai_api_key
    elif provider == "anthropic":
        return settings.anthropic_api_key
    return ""


def _create_model_client(model_string: str, provider: str, api_key: str, base_url: str):
    if provider == "anthropic":
        try:
            from pydantic_ai.models.anthropic import AnthropicModel
            import anthropic

            client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
            return AnthropicModel(anthropic_client=client)
        except Exception:
            return model_string
    else:
        try:
            from pydantic_ai.models.openai import OpenAIModel
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=base_url)
            return OpenAIModel(openai_client=client)
        except Exception:
            return model_string


def _register_tools(agent: Agent):
    from dream_foundry.agent.tools import register_memory_tools

    register_memory_tools(agent)


async def stream_chat(
    session_id: str,
    user_message: str,
    send_event: Callable[[dict], Awaitable[None]],
):
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

    model_id = session["model_id"]
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
    history = _load_history(messages[:-1])

    agent = create_agent(model_id, session.get("system_prompt", ""))
    deps = AgentDeps(session_id=session_id, model_id=model_id, send_event=send_event)

    start_time = time.monotonic()
    assistant_id = None
    full_text = ""
    input_tokens = 0
    output_tokens = 0
    pending_tool_calls: dict[str, dict] = {}

    try:
        async with agent.iter(user_message, message_history=history, deps=deps) as run:
            async for node in run:
                if isinstance(node, ModelRequest):
                    pass

                elif isinstance(node, ModelResponse):
                    for part in node.parts:
                        if isinstance(part, TextPart):
                            full_text = part.content
                            if not assistant_id:
                                assistant_id = (
                                    await crud.create_message(
                                        db,
                                        session_id,
                                        "assistant",
                                        "",
                                        model_id=model_id,
                                    )
                                )["id"]
                            await send_event(
                                {
                                    "type": "stream.delta",
                                    "message_id": user_msg["id"],
                                    "part_id": assistant_id,
                                    "text": part.content,
                                }
                            )
                        elif isinstance(part, ToolCallPart):
                            tc_id = part.tool_call_id or ""
                            tool_name = part.tool_name
                            args = (
                                part.args_as_dict()
                                if hasattr(part, "args_as_dict")
                                else (part.args if isinstance(part.args, dict) else {})
                            )
                            pending_tool_calls[tc_id] = {"tool_name": tool_name}
                            await send_event(
                                {
                                    "type": "tool.call",
                                    "tool_call_id": tc_id,
                                    "tool_name": tool_name,
                                    "args": args,
                                }
                            )

                elif isinstance(node, ModelRequest):
                    for part in node.parts:
                        if isinstance(part, ToolReturnPart):
                            tc_id = part.tool_call_id or ""
                            meta = pending_tool_calls.pop(tc_id, {})
                            await send_event(
                                {
                                    "type": "tool.result",
                                    "tool_call_id": tc_id,
                                    "tool_name": meta.get("tool_name", ""),
                                    "result": str(part.content),
                                }
                            )

        result = run.result
        if result:
            if not full_text and result.output:
                full_text = str(result.output)
                if not assistant_id:
                    assistant_id = (
                        await crud.create_message(
                            db, session_id, "assistant", full_text, model_id=model_id
                        )
                    )["id"]
                else:
                    await crud.update_message(db, assistant_id, content=full_text)

            usage = result.usage()
            if usage:
                input_tokens = usage.input_tokens
                output_tokens = usage.output_tokens

            all_msgs = result.all_messages()
            if assistant_id:
                await crud.update_message(
                    db,
                    assistant_id,
                    content=full_text,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ms=int((time.monotonic() - start_time) * 1000),
                    model_messages_json=json.dumps(
                        [_serialize_msg(m) for m in all_msgs], default=str
                    ),
                )

        duration = int((time.monotonic() - start_time) * 1000)
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

    except Exception as e:
        await send_event(
            {
                "type": "stream.error",
                "message_id": user_msg["id"],
                "error": {"code": "internal_error", "message": str(e)},
            }
        )


def _serialize_msg(msg):
    if hasattr(msg, "model_dump"):
        return msg.model_dump()
    return str(msg)


def _load_history(messages: list[dict]) -> list[ModelMessage]:
    if not messages:
        return []
    for msg in reversed(messages):
        raw = msg.get("model_messages_json", "[]")
        if raw and raw != "[]":
            try:
                data = json.loads(raw)
                result = []
                for m in data:
                    try:
                        result.append(ModelMessage.model_validate(m))
                    except Exception:
                        pass
                if result:
                    return result
            except Exception:
                pass
    return []
