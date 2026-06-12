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
    ThinkingPart,
)

from foundry_app.agent.registry import estimate_tokens, get_provider_prefix
from foundry_app.agent.overflow import usable_tokens
from foundry_app.config import settings
from foundry_app.logger import get_logger

logger = get_logger("agent.compaction")

PRUNE_MINIMUM = 20_000
PRUNE_PROTECT = 40_000
PRUNE_PROTECTED_TOOLS = ["skill"]
TOOL_OUTPUT_MAX_CHARS = 2_000
DEFAULT_TAIL_TURNS = 2
MIN_PRESERVE_TOKENS = 2_000
MAX_PRESERVE_TOKENS = 8_000
COMPACT_SUMMARY_MAX_CHARS = 300
COMPACT_TOOL_RESULT_MAX_CHARS = 150
PRUNE_PLACEHOLDER = "[Old tool result content cleared]"

SUMMARY_TEMPLATE = """## Goal
[Single-sentence task summary]

## Constraints & Preferences
[User constraints and preferences]

## Progress
### Done
- [Completed items]

### In Progress
- [Items currently being worked on]

### Blocked
- [Blocked items]

## Key Decisions
- [Decision + reasoning]

## Next Steps
1. [Next actions in order]

## Critical Context
[Technical facts, error messages, open questions]

## Relevant Files
- path/to/file — [Why it matters]
"""


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
            elif isinstance(part, ToolCallPart):
                total += estimate_tokens(part.tool_name)
                total += estimate_tokens(str(part.args))
            elif isinstance(part, ToolReturnPart):
                total += estimate_tokens(str(part.content))
            elif isinstance(part, ThinkingPart):
                total += estimate_tokens(part.content or "")
    return total


def _turns(messages: list[ModelMessage]) -> list[dict]:
    turns = []
    for i, msg in enumerate(messages):
        if isinstance(msg, ModelRequest):
            has_user_text = any(
                isinstance(p, UserPromptPart) for p in msg.parts
            )
            if has_user_text:
                turns.append({"start": i, "end": len(messages)})
    for j in range(len(turns) - 1):
        turns[j]["end"] = turns[j + 1]["start"]
    return turns


def _split_turn(
    messages: list[ModelMessage], turn: dict, budget: int
) -> dict | None:
    if budget <= 0 or turn["end"] - turn["start"] <= 1:
        return None
    for start in range(turn["start"] + 1, turn["end"]):
        size = sum(_count_msg_tokens(m) for m in messages[start : turn["end"]])
        if size <= budget:
            return {"start": start}
    return None


def _preserve_recent_budget(model_id: str) -> int:
    usable = usable_tokens(model_id)
    budget = int(usable * 0.25)
    return max(MIN_PRESERVE_TOKENS, min(budget, MAX_PRESERVE_TOKENS))


def select(
    messages: list[ModelMessage], model_id: str
) -> tuple[list[ModelMessage], int | None]:
    tail_turns = settings.compaction_tail_turns
    if tail_turns <= 0:
        return messages, None

    budget = _preserve_recent_budget(model_id)
    all_turns = _turns(messages)
    if not all_turns:
        return messages, None

    recent = all_turns[-tail_turns:]
    sizes = []
    for t in recent:
        size = sum(_count_msg_tokens(m) for m in messages[t["start"] : t["end"]])
        sizes.append(size)

    total = 0
    keep = None
    for i in range(len(recent) - 1, -1, -1):
        if total + sizes[i] <= budget:
            total += sizes[i]
            keep = recent[i]
        else:
            remaining = budget - total
            split = _split_turn(messages, recent[i], remaining)
            if split:
                keep = split
            elif keep is None:
                logger.warning(
                    "compaction select: cannot fit any recent turn in budget=%d, keeping last turn",
                    budget,
                )
                keep = recent[-1]
            break

    if keep is None or keep["start"] == 0:
        return messages, None

    head = messages[: keep["start"]]
    return head, keep["start"]


def _build_compact_summary(
    messages: list[ModelMessage], tool_max: int = COMPACT_TOOL_RESULT_MAX_CHARS
) -> str:
    lines = []
    for msg in messages:
        try:
            if isinstance(msg, ModelRequest):
                for part in msg.parts:
                    if isinstance(part, UserPromptPart):
                        content = part.content
                        if isinstance(content, str):
                            text = content[:COMPACT_SUMMARY_MAX_CHARS]
                        elif isinstance(content, list):
                            text = " ".join(str(c)[:150] for c in content)[
                                :COMPACT_SUMMARY_MAX_CHARS
                            ]
                        else:
                            text = str(content)[:COMPACT_SUMMARY_MAX_CHARS]
                        lines.append(f"User: {text}")
            elif isinstance(msg, ModelResponse):
                for part in msg.parts:
                    if isinstance(part, TextPart):
                        lines.append(
                            f"Assistant: {part.content[:COMPACT_SUMMARY_MAX_CHARS]}"
                        )
                    elif isinstance(part, ToolCallPart):
                        args_str = str(part.args)[:tool_max]
                        lines.append(f"Tool call: {part.tool_name}({args_str})")
                    elif isinstance(part, ToolReturnPart):
                        content_str = str(part.content)[:tool_max]
                        lines.append(f"Tool result: {content_str}")
        except Exception:
            pass
    return "\n".join(lines)


def _build_prompt(previous_summary: str | None) -> str:
    if previous_summary:
        return (
            "Update the anchored summary below using the conversation history above. "
            "Preserve still-true details, remove stale details, and merge in the new facts.\n\n"
            f"<previous-summary>\n{previous_summary}\n</previous-summary>\n\n"
            "Produce an updated summary following this template:\n"
            + SUMMARY_TEMPLATE
        )
    return (
        "Create a new anchored summary from the conversation history above.\n\n"
        "Follow this template:\n"
        + SUMMARY_TEMPLATE
    )


async def _generate_summary(
    messages: list[ModelMessage],
    model_id: str,
    previous_summary: str | None = None,
) -> str:
    text = _build_compact_summary(messages, tool_max=TOOL_OUTPUT_MAX_CHARS)
    if not text.strip():
        return "Previous conversation occurred."

    model_string = get_provider_prefix(model_id)
    prompt = _build_prompt(previous_summary)

    try:
        agent = Agent(
            model_string,
            instructions="Summarize concisely. Preserve key decisions, preferences, technical details, file paths, and error messages. Keep every section even if empty.",
        )
        result = await agent.run(f"{prompt}\n\n{text}")
        return str(result.output)
    except Exception:
        logger.exception("compaction summary generation failed")
        return text[:2000] if text else "Previous conversation occurred."


def filter_compacted(messages: list[ModelMessage]) -> list[ModelMessage]:
    summary_idx = None
    for i, msg in enumerate(messages):
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if (
                    isinstance(part, SystemPromptPart)
                    and part.content.startswith("[Conversation Summary]\n")
                ):
                    summary_idx = i

    if summary_idx is not None and summary_idx > 0:
        return messages[summary_idx:]

    return messages


async def process_compaction(
    messages: list[ModelMessage],
    model_id: str,
    previous_summary: str | None = None,
) -> str:
    head, tail_start = select(messages, model_id)

    if tail_start is None:
        logger.info("compaction: no tail split possible, summarizing all")
        head = messages

    summary = await _generate_summary(head, model_id, previous_summary)
    return summary


async def prune(messages: list[ModelMessage]) -> list[ModelMessage]:
    if not settings.compaction_prune:
        return messages

    total = 0
    to_prune = []
    turns = 0

    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if isinstance(msg, ModelRequest):
            turns += 1
        if turns < 2:
            continue

        if isinstance(msg, ModelResponse):
            for j, part in enumerate(msg.parts):
                if not isinstance(part, ToolReturnPart):
                    continue
                tool_name = getattr(part, "tool_name", "")
                if tool_name in PRUNE_PROTECTED_TOOLS:
                    continue

                part_tokens = estimate_tokens(str(part.content))
                total += part_tokens
                if total > PRUNE_PROTECT:
                    to_prune.append((i, j))

    if not to_prune or total - PRUNE_PROTECT < PRUNE_MINIMUM:
        return messages

    result = []
    prune_set = {(i, j) for i, j in to_prune}
    for i, msg in enumerate(messages):
        if isinstance(msg, ModelResponse) and any(pi == i for pi, _ in prune_set):
            new_parts = []
            for j, part in enumerate(msg.parts):
                if (i, j) in prune_set:
                    new_parts.append(
                        ToolReturnPart(
                            content=PRUNE_PLACEHOLDER,
                            tool_call_id=part.tool_call_id,
                        )
                    )
                else:
                    new_parts.append(part)
            result.append(ModelResponse(parts=new_parts))
        else:
            result.append(msg)

    logger.info("prune: replaced %d tool outputs with placeholder", len(to_prune))
    return result
