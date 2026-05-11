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
