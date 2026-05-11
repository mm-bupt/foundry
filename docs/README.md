# Dream Foundry — Design Documents

## Overview

Dream Foundry is a full-stack AI Agent application with a separated backend (Python/FastAPI + Pydantic AI) and TUI frontend (Python/Textual), styled to match the opencode terminal UI.

## Documents

| Document | Description |
|----------|-------------|
| [01-architecture.md](./01-architecture.md) | System architecture, tech stack, project structure |
| [02-api-design.md](./02-api-design.md) | REST + WebSocket + SSE API specifications |
| [03-agent-design.md](./03-agent-design.md) | Pydantic AI agent, model registry, tools, memory |
| [04-tui-design.md](./04-tui-design.md) | TUI layout, widgets, opencode-style theme |
| [05-protocol.md](./05-protocol.md) | WebSocket/SSE message protocol |
| [06-database.md](./06-database.md) | SQLite schema, sqlite-vec vector storage |
| [07-implementation-plan.md](./07-implementation-plan.md) | Phase-by-phase implementation roadmap |

## Quick Start

```bash
# Backend
cd foundry && pip install -e ".[dev]"
python -m foundry.app.main

# TUI
cd tui && pip install -e ".[dev]"
python -m tui.src.app

# Or single-process mode
python -m dream_foundry
```
