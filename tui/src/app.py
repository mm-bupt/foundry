from textual.app import App
from textual.binding import Binding

from src.screens.main_screen import MainScreen
from src.stores.app_store import AppStore
from src.connection.ws import WSClient


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
        Binding("ctrl+backslash", "interrupt", "Interrupt"),
    ]

    def __init__(self, backend_url: str = "http://localhost:8000"):
        super().__init__()
        self.store = AppStore()
        self.ws = WSClient(base_url=backend_url.replace("http", "ws"))
        self.ws.set_event_handler(self._on_ws_event)
        self._streaming_bubble = None
        self._streaming_text = ""
        self._pending_tool_calls: dict[str, dict] = {}

    def on_mount(self) -> None:
        self.push_screen(MainScreen())
        self.run_worker(self._init_app(), exclusive=True)

    async def _init_app(self):
        try:
            await self.store.fetch_models()
            sessions = await self.store.fetch_sessions()
            if not sessions:
                session = await self.store.create_session()
            else:
                session = sessions[0]
            self.store.current_session_id = session["id"]
            self.store.current_model = session.get("model_id", "claude-sonnet")
            await self.ws.connect(session["id"])
            self.store.connection_status = "connected" if self.ws.connected else "disconnected"
            await self.store.fetch_memories(session["id"])
            session_data = await self.store.get_session(session["id"])
            if session_data:
                self.store.messages = session_data.get("messages", [])
            screen = self.screen_stack[-1] if len(self.screen_stack) > 1 else None
            if screen and hasattr(screen, "full_refresh"):
                screen.full_refresh()
        except Exception as e:
            self.store.connection_status = "disconnected"

    async def _on_ws_event(self, event: dict):
        event_type = event.get("type", "")
        screen = self.screen_stack[-1] if len(self.screen_stack) > 1 else None
        if not screen or not hasattr(screen, "handle_ws_event"):
            return
        self.call_from_thread(screen.handle_ws_event, event)

    def handle_ws_event_sync(self, event: dict):
        screen = self.screen_stack[-1] if len(self.screen_stack) > 1 else None
        if screen and hasattr(screen, "handle_ws_event"):
            screen.handle_ws_event(event)

    def action_new_session(self) -> None:
        self.run_worker(self._new_session(), exclusive=True)

    async def _new_session(self):
        session = await self.store.create_session(model_id=self.store.current_model)
        self.store.current_session_id = session["id"]
        self.store.messages = []
        self.store.memory_count = 0
        await self.ws.disconnect()
        await self.ws.connect(session["id"])
        self.store.connection_status = "connected" if self.ws.connected else "disconnected"
        screen = self.screen_stack[-1] if len(self.screen_stack) > 1 else None
        if screen and hasattr(screen, "full_refresh"):
            screen.full_refresh()

    def action_toggle_sidebar(self) -> None:
        screen = self.screen_stack[-1] if len(self.screen_stack) > 1 else None
        if screen and hasattr(screen, "toggle_sidebar"):
            screen.toggle_sidebar()

    def action_focus_input(self) -> None:
        screen = self.screen_stack[-1] if len(self.screen_stack) > 1 else None
        if screen and hasattr(screen, "focus_chat_input"):
            screen.focus_chat_input()

    def action_prev_session(self) -> None:
        self.run_worker(self._switch_session(-1), exclusive=True)

    def action_next_session(self) -> None:
        self.run_worker(self._switch_session(1), exclusive=True)

    async def _switch_session(self, direction: int):
        sessions = self.store.sessions
        idx = next((i for i, s in enumerate(sessions) if s["id"] == self.store.current_session_id), 0)
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(sessions):
            return
        session = sessions[new_idx]
        self.store.current_session_id = session["id"]
        self.store.current_model = session.get("model_id", "claude-sonnet")
        await self.ws.disconnect()
        await self.ws.connect(session["id"])
        self.store.connection_status = "connected" if self.ws.connected else "disconnected"
        await self.store.fetch_memories(session["id"])
        session_data = await self.store.get_session(session["id"])
        self.store.messages = session_data.get("messages", []) if session_data else []
        screen = self.screen_stack[-1] if len(self.screen_stack) > 1 else None
        if screen and hasattr(screen, "full_refresh"):
            screen.full_refresh()

    def action_switch_model(self) -> None:
        models = self.store.models
        if not models:
            return
        current = self.store.current_model
        idx = next((i for i, m in enumerate(models) if m["id"] == current), -1)
        next_idx = (idx + 1) % len(models)
        self.store.current_model = models[next_idx]["id"]
        self.run_worker(
            self.store.update_session(self.store.current_session_id, model_id=self.store.current_model),
            exclusive=True,
        )
        screen = self.screen_stack[-1] if len(self.screen_stack) > 1 else None
        if screen and hasattr(screen, "refresh_header"):
            screen.refresh_header()

    def action_interrupt(self) -> None:
        self.run_worker(self.ws.interrupt(), exclusive=True)

    def send_chat_message(self, content: str):
        self.run_worker(self._send_chat(content), exclusive=True)

    async def _send_chat(self, content: str):
        await self.ws.send_message(content)


def main():
    app = DreamFoundryApp()
    app.run()


if __name__ == "__main__":
    main()
