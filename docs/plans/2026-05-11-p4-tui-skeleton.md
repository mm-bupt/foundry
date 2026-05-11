# P4: TUI Skeleton Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working Textual TUI with 3-panel layout (sidebar + chat + context), header/footer, opencode dark theme, key bindings, and session list — no backend connection yet, just the UI skeleton with mock data.

**Architecture:** Textual App with MainScreen containing Header, Horizontal Container (SessionSidebar + ChatPanel), and Footer. All styling from existing `styles.tcss`. Theme colors from existing `theme/opencode.py`. Mock data for sessions and messages.

**Tech Stack:** Textual >=3.0, Rich >=13.0, Pygments >=2.17

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `tui/pyproject.toml` | Add entry point |
| Create | `tui/src/app.py` | Main DreamFoundryApp class |
| Create | `tui/src/screens/main_screen.py` | 3-panel layout screen |
| Create | `tui/src/widgets/common/header.py` | Header bar widget |
| Create | `tui/src/widgets/common/footer.py` | Footer bar widget |
| Create | `tui/src/widgets/session/sidebar.py` | Session sidebar with list |
| Create | `tui/src/widgets/chat/panel.py` | Chat panel with message list + input |
| Create | `tui/src/widgets/chat/message.py` | Message bubble widget |
| Create | `tui/src/widgets/chat/input.py` | Chat input widget |

---

## Chunk 1: App + Screen + Header + Footer

### Task 1: Add entry point to pyproject.toml

**Files:**
- Modify: `tui/pyproject.toml`

- [ ] **Step 1: Add scripts entry point**

In `tui/pyproject.toml`, add after `dependencies`:

```toml
[project.scripts]
dream-foundry-tui = "src.app:main"
```

- [ ] **Step 2: Commit**

```bash
git add tui/pyproject.toml
git commit -m "chore: add TUI entry point"
```

### Task 2: Create the main App class

**Files:**
- Create: `tui/src/app.py`

- [ ] **Step 1: Write app.py**

```python
from textual.app import App, ComposeResult
from textual.binding import Binding

from src.screens.main_screen import MainScreen


class DreamFoundryApp(App):
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=False),
        Binding("ctrl+n", "new_session", "New Session"),
        Binding("ctrl+s", "toggle_sidebar", "Toggle Sidebar"),
        Binding("ctrl+l", "focus_input", "Focus Input"),
        Binding("ctrl+j", "prev_session", "Prev Session"),
        Binding("ctrl+k", "next_session", "Next Session"),
        Binding("ctrl+m", "switch_model", "Switch Model"),
    ]

    def __init__(self):
        super().__init__()
        self.current_session_id: str = "mock-1"
        self.current_model: str = "claude-sonnet"
        self.model_index: int = 0
        self.models: list[str] = ["claude-sonnet", "gpt-4o", "claude-haiku", "gpt-4o-mini"]
        self.connection_status: str = "disconnected"
        self.memory_count: int = 2
        self.sessions: list[dict] = [
            {"id": "mock-1", "title": "New Chat", "model_id": "claude-sonnet"},
            {"id": "mock-2", "title": "Quick Sort", "model_id": "claude-sonnet"},
            {"id": "mock-3", "title": "Refactor API", "model_id": "gpt-4o"},
        ]

    def on_mount(self) -> None:
        self.push_screen(MainScreen())

    def action_new_session(self) -> None:
        new_id = f"mock-{len(self.sessions) + 1}"
        self.sessions.insert(0, {"id": new_id, "title": "New Chat", "model_id": self.current_model})
        self.current_session_id = new_id
        screen = self.screen_stack[-1] if self.screen_stack else None
        if screen and hasattr(screen, "refresh_sessions"):
            screen.refresh_sessions()

    def action_toggle_sidebar(self) -> None:
        screen = self.screen_stack[-1] if self.screen_stack else None
        if screen and hasattr(screen, "toggle_sidebar"):
            screen.toggle_sidebar()

    def action_focus_input(self) -> None:
        screen = self.screen_stack[-1] if self.screen_stack else None
        if screen and hasattr(screen, "focus_chat_input"):
            screen.focus_chat_input()

    def action_prev_session(self) -> None:
        idx = next((i for i, s in enumerate(self.sessions) if s["id"] == self.current_session_id), 0)
        if idx > 0:
            self.current_session_id = self.sessions[idx - 1]["id"]
            screen = self.screen_stack[-1] if self.screen_stack else None
            if screen and hasattr(screen, "refresh_sessions"):
                screen.refresh_sessions()

    def action_next_session(self) -> None:
        idx = next((i for i, s in enumerate(self.sessions) if s["id"] == self.current_session_id), 0)
        if idx < len(self.sessions) - 1:
            self.current_session_id = self.sessions[idx + 1]["id"]
            screen = self.screen_stack[-1] if self.screen_stack else None
            if screen and hasattr(screen, "refresh_sessions"):
                screen.refresh_sessions()

    def action_switch_model(self) -> None:
        self.model_index = (self.model_index + 1) % len(self.models)
        self.current_model = self.models[self.model_index]
        screen = self.screen_stack[-1] if self.screen_stack else None
        if screen and hasattr(screen, "refresh_header"):
            screen.refresh_header()


def main():
    app = DreamFoundryApp()
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add tui/src/app.py
git commit -m "feat: create DreamFoundryApp with key bindings and mock state"
```

### Task 3: Create Header widget

**Files:**
- Create: `tui/src/widgets/common/header.py`

- [ ] **Step 1: Write header.py**

```python
from textual.widgets import Static
from textual.reactive import reactive

from src.theme.opencode import OpencodeTheme


class AppHeader(Static):
    DEFAULT_CSS = """
    AppHeader {
        background: $background;
        padding: 0 2;
        height: 1;
        border-bottom: solid #484848;
    }
    """

    model_name: reactive[str] = reactive("claude-sonnet")
    connection: reactive[str] = reactive("disconnected")

    def __init__(self, model_name: str = "claude-sonnet", connection: str = "disconnected"):
        super().__init__()
        self.model_name = model_name
        self.connection = connection

    def watch_model_name(self, new_name: str) -> None:
        self._render_header()

    def watch_connection(self, new_status: str) -> None:
        self._render_header()

    def on_mount(self) -> None:
        self._render_header()

    def _render_header(self) -> None:
        t = OpencodeTheme
        dot_colors = {"connected": t.success, "sse": t.warning, "disconnected": t.error}
        dot_color = dot_colors.get(self.connection, t.error)
        conn_label = {"connected": "WS", "sse": "SSE", "disconnected": "OFF"}.get(self.connection, "OFF")

        from rich.text import Text
        text = Text()
        text.append(" Dream Foundry", style="bold")
        text.append("   ")
        text.append("● ", style=f"color({t.primary})")
        text.append(f"{self.model_name} ▾", style=f"color({t.primary})")
        text.append("   ")
        text.append(f"[{conn_label} ", style=f"color({dot_color})")
        text.append("●", style=f"color({dot_color})")
        text.append("]", style=f"color({dot_color})")
        self.update(text)

    def update_model(self, model_name: str) -> None:
        self.model_name = model_name

    def update_connection(self, status: str) -> None:
        self.connection = status
```

- [ ] **Step 2: Commit**

```bash
git add tui/src/widgets/common/header.py
git commit -m "feat: create Header widget with model and connection status"
```

### Task 4: Create Footer widget

**Files:**
- Create: `tui/src/widgets/common/footer.py`

- [ ] **Step 1: Write footer.py**

```python
import os

from textual.widgets import Static

from src.theme.opencode import OpencodeTheme


class AppFooter(Static):
    DEFAULT_CSS = """
    AppFooter {
        background: #141414;
        padding: 0 2;
        height: 1;
        border-top: solid #484848;
    }
    """

    def __init__(self, memory_count: int = 0):
        super().__init__()
        self.memory_count = memory_count

    def on_mount(self) -> None:
        self._render_footer()

    def _render_footer(self) -> None:
        t = OpencodeTheme
        cwd = os.getcwd()
        home = os.path.expanduser("~")
        if cwd.startswith(home):
            cwd = "~" + cwd[len(home):]
        display = cwd.split(os.sep)[-1] or cwd

        from rich.text import Text
        text = Text()
        text.append(f" ~/{display}", style=f"color({t.text_muted})")
        padding = 80 - len(display) - 20
        if padding > 0:
            text.append(" " * padding)
        text.append(f"{self.memory_count} Memory", style=f"color({t.text_muted})")
        text.append("  ")
        text.append("/help", style=f"color({t.text_muted})")
        self.update(text)

    def update_memory_count(self, count: int) -> None:
        self.memory_count = count
        self._render_footer()
```

- [ ] **Step 2: Commit**

```bash
git add tui/src/widgets/common/footer.py
git commit -m "feat: create Footer widget with cwd and memory count"
```

---

## Chunk 2: Session Sidebar + Chat Panel

### Task 5: Create Session Sidebar widget

**Files:**
- Create: `tui/src/widgets/session/sidebar.py`

- [ ] **Step 1: Write sidebar.py**

```python
from textual.widgets import Static
from textual.containers import VerticalScroll

from src.theme.opencode import OpencodeTheme


class SessionItem(Static):
    DEFAULT_CSS = """
    SessionItem {
        padding: 0 2;
        height: 1;
        color: #808080;
    }
    SessionItem:hover {
        background: #1e1e1e;
        color: #eeeeee;
    }
    SessionItem.active {
        color: #fab283;
        text-style: bold;
    }
    """

    def __init__(self, session_id: str, title: str, active: bool = False):
        super().__init__()
        self.session_id = session_id
        self.session_title = title
        self.is_active = active

    def on_mount(self) -> None:
        self._render()

    def _render(self) -> None:
        t = OpencodeTheme
        from rich.text import Text
        text = Text()
        if self.is_active:
            text.append("● ", style=f"color({t.primary})")
            text.append(self.session_title, style=f"color({t.primary}) bold")
        else:
            text.append("  ")
            text.append(self.session_title, style=f"color({t.text_muted})")
        self.update(text)
        self.set_class(self.is_active, "active")

    def set_active(self, active: bool) -> None:
        self.is_active = active
        self._render()


class SessionSidebar(Static):
    DEFAULT_CSS = """
    SessionSidebar {
        width: 42;
        background: #141414;
        dock: left;
        display: none;
    }
    SessionSidebar.visible {
        display: block;
    }
    """

    def __init__(self):
        super().__init__()
        self._visible = False

    def compose(self):
        yield Static(" Sessions", classes="sidebar-title")
        self.session_list = VerticalScroll(classes="session-list")
        yield self.session_list
        yield Static(" ──────────────", classes="sidebar-divider")
        yield Static(" ● v0.1.0", classes="sidebar-version")

    def update_sessions(self, sessions: list[dict], current_id: str) -> None:
        self.session_list.remove_children()
        for s in sessions:
            item = SessionItem(s["id"], s["title"], s["id"] == current_id)
            self.session_list.mount(item)

    def toggle(self) -> bool:
        self._visible = not self._visible
        self.set_class(self._visible, "visible")
        return self._visible
```

- [ ] **Step 2: Commit**

```bash
git add tui/src/widgets/session/sidebar.py
git commit -m "feat: create SessionSidebar with session list"
```

### Task 6: Create Message Bubble widget

**Files:**
- Create: `tui/src/widgets/chat/message.py`

- [ ] **Step 1: Write message.py**

```python
from textual.widgets import Static

from src.theme.opencode import OpencodeTheme


class MessageBubble(Static):
    DEFAULT_CSS = """
    MessageBubble {
        padding: 1 2;
    }
    MessageBubble.user {
        background: #141414;
        border-left: outer #fab283;
    }
    MessageBubble.assistant {
        border-left: outer #9d7cd8;
    }
    """

    def __init__(self, role: str, content: str, model: str = "", duration: float = 0.0):
        super().__init__()
        self.role = role
        self.content = content
        self.model = model
        self.duration = duration

    def on_mount(self) -> None:
        t = OpencodeTheme
        from rich.text import Text
        from rich.markdown import Markdown

        text = Text()
        if self.role == "user":
            text.append(self.content)
            self.update(text)
            self.set_class(True, "user")
        else:
            md = Markdown(self.content)
            from rich.console import Group
            group_items = [md]
            if self.model:
                meta = Text()
                meta.append(f" ▣ Agent · {self.model}", style=f"color({t.accent})")
                if self.duration:
                    meta.append(f" · {self.duration:.1f}s", style=f"color({t.text_muted})")
                group_items.append(meta)
            self.update(Group(*group_items))
            self.set_class(True, "assistant")
```

- [ ] **Step 2: Commit**

```bash
git add tui/src/widgets/chat/message.py
git commit -m "feat: create MessageBubble with markdown rendering"
```

### Task 7: Create Chat Input widget

**Files:**
- Create: `tui/src/widgets/chat/input.py`

- [ ] **Step 1: Write input.py**

```python
from textual.widgets import TextArea, Static
from textual.containers import Vertical

from src.theme.opencode import OpencodeTheme


class ChatInputArea(Vertical):
    DEFAULT_CSS = """
    ChatInputArea {
        background: #1e1e1e;
        border-left: outer #9d7cd8;
        padding: 1 2;
        height: auto;
        max-height: 10;
    }
    """

    def __init__(self, model_name: str = "claude-sonnet"):
        super().__init__()
        self.model_name = model_name

    def compose(self):
        self.input = TextArea(
            "",
            placeholder="Ask anything... (Enter to send, Shift+Enter for new line)",
        )
        self.input.styles.height = 1
        yield self.input
        t = OpencodeTheme
        self.meta = Static(f" agent · {self.model_name}", style=f"color({t.text_muted})")
        yield self.meta

    def update_model(self, model_name: str) -> None:
        self.model_name = model_name
        t = OpencodeTheme
        self.meta.update(f" agent · {model_name}", style=f"color({t.text_muted})")
```

- [ ] **Step 2: Commit**

```bash
git add tui/src/widgets/chat/input.py
git commit -m "feat: create ChatInput with model metadata"
```

### Task 8: Create Chat Panel widget

**Files:**
- Create: `tui/src/widgets/chat/panel.py`

- [ ] **Step 1: Write panel.py**

```python
from textual.widgets import Static
from textual.containers import Vertical, VerticalScroll

from src.widgets.chat.message import MessageBubble
from src.widgets.chat.input import ChatInputArea


MOCK_MESSAGES = [
    {"role": "user", "content": "帮我写一个快排算法"},
    {
        "role": "assistant",
        "content": "好的，这是快速排序的实现：\n\n```python\ndef quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)\n```\n\n时间复杂度：平均 O(n log n)，最坏 O(n²)。",
        "model": "claude-sonnet",
        "duration": 3.2,
    },
]


class ChatPanel(Vertical):
    DEFAULT_CSS = """
    ChatPanel {
        background: #0a0a0a;
        padding: 0 2;
    }
    """

    def __init__(self, model_name: str = "claude-sonnet"):
        super().__init__()
        self.model_name = model_name

    def compose(self):
        self.message_list = VerticalScroll(classes="message-list")
        yield self.message_list
        self.input_area = ChatInputArea(self.model_name)
        yield self.input_area

    def on_mount(self) -> None:
        for msg in MOCK_MESSAGES:
            bubble = MessageBubble(
                role=msg["role"],
                content=msg["content"],
                model=msg.get("model", ""),
                duration=msg.get("duration", 0.0),
            )
            self.message_list.mount(bubble)
        self.message_list.scroll_end(animate=False)

    def focus_input(self) -> None:
        self.input_area.input.focus()

    def update_model(self, model_name: str) -> None:
        self.model_name = model_name
        self.input_area.update_model(model_name)
```

- [ ] **Step 2: Commit**

```bash
git add tui/src/widgets/chat/panel.py
git commit -m "feat: create ChatPanel with message list and mock data"
```

---

## Chunk 3: Main Screen + Integration

### Task 9: Create Main Screen

**Files:**
- Create: `tui/src/screens/main_screen.py`

- [ ] **Step 1: Write main_screen.py**

```python
from textual.screen import Screen
from textual.containers import Horizontal

from src.widgets.common.header import AppHeader
from src.widgets.common.footer import AppFooter
from src.widgets.session.sidebar import SessionSidebar
from src.widgets.chat.panel import ChatPanel


class MainScreen(Screen):
    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }
    MainScreen > Horizontal {
        height: 1fr;
    }
    """

    def compose(self):
        self.header = AppHeader()
        yield self.header
        body = Horizontal()
        self.sidebar = SessionSidebar()
        body._add_child(self.sidebar)
        self.chat = ChatPanel()
        body._add_child(self.chat)
        yield body
        self.footer = AppFooter(memory_count=self.app.memory_count)
        yield self.footer

    def on_mount(self) -> None:
        self.sidebar.update_sessions(self.app.sessions, self.app.current_session_id)
        self.header.update_connection(self.app.connection_status)

    def refresh_sessions(self) -> None:
        self.sidebar.update_sessions(self.app.sessions, self.app.current_session_id)

    def refresh_header(self) -> None:
        self.header.update_model(self.app.current_model)
        self.chat.update_model(self.app.current_model)

    def toggle_sidebar(self) -> None:
        self.sidebar.toggle()

    def focus_chat_input(self) -> None:
        self.chat.focus_input()
```

- [ ] **Step 2: Commit**

```bash
git add tui/src/screens/main_screen.py
git commit -m "feat: create MainScreen with 3-panel layout"
```

### Task 10: Update __init__.py files for imports

**Files:**
- Modify: `tui/src/__init__.py`
- Modify: `tui/src/screens/__init__.py`
- Modify: `tui/src/widgets/__init__.py`
- Modify: `tui/src/widgets/common/__init__.py`
- Modify: `tui/src/widgets/chat/__init__.py`
- Modify: `tui/src/widgets/session/__init__.py`

- [ ] **Step 1: Leave all __init__.py files empty** — they just need to exist as packages. They are already empty stubs, no changes needed.

- [ ] **Step 2: Verify no changes needed**

All `__init__.py` files already exist as empty stubs. No modifications needed.

### Task 11: Install and test

- [ ] **Step 1: Install TUI package**

Run: `pip install -e tui`

- [ ] **Step 2: Launch TUI**

Run: `python -m src.app` from the `tui/` directory, or `python tui/src/app.py`

Verify:
- Dark theme with #0a0a0a background
- Header showing "Dream Foundry ● claude-sonnet ▾ [OFF ●]"
- Chat area with mock messages
- Footer showing cwd and memory count
- Ctrl+S toggles sidebar
- Ctrl+M cycles models
- Ctrl+J / Ctrl+K switches sessions
- Ctrl+Q quits

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: complete P4 TUI skeleton with 3-panel layout"
```
