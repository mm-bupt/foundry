# AGENTS.md — Dream Foundry Project Guide

## Project Overview

Dream Foundry is a full-stack AI Agent application:
- **Backend (foundry/)**: Python/FastAPI + Pydantic AI + SQLite
- **TUI Frontend (tui/)**: Python/Textual terminal UI (opencode-style)
- **Communication**: WebSocket (default) + SSE (fallback)

## Current Status

| Phase | Description | Status |
|-------|-------------|--------|
| P1 | Backend base — FastAPI + SQLite + Session CRUD | **DONE** |
| P2 | Agent engine — Pydantic AI + Model Registry + Chat + WS + SSE | **DONE** |
| P3 | Memory + Context — sqlite-vec + embedding cache + LLM summarization | **DONE** |
| P4 | TUI skeleton — Textual App + 3-panel layout + opencode theme | **DONE** |
| P5 | TUI Chat — WS streaming + delta rendering + tool call display | **DONE** |
| P6 | TUI Session — sidebar + click to switch + session CRUD | **DONE** |
| P7 | TUI model selector + context panel + memory viewer | **DONE** |
| P8 | Key bindings + spinner + footer + polish | **DONE** |

## Project Structure

```
dream-foundry/
├── foundry/                         # Backend package (pip install -e foundry)
│   ├── dream_foundry/               # Python package (importable as dream_foundry.*)
│   │   ├── main.py                  # FastAPI app entry, all routers registered
│   │   ├── config.py                # Settings (env vars: DREAM_FOUNDRY_*)
│   │   ├── shared_protocol.py       # WS/SSE message type definitions
│   │   ├── api/
│   │   │   ├── sessions.py          # CRUD /api/sessions
│   │   │   ├── models.py            # GET /api/models, /api/models/active
│   │   │   ├── ws.py                # WebSocket endpoint ws://{host}/ws/{session_id}
│   │   │   ├── sse.py               # SSE fallback GET /api/chat/{session_id}/stream
│   │   │   └── memory.py            # Memory CRUD /api/memory/{session_id}
│   │   ├── agent/
│   │   │   ├── core.py              # Agent factory + stream_chat() main loop
│   │   │   ├── registry.py          # Model registry (gpt-4o, claude-sonnet, etc.)
│   │   │   ├── tools.py             # Agent tools: store_memory, recall_memory
│   │   │   ├── memory.py            # embed_text() using OpenAI embeddings
│   │   │   └── context.py           # History processors (trim)
│   │   ├── db/
│   │   │   ├── database.py          # SQLite + aiosqlite connection, schema init
│   │   │   ├── models.py            # SQLModel table definitions
│   │   │   └── crud.py              # All database operations
│   │   └── schemas/
│   │       ├── session.py           # Session request/response models
│   │       ├── chat.py              # Chat request models
│   │       └── memory.py            # Memory response models
│   └── pyproject.toml
├── tui/                             # TUI frontend (not yet implemented)
├── shared/                          # Original shared protocol (copied into foundry)
├── docs/                            # Design documents
└── AGENTS.md                        # This file
```

## Key Commands

```bash
# Install backend
pip install -e foundry

# Run backend server
python -m uvicorn dream_foundry.main:app --host 0.0.0.0 --port 8000 --reload

# API docs (when server running)
# Swagger: http://localhost:8000/docs
# ReDoc:   http://localhost:8000/redoc
```

## API Endpoints (Phase 1 + 2)

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/health | Health check |
| GET | /api/sessions | List all sessions |
| POST | /api/sessions | Create session |
| GET | /api/sessions/{id} | Get session + messages |
| PATCH | /api/sessions/{id} | Update session (title, model) |
| DELETE | /api/sessions/{id} | Delete session |
| GET | /api/models | List available models |
| GET | /api/models/active | Get active model |
| GET | /api/memory/{session_id} | List session memories |
| POST | /api/memory/{session_id}/search | Search memories by similarity |
| DELETE | /api/memory/{memory_id} | Delete memory |
| WS | /ws/{session_id} | WebSocket chat (default) |
| GET | /api/chat/{session_id}/stream | SSE chat fallback |

## WebSocket Protocol

Client → Server:
- `{"type": "chat.message", "content": "...", "message_id": "uuid"}`
- `{"type": "chat.interrupt"}`
- `{"type": "ping"}`

Server → Client:
- `{"type": "stream.delta", "message_id": "...", "part_id": "...", "text": "..."}`
- `{"type": "stream.done", "message_id": "...", "usage": {...}, "duration_ms": N}`
- `{"type": "stream.error", "error": {"code": "...", "message": "..."}}`
- `{"type": "tool.call", "tool_call_id": "...", "tool_name": "...", "args": {...}}`
- `{"type": "tool.result", "tool_call_id": "...", "tool_name": "...", "result": "..."}`
- `{"type": "pong"}`

## Environment Variables

All env vars use prefix `DREAM_FOUNDRY_`:
- `DREAM_FOUNDRY_OPENAI_API_KEY` — OpenAI API key
- `DREAM_FOUNDRY_ANTHROPIC_API_KEY` — Anthropic API key
- `DREAM_FOUNDRY_DB_PATH` — SQLite database path (default: ~/.dream-foundry/dream-foundry.db)
- `DREAM_FOUNDRY_DEFAULT_MODEL` — Default model ID (default: claude-sonnet)
- `DREAM_FOUNDRY_DEBUG` — Enable debug mode

## Available Models

| ID | Provider | Context Window |
|----|----------|----------------|
| gpt-4o | OpenAI | 128K |
| gpt-4o-mini | OpenAI | 128K |
| claude-sonnet | Anthropic | 200K |
| claude-haiku | Anthropic | 200K |

## Design Documents

Full design docs in `docs/`:
- `01-architecture.md` — System architecture, tech stack, data flow
- `02-api-design.md` — REST + WS + SSE API specs
- `03-agent-design.md` — Pydantic AI agent, tools, memory, context
- `04-tui-design.md` — Textual TUI layout, opencode theme, widgets
- `05-protocol.md` — WebSocket/SSE message protocol
- `06-database.md` — SQLite schema, vector storage
- `07-implementation-plan.md` — Phase-by-phase roadmap

## Next Steps (Phase 3)

Phase 3 will add:
- Full vector-based long-term memory with sqlite-vec
- History processors: auto-summarization of old messages
- Agent tools integration: store_memory / recall_memory wired into agent.core
- Embedding pipeline for memory search

## Notes for Developer

- Backend package name is `dream_foundry` (installed from `foundry/` dir)
- Database auto-creates on first run at `~/.dream-foundry/dream-foundry.db`
- WebSocket is default transport; SSE is fallback for restrictive proxies
- Opencode TUI style reference: `docs/04-tui-design.md` has full color palette + widget specs
