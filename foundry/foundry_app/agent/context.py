from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    UserPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
)

from foundry_app.agent.registry import estimate_tokens


async def trim_and_summarize(messages: list[ModelMessage]) -> list[ModelMessage]:
    if len(messages) <= 10:
        return messages

    total_tokens = sum(_count_msg_tokens(m) for m in messages)

    if total_tokens < 40000:
        return messages

    recent_keep = 15
    recent = messages[-recent_keep:]
    old = messages[:-recent_keep]

    summary = await _generate_summary(old)

    summary_part = SystemPromptPart(content=f"[Conversation Summary]\n{summary}")
    summary_msg = ModelRequest(parts=[summary_part])

    return [summary_msg] + recent


def _count_msg_tokens(msg: ModelMessage) -> int:
    total = 0
    if isinstance(msg, ModelRequest):
        for part in msg.parts:
            if isinstance(part, UserPromptPart):
                content = part.content
                if isinstance(content, str):
                    total += estimate_tokens(content)
                elif isinstance(content, list):
                    total += estimate_tokens(" ".join(str(c) for c in content))
    elif isinstance(msg, ModelResponse):
        for part in msg.parts:
            if isinstance(part, TextPart):
                total += estimate_tokens(part.content)
    return total


async def _generate_summary(messages: list[ModelMessage]) -> str:
    text = _build_compact_summary(messages)
    if not text:
        return "Previous conversation occurred."

    try:
        from foundry_app.config import settings

        agent = Agent(
            settings.summary_model,
            instructions="Summarize concisely. Preserve key decisions, preferences, and technical details. Use bullet points.",
        )
        result = await agent.run(
            f"Summarize this conversation in under 300 words:\n\n{text}"
        )
        return str(result.output)
    except Exception:
        return text[:2000]


def _build_compact_summary(messages: list[ModelMessage]) -> str:
    lines = []
    for msg in messages:
        try:
            if isinstance(msg, ModelRequest):
                for part in msg.parts:
                    if isinstance(part, UserPromptPart):
                        content = part.content
                        if isinstance(content, str):
                            text = content[:300]
                        elif isinstance(content, list):
                            text = " ".join(str(c)[:150] for c in content)[:300]
                        else:
                            text = str(content)[:300]
                        lines.append(f"User: {text}")
            elif isinstance(msg, ModelResponse):
                for part in msg.parts:
                    if isinstance(part, TextPart):
                        lines.append(f"Assistant: {part.content[:300]}")
                    elif isinstance(part, ToolCallPart):
                        lines.append(f"Tool call: {part.tool_name}")
                    elif isinstance(part, ToolReturnPart):
                        lines.append(f"Tool result: {str(part.content)[:150]}")
        except Exception:
            pass

    if not lines:
        return ""

    return "\n".join(lines)
