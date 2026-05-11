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
