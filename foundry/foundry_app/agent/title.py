import sys
from typing import Callable, Awaitable

from pydantic_ai import Agent

from foundry_app.agent.core import _resolve_api_key, _create_model_client
from foundry_app.agent.registry import get_model_info, get_provider_prefix
from foundry_app.db import crud
from foundry_app.db.database import get_db
from foundry_app.logger import get_logger

logger = get_logger("agent.title")

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
        logger.debug("generate_title start | session=%s model=%s", session_id, model_id)
        agent = _create_title_agent(model_id)
        logger.debug("generate_title agent created, calling run...")
        result = await agent.run(first_message)
        logger.debug("generate_title agent.run done | output=%s", repr(result.output)[:100])
        title = result.output.strip() if result.output else ""
        if not title:
            logger.debug("generate_title empty title, skipping")
            return
        db = await get_db()
        session = await crud.get_session(db, session_id)
        if not session:
            logger.debug("generate_title session not found")
            return
        if session["title"] != "New Chat":
            logger.debug("generate_title title already set: %s", session["title"])
            return
        await crud.update_session(db, session_id, title=title)
        logger.debug("generate_title updated | title=%s", title)
        if send_event:
            await send_event(
                {
                    "type": "session.title_updated",
                    "session_id": session_id,
                    "title": title,
                }
            )
            logger.debug("generate_title event sent")
    except Exception as e:
        logger.exception("generate_title failed | session=%s error=%s", session_id, e)
