from textual.screen import Screen
from textual.containers import Horizontal

from src.widgets.common.header import AppHeader
from src.widgets.common.footer import AppFooter
from src.widgets.session.sidebar import SessionSidebar
from src.widgets.chat.panel import ChatPanel
from src.widgets.chat.message import MessageBubble
from src.widgets.context.panel import ContextPanel
from src.theme.opencode import OpencodeTheme, TOOL_ICONS, DEFAULT_TOOL_ICON


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
        self.context_panel = ContextPanel()
        body._add_child(self.context_panel)
        yield body
        self.footer = AppFooter(memory_count=self.app.store.memory_count)
        yield self.footer

    def on_mount(self) -> None:
        self.sidebar.update_sessions(self.app.store.sessions, self.app.store.current_session_id)
        self.header.update_connection(self.app.store.connection_status)
        self.header.update_model(self.app.store.current_model)
        self._load_messages()

    def _load_messages(self):
        self.chat.clear_messages()
        for msg in self.app.store.messages:
            bubble = MessageBubble(
                role=msg["role"],
                content=msg["content"],
                model=msg.get("model_id", ""),
                duration=msg.get("duration_ms", 0) / 1000.0,
            )
            self.chat.add_message(bubble)
        self.chat.scroll_to_bottom()

    def full_refresh(self) -> None:
        self.sidebar.update_sessions(self.app.store.sessions, self.app.store.current_session_id)
        self.header.update_model(self.app.store.current_model)
        self.header.update_connection(self.app.store.connection_status)
        self.chat.update_model(self.app.store.current_model)
        self.footer.update_memory_count(self.app.store.memory_count)
        self._load_messages()
        self.run_worker(self._load_memories(), exclusive=True)

    def refresh_sessions(self) -> None:
        self.sidebar.update_sessions(self.app.store.sessions, self.app.store.current_session_id)

    def refresh_header(self) -> None:
        self.header.update_model(self.app.store.current_model)
        self.chat.update_model(self.app.store.current_model)

    def toggle_sidebar(self) -> None:
        self.sidebar.toggle()

    def toggle_context(self) -> None:
        if hasattr(self, 'context_panel'):
            self.context_panel.toggle()

    async def _load_memories(self):
        memories = await self.app.store.fetch_memories(self.app.store.current_session_id)
        if hasattr(self, 'context_panel'):
            self.context_panel.update_memories(memories)

    def focus_chat_input(self) -> None:
        self.chat.focus_input()

    def handle_ws_event(self, event: dict) -> None:
        event_type = event.get("type", "")

        if event_type == "stream.delta":
            text = event.get("text", "")
            if self.app._streaming_bubble is None:
                self.chat.show_spinner()
                bubble = MessageBubble(role="assistant", content="", streaming=True)
                self.chat.add_message(bubble)
                self.chat.hide_spinner()
                self.app._streaming_bubble = bubble
                self.app._streaming_text = ""
            self.app._streaming_text += text
            self.app._streaming_bubble.update_streaming(self.app._streaming_text)
            self.chat.scroll_to_bottom()

        elif event_type == "stream.done":
            self.chat.hide_spinner()
            if self.app._streaming_bubble:
                self.app._streaming_bubble.finalize_stream(
                    content=self.app._streaming_text,
                    model=self.app.store.current_model,
                    duration=event.get("duration_ms", 0) / 1000.0,
                )
                self.app._streaming_bubble = None
                self.app._streaming_text = ""

        elif event_type == "stream.error":
            self.chat.hide_spinner()
            error = event.get("error", {})
            bubble = MessageBubble(role="assistant", content=f"Error: {error.get('message', 'Unknown error')}")
            self.chat.add_message(bubble)
            self.app._streaming_bubble = None
            self.app._streaming_text = ""

        elif event_type == "tool.call":
            tool_name = event.get("tool_name", "")
            args = event.get("args", {})
            tc_id = event.get("tool_call_id", "")
            icon = TOOL_ICONS.get(tool_name, DEFAULT_TOOL_ICON)
            self.app._pending_tool_calls[tc_id] = {"tool_name": tool_name, "icon": icon}
            arg_str = " ".join(f"{k}={v}" for k, v in args.items()) if args else ""
            from textual.widgets import Static
            from rich.text import Text
            t = OpencodeTheme
            tool_widget = Static(
                Text(f" {icon} {tool_name} {arg_str}", style=f"color({t.text_muted})"),
                classes="tool-call tool-call-pending",
            )
            tool_widget._tool_call_id = tc_id
            self.chat.add_message(tool_widget)

        elif event_type == "tool.result":
            tc_id = event.get("tool_call_id", "")
            tool_name = event.get("tool_name", "")
            result = event.get("result", "")
            icon = TOOL_ICONS.get(tool_name, DEFAULT_TOOL_ICON)
            self.app._pending_tool_calls.pop(tc_id, None)
            for child in self.chat.message_list.children:
                if hasattr(child, "_tool_call_id") and child._tool_call_id == tc_id:
                    t = OpencodeTheme
                    from rich.text import Text
                    icon = TOOL_ICONS.get(tool_name, DEFAULT_TOOL_ICON)
                    display_result = result[:200] + "..." if len(result) > 200 else result
                    child.update(
                        Text(f" {icon} {tool_name} → {display_result}", style=f"color({t.text_muted})")
                    )
                    child.set_class(False, "tool-call-pending")
                    break

        elif event_type == "memory.stored":
            self.app.store.memory_count += 1
            self.footer.update_memory_count(self.app.store.memory_count)
            self.run_worker(self._load_memories(), exclusive=True)

        elif event_type == "connection.lost":
            self.app.store.connection_status = "disconnected"
            self.header.update_connection("disconnected")

        elif event_type == "pong":
            pass
