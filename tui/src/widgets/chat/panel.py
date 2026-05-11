from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static
from rich.text import Text

from src.widgets.chat.message import MessageBubble
from src.widgets.chat.input import ChatInputArea
from src.theme.opencode import OpencodeTheme


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
        self.input_area = ChatInputArea(self.model_name, self._on_send)
        yield self.input_area

    def _on_send(self, content: str):
        if not content.strip():
            return
        bubble = MessageBubble(role="user", content=content)
        self.add_message(bubble)
        self.scroll_to_bottom()
        app = self.app
        if hasattr(app, "send_chat_message"):
            app.send_chat_message(content)

    def add_message(self, widget) -> None:
        self.message_list.mount(widget)

    def clear_messages(self) -> None:
        self.message_list.remove_children()

    def scroll_to_bottom(self) -> None:
        self.message_list.scroll_end(animate=False)

    def focus_input(self) -> None:
        self.input_area.input.focus()

    def update_model(self, model_name: str) -> None:
        self.model_name = model_name
        self.input_area.update_model(model_name)

    def show_spinner(self) -> None:
        t = OpencodeTheme
        self._spinner = Static(Text(" ⠋ Thinking...", style=f"color({t.primary})"), classes="spinner")
        self.message_list.mount(self._spinner)
        self.scroll_to_bottom()

    def hide_spinner(self) -> None:
        if hasattr(self, '_spinner') and self._spinner is not None:
            self._spinner.remove()
            self._spinner = None
