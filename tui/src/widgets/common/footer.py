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
