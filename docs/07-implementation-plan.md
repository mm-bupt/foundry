# 07 — Implementation Plan

## Overview

8 phases, ordered by dependency. Each phase produces a runnable increment.

## Phase 1: Backend Foundation

**Goal**: FastAPI app with SQLite, session CRUD, health endpoint.

**Files to create**:
```
foundry/
├── pyproject.toml
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, CORS
│   ├── config.py             # Settings: API keys, DB path
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py       # SQLite + aiosqlite, init_db
│   │   ├── models.py         # SQLModel tables
│   │   └── crud.py           # CRUD operations
│   ├── api/
│   │   ├── __init__.py
│   │   └── sessions.py       # GET/POST/PATCH/DELETE /api/sessions
│   └── schemas/
│       ├── __init__.py
│       └── session.py        # Request/Response models
```

**Verify**: `curl localhost:8000/api/sessions` returns `[]`

---

## Phase 2: Agent Engine + Chat Streaming

**Goal**: Pydantic AI agent with model registry, WebSocket + SSE streaming.

**Files to create**:
```
foundry/app/
├── agent/
│   ├── __init__.py
│   ├── core.py               # Agent factory
│   └── registry.py           # Model registry
├── api/
│   ├── ws.py                 # WebSocket endpoint
│   ├── sse.py                # SSE fallback
│   ├── chat.py               # POST /api/chat (SSE mode)
│   └── models.py             # GET /api/models
├── schemas/
│   └── chat.py               # Chat request/response models
shared/
├── __init__.py
└── protocol.py               # Shared WS message types
```

**Verify**: Connect via websocat, send message, receive streaming response

---

## Phase 3: Memory + Context System

**Goal**: Vector-based long-term memory, history processors, agent tools.

**Files to create**:
```
foundry/app/
├── agent/
│   ├── tools.py              # store_memory, recall_memory tools
│   ├── memory.py             # Embedding, vector ops
│   └── context.py            # History processors
├── api/
│   └── memory.py             # GET/POST/DELETE /api/memory
├── schemas/
│   └── memory.py
```

**Update**:
- `foundry/app/agent/core.py` — add tools to agent
- `foundry/app/db/database.py` — add vec_memory virtual table
- `foundry/app/db/crud.py` — add memory CRUD + search

**Verify**: Agent stores/recalls memories during conversation

---

## Phase 4: TUI Skeleton

**Goal**: Textual app with 3-panel layout, opencode theme, header/footer.

**Files to create**:
```
tui/
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── app.py                # DreamFoundryApp
│   ├── screens/
│   │   ├── __init__.py
│   │   └── main_screen.py   # 3-panel layout
│   ├── widgets/
│   │   ├── __init__.py
│   │   └── common/
│   │       ├── __init__.py
│   │       ├── header.py
│   │       ├── footer.py
│   │       └── connection_badge.py
│   ├── theme/
│   │   ├── __init__.py
│   │   └── opencode.py      # Color constants
│   └── styles.tcss           # Textual CSS
```

**Verify**: `python -m tui.src.app` shows 3-panel layout with header/footer

---

## Phase 5: TUI Chat

**Goal**: Message list, markdown rendering, input box, WebSocket streaming.

**Files to create**:
```
tui/src/
├── widgets/chat/
│   ├── __init__.py
│   ├── chat_panel.py         # Chat area container
│   ├── message_list.py       # Scrollable message list
│   ├── message_bubble.py     # Single message (Rich Markdown)
│   ├── tool_call.py          # Tool call inline/block rendering
│   ├── thinking_block.py     # Thinking block
│   └── chat_input.py         # Auto-expanding input
├── connection/
│   ├── __init__.py
│   ├── manager.py            # Unified WS + SSE manager
│   ├── ws_client.py          # WebSocket client
│   └── sse_client.py         # SSE fallback
├── stores/
│   ├── __init__.py
│   └── chat_store.py         # Message state
```

**Verify**: Type a message, see streaming response with markdown rendering

---

## Phase 6: TUI Session Sidebar

**Goal**: Session list, create/switch/delete sessions.

**Files to create**:
```
tui/src/
├── widgets/session/
│   ├── __init__.py
│   ├── session_sidebar.py    # Sidebar container
│   └── session_item.py       # Session row widget
├── stores/
│   └── session_store.py      # Session state
```

**Verify**: Create new sessions, switch between them, sidebar shows list

---

## Phase 7: Model Selector + Context Panel

**Goal**: Model switching UI, context/memory display.

**Files to create**:
```
tui/src/
├── widgets/model/
│   ├── __init__.py
│   └── model_selector.py    # Model dropdown
├── widgets/context/
│   ├── __init__.py
│   ├── context_panel.py     # Context info panel
│   └── memory_viewer.py     # Memory list
├── stores/
│   └── model_store.py       # Active model state
```

**Update**:
- `tui/src/widgets/common/header.py` — integrate ModelSelector

**Verify**: Switch models in header, see memory entries in context panel

---

## Phase 8: Polish

**Goal**: Key bindings, spinner, error handling, single-process mode.

**Files to update**:
```
tui/src/
├── app.py                    # Add key bindings
├── screens/main_screen.py    # Sidebar auto-show logic
├── widgets/chat/
│   ├── tool_call.py          # Spinner animation
│   └── message_bubble.py     # Error state rendering
foundry/app/main.py           # Single-process launcher option
Makefile                      # Dev commands
```

**Key bindings to implement**:
- `Ctrl+N` new session
- `Ctrl+J/K` prev/next session
- `Ctrl+M` model switch
- `Ctrl+S` toggle sidebar
- `Ctrl+T` toggle thinking
- `Ctrl+\` interrupt
- `Ctrl+Q` quit

**Spinner**: `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` at 80ms

**Single-process mode**:
```python
# python -m foundry_app
# Starts FastAPI + TUI in one process
```

**Verify**: All key bindings work, spinner animates, errors display cleanly

## Dependency Summary

```
Phase 1 ──▶ Phase 2 ──▶ Phase 3 (backend complete)
                                     │
Phase 4 ──▶ Phase 5 ──▶ Phase 6 ──▶ Phase 7 ──▶ Phase 8 (TUI complete)
     │            ▲
     └────────────┘ (needs Phase 2 for WS)
```

Phases 1-3 (backend) and Phase 4 (TUI skeleton) can start in parallel. Phase 5+ requires Phase 2.

## Estimated Effort

| Phase | Scope |
|-------|-------|
| P1 | ~8 files, DB + CRUD |
| P2 | ~8 files, agent + WS + SSE |
| P3 | ~6 files, memory + context |
| P4 | ~8 files, layout + theme |
| P5 | ~9 files, chat + streaming |
| P6 | ~4 files, session sidebar |
| P7 | ~5 files, model + context |
| P8 | Updates + polish |
