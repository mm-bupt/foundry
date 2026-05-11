from textual.screen import Screen
from textual.containers import Horizontal

from src.widgets.common.header import AppHeader
from src.widgets.common.footer import AppFooter
from src.widgets.session.sidebar import SessionSidebar
from src.widgets.chat.panel import ChatPanel


class MainScreen(Screen):
    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }
    MainScreen > Horizontal {
        height: 1fr;
    }
    """

    def compose(self):
        self.header = AppHeader()
        yield self.header
        body = Horizontal()
        self.sidebar = SessionSidebar()
        body._add_child(self.sidebar)
        self.chat = ChatPanel()
        body._add_child(self.chat)
        yield body
        self.footer = AppFooter(memory_count=self.app.memory_count)
        yield self.footer

    def on_mount(self) -> None:
        self.sidebar.update_sessions(self.app.sessions, self.app.current_session_id)
        self.header.update_connection(self.app.connection_status)

    def refresh_sessions(self) -> None:
        self.sidebar.update_sessions(self.app.sessions, self.app.current_session_id)

    def refresh_header(self) -> None:
        self.header.update_model(self.app.current_model)
        self.chat.update_model(self.app.current_model)

    def toggle_sidebar(self) -> None:
        self.sidebar.toggle()

    def focus_chat_input(self) -> None:
        self.chat.focus_input()
