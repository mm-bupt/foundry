# 04 — TUI Design

## Framework: Textual

Textual is a Python TUI framework that supports:
- CSS-based layout and styling
- Reactive properties (automatic UI updates)
- Async workers (non-blocking background tasks)
- Rich rendering (markdown, syntax highlighting, tables)
- Key bindings with command palette
- Composable widget hierarchy

## Layout

### Full Layout (>120 columns)

```
┌─ Dream Foundry ─── ● Claude Sonnet ▾ ─── [WS ●] ──────────────────────────────┐
├──────────────┬──────────────────────────────────────────────────────────────────┤
│ Sessions     │  Chat Messages                                                   │
│              │                                                                    │
│ ● New Chat   │  ┃ 帮我写一个快排算法                                              │
│   Session 1  │  ┃                                                                │
│   Session 2  │  ┃ 好的，这是快速排序的实现：                                      │
│   Session 3  │  ┃                                                                │
│              │  ┃ ```python                                                      │
│              │  ┃ def quicksort(arr):                                            │
│ ──────────── │  ┃     if len(arr) <= 1:                                         │
│ • v0.1.0     │  ┃         return arr                                            │
│              │  ┃     pivot = arr[len(arr) // 2]                                 │
│              │  ┃     ...                                                        │
│              │  ┃ ```                                                            │
│              │  ┃                                                                │
│              │  ┃ ✱ recall_memory "用户偏好" (3 matches)                         │
│              │  ┃ ← "用户偏好: 中文回复"                                          │
│              │  ┃                                                                │
│              │  ┃ ▣ Agent · claude-sonnet · 3.2s                                 │
│              │                                                                    │
│──────────────│──────────────────────────────────────────────────────────────────│
│              │  ╹ Ask anything... "Fix a TODO"                            █     │
│              │  agent · claude-sonnet · anthropic                               │
├──────────────┴──────────────────────────────────────────────────────────────────┤
│ ~/dream-foundry                              2 Memory  /help                    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Narrow Layout (<120 columns — sidebar hidden)

```
┌─ Dream Foundry ─── ● Claude Sonnet ▾ ─── [WS ●] ───────────────┐
│                                                                  │
│  ┃ 帮我写一个快排算法                                            │
│  ┃                                                                │
│  ┃ 好的，这是快速排序的实现：                                    │
│  ┃ ```python ... ```                                             │
│  ┃                                                                │
│  ┃ ▣ Agent · claude-sonnet · 3.2s                                 │
│                                                                  │
│──────────────────────────────────────────────────────────────────│
│  ╹ Ask anything... "Fix a TODO"                            █     │
│  agent · claude-sonnet · anthropic                               │
├──────────────────────────────────────────────────────────────────┤
│ ~/dream-foundry                              2 Memory  /help     │
└──────────────────────────────────────────────────────────────────┘
```

### Layout Rules

- **Sidebar**: 42 columns, auto-show when terminal > 120 cols
- **Main content**: paddingLeft=2, paddingRight=2, paddingBottom=1
- **Messages**: Scrollable area, bottom-anchored (new messages auto-scroll)
- **Input**: Fixed at bottom, 1-6 lines auto-expanding

## Opencode Color Theme

### Core Palette (Dark)

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `background` | `#0a0a0a` | (10,10,10) | Main background |
| `background_panel` | `#141414` | (20,20,20) | Sidebar, message backgrounds |
| `background_element` | `#1e1e1e` | (30,30,30) | Input box, hover states |
| `background_menu` | `#282828` | (40,40,40) | Dropdowns, popovers |
| `primary` | `#fab283` | (250,178,131) | User messages, links, accents |
| `secondary` | `#5c9cf5` | (92,156,245) | Secondary accents |
| `accent` | `#9d7cd8` | (157,124,216) | Assistant messages, headings |
| `error` | `#e06c75` | (224,108,117) | Error messages |
| `warning` | `#f5a742` | (245,167,66) | Warnings, permission dialogs |
| `success` | `#7fd88f` | (127,216,143) | Success, connected status |
| `info` | `#56b6c2` | (86,182,194) | Info messages |
| `text` | `#eeeeee` | (238,238,238) | Primary text |
| `text_muted` | `#808080` | (128,128,128) | Secondary text, timestamps |
| `border` | `#484848` | (72,72,72) | Borders, separators |
| `border_active` | `#606060` | (96,96,96) | Active/focused borders |

### Markdown Colors

| Element | Color | Hex |
|---------|-------|-----|
| Headings | Purple | `#9d7cd8` |
| Links | Orange | `#fab283` |
| Link text | Cyan | `#56b6c2` |
| Inline code | Green | `#7fd88f` |
| Block quotes | Yellow | `#e5c07b` |
| Bold text | Orange | `#f5a742` |
| List items | Orange | `#fab283` |
| Enum items | Cyan | `#56b6c2` |
| Code text | Near white | `#eeeeee` |

### Syntax Highlighting

| Scope | Color | Hex |
|-------|-------|-----|
| Comments | Muted + italic | `#808080` |
| Keywords | Purple + italic | `#9d7cd8` |
| Functions | Orange | `#fab283` |
| Strings | Green | `#7fd88f` |
| Numbers | Orange | `#f5a742` |
| Types | Yellow | `#e5c07b` |
| Operators | Cyan | `#56b6c2` |

### Diff Colors

| Element | Hex |
|---------|-----|
| Added text | `#4fd6be` |
| Removed text | `#c53b53` |
| Added background | `#20303b` |
| Removed background | `#37222c` |
| Context background | `#141414` |

## Widget Design

### Header

```
 Dream Foundry   ● Claude Sonnet ▾   [WS ●]
```

- Left: App name in bold
- Center: Active model with dropdown indicator, green dot = active
- Right: Connection status badge (WS green dot / SSE orange dot / Disconnected red dot)

### Session Sidebar (42 cols)

```
 Sessions

 ● New Chat               ← primary color, bold
   Quick sort              ← muted, hover → text
   Refactor API            ← muted
   Debug auth issue        ← muted

 ─────────────────
 • v0.1.0                  ← green dot + version
```

- Current session: `●` in primary color, text in bold
- Other sessions: muted text, hover highlights
- Scrollable if many sessions
- Footer: green dot + version number

### User Message

```
 ┃ (left border, primary color #fab283)
 ┃ 帮我写一个快排算法
 ┃
```

- Left border `┃` in primary color
- Background: panel color `#141414`, hover: element color `#1e1e1e`
- Padding: top=1, bottom=1, left=2

### Assistant Message

```
 ┃ (left border, accent color #9d7cd8)
 ┃ 好的，这是快速排序的实现：
 ┃
 ┃ ```python
 ┃ def quicksort(arr):
 ┃     ...
 ┃ ```
 ┃
 ┃ ✱ recall_memory "用户偏好" (3 matches)
 ┃ ← "用户偏好: 中文回复"
 ┃
 ┃ ▣ Agent · claude-sonnet · 3.2s
```

- Left border `┃` in accent color
- No background (transparent)
- Tool calls rendered inline with icons
- Footer metadata: `▣` in accent color + model + duration

### Thinking Block

```
 │ (left border, background_element color #1e1e1e)
 │ _Thinking:_ The user wants me to...
 │ I should first check memory for...
 │
```

- Subtle left border in `background_element` color
- Content rendered at 60% opacity (dimmed)
- Prefix: `_Thinking:_` in italic

### Tool Call (Inline Style)

```
      ~ Reading file...                     ← pending (spinning)
      → Read src/index.ts                   ← completed
      ✱ recall_memory "query" (5 matches)   ← search with count
      ← store_memory → "Stored"             ← write/store result
      $ npm test                            ← shell command
      ⚙ custom_tool arg1 arg2               ← generic
```

**States**:
- Pending: `~ message...` with spinner `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` at 80ms
- Completed: `icon details`
- Error: `✗ tool_name: error message` in error color

### Tool Call (Block Style — for large output)

```
 ╭─ left border (accent color) ─────────────────────────
 │  # Edit src/index.ts
 │
 │     1 │ import { foo } from "bar"
 │     2 │ const x = foo()
 │
 ╰───────────────────────────────────────────────────────
```

### Chat Input

```
 ╹ (left border, tinted by agent color)
 │  Ask anything... "Fix a TODO in the codebase"    █
 │  agent · claude-sonnet · anthropic
 ╰────────────────────────────────────────────────────
```

- Left border `╹` in agent color
- Background: element color `#1e1e1e`
- 1-6 lines auto-expanding textarea
- Bottom: model metadata in muted color
- Placeholder: `"Ask anything..."` in muted

### Footer

```
 ~/dream-foundry                              2 Memory  /help
```

- Left: Current working directory
- Right: Memory count + help hint
- Background: panel color `#141414`

## Key Bindings

| Key | Action | Context |
|-----|--------|---------|
| `Enter` | Send message | Input focused |
| `Shift+Enter` | New line | Input focused |
| `Ctrl+N` | New session | Global |
| `Ctrl+J` | Previous session | Global |
| `Ctrl+K` | Next session | Global |
| `Ctrl+L` | Focus input | Global |
| `Ctrl+M` | Switch model | Global |
| `Ctrl+S` | Toggle sidebar | Global |
| `Ctrl+T` | Toggle thinking blocks | Global |
| `Ctrl+\` | Interrupt generation | Global |
| `Ctrl+Q` | Quit | Global |
| `Up` | History prev | Input empty + focused |
| `Down` | History next | Input empty + focused |
| `Escape` | Blur input / cancel | Global |

## Spinner

Frames: `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`
Interval: 80ms
Fallback (no animation): `⋯`

## Textual CSS (styles.tcss)

```css
Screen {
    background: #0a0a0a;
}

.sidebar {
    width: 42;
    background: #141414;
    dock: left;
    display: none;          /* shown via CSS when terminal > 120 */
}

.sidebar.visible {
    display: block;
}

.chat-area {
    background: #0a0a0a;
    padding: 0 2;
}

.message-user {
    background: #141414;
    border-left: outer #fab283;
    padding: 1 2;
}

.message-assistant {
    border-left: outer #9d7cd8;
    padding: 1 2;
}

.thinking-block {
    border-left: outer #1e1e1e;
    padding: 1 2;
    text-style: dim;
}

.input-area {
    background: #1e1e1e;
    border-left: outer #9d7cd8;
    padding: 1 2;
}

.header {
    background: #0a0a0a;
    padding: 0 2;
    border-bottom: solid #484848;
}

.footer {
    background: #141414;
    padding: 0 2;
    border-top: solid #484848;
}

.tool-call {
    color: #808080;
    padding: 0 2;
}

.tool-call-pending {
    color: #f5a742;
}

.tool-call-error {
    color: #e06c75;
}

.session-item {
    padding: 0 2;
}

.session-item:hover {
    background: #1e1e1e;
    color: #eeeeee;
}

.session-item.active {
    color: #fab283;
    text-style: bold;
}

.connection-dot {
    color: #7fd88f;
}

.connection-dot.disconnected {
    color: #e06c75;
}

.connection-dot.sse {
    color: #f5a742;
}
```

## Widget Hierarchy

```
DreamFoundryApp (App)
└── MainScreen (Screen)
    ├── Header (Widget)
    │   ├── AppTitle (Label)
    │   ├── ModelSelector (Widget)
    │   └── ConnectionBadge (Widget)
    ├── Container (Horizontal)
    │   ├── SessionSidebar (Widget)        # dock left, 42 cols
    │   │   ├── SessionList (Widget)
    │   │   │   └── SessionItem (Widget) × N
    │   │   └── SidebarFooter (Widget)
    │   └── ChatPanel (Widget)             # main area
    │       ├── MessageList (ScrollableContainer)
    │       │   └── (MessageBubble | ToolCall | ThinkingBlock) × N
    │       └── InputContainer (Widget)
    │           ├── ChatInput (TextArea)
    │           └── InputMeta (Label)
    └── Footer (Widget)
        ├── CwdPath (Label)
        └── StatusInfo (Label)
```
