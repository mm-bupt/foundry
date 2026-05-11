from textual.app import App, ComposeResult
from textual.binding import Binding

from src.screens.main_screen import MainScreen


class DreamFoundryApp(App):
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=False),
        Binding("ctrl+n", "new_session", "New Session"),
        Binding("ctrl+s", "toggle_sidebar", "Toggle Sidebar"),
        Binding("ctrl+l", "focus_input", "Focus Input"),
        Binding("ctrl+j", "prev_session", "Prev Session"),
        Binding("ctrl+k", "next_session", "Next Session"),
        Binding("ctrl+m", "switch_model", "Switch Model"),
    ]

    def __init__(self):
        super().__init__()
        self.current_session_id: str = "mock-1"
        self.current_model: str = "claude-sonnet"
        self.model_index: int = 0
        self.models: list[str] = ["claude-sonnet", "gpt-4o", "claude-haiku", "gpt-4o-mini"]
        self.connection_status: str = "disconnected"
        self.memory_count: int = 2
        self.sessions: list[dict] = [
            {"id": "mock-1", "title": "New Chat", "model_id": "claude-sonnet"},
            {"id": "mock-2", "title": "Quick Sort", "model_id": "claude-sonnet"},
            {"id": "mock-3", "title": "Refactor API", "model_id": "gpt-4o"},
        ]

    def on_mount(self) -> None:
        self.push_screen(MainScreen())

    def action_new_session(self) -> None:
        new_id = f"mock-{len(self.sessions) + 1}"
        self.sessions.insert(0, {"id": new_id, "title": "New Chat", "model_id": self.current_model})
        self.current_session_id = new_id
        screen = self.screen_stack[-1] if self.screen_stack else None
        if screen and hasattr(screen, "refresh_sessions"):
            screen.refresh_sessions()

    def action_toggle_sidebar(self) -> None:
        screen = self.screen_stack[-1] if self.screen_stack else None
        if screen and hasattr(screen, "toggle_sidebar"):
            screen.toggle_sidebar()

    def action_focus_input(self) -> None:
        screen = self.screen_stack[-1] if self.screen_stack else None
        if screen and hasattr(screen, "focus_chat_input"):
            screen.focus_chat_input()

    def action_prev_session(self) -> None:
        idx = next((i for i, s in enumerate(self.sessions) if s["id"] == self.current_session_id), 0)
        if idx > 0:
            self.current_session_id = self.sessions[idx - 1]["id"]
            screen = self.screen_stack[-1] if self.screen_stack else None
            if screen and hasattr(screen, "refresh_sessions"):
                screen.refresh_sessions()

    def action_next_session(self) -> None:
        idx = next((i for i, s in enumerate(self.sessions) if s["id"] == self.current_session_id), 0)
        if idx < len(self.sessions) - 1:
            self.current_session_id = self.sessions[idx + 1]["id"]
            screen = self.screen_stack[-1] if self.screen_stack else None
            if screen and hasattr(screen, "refresh_sessions"):
                screen.refresh_sessions()

    def action_switch_model(self) -> None:
        self.model_index = (self.model_index + 1) % len(self.models)
        self.current_model = self.models[self.model_index]
        screen = self.screen_stack[-1] if self.screen_stack else None
        if screen and hasattr(screen, "refresh_header"):
            screen.refresh_header()


def main():
    app = DreamFoundryApp()
    app.run()


if __name__ == "__main__":
    main()
