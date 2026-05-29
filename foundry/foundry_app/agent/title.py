import sys
from typing import Callable, Awaitable

from pydantic_ai import Agent

from foundry_app.agent.core import _resolve_api_key, _create_model_client
from foundry_app.agent.registry import get_model_info, get_provider_prefix
from foundry_app.db import crud
from foundry_app.db.database import get_db

TITLE_SYSTEM_PROMPT = (
    "Generate a concise title (<=10 words) for this conversation. "
    "Output only the title, nothing else. "
    "Use the same language as the user's message."
)


def _create_title_agent(model_id: str) -> Agent:
    model_info = get_model_info(model_id)
    model_string = get_provider_prefix(model_id)

    if model_info and model_info.api_base:
        api_key = model_info.api_key or _resolve_api_key(model_info.provider)
        model_obj = _create_model_client(
            model_string, model_info.provider, api_key, model_info.api_base
        )
        return Agent(
            model_obj,
            instructions=TITLE_SYSTEM_PROMPT,
            model_settings={"max_tokens": 80},
        )
    return Agent(
        model_string,
        instructions=TITLE_SYSTEM_PROMPT,
        model_settings={"max_tokens": 80},
    )


async def generate_title(
    session_id: str,
    model_id: str,
    first_message: str,
    send_event: "Callable[[dict], Awaitable[None]] | None" = None,
) -> None:
    try:
        agent = _create_title_agent(model_id)
        result = await agent.run(first_message)
        title = result.output.strip() if result.output else ""
        if not title:
            return
        db = await get_db()
        session = await crud.get_session(db, session_id)
        if not session:
            return
        if session["title"] != "New Chat":
            return
        await crud.update_session(db, session_id, title=title)
        if send_event:
            await send_event(
                {
                    "type": "session.title_updated",
                    "session_id": session_id,
                    "title": title,
                }
            )
    except Exception as e:
        print(f"[generate_title] failed: {e}", file=sys.stderr, flush=True)
