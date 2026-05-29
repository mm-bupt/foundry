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
│   ├── foundry_app/               # Python package (importable as foundry_app.*)
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
# === Dev Mode (backend + TUI together) ===
# Windows:
dev.bat

# Linux/macOS:
./dev.sh

# Individual components:
pip install -e foundry                  # Install backend
python -m uvicorn foundry_app.main:app --host 0.0.0.0 --port 8000 --reload  # Backend only
cd tui && bun install && bun run src/index.tsx  # TUI only

# === Production Build ===
python build.py          # Build all (self-contained folder)
python build.py backend  # Backend only (PyInstaller onefile)
python build.py tui      # TUI only (sources + node_modules)
python build.py bun      # Bundle Bun runtime only

# Output: dist/dream-foundry/
#   dream-foundry.bat (or .sh)  ← double-click to run
#   bin/dream-foundry-server    ← backend
#   bin/bun                     ← Bun runtime (no install needed)
#   lib/tui/                    ← TUI sources
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
| GET | /api/config | Get runtime config (work_dir, etc.) |
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
- `DREAM_FOUNDRY_WORK_DIR` — Agent working directory for file operations (default: cwd)
- `DREAM_FOUNDRY_DEFAULT_MODEL` — Default model ID (default: claude-sonnet)
- `DREAM_FOUNDRY_DEBUG` — Enable debug mode

Work dir priority: `--work-dir` CLI arg > `DREAM_FOUNDRY_WORK_DIR` env > `workDir` in YAML config > `os.getcwd()`

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

## Next Steps

All phases P1-P8 complete. Future work:
- Improved markdown/code rendering with tree-sitter
- More slash commands and dialog-based interactions
- Theme system with multiple built-in themes
- Sound effects and animations
- Plugin system

## Project Structure (Updated)

```
dream-foundry/
├── build.py                         # Build script (PyInstaller + Bun compile)
├── dev.sh / dev.bat                 # Dev launcher (backend + TUI)
├── foundry/                         # Backend (Python/FastAPI/Pydantic AI)
│   └── foundry_app/
│       ├── main.py, config.py
│       ├── agent/ (core, registry, tools, memory, context)
│       ├── api/ (sessions, models, ws, sse, memory)
│       ├── db/ (database, models, crud)
│       └── schemas/
├── tui/                             # TUI (Bun/TypeScript/@opentui/solid)
│   └── src/
│       ├── index.tsx, App.tsx
│       ├── api.ts, ws.ts, store.ts, commands.ts, theme.ts
│       └── components/ (Header, ChatArea, InputBar, Sidebar, Footer, ContextPanel)
└── docs/                            # Design documents
```

## React Debugging

- `agent-react-devtools start` — 启动守护进程
- `agent-react-devtools status` — 检查应用是否已连接
- `agent-react-devtools get tree [@c1] --depth N` — 获取组件树
- `agent-react-devtools get component &lt;id&gt;` — 查看 props, state, hooks
- `agent-react-devtools find &lt;Name&gt;` — 搜索组件
- `agent-react-devtools errors` — 列出报错组件

## 调试方法

### 后端调试
```bash
pip install -e foundry
python -m uvicorn foundry_app.main:app --host 0.0.0.0 --port 8000 --reload
```
更新后使用 uvicorn --reload 自动重载。

### TUI 调试
使用 `agent-react-devtools` 进行调试，参见上方 React Debugging 章节。

### Web UI 调试（Playwright CLI）
使用 playwright-cli 对 webui 页面进行自动化调试和交互：

```bash
# 启动 webui 开发服务器
cd webui && bun install && bun run dev   # 默认 http://localhost:5173

# 使用 playwright-cli 打开页面并调试
npx @anthropic-ai/playwright-cli@latest open http://localhost:5173

# 常用 playwright-cli 命令：
# 截图              npx @anthropic-ai/playwright-cli@latest screenshot http://localhost:5173
# 点击元素          npx @anthropic-ai/playwright-cli@latest click "button.submit"
# 填写表单          npx @anthropic-ai/playwright-cli@latest fill "input[name=email]" "test@example.com"
# 获取页面内容      npx @anthropic-ai/playwright-cli@latest content http://localhost:5173
# 执行 JS           npx @anthropic-ai/playwright-cli@latest evaluate "document.title"
# 等待选择器出现    npx @anthropic-ai/playwright-cli@latest wait "div.chat-message"
```

调试记录保存在 `.playwright-cli/` 目录下。