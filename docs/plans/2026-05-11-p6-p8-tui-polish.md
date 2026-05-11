# P6-P8: TUI Session Management + Model Selector + Context Panel + Polish

> **For agentic workers:** Execute all tasks in this plan. Edit files directly.

**Goal:** Add session switching/clicking in sidebar, model selector dropdown, context panel showing memories, spinner animation during streaming, and final polish.

**Architecture:** SessionItem clickable to switch sessions. Model selector as an OptionSelect overlay. Context panel docks right showing memories for current session. Spinner overlay during generation.

**Tech Stack:** Textual, httpx

---

## Task 1: Update SessionItem — clickable session switching

**Files:**
- Modify: `tui/src/widgets/session/sidebar.py`

Replace entire file:

```python
from textual.widgets import Static
from textual.containers import VerticalScroll
from textual.events import Click

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

    def on_click(self, event: Click) -> None:
        if self.is_active:
            return
        app = self.app
        if hasattr(app, "switch_to_session"):
            app.switch_to_session(self.session_id)

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

## Task 2: Add switch_to_session to app.py

**Files:**
- Modify: `tui/src/app.py`

Add this method to `DreamFoundryApp` class (after `action_interrupt`):

```python
    def switch_to_session(self, session_id: str) -> None:
        if session_id == self.store.current_session_id:
            return
        self.store.current_session_id = session_id
        session = self.store.get_current_session()
        if session:
            self.store.current_model = session.get("model_id", "claude-sonnet")
        self.run_worker(self._switch_session(0), exclusive=True)
```

And update `_switch_session` to handle direction=0 for direct switch:

In `_switch_session`, change the first line that computes `new_idx` to:
```python
    async def _switch_session(self, direction: int):
        sessions = self.store.sessions
        idx = next((i for i, s in enumerate(sessions) if s["id"] == self.store.current_session_id), 0)
        if direction == 0:
            new_idx = idx
        else:
            new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(sessions):
            return
```

## Task 3: Create Context Panel widget

**Files:**
- Create: `tui/src/widgets/context/panel.py`

```python
from textual.widgets import Static
from textual.containers import VerticalScroll

from src.theme.opencode import OpencodeTheme


class MemoryItem(Static):
    DEFAULT_CSS = """
    MemoryItem {
        padding: 0 2;
        height: auto;
        max-height: 3;
        color: #808080;
    }
    """

    def __init__(self, category: str, content: str):
        super().__init__()
        self.memory_category = category
        self.memory_content = content

    def on_mount(self) -> None:
        t = OpencodeTheme
        from rich.text import Text
        text = Text()
        text.append(f" [{self.memory_category}]", style=f"color({t.accent})")
        text.append(f" {self.memory_content[:80]}", style=f"color({t.text_muted})")
        if len(self.memory_content) > 80:
            text.append("...", style=f"color({t.text_muted})")
        self.update(text)


class ContextPanel(Static):
    DEFAULT_CSS = """
    ContextPanel {
        width: 30;
        background: #141414;
        dock: right;
        display: none;
        border-left: solid #484848;
    }
    ContextPanel.visible {
        display: block;
    }
    """

    def __init__(self):
        super().__init__()
        self._visible = False

    def compose(self):
        yield Static(" Context", classes="sidebar-title")
        self.memory_list = VerticalScroll(classes="memory-list")
        yield self.memory_list

    def update_memories(self, memories: list[dict]) -> None:
        self.memory_list.remove_children()
        for m in memories:
            item = MemoryItem(m.get("category", "note"), m.get("content", ""))
            self.memory_list.mount(item)

    def toggle(self) -> bool:
        self._visible = not self._visible
        self.set_class(self._visible, "visible")
        return self._visible
```

## Task 4: Add context panel to MainScreen + toggle binding

**Files:**
- Modify: `tui/src/screens/main_screen.py`

In `compose()`, after `body._add_child(self.chat)`, add:

```python
        self.context_panel = ContextPanel()
        body._add_child(self.context_panel)
```

Add the import at top:
```python
from src.widgets.context.panel import ContextPanel
```

Add a new method:

```python
    def toggle_context(self) -> None:
        if hasattr(self, 'context_panel'):
            self.context_panel.toggle()
```

In `full_refresh()`, after `self.footer.update_memory_count(...)`, add:

```python
        self.run_worker(self._load_memories(), exclusive=True)
```

Add this method:

```python
    async def _load_memories(self):
        memories = await self.app.store.fetch_memories(self.app.store.current_session_id)
        if hasattr(self, 'context_panel'):
            self.context_panel.update_memories(memories)
```

In `handle_ws_event`, in the `memory.stored` block, add:

```python
            self.run_worker(self._load_memories(), exclusive=True)
```

## Task 5: Add Ctrl+T binding for context panel toggle

**Files:**
- Modify: `tui/src/app.py`

Add to BINDINGS list:
```python
        Binding("ctrl+t", "toggle_context", "Context"),
```

Add action method:
```python
    def action_toggle_context(self) -> None:
        screen = self.screen_stack[-1] if len(self.screen_stack) > 1 else None
        if screen and hasattr(screen, "toggle_context"):
            screen.toggle_context()
```

## Task 6: Add spinner during streaming

**Files:**
- Modify: `tui/src/widgets/chat/panel.py`

Add a spinner indicator. When streaming starts, show a spinner at the bottom of message list.

Add to ChatPanel class:

```python
    def show_spinner(self) -> None:
        t = OpencodeTheme
        from rich.text import Text
        if not hasattr(self, '_spinner') or self._spinner is None:
            self._spinner = Static(Text(" ⠋ Thinking...", style=f"color({t.primary})"), classes="spinner")
            self.message_list.mount(self._spinner)
            self.scroll_to_bottom()

    def hide_spinner(self) -> None:
        if hasattr(self, '_spinner') and self._spinner is not None:
            self._spinner.remove()
            self._spinner = None
```

In `MainScreen.handle_ws_event`, in the `stream.delta` block (when `_streaming_bubble is None`), add:
```python
                self.chat.show_spinner()
```

Then after creating the bubble, add:
```python
                self.chat.hide_spinner()
```

Also in `stream.done` and `stream.error` handlers, add `self.chat.hide_spinner()`.

## Task 7: Commit all

```bash
git add -A
git commit -m "feat: P6-P8 session management, model selector, context panel, spinner"
```
