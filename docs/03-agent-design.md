# 03 — Agent Design

## Pydantic AI Agent Architecture

### Agent Factory

The agent factory (`foundry/app/agent/core.py`) creates agents dynamically based on the active model and session context.

```python
from pydantic_ai import Agent

def create_agent(model_id: str, system_prompt: str = "") -> Agent:
    model_string = MODEL_REGISTRY[model_id]
    agent = Agent(
        model_string,
        instructions=system_prompt,
        tools=[store_memory, recall_memory, web_search],
        history_processors=[trim_and_summarize],
    )
    return agent
```

### Agent Instructions (System Prompt)

```
You are Dream Foundry AI, a helpful coding assistant.

You have access to long-term memory. Use `recall_memory` before responding
to check for relevant user preferences and past context. Use `store_memory`
when the user shares important information worth remembering (preferences,
project details, decisions made).

Be concise, direct, and helpful. Format code with markdown code blocks.
```

## Model Registry

### Supported Models

| ID | Provider | Model String | Context Window |
|----|----------|-------------|----------------|
| `gpt-4o` | OpenAI | `openai:gpt-4o` | 128K |
| `gpt-4o-mini` | OpenAI | `openai:gpt-4o-mini` | 128K |
| `claude-sonnet` | Anthropic | `anthropic:claude-sonnet-4-20250514` | 200K |
| `claude-haiku` | Anthropic | `anthropic:claude-haiku-4-20250414` | 200K |

### Model Registry Implementation

```python
# foundry/app/agent/registry.py

from dataclasses import dataclass

@dataclass
class ModelInfo:
    id: str
    name: str
    provider: str
    provider_prefix: str
    context_window: int
    max_output_tokens: int

MODEL_REGISTRY: dict[str, ModelInfo] = {
    "gpt-4o": ModelInfo(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        provider_prefix="openai:gpt-4o",
        context_window=128000,
        max_output_tokens=16384,
    ),
    "gpt-4o-mini": ModelInfo(...),
    "claude-sonnet": ModelInfo(...),
    "claude-haiku": ModelInfo(...),
}
```

### Runtime Model Switching

Each session stores its `model_id`. When the user switches models:

1. `PATCH /api/sessions/{id}` updates `model_id`
2. Next chat message creates a new agent with the new model
3. `message_history` is preserved (Pydantic AI handles model-agnostic history)
4. If provider doesn't support certain tools, they are silently excluded

## Agent Tools

### Memory Tools

```python
@agent.tool
async def store_memory(ctx: RunContext[SessionDeps], content: str, category: str) -> str:
    """Store important information to long-term memory.

    Args:
        content: The information to store.
        category: One of "preference", "fact", "decision", "project", "note".
    """
    embedding = await embed_text(content)
    await db.insert_memory(
        session_id=ctx.deps.session_id,
        content=content,
        category=category,
        embedding=embedding,
    )
    return f"Stored in memory (category: {category})."


@agent.tool
async def recall_memory(ctx: RunContext[SessionDeps], query: str, limit: int = 5) -> str:
    """Search long-term memory for relevant information.

    Args:
        query: The search query.
        limit: Max results to return (default 5).
    """
    embedding = await embed_text(query)
    results = await db.search_memory(
        session_id=ctx.deps.session_id,
        query_embedding=embedding,
        limit=limit,
    )
    if not results:
        return "No relevant memories found."
    return "\n".join(f"- [{r.category}] {r.content}" for r in results)
```

### Tool Icons (TUI Mapping)

| Tool | Icon | Style |
|------|------|-------|
| `recall_memory` | `✱` | InlineTool |
| `store_memory` | `←` | InlineTool |
| `web_search` | `◈` | InlineTool or BlockTool |
| Shell commands | `$` | BlockTool |
| Generic | `⚙` | InlineTool |

## Memory System

### Short-term Memory (Conversation History)

Managed by Pydantic AI's built-in `message_history`:

```python
# Per run, pass accumulated history
result = await agent.run(
    user_message,
    message_history=session.messages,  # List[ModelMessage]
    deps=session_deps,
)
# Store new messages back
session.messages = result.all_messages()
```

### Long-term Memory (Vector RAG)

**Storage**: `memory_vectors` table in SQLite with `sqlite-vec` extension.

**Embedding Model**: `text-embedding-3-small` (OpenAI) or configurable.

**Flow**:
1. Agent calls `store_memory` tool → embed text → insert into `memory_vectors`
2. Agent calls `recall_memory` tool → embed query → cosine similarity search → return top-k
3. Agent automatically uses recalled context in response

**Categories**:

| Category | Description | Example |
|----------|-------------|---------|
| `preference` | User preferences | "User prefers Chinese responses" |
| `fact` | Important facts | "Project uses Python 3.12" |
| `decision` | Design decisions | "Decided to use SQLite over Postgres" |
| `project` | Project details | "Working on dream-foundry, an AI agent" |
| `note` | General notes | "Deadline is next Friday" |

### Memory Summarization

A history processor that summarizes old conversation turns:

```python
async def summarize_old_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Keep recent messages, summarize old ones into a compact form."""
    if len(messages) <= 20:
        return messages

    recent = messages[-15:]
    old = messages[:-15]

    summary = await generate_summary(old)

    return [SystemMessage(f"[Conversation Summary]\n{summary}")] + recent
```

## Context Management

### History Processors Chain

```python
agent = Agent(
    model_string,
    history_processors=[
        trim_to_context_window,
        summarize_old_messages,
    ],
)
```

### Context Window Strategy

1. **Trim**: Remove oldest messages when approaching 80% of context window
2. **Summarize**: Generate a summary of removed messages and prepend as system message
3. **Priority**: Never remove system prompt or the last 15 messages

### Token Budget

```
┌─────────────────────────────────────────────────┐
│ Context Window (e.g., 128K tokens)              │
├──────────────┬──────────────────────────────────┤
│ System Prompt│  ~500 tokens                     │
│ Summary      │  ~1000 tokens (from old messages)│
│ Memories     │  ~500 tokens (recalled facts)    │
│ Recent Msgs  │  Remaining budget                │
│ Output       │  Reserved (max_output_tokens)    │
└──────────────┴──────────────────────────────────┘
```

## Streaming Architecture

### Pydantic AI Event Streaming

```python
async def stream_chat(session_id: str, message: str, send_event: Callable):
    agent = create_agent(session.model_id)
    async with agent.iter(message, message_history=session.history) as run:
        async for event in run.stream_events():
            match event:
                case PartDeltaEvent(delta=TextDelta(text=text)):
                    await send_event(StreamDelta(text=text))
                case FunctionToolCallEvent(tool_name=name, args=args):
                    await send_event(ToolCall(tool_name=name, args=args))
                case FunctionToolResultEvent(result=result):
                    await send_event(ToolResult(result=str(result)))
```

### WebSocket Integration

The WS endpoint wraps the streaming loop:

```python
@router.websocket("/ws/{session_id}")
async def ws_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()

    async def send_event(event: dict):
        await websocket.send_json(event)

    while True:
        data = await websocket.receive_json()
        if data["type"] == "chat.message":
            await stream_chat(session_id, data["content"], send_event)
        elif data["type"] == "chat.interrupt":
            # Cancel ongoing stream
            pass
```

## Dependencies (Deps Type)

```python
@dataclass
class SessionDeps:
    session_id: str
    model_id: str
    db: Database
```

Injected into every agent run via `deps=SessionDeps(...)` and accessed in tools via `ctx: RunContext[SessionDeps]`.
