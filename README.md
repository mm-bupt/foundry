# Foundry

Full-stack AI Agent application with a FastAPI backend and terminal UI frontend.

## Architecture

```
┌──────────────┐    WebSocket/SSE    ┌──────────────────┐
│  TUI (Bun)   │ ◄──────────────────► │  Backend (Python) │
│  @opentui    │                      │  FastAPI          │
│  SolidJS     │                      │  Pydantic AI      │
└──────────────┘                      │  SQLite + sqlite-vec
                                      └──────────────────┘
```

- **Backend** — Python / FastAPI / Pydantic AI / SQLite + sqlite-vec
- **TUI** — Bun / TypeScript / SolidJS / @opentui
- **Communication** — WebSocket (default) + SSE (fallback)

## Quick Start

### Prerequisites

- Python >= 3.10
- Bun >= 1.0

### Configuration

Create `~/.config/foundry/config.yaml`:

```yaml
provider:
  my-openai:
    type: "openai"
    options:
      - api: "https://api.openai.com/v1"
      - apiKey: "sk-..."
    models:
      - "gpt-4o"
      - "gpt-4o-mini"
  my-anthropic:
    type: "anthropic"
    options:
      - api: "https://api.anthropic.com"
      - apiKey: "sk-ant-..."
    models:
      - "claude-sonnet-4-20250514"
model: my-openai:gpt-4o
```

The `type` field determines which provider protocol to use (`openai` or `anthropic`), enabling custom API endpoints for compatible services.

### Run

```bash
# Dev mode (backend + TUI together)
scripts\dev.bat          # Windows CMD
scripts\dev.ps1          # Windows PowerShell
./scripts/dev.sh         # Linux/macOS

# Or run individually
pip install -e foundry
$env:FOUNDRY_WORK_DIR="D:\1-Project\4-github\develop-cli"
python -m uvicorn foundry_app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir foundry/foundry_app

# default or web debug
cd webui && bun install && bun run dev 

cd tui && bun install && bun run src/index.tsx
```

```bash

# debug
$env:HTTP_PROXY="http://127.0.0.1:8080"
$env:HTTPS_PROXY="http://127.0.0.1:8080"
# 代理
mitmweb --listen-port 8080 --web-port 8081

### Production Build

```bash
python scripts/build.py          # Build all
python scripts/build.py backend  # Backend only (PyInstaller)
python scripts/build.py tui      # TUI only
```

Output goes to `dist/foundry/` with a launcher script.

## Project Structure

```
foundry/
├── foundry/                          # Backend
│   └── foundry_app/
│       ├── main.py                   # FastAPI entry point
│       ├── config.py                 # Settings (env + yaml)
│       ├── yaml_config.py            # ~/.config/foundry/config.yaml parser
│       ├── api/                      # REST + WS + SSE endpoints
│       ├── agent/                    # Pydantic AI agent, tools, memory
│       ├── db/                       # SQLite + sqlite-vec
│       └── schemas/                  # Pydantic models
├── tui/                              # Terminal UI
│   └── src/
│       ├── App.tsx                   # Main app component
│       ├── api.ts, ws.ts, store.ts   # API/WebSocket/state layer
│       ├── commands.ts               # Slash commands
│       └── components/               # UI components
├── docs/                             # Design documents
└── scripts/                          # Build & dev scripts
    ├── build.py                      # Production build
    ├── dev.bat                       # Windows CMD dev launcher
    ├── dev.ps1                       # PowerShell dev launcher
    └── dev.sh                        # Linux/macOS dev launcher
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/sessions` | List sessions |
| POST | `/api/sessions` | Create session |
| GET | `/api/sessions/{id}` | Get session + messages |
| PATCH | `/api/sessions/{id}` | Update session |
| DELETE | `/api/sessions/{id}` | Delete session |
| GET | `/api/models` | List available models |
| GET | `/api/models/active` | Get active model |
| GET | `/api/memory/{session_id}` | List memories |
| POST | `/api/memory/{session_id}/search` | Search memories |
| DELETE | `/api/memory/{memory_id}` | Delete memory |
| WS | `/ws/{session_id}` | WebSocket chat |
| GET | `/api/chat/{session_id}/stream` | SSE fallback |

## TUI Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `/new` | `/n` | Create new session |
| `/model [id]` | `/m` | Open model picker (or set directly) |
| `/sessions [id]` | `/s` | Toggle sidebar or switch session |
| `/sidebar` | | Toggle sidebar |
| `/context` | | Toggle context panel |
| `/memories` | | View session memories |
| `/rename <title>` | | Rename current session |
| `/delete` | `/del` | Delete current session |
| `/clear` | `/cls` | Clear messages |
| `/compact` | `/summarize` | Compact session (coming soon) |
| `/help` | `/h` | Show help |
| `/exit` | `/q` | Exit app |

## Environment Variables

All env vars use prefix `FOUNDRY_`:

| Variable | Default | Description |
|----------|---------|-------------|
| `FOUNDRY_OPENAI_API_KEY` | | OpenAI API key |
| `FOUNDRY_ANTHROPIC_API_KEY` | | Anthropic API key |
| `FOUNDRY_DEFAULT_MODEL` | `claude-sonnet` | Default model ID |
| `FOUNDRY_DB_PATH` | `~/.foundry/foundry.db` | SQLite path |
| `FOUNDRY_DEBUG` | `false` | Debug mode |

Environment variables take precedence over `config.yaml` values.

## Configuration File

The YAML config at `~/.config/foundry/config.yaml` supports:

- **Multiple providers** — Register any OpenAI-compatible or Anthropic-compatible API
- **Custom endpoints** — Set `api` URL for each provider
- **Multiple models per provider** — List all model IDs under each provider
- **Default model selection** — `model: provider_name:model_id`

When `config.yaml` is present, models are loaded from it. Otherwise, built-in defaults (gpt-4o, claude-sonnet, etc.) are used as fallback.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Pydantic AI, SQLModel, aiosqlite, sqlite-vec |
| AI Models | OpenAI, Anthropic (and compatible endpoints) |
| TUI | Bun, TypeScript, SolidJS, @opentui |
| Database | SQLite + sqlite-vec (vector search) |
| Communication | WebSocket, SSE |

## License

MIT
