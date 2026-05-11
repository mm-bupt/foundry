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
