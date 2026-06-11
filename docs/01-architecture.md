# 01 — System Architecture

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Backend Framework | FastAPI + Uvicorn | First-class Pydantic integration, async, auto OpenAPI docs |
| AI Engine | Pydantic AI | Agent orchestration, streaming, tools, structured output |
| Models | OpenAI + Anthropic | Via Pydantic AI `provider:model` prefix pattern |
| Storage | SQLite + sqlite-vec | Zero external deps, sqlite-vec for vector embeddings |
| Frontend | Textual (Python TUI) | Same language as backend, rich terminal rendering |
| Rendering | Rich + Pygments | Markdown, syntax highlighting, formatted output |
| Real-time | WebSocket (default) + SSE (fallback) | Bidirectional streaming, auto-fallback |
| State | Textual reactive properties | Built-in reactivity, no external lib needed |

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│  Textual TUI (terminal)                                  │
│  ┌───────────┐ ┌──────────────────┐ ┌─────────────────┐ │
│  │ Session    │ │  Chat Panel      │ │ Context Panel   │ │
│  │ Sidebar    │ │  (WS streaming)  │ │ (Memory, Model, │ │
│  │ (42 cols)  │ │                  │ │  Context info)  │ │
│  └───────────┘ └──────────────────┘ └─────────────────┘ │
│         │             │  WS/SSE              │           │
│         └─────────────┼──────────────────────┘           │
│                       ▼                                  │
└───────────────────────┬──────────────────────────────────┘
                       │ WebSocket / HTTP
                       ▼
┌──────────────────────────────────────────────────────────┐
│  FastAPI Backend (:8000)                                 │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │ /api/     │ │ /ws/     │ │ /api/    │ │ /api/      │  │
│  │ sessions  │ │ {sid}    │ │ models   │ │ memory     │  │
│  │ CRUD      │ │ WS chat  │ │ switch   │ │ CRUD+search│  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │
│                       │                                  │
│                       ▼                                  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Pydantic AI Agent Layer                            │ │
│  │   - Agent with tools + capabilities                 │ │
│  │   - Model registry (openai / anthropic)             │ │
│  │   - History processors (context trimming)           │ │
│  │   - Memory manager (embeddings + RAG)               │ │
│  └─────────────────────────────────────────────────────┘ │
│                       │                                  │
│                       ▼                                  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  SQLite + sqlite-vec                                │ │
│  │   - sessions, messages, memory_vectors tables       │ │
│  │   - Embedding similarity search                     │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## Project Structure

```
foundry/
├── foundry/                              # Backend
│   ├── app/
│   │   ├── main.py                       # FastAPI app, CORS, lifespan
│   │   ├── config.py                     # Settings (model keys, DB path)
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py               # Session CRUD endpoints
│   │   │   ├── chat.py                   # Chat HTTP endpoint (SSE mode)
│   │   │   ├── ws.py                     # WebSocket endpoint (default)
│   │   │   ├── sse.py                    # SSE fallback endpoint
│   │   │   ├── models.py                 # Model list/switch
│   │   │   └── memory.py                # Memory CRUD + search
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── core.py                   # Pydantic AI Agent factory
│   │   │   ├── registry.py               # Model registry
│   │   │   ├── tools.py                  # Agent tools
│   │   │   ├── memory.py                 # Short-term + long-term memory
│   │   │   └── context.py                # History processors
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py               # SQLite + aiosqlite setup
│   │   │   ├── models.py                 # SQLModel tables
│   │   │   └── crud.py                   # DB operations
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── session.py
│   │       ├── chat.py
│   │       └── memory.py
│   └── pyproject.toml
├── tui/                                  # Frontend TUI
│   ├── src/
│   │   ├── __init__.py
│   │   ├── app.py                        # Textual App entry
│   │   ├── screens/
│   │   │   ├── __init__.py
│   │   │   └── main_screen.py            # Main 3-panel screen
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── chat/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chat_panel.py
│   │   │   │   ├── message_list.py
│   │   │   │   ├── message_bubble.py
│   │   │   │   ├── tool_call.py
│   │   │   │   ├── thinking_block.py
│   │   │   │   └── chat_input.py
│   │   │   ├── session/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── session_sidebar.py
│   │   │   │   └── session_item.py
│   │   │   ├── context/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── context_panel.py
│   │   │   │   └── memory_viewer.py
│   │   │   ├── model/
│   │   │   │   ├── __init__.py
│   │   │   │   └── model_selector.py
│   │   │   └── common/
│   │   │       ├── __init__.py
│   │   │       ├── header.py
│   │   │       ├── footer.py
│   │   │       └── connection_badge.py
│   │   ├── connection/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py                # Unified WS + SSE manager
│   │   │   ├── ws_client.py
│   │   │   └── sse_client.py
│   │   ├── stores/
│   │   │   ├── __init__.py
│   │   │   ├── session_store.py
│   │   │   ├── chat_store.py
│   │   │   └── model_store.py
│   │   ├── theme/
│   │   │   ├── __init__.py
│   │   │   └── opencode.py
│   │   └── styles.tcss
│   └── pyproject.toml
├── shared/
│   ├── __init__.py
│   └── protocol.py                       # WS message types
├── docs/
├── Makefile
└── README.md
```

## Data Flow

### Chat Flow (WebSocket, default)

```
TUI                          Server                         Pydantic AI
 │                              │                              │
 │── WS connect ────────────────▶│                              │
 │                              │                              │
 │── {type: "chat.message"} ───▶│                              │
 │                              │── agent.run_stream_events() ─▶│
 │                              │                              │── LLM API ──▶
 │                              │◀── stream event: delta ───────│◀─────────────
 │◀─ {type: "stream.delta"} ───│                              │
 │◀─ {type: "stream.delta"} ───│                              │
 │◀─ {type: "tool.call"} ──────│                              │
 │◀─ {type: "tool.result"} ────│                              │
 │◀─ {type: "stream.done"} ────│                              │
 │                              │                              │
 │── {type: "chat.interrupt"} ─▶│── cancel agent run ──────────▶│
```

### Chat Flow (SSE fallback)

```
TUI                          Server                         Pydantic AI
 │                              │                              │
 │── POST /api/chat/{sid} ────▶│                              │
 │                              │                              │
 │── GET /api/chat/{sid}/stream │                              │
 │                              │── agent.run_stream_events() ─▶│
 │◀── SSE: stream.delta ───────│                              │
 │◀── SSE: stream.done ────────│                              │
```

## Design Principles

1. **Protocol-agnostic frontend**: TUI connection manager auto-selects WS or SSE, UI code doesn't care
2. **Single-process option**: Backend + TUI can run in one Python process via `asyncio`
3. **Opencode visual parity**: Match opencode's color scheme, layout, key bindings
4. **Pydantic AI idioms**: Use `message_history`, `history_processors`, `run_stream_events()`, tools
5. **SQLite-first**: Zero external infrastructure for development, swappable to Postgres later
