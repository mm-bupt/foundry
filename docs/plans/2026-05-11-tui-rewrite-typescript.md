# TUI Rewrite: Bun + TypeScript + OpenTUI

> **For agentic workers:** Execute all tasks in this plan. Edit files directly.

**Goal:** Replace Python/Textual TUI with Bun + TypeScript + @opentui/solid TUI that matches opencode's appearance. Use slash commands (/xx) for all controls. Connect to existing Dream Foundry backend via HTTP + WebSocket.

**Architecture:** @opentui/solid for SolidJS-based terminal rendering. Bun for runtime. HTTP client for REST API, WebSocket for streaming chat. Slash command system inspired by opencode.

**Tech Stack:** Bun, TypeScript, @opentui/core, @opentui/solid, solid-js

---

## File Structure

```
tui/
├── package.json
├── tsconfig.json
├── bunfig.toml
├── src/
│   ├── index.tsx                    # Entry point
│   ├── app.tsx                      # Main App component
│   ├── theme.ts                     # Opencode color theme constants
│   ├── api.ts                       # HTTP client for backend REST API
│   ├── ws.ts                        # WebSocket client for streaming
│   ├── store.ts                     # SolidJS store for app state
│   ├── commands.ts                  # Slash command registry
│   ├── routes/
│   │   ├── home.tsx                 # Home screen (logo + prompt)
│   │   └── session.tsx              # Session view (messages + prompt + sidebar)
│   ├── components/
│   │   ├── prompt.tsx               # Input prompt with /command autocomplete
│   │   ├── autocomplete.tsx         # /command and @mention autocomplete
│   │   ├── message.tsx              # Message rendering (user/assistant)
│   │   ├── tool-call.tsx            # Tool call rendering
│   │   ├── sidebar.tsx              # Right sidebar (session info + memories)
│   │   ├── footer.tsx               # Bottom status bar
│   │   ├── spinner.tsx              # Animated spinner
│   │   ├── dialog.tsx               # Modal dialog overlay
│   │   └── toast.tsx                # Toast notifications
│   └── util/
│       └── markdown.ts              # Markdown rendering helpers
```

## Slash Commands

| Command | Description |
|---------|-------------|
| `/new` | Create new session |
| `/sessions` | Switch session |
| `/models` | Switch model |
| `/sidebar` | Toggle sidebar |
| `/context` | Toggle context/memory panel |
| `/help` | Show available commands |
| `/exit` | Exit app |
| `/compact` | Compact/summarize current session |
| `/rename <name>` | Rename current session |
| `/memories` | View memories for current session |
| `/clear` | Clear message display |

---

## Task 1: Remove old Python TUI

Delete all Python TUI files under tui/ (keep the directory).

## Task 2: Create package.json

```json
{
  "name": "dream-foundry-tui",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "bun run --hot src/index.tsx",
    "start": "bun run src/index.tsx"
  },
  "dependencies": {
    "@opentui/core": "^0.2.6",
    "@opentui/solid": "^0.2.6",
    "solid-js": "^1.9.0"
  },
  "devDependencies": {
    "typescript": "^5.7.0",
    "@types/bun": "^1.1.0"
  }
}
```

## Task 3: Create tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "jsxImportSource": "@opentui/solid",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "dist",
    "rootDir": "src",
    "types": ["bun-types"]
  },
  "include": ["src/**/*"]
}
```

## Task 4: Create theme.ts

Opencode dark theme color constants matching the existing design doc.

## Task 5: Create api.ts

HTTP client using Bun.fetch for backend REST API.

## Task 6: Create ws.ts

WebSocket client connecting to ws://localhost:8000/ws/{session_id}.

## Task 7: Create store.ts

SolidJS reactive store for sessions, messages, models, memories, connection status.

## Task 8: Create commands.ts

Slash command registry with fuzzy matching.

## Task 9: Create components (prompt, message, sidebar, footer, spinner, dialog, toast, autocomplete, tool-call)

All UI components using @opentui/solid.

## Task 10: Create routes (home.tsx, session.tsx)

Home screen and session view.

## Task 11: Create app.tsx

Main App component with router.

## Task 12: Create index.tsx

Entry point that renders the App.

## Task 13: Install and test

```bash
cd tui && bun install && bun run src/index.tsx
```

## Task 14: Commit

```bash
git add -A && git commit -m "feat: rewrite TUI with Bun + TypeScript + OpenTUI"
```
