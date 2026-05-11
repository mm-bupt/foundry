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
