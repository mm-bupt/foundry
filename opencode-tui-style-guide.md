# OpenCode TUI Visual Style Guide

> Source: https://github.com/anomalyco/opencode (branch: dev)
> TUI location: `packages/opencode/src/cli/cmd/tui/`
> Framework: **OpenTUI** (SolidJS-based terminal UI framework) — NOT Go/Bubble Tea

---

## 1. COLOR SCHEME

### Default Theme: "opencode"

The default theme uses a 12-step grayscale ramp for dark/light modes with accent colors inspired by Tokyo Night.

#### Dark Mode Colors

| Token | Hex | Usage |
|---|---|---|
| **background** | `#0a0a0a` | Main background (near-black) |
| **backgroundPanel** | `#141414` | User message bg, sidebar bg |
| **backgroundElement** | `#1e1e1e` | Hover states, secondary bg |
| **backgroundMenu** | `#1e1e1e` | Dropdown menus (falls back to backgroundElement) |
| **text** | `#eeeeee` | Primary text |
| **textMuted** | `#808080` | Secondary/muted text |
| **primary** | `#fab283` | Warm orange-peach accent |
| **secondary** | `#5c9cf5` | Blue accent |
| **accent** | `#9d7cd8` | Purple accent |
| **error** | `#e06c75` | Red |
| **warning** | `#f5a742` | Orange |
| **success** | `#7fd88f` | Green |
| **info** | `#56b6c2` | Cyan |
| **border** | `#484848` | Default borders |
| **borderActive** | `#606060` | Active/focused borders |
| **borderSubtle** | `#3c3c3c` | Subtle borders |

#### Light Mode Colors

| Token | Hex | Usage |
|---|---|---|
| **background** | `#ffffff` | White |
| **backgroundPanel** | `#fafafa` | Near-white panels |
| **backgroundElement** | `#f5f5f5` | Light gray elements |
| **text** | `#1a1a1a` | Near-black text |
| **textMuted** | `#8a8a8a` | Gray muted text |
| **primary** | `#3b7dd8` | Blue accent |
| **secondary** | `#7b5bb6` | Purple |
| **accent** | `#d68c27` | Amber/orange |
| **error** | `#d1383d` | Red |
| **warning** | `#d68c27` | Orange |
| **success** | `#3d9a57` | Green |
| **info** | `#318795` | Teal |
| **border** | `#b8b8b8` | Light gray borders |
| **borderActive** | `#a0a0a0` | Active borders |
| **borderSubtle** | `#d4d4d4` | Subtle borders |

#### Diff Colors (Dark)

| Token | Hex |
|---|---|
| diffAdded | `#4fd6be` |
| diffRemoved | `#c53b53` |
| diffAddedBg | `#20303b` |
| diffRemovedBg | `#37222c` |

#### Markdown Syntax Colors (Dark)

| Token | Hex |
|---|---|
| markdownHeading | `#9d7cd8` (accent purple) |
| markdownLink | `#fab283` (primary orange) |
| markdownLinkText | `#56b6c2` (cyan) |
| markdownCode | `#7fd88f` (green) |
| markdownBlockQuote | `#e5c07b` (yellow) |
| markdownEmph | `#e5c07b` (yellow) |
| markdownStrong | `#f5a742` (warning orange) |
| markdownListItem | `#fab283` (primary) |
| markdownListEnumeration | `#56b6c2` (cyan) |
| markdownCodeBlock | `#eeeeee` (text) |

#### Code Syntax Colors (Dark)

| Token | Hex |
|---|---|
| syntaxComment | `#808080` (textMuted) |
| syntaxKeyword | `#9d7cd8` (accent/purple) |
| syntaxFunction | `#fab283` (primary/peach) |
| syntaxVariable | `#e06c75` (red) |
| syntaxString | `#7fd88f` (green) |
| syntaxNumber | `#f5a742` (orange) |
| syntaxType | `#e5c07b` (yellow) |
| syntaxOperator | `#56b6c2` (cyan) |
| syntaxPunctuation | `#eeeeee` (text) |

---

## 2. LAYOUT

### Architecture
- **Two routes**: Home (initial screen) and Session (chat view)
- Uses full terminal width/height via `useTerminalDimensions()`
- Renderer at 60 FPS target

### Home Screen Layout
```
┌─────────────────────────────────────────────┐
│                                             │  ← flexGrow spacer
│                                             │
│             █▀▀█ █▀▀█ █▀▀█ █▀▀▄            │  ← Logo (centered)
│             █__█ █__█ █^^^ █__█             │     4-line block art
│             ▀▀▀▀ █▀▀▀ ▀▀▀▀ ▀~~▀            │
│                                             │  ← 1-line gap
│  ┌─────────────────────────────────────────┐│  ← Prompt (max-width: 75)
│  │ > _                                     ││     centered, with padding
│  └─────────────────────────────────────────┘│
│                                             │  ← flexGrow spacer
│  /path/to/directory           /status       │  ← Footer bar
└─────────────────────────────────────────────┘
```

### Session Layout (wide terminal > 120 cols)
```
┌──────────────────────────────────┬──────────┐
│  Chat Messages (scrollable)      │ Sidebar  │
│  ┌─────────────────────────────┐ │ width:42 │
│  │ User message (left border)  │ │          │
│  └─────────────────────────────┘ │ Title    │
│  ┌─────────────────────────────┐ │ Session  │
│  │ Assistant response          │ │ info     │
│  │   ▣ build · model · 5.2s   │ │          │
│  └─────────────────────────────┘ │ Share URL│
│  ...                             │          │
│                                  │ • Open   │
│  ┌─────────────────────────────┐ │ Code v1.x│
│  │ > Input prompt              │ │          │
│  └─────────────────────────────┘ │          │
├──────────────────────────────────┴──────────┤
│ /dir/path          • LSP  ⊙ MCP  /status   │  ← Footer
└─────────────────────────────────────────────┘
```

### Session Layout (narrow terminal ≤ 120 cols)
- Sidebar is hidden by default
- Toggling sidebar shows it as an **absolute overlay** with semi-transparent black backdrop (`RGBA(0,0,0,70)`)
- Content area = full width minus 4 (padding)

### Key Dimensions
- Sidebar width: **42 columns**
- Content padding: **2 columns** (left/right), **1 row** (bottom)
- Message padding: **2 columns** (left), **1 row** (top/bottom)
- Prompt max-width: **75 columns** (home screen)
- User messages: `marginTop = 1` (except first message)
- Assistant metadata: `paddingLeft = 3`

---

## 3. TYPOGRAPHY / FORMATTING

### Message Rendering

#### User Messages
- Left border using `┃` character, colored by agent color
- Background: `theme.backgroundPanel` (#141414 dark)
- Hover background: `theme.backgroundElement` (#1e1e1e dark)
- Text: `theme.text`
- File attachments shown as badges:
  - Image files: accent-colored badge ` img filename `
  - PDF files: primary-colored badge ` pdf filename `
  - Other: secondary-colored badge ` txt/dir filename `
- Clicking opens a dialog for edit/delete/retry

#### Assistant Messages
- Text parts: rendered as markdown with syntax highlighting
  - Uses `<markdown>` component with streaming support
  - Conceal mode available (collapses code blocks)
  - `paddingLeft: 3` indentation
- Thinking/Reasoning parts:
  - Left border with `theme.backgroundElement` color
  - Rendered as markdown with italic `_Thinking:_ ` prefix
  - Uses `subtleSyntax` (reduced opacity based on `thinkingOpacity` = 0.6)
  - Hidden by default, togglable
- Tool calls: rendered as expandable sections with status indicators
- Metadata footer at end of message:
  - `▣` symbol in agent color
  - Mode (e.g., "Build"), model name, duration
  - Format: `▣ Mode · model-name · 5.2s`

#### Markdown Rendering
- Full markdown support via `<markdown>` component
- Syntax highlighting for code blocks using tree-sitter
- Inline code, links, bold, italic, lists, headings, blockquotes
- Conceal mode: hides code block content, shows only file path

---

## 4. BORDERS AND SEPARATORS

### Border Styles

```typescript
// Empty border (no visible characters)
export const EmptyBorder = {
  topLeft: "", bottomLeft: "", vertical: "", topRight: "",
  bottomRight: "", horizontal: " ", bottomT: "", topT: "",
  cross: "", leftT: "", rightT: "",
}

// Split border (only vertical line on left/right)
export const SplitBorder = {
  border: ["left", "right"],
  customBorderChars: { ...EmptyBorder, vertical: "┃" },
}
```

- **User messages**: Left-only border using `┃` in agent color
- **Thinking blocks**: Left-only border using `┃` in `backgroundElement` color
- **Error blocks**: Left-only border using `┃` in `error` color
- **Compaction divider**: Top border with centered title ` Compaction ` in `borderActive` color
- **Revert indicator**: Left border in `backgroundPanel` color

### Padding
- App-level: `paddingLeft: 2, paddingRight: 2, paddingBottom: 1`
- Message inner: `paddingLeft: 2, paddingTop: 1, paddingBottom: 1`
- Sidebar: `paddingTop: 1, paddingBottom: 1, paddingLeft: 2, paddingRight: 2`

---

## 5. STATUS BAR / HEADER / FOOTER

### Session Footer (`footer.tsx`)
- Horizontal row with space-between layout
- **Left side**: Current directory path (in `textMuted`)
- **Right side** (when connected):
  - Permission indicator: `△ N Permission(s)` in warning color
  - LSP indicator: `• N LSP` (green dot if active, muted if not)
  - MCP indicator: `⊙ N MCP` (green if all connected, red `⊙` if any error)
  - `/status` text in textMuted
- **Right side** (when not connected):
  - Alternates between hidden and `"Get started /connect"` every 5-10 seconds

### Sidebar Footer
- Bottom of sidebar, fixed position
- Shows: `• OpenCode v1.x.x` (green dot, bold "Open" + "Code")
- Version number in textMuted

---

## 6. INPUT AREA (Prompt Component)

### Home Screen Prompt
- Centered, max-width 75 columns
- Full-width within max constraint
- Placeholder examples: "Fix a TODO in the codebase", "What is the tech stack?"
- Supports shell mode with different placeholders
- `paddingTop: 1`

### Session Prompt
- Full-width of content area (minus sidebar if visible)
- Positioned at bottom of layout (flexShrink: 0)
- Supports:
  - Multi-line input (shift+enter, ctrl+enter, alt+enter)
  - Autocomplete dropdown
  - Slash commands (with tab completion)
  - File attachments via @-mentions
  - History navigation (up/down arrows)
  - Stash/pop functionality
  - Right-side plugin slots

---

## 7. SESSION LIST (Sidebar)

### Sidebar Content
- Width: 42 columns
- Background: `theme.backgroundPanel`
- Scrollable content area
- Shows:
  - Session title (bold, in `theme.text`)
  - Session ID (only in non-latest channel)
  - Workspace label with status icon
  - Share URL (if shared)
- Footer: `• OpenCode v1.x.x`

### Session List Dialog
- Full-screen overlay dialog
- List of sessions with search/filter
- Each session shows title, date, model info
- Supports: select, rename, delete, fork

---

## 8. ICONS AND INDICATORS

### Spinner
```typescript
const SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
// Interval: 80ms per frame
// Fallback (animations disabled): "⋯ "
```

### Status Indicators
| Symbol | Meaning | Color |
|---|---|---|
| `•` | Connected/active (LSP, OpenCode) | `theme.success` (green) |
| `⊙` | MCP server | `theme.success` or `theme.error` |
| `△` | Pending permission | `theme.warning` |
| `▣` | Assistant message marker | Agent color |
| `┃` | Message left border | Agent color / theme colors |

### Agent Colors
- Each agent has a configurable color
- User message left border is colored by the agent that generated it
- The `QUEUED` badge uses agent color as background

### Toast Notifications
- Variants: `info`, `warning`, `error`, `success`
- Auto-dismiss with configurable duration (typically 3-5 seconds)

---

## 9. THEME SYSTEM

### Theme Architecture
- **34 built-in themes**: opencode (default), tokyonight, dracula, catppuccin, gruvbox, nord, one-dark, rosepine, everforest, flexoki, kanagawa, material, monokai, nightowl, solarized, ayu, aura, cobalt2, cursor, github, matrix, mercury, orng, lucent-orng, palenight, synthwave84, vercel, vesper, zenburn, carbonfox, catppuccin-frappe, catppuccin-macchiato, osaka-jade
- **System theme**: Auto-generated from terminal color palette (16 colors)
- **Custom themes**: Loaded from `~/.config/opencode/themes/*.json` and `.opencode/themes/*.json`

### Dark/Light Mode
- Mode detected from terminal (`renderer.waitForThemeMode()`)
- Can be manually toggled: `theme.switch_mode` command
- Can be locked: `theme.mode.lock` command
- Each theme defines both `dark` and `light` variants per color
- Stored in KV store: `theme_mode`, `theme_mode_lock`

### Theme JSON Format
```json
{
  "$schema": "https://opencode.ai/theme.json",
  "defs": { "colorName": "#hexcolor" },
  "theme": {
    "primary": { "dark": "#hex", "light": "#hex" },
    "background": { "dark": "#hex", "light": "#hex" },
    // ... all 40+ color tokens
  }
}
```

### Color Resolution
- Supports: hex colors, named references (via `defs`), dark/light variants, RGBA values
- Circular reference detection
- `selectedListItemText`: optional, falls back to background
- `backgroundMenu`: optional, falls back to `backgroundElement`
- `thinkingOpacity`: optional, defaults to 0.6

---

## 10. KEY BINDINGS

### Leader Key
- Default: `Ctrl+X` (referred to as `<leader>`)

### Navigation
| Key | Action |
|---|---|
| `Ctrl+C`, `Ctrl+D`, `<leader>q` | Exit application |
| `Tab` | Cycle to next agent |
| `Shift+Tab` | Cycle to previous agent |
| `Escape` | Interrupt current session |
| `Ctrl+P` | Command palette |
| `<leader>n` | New session |
| `<leader>l` | List sessions |
| `<leader>b` | Toggle sidebar |

### Leader Key Combines
| Key | Action |
|---|---|
| `<leader>t` | Switch theme |
| `<leader>m` | Switch model |
| `<leader>a` | Switch agent |
| `<leader>s` | View status |
| `<leader>e` | Open external editor |
| `<leader>g` | Session timeline |
| `<leader>c` | Compact session |
| `<leader>x` | Export session |
| `<leader>u` | Undo message |
| `<leader>r` | Redo message |
| `<leader>y` | Copy last message |
| `<leader>h` | Toggle conceal / tips |

### Scrolling
| Key | Action |
|---|---|
| `PageUp`, `Ctrl+Alt+B` | Scroll up one page |
| `PageDown`, `Ctrl+Alt+F` | Scroll down one page |
| `Ctrl+Alt+Y` | Scroll up one line |
| `Ctrl+Alt+E` | Scroll down one line |
| `Ctrl+Alt+U` | Half page up |
| `Ctrl+Alt+D` | Half page down |
| `Ctrl+G`, `Home` | First message |
| `Ctrl+Alt+G`, `End` | Last message |

### Session Navigation
| Key | Action |
|---|---|
| `Up` | Go to parent session (in child) / history prev (in input) |
| `Down` | History next (in input) |
| `Left` | Previous child session |
| `Right` | Next child session |
| `<leader>Down` | First child session |
| `Ctrl+R` | Rename session |
| `Ctrl+D` | Delete session |
| `Ctrl+T` | Cycle model variants |

### Input
| Key | Action |
|---|---|
| `Return` | Submit |
| `Shift+Return`, `Ctrl+Return`, `Alt+Return` | New line |
| `Ctrl+A` | Start of line |
| `Ctrl+E` | End of line |
| `Ctrl+K` | Delete to end of line |
| `Ctrl+U` | Delete to start of line |
| `Ctrl+W` | Delete word backward |
| `Ctrl+V` | Paste (with system clipboard) |
| `Ctrl+Z` (Win) / `Ctrl+-` (Unix) | Undo |
| `Ctrl+.` | Redo |
| `Ctrl+Backspace`, `Alt+Backspace` | Delete word backward |

### Dialogs
| Key | Action |
|---|---|
| `Up`, `Ctrl+P` | Previous item |
| `Down`, `Ctrl+N` | Next item |
| `Return` | Select |
| `Escape` | Close |
| `Space` | Toggle (MCP, plugins) |

---

## APPENDIX: CLI Style Constants (non-TUI mode)

For the basic CLI mode (not the TUI), opencode uses ANSI escape codes:

```typescript
export const Style = {
  TEXT_HIGHLIGHT:      "\x1b[96m",      // bright cyan
  TEXT_HIGHLIGHT_BOLD: "\x1b[96m\x1b[1m",
  TEXT_DIM:            "\x1b[90m",      // gray
  TEXT_DIM_BOLD:       "\x1b[90m\x1b[1m",
  TEXT_NORMAL:         "\x1b[0m",
  TEXT_NORMAL_BOLD:    "\x1b[1m",
  TEXT_WARNING:        "\x1b[93m",      // bright yellow
  TEXT_WARNING_BOLD:   "\x1b[93m\x1b[1m",
  TEXT_DANGER:         "\x1b[91m",      // bright red
  TEXT_DANGER_BOLD:    "\x1b[91m\x1b[1m",
  TEXT_SUCCESS:        "\x1b[92m",      // bright green
  TEXT_SUCCESS_BOLD:   "\x1b[92m\x1b[1m",
  TEXT_INFO:           "\x1b[94m",      // bright blue
  TEXT_INFO_BOLD:      "\x1b[94m\x1b[1m",
}
```

Logo rendering uses block characters with color:
- Left half: fg `#90m` (gray), shadow `xterm-235`, bg `xterm-235`
- Right half: fg default, shadow `xterm-238`, bg `xterm-238`
- Characters: `_` (bg fill), `^` (upper half block ▀ with fg+bg), `~` (shadow)

---

## Summary for Python Textual Replication

### Key Design Principles
1. **Near-black background** (#0a0a0a) with subtle gray layers
2. **Warm accent palette**: peach primary, purple accent, blue secondary
3. **Minimal borders**: only left-side `┃` borders on messages
4. **Typography-driven**: heavy use of markdown rendering with syntax highlighting
5. **Two-panel layout**: main content + optional sidebar (42 cols wide)
6. **Bottom-fixed input**: prompt always at bottom
7. **Status footer**: directory + LSP/MCP/connection indicators
8. **Spinner**: braille dot animation at 80ms intervals
9. **Leader key system**: Ctrl+X as prefix for most actions
10. **34 themes + system auto-detection + custom theme JSON files**
