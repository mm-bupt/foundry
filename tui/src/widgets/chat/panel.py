from textual.widgets import Static
from textual.containers import Vertical, VerticalScroll

from src.widgets.chat.message import MessageBubble
from src.widgets.chat.input import ChatInputArea


MOCK_MESSAGES = [
    {"role": "user", "content": "帮我写一个快排算法"},
    {
        "role": "assistant",
        "content": "好的，这是快速排序的实现：\n\n```python\ndef quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)\n```\n\n时间复杂度：平均 O(n log n)，最坏 O(n²)。",
        "model": "claude-sonnet",
        "duration": 3.2,
    },
]


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
        self.input_area = ChatInputArea(self.model_name)
        yield self.input_area

    def on_mount(self) -> None:
        for msg in MOCK_MESSAGES:
            bubble = MessageBubble(
                role=msg["role"],
                content=msg["content"],
                model=msg.get("model", ""),
                duration=msg.get("duration", 0.0),
            )
            self.message_list.mount(bubble)
        self.message_list.scroll_end(animate=False)

    def focus_input(self) -> None:
        self.input_area.input.focus()

    def update_model(self, model_name: str) -> None:
        self.model_name = model_name
        self.input_area.update_model(model_name)
