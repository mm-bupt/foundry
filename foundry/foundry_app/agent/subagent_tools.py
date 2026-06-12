from __future__ import annotations

import asyncio
import time
from typing import Callable, Awaitable

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    PartStartEvent,
    PartDeltaEvent,
    TextPartDelta,
    ToolCallPartDelta,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
)
from pydantic_ai.agent import ModelRequestNode, CallToolsNode

from foundry_app.agent.deps import AgentDeps
from foundry_app.session.history import serialize_msg
from foundry_app.agent.subagent import (
    get_subagent,
    create_sub_agent,
    _MAX_NESTING_DEPTH,
)
from foundry_app.db import crud
from foundry_app.db.database import get_db
from foundry_app.logger import get_logger

logger = get_logger("agent.subagent_tools")


def register_task_tools(agent: Agent):
    @agent.tool
    async def task(
        ctx: RunContext[AgentDeps],
        description: str,
        prompt: str,
        subagent_type: str,
        task_id: str | None = None,
        background: bool = False,
    ) -> str:
        """Launch a new agent to handle complex, multistep tasks autonomously.

        When using the Task tool, you must specify a subagent_type parameter to select which agent type to use.

        When NOT to use the Task tool:
        - If you want to read a specific file path, use the read_file tool instead
        - If you are searching for a specific class definition like "class Foo", use the grep tool instead
        - If you are searching for code within a specific file or set of 2-3 files, use the read_file tool instead
        - If no available agent is a good fit for the task, use other tools directly

        Usage notes:
        1. Launch multiple agents concurrently whenever possible, to maximize performance; to do that, use a single message with multiple tool uses
        2. When the agent is done, it will return a single message back to you. The result returned by the agent is not visible to the user. To show the user the result, you should send a text message back to the user with a concise summary of the result. The output includes a task_id you can reuse later to continue the same subagent session.
        3. Each agent invocation starts with a fresh context unless you provide task_id to resume the same subagent session (which continues with its previous messages and tool outputs). When starting fresh, your prompt should contain a highly detailed task description for the agent to perform autonomously and you should specify exactly what information the agent should return back to you in its final and only message to you.
        4. The agent's outputs should generally be trusted
        5. Clearly tell the agent whether you expect it to write code or just to do research (search, file reads, web fetches, etc.), since it is not aware of the user's intent. Tell it how to verify its work if possible (e.g., relevant test commands).

        Available agent types and the tools they have access to:
        - explore: Fast agent specialized for exploring codebases. Tools: glob, grep, read_file, run_command (read-only).
        - general: General-purpose agent for researching complex questions and executing multi-step tasks. All tools.

        Args:
            description: A short (3-5 words) description of the task.
            prompt: The task for the agent to perform.
            subagent_type: The type of specialized agent to use for this task.
            task_id: Resume a previous subagent session (optional).
            background: Run the agent in the background. You will be notified when it completes.
        """
        if ctx.deps.is_subagent:
            return "Error: Task tool cannot be used inside a subagent."

        sub_def = get_subagent(subagent_type)
        if not sub_def:
            available = ", ".join(sorted(_list_subagent_names()))
            return f"Error: Unknown agent type '{subagent_type}'. Available: {available}"

        send_event = ctx.deps.send_event
        if not send_event:
            return "Error: No event sender available."

        db = await get_db()

        model_id = ctx.deps.model_id

        sub_session_id = task_id
        is_resume = False

        if sub_session_id:
            existing = await crud.get_session(db, sub_session_id)
            if existing:
                is_resume = True
            else:
                sub_session_id = None

        if not sub_session_id:
            sub_session = await crud.create_session(
                db,
                title=f"{description} (@{subagent_type} subagent)",
                model_id=model_id,
                parent_id=ctx.deps.session_id,
            )
            sub_session_id = sub_session["id"]

        task_record = await crud.create_task_record(
            db,
            parent_session_id=ctx.deps.session_id,
            subagent_type=subagent_type,
            description=description,
            background=background,
        )
        task_db_id = task_record["id"]

        await send_event({
            "type": "task.started",
            "task_id": sub_session_id,
            "subagent_type": subagent_type,
            "description": description,
            "background": background,
        })

        async def _run_subagent() -> tuple[str, str]:
            sub_agent = create_sub_agent(sub_def, model_id, ctx.deps.work_dir)
            sub_deps = AgentDeps(
                session_id=sub_session_id,
                model_id=model_id,
                work_dir=ctx.deps.work_dir,
                send_event=_make_subagent_event_sender(send_event, sub_session_id, subagent_type),
                is_subagent=True,
                parent_session_id=ctx.deps.session_id,
                task_id=sub_session_id,
            )

            messages = await crud.list_messages(db, sub_session_id)
            history = _load_history(messages[:-1] if is_resume else [])

            start_time = time.monotonic()
            full_text = ""
            assistant_id = None

            async def _ensure_assistant_id() -> str:
                nonlocal assistant_id
                if not assistant_id:
                    assistant_id = (
                        await crud.create_message(
                            db, sub_session_id, "assistant", "", model_id=model_id,
                        )
                    )["id"]
                return assistant_id

            try:
                async with sub_agent.iter(prompt, message_history=history, deps=sub_deps) as run:
                    async for node in run:
                        if isinstance(node, ModelRequestNode):
                            async with node.stream(run.ctx) as agent_stream:
                                async for event in agent_stream:
                                    if isinstance(event, PartStartEvent):
                                        part = event.part
                                        if isinstance(part, TextPart) and part.content:
                                            full_text += part.content
                                    elif isinstance(event, PartDeltaEvent):
                                        delta = event.delta
                                        if isinstance(delta, TextPartDelta):
                                            full_text += delta.content_delta

                        elif isinstance(node, CallToolsNode):
                            async with node.stream(run.ctx) as stream:
                                async for event in stream:
                                    if isinstance(event, FunctionToolCallEvent):
                                        await _ensure_assistant_id()
                                    elif isinstance(event, FunctionToolResultEvent):
                                        pass

                result = run.result
                if result and result.output and not full_text:
                    full_text = str(result.output)

                duration = int((time.monotonic() - start_time) * 1000)

                if not assistant_id and full_text:
                    assistant_id = (
                        await crud.create_message(
                            db, sub_session_id, "assistant", full_text, model_id=model_id,
                        )
                    )["id"]
                elif assistant_id and full_text:
                    await crud.update_message(db, assistant_id, content=full_text)

                return full_text, sub_session_id

            except asyncio.CancelledError:
                if full_text and not assistant_id:
                    await crud.create_message(
                        db, sub_session_id, "assistant", full_text, model_id=model_id,
                    )
                raise

        if background:
            async def _bg_run():
                try:
                    text, sid = await _run_subagent()
                    preview = text[:200] if text else ""
                    await crud.update_task_record(db, task_db_id, status="completed", result_preview=preview)
                    await send_event({
                        "type": "task.completed",
                        "task_id": sid,
                        "subagent_type": subagent_type,
                        "result_preview": preview,
                    })
                except asyncio.CancelledError:
                    await crud.update_task_record(db, task_db_id, status="cancelled")
                    await send_event({
                        "type": "task.error",
                        "task_id": sub_session_id,
                        "subagent_type": subagent_type,
                        "error": "Task was cancelled",
                    })
                except Exception as e:
                    logger.exception("background task error | task=%s", sub_session_id)
                    await crud.update_task_record(db, task_db_id, status="error")
                    await send_event({
                        "type": "task.error",
                        "task_id": sub_session_id,
                        "subagent_type": subagent_type,
                        "error": str(e),
                    })

            asyncio.create_task(_bg_run())

            return _background_output(sub_session_id)

        else:
            try:
                text, sid = await _run_subagent()
                preview = text[:200] if text else ""
                await crud.update_task_record(db, task_db_id, status="completed", result_preview=preview)
                await send_event({
                    "type": "task.completed",
                    "task_id": sid,
                    "subagent_type": subagent_type,
                    "result_preview": preview,
                })
                return _output(sid, text)
            except asyncio.CancelledError:
                await crud.update_task_record(db, task_db_id, status="cancelled")
                raise
            except Exception as e:
                logger.exception("task error | task=%s", sub_session_id)
                await crud.update_task_record(db, task_db_id, status="error")
                await send_event({
                    "type": "task.error",
                    "task_id": sub_session_id,
                    "subagent_type": subagent_type,
                    "error": str(e),
                })
                return f'<task id="{sub_session_id}" state="error">\n<task_error>{e}</task_error>\n</task>'


def _output(session_id: str, text: str) -> str:
    return (
        f'<task id="{session_id}" state="completed">\n'
        f"<task_result>\n{text}\n</task_result>\n"
        f"</task>"
    )


def _background_output(session_id: str) -> str:
    return (
        f'<task id="{session_id}" state="running">\n'
        f"<summary>Background task started</summary>\n"
        f"<task_result>\n"
        f"Background task started. You will be notified automatically when it finishes; do not poll for progress.\n"
        f"Do not duplicate its work. Continue only with non-overlapping work, or stop if there is nothing else useful to do.\n"
        f"</task_result>\n"
        f"</task>"
    )


def _make_subagent_event_sender(
    parent_send: Callable[[dict], Awaitable[None]],
    task_id: str,
    subagent_type: str,
) -> Callable[[dict], Awaitable[None]]:
    async def send_wrapped(event: dict):
        event_type = event.get("type", "")
        if event_type in ("tool.call", "tool.result", "stream.delta"):
            wrapped = {**event, "task_id": task_id, "subagent_type": subagent_type}
            await parent_send(wrapped)
    return send_wrapped


def _load_history(messages: list[dict]) -> list[ModelMessage]:
    from foundry_app.session.history import load_history
    return load_history(messages)


def _list_subagent_names() -> list[str]:
    from foundry_app.agent.subagent import SUBAGENTS
    return list(SUBAGENTS.keys())
