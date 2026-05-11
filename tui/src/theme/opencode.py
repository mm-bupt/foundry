from rich.color import Color
from rich.style import Style


class OpencodeTheme:
    background = "#0a0a0a"
    background_panel = "#141414"
    background_element = "#1e1e1e"
    background_menu = "#282828"

    primary = "#fab283"
    secondary = "#5c9cf5"
    accent = "#9d7cd8"
    error = "#e06c75"
    warning = "#f5a742"
    success = "#7fd88f"
    info = "#56b6c2"

    text = "#eeeeee"
    text_muted = "#808080"
    border = "#484848"
    border_active = "#606060"

    heading = "#9d7cd8"
    link = "#fab283"
    link_text = "#56b6c2"
    inline_code = "#7fd88f"
    block_quote = "#e5c07b"
    bold_text = "#f5a742"
    list_item = "#fab283"
    enum_item = "#56b6c2"

    diff_added = "#4fd6be"
    diff_removed = "#c53b53"
    diff_added_bg = "#20303b"
    diff_removed_bg = "#37222c"

    @classmethod
    def user_border_style(cls) -> Style:
        return Style(color=cls.primary)

    @classmethod
    def assistant_border_style(cls) -> Style:
        return Style(color=cls.accent)

    @classmethod
    def thinking_border_style(cls) -> Style:
        return Style(color=cls.background_element)

    @classmethod
    def tool_call_style(cls) -> Style:
        return Style(color=cls.text_muted)

    @classmethod
    def tool_pending_style(cls) -> Style:
        return Style(color=cls.warning)

    @classmethod
    def tool_error_style(cls) -> Style:
        return Style(color=cls.error)

    @classmethod
    def connection_style(cls) -> Style:
        return Style(color=cls.success)

    @classmethod
    def connection_sse_style(cls) -> Style:
        return Style(color=cls.warning)

    @classmethod
    def connection_off_style(cls) -> Style:
        return Style(color=cls.error)


TOOL_ICONS = {
    "recall_memory": "✱",
    "store_memory": "←",
    "list_all_memories": "≡",
    "web_search": "◈",
    "shell": "$",
    "read": "→",
    "write": "←",
    "edit": "←",
    "glob": "✱",
    "grep": "✱",
}

DEFAULT_TOOL_ICON = "⚙"

SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
SPINNER_INTERVAL = 0.08
