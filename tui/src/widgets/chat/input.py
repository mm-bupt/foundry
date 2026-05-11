from textual.widgets import TextArea, Static
from textual.containers import Vertical
from textual.events import Key

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

    def __init__(self, model_name: str = "claude-sonnet", on_send=None):
        super().__init__()
        self.model_name = model_name
        self._on_send = on_send

    def compose(self):
        self.input = TextArea(
            "",
        )
        self.input.styles.height = 1
        yield self.input
        t = OpencodeTheme
        self.meta = Static(f" agent · {self.model_name}", style=f"color({t.text_muted})")
        yield self.meta

    def on_key(self, event: Key) -> None:
        if event.key == "enter" and not event.shift:
            event.prevent_default()
            text = self.input.text
            if text.strip() and self._on_send:
                self._on_send(text)
                self.input.load_text("")
        elif event.key == "escape":
            self.input.blur()

    def update_model(self, model_name: str) -> None:
        self.model_name = model_name
        t = OpencodeTheme
        self.meta.update(f" agent · {model_name}", style=f"color({t.text_muted})")
