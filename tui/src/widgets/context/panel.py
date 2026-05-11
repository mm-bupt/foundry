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
