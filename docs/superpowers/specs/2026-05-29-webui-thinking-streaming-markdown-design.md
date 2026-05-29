# WebUI: Thinking Display, True Streaming, Markdown Rendering

## Overview

Enhance the Dream Foundry WebUI with three features:
1. Display AI thinking process in a collapsible panel
2. Fix streaming to use true incremental deltas (not full-text-at-once)
3. Render markdown in AI response bubbles

## Current State

| Feature | Backend | Frontend | Gap |
|---------|---------|----------|-----|
| Thinking | `ThinkingDelta` type defined but never emitted | Not handled | Full implementation needed |
| Streaming | Sends full `TextPart.content` as single `stream.delta` | `appendStreamText` works, uses fake `typing` animation | Backend needs incremental deltas, remove fake typing |
| Markdown | N/A | Plain text in Bubble | Need react-markdown + remark-gfm |

## Design

### 1. Thinking Process Display

**Backend changes** (`foundry_app/agent/core.py`):

- Within `agent.iter()` node streaming, detect `ThinkingPart` from pydantic_ai's response parts
- For Claude models with extended thinking: emit `thinking.delta` events with incremental text
- For non-Claude models: emit `thinking.start` when model processing begins, `thinking.end` when first text arrives
- Protocol additions:
  - `{type: "thinking.delta", message_id: "...", text: "..."}`
  - `{type: "thinking.start", message_id: "..."}`
  - `{type: "thinking.end", message_id: "..."}`

**Frontend changes**:

- **Store** (`store.ts`): Add `thinkingText: string` and `isThinking: boolean` state, with actions `appendThinkingText()`, `startThinking()`, `clearThinking()`
- **Types** (`types.ts`): Add `AppStatus = "thinking"` status
- **App.tsx**: Handle `thinking.delta`, `thinking.start`, `thinking.end` WS events
- **ChatPanel.tsx**: Use `@ant-design/x` `Think` component:
  - Render above AI bubble content when `isThinking` or `thinkingText` is non-empty
  - `Think` props: `loading={isThinking}`, `blink={isThinking}`, `defaultExpanded={false}`
  - Content: accumulated `thinkingText` rendered as markdown

### 2. True Streaming Deltas

**Backend changes** (`foundry_app/agent/core.py`):

The current code sends `stream.delta` with full `TextPart.content` after the model finishes. Need to use pydantic_ai's stream events to send incremental text.

- Within `CallToolsNode.stream(run.ctx)` context, handle `PartDeltaEvent` (or equivalent) for text content deltas
- Each delta sends `{type: "stream.delta", message_id: "...", part_id: "...", text: "<incremental>"}`
- Keep existing handling for `ToolReturnPart` events
- On stream end, send `stream.done` with the complete text (for DB persistence)

**Frontend changes**:

- Remove `typing: { effect: "typing", step: 5, interval: 50 }` from AI bubble role config in `ChatPanel.tsx`
- Keep `streaming: true` on the last bubble item — this tells Bubble to render content as it arrives
- The `appendStreamText` accumulation already works correctly for incremental deltas

### 3. Markdown Rendering

**New dependencies**:
```
react-markdown
remark-gfm
```

**Frontend changes** (`ChatPanel.tsx`):

- Use Bubble's `contentRender` prop for AI role to render markdown
- Create a `MarkdownContent` component:
  - Uses `react-markdown` with `remark-gfm` plugin (tables, strikethrough, autolinks)
  - Custom `code` component: use `@ant-design/x` `CodeHighlighter` for fenced code blocks, inline code with styled `<code>`
  - Custom styling for headings, lists, blockquotes, links, tables
- User messages remain plain text (no markdown rendering)

```tsx
// AI role contentRender
ai: {
  contentRender: (content) => <MarkdownContent>{content}</MarkdownContent>,
  // ... other props
}
```

- Streaming bubbles: markdown renders progressively as text accumulates (react-markdown handles partial markdown gracefully)

## Files Changed

### Backend
- `foundry/foundry_app/agent/core.py` — streaming delta logic, thinking detection, thinking events

### Frontend
- `webui/package.json` — add react-markdown, remark-gfm
- `webui/src/types.ts` — add thinking-related state types
- `webui/src/store.ts` — add thinking state + actions
- `webui/src/App.tsx` — handle thinking WS events
- `webui/src/components/ChatPanel.tsx` — Think component, MarkdownContent, remove fake typing
- `webui/src/components/MarkdownContent.tsx` — new component for markdown rendering

## Implementation Order

1. **Streaming fix** (backend first) — this is the foundation; thinking and markdown both depend on proper streaming
2. **Markdown rendering** (frontend only) — add react-markdown, create MarkdownContent component
3. **Thinking display** (backend + frontend) — detect thinking, emit events, render Think component
