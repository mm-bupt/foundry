from pydantic_ai import ModelMessage


async def trim_to_recent(
    messages: list[ModelMessage], max_messages: int = 30
) -> list[ModelMessage]:
    if len(messages) <= max_messages:
        return messages
    return messages[-max_messages:]


async def trim_and_summarize(messages: list[ModelMessage]) -> list[ModelMessage]:
    if len(messages) <= 25:
        return messages

    recent = messages[-15:]
    old = messages[:-15]

    summary = _build_compact_summary(old)

    from pydantic_ai.messages import ModelRequest, SystemPromptPart

    summary_part = SystemPromptPart(content=f"[Conversation Summary]\n{summary}")
    summary_msg = ModelRequest(parts=[summary_part])

    return [summary_msg] + recent


def _build_compact_summary(messages: list[ModelMessage]) -> str:
    lines = []
    for msg in messages:
        try:
            from pydantic_ai.messages import (
                ModelRequest,
                ModelResponse,
                UserPromptPart,
                TextPart,
                ToolCallPart,
                ToolReturnPart,
            )

            if isinstance(msg, ModelRequest):
                for part in msg.parts:
                    if isinstance(part, UserPromptPart):
                        content = part.content
                        if isinstance(content, str):
                            text = content[:200]
                        elif isinstance(content, list):
                            text = " ".join(str(c)[:100] for c in content)[:200]
                        else:
                            text = str(content)[:200]
                        lines.append(f"User: {text}")
            elif isinstance(msg, ModelResponse):
                for part in msg.parts:
                    if isinstance(part, TextPart):
                        lines.append(f"Assistant: {part.content[:200]}")
                    elif isinstance(part, ToolCallPart):
                        lines.append(f"Tool call: {part.tool_name}")
                    elif isinstance(part, ToolReturnPart):
                        lines.append(f"Tool result: {str(part.content)[:100]}")
        except Exception:
            pass

    if not lines:
        return "Previous conversation occurred."

    return "\n".join(lines)
