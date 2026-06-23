# Auto Session Title Generation

## Summary

Automatically generate concise session titles after the first user message, using a lightweight Title agent that runs asynchronously in the background without blocking the main chat flow.

## Architecture

**Approach**: Backend-triggered (Option A). After `stream_chat()` completes and emits `stream.done`, the backend checks whether the session title is still the default "New Chat". If so, it spawns an `asyncio.Task` to generate a title using a dedicated Title agent.

**Trigger conditions** (both must be true):
1. Session title equals `"New Chat"`
2. This is the first user message in the session (message count <= 1)

## Title Agent

**Module**: `var_app/agent/title.py`

- Uses the session's current model (same as main chat)
- No tools registered — pure text generation
- `max_tokens=80` to keep output short
- System prompt (~50 chars):

  > "Generate a concise title (<=10 words) for this conversation. Output only the title, nothing else. Use the same language as the user's message."

- Input: the first user message content
- Output: plain text title

## Data Flow

```
stream_chat() completes
  → emits stream.done
  → checks: title == "New Chat" && first message?
    → YES: asyncio.create_task(generate_title(session_id, model_id, user_message))
    → NO: do nothing

generate_title(session_id, model_id, first_message):
  → create_agent(model_id, TITLE_SYSTEM_PROMPT)  # no tools
  → agent.run(first_message) with max_tokens=80
  → extract title from response text
  → crud.update_session(db, session_id, title=title)
```

## Protocol Changes

### New Event: `session.title_updated`

```json
{
  "type": "session.title_updated",
  "session_id": "...",
  "title": "Generated Title Here"
}
```

**Delivery**: For now, the title is updated directly in the database. No WS push event is emitted — the frontend will see the updated title on next session list fetch. The `SessionTitleUpdated` dataclass is added to `shared_protocol.py` for future use.

## File Changes

| File | Change |
|------|--------|
| `var_app/agent/title.py` | **New**: `generate_title()` async function |
| `var_app/agent/core.py` | **Modified**: call title generation after `stream.done` |
| `var_app/shared_protocol.py` | **Modified**: add `SessionTitleUpdated` dataclass |

## Error Handling

- Title generation failure → silently ignore, no impact on chat
- API/network errors → silently ignore
- Empty or invalid title → don't update, keep "New Chat"
- All exceptions caught and logged to stderr

## Manual Title Protection

Only triggers when `title == "New Chat"`. Once a user manually sets a title (or auto-generation succeeds), it will never be overwritten.

## Design Decisions

1. **Use session's model** — avoids needing a separate model config; max_tokens=80 keeps cost minimal
2. **No WS push** — simpler implementation; frontend already fetches session list periodically
3. **asyncio.Task** — non-blocking; if the task fails, nothing is affected
4. **No tool registration** — the Title agent is purely generative, doesn't need memory or other tools
