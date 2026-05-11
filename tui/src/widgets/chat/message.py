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

    def __init__(self, role: str, content: str, model: str = "", duration: float = 0.0, streaming: bool = False):
        super().__init__()
        self.role = role
        self.content = content
        self.model = model
        self.duration = duration
        self.streaming = streaming

    def on_mount(self) -> None:
        if self.streaming:
            from rich.text import Text
            self.update(Text(self.content + "▌"))
            self.set_class(True, "assistant")
        else:
            self._render_final()

    def _render_final(self) -> None:
        t = OpencodeTheme
        if self.role == "user":
            from rich.text import Text
            self.update(Text(self.content))
            self.set_class(True, "user")
        else:
            from rich.markdown import Markdown
            from rich.console import Group
            from rich.text import Text

            md = Markdown(self.content)
            group_items = [md]
            if self.model:
                meta = Text()
                meta.append(f" ▣ Agent · {self.model}", style=f"color({t.accent})")
                if self.duration:
                    meta.append(f" · {self.duration:.1f}s", style=f"color({t.text_muted})")
                group_items.append(meta)
            self.update(Group(*group_items))
            self.set_class(True, "assistant")

    def update_streaming(self, text: str) -> None:
        from rich.text import Text
        self.update(Text(text + "▌"))

    def finalize_stream(self, content: str, model: str = "", duration: float = 0.0) -> None:
        self.content = content
        self.model = model
        self.duration = duration
        self.streaming = False
        self._render_final()
