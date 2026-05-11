"""
P6-P8 Patches for app.py and main_screen.py
Apply these AFTER P5 is complete.
"""

# === app.py additions ===

# 1. Add to BINDINGS list:
#    Binding("ctrl+t", "toggle_context", "Context"),

# 2. Add method to DreamFoundryApp:
"""
    def switch_to_session(self, session_id: str) -> None:
        if session_id == self.store.current_session_id:
            return
        self.store.current_session_id = session_id
        session = self.store.get_current_session()
        if session:
            self.store.current_model = session.get("model_id", "claude-sonnet")
        self.run_worker(self._switch_session(0), exclusive=True)

    def action_toggle_context(self) -> None:
        screen = self.screen_stack[-1] if len(self.screen_stack) > 1 else None
        if screen and hasattr(screen, "toggle_context"):
            screen.toggle_context()
"""

# 3. In _switch_session, change the new_idx calculation:
"""
    if direction == 0:
        new_idx = idx
    else:
        new_idx = idx + direction
"""

# === main_screen.py additions ===

# 1. Add import: from src.widgets.context.panel import ContextPanel

# 2. In compose(), after body._add_child(self.chat), add:
"""
        self.context_panel = ContextPanel()
        body._add_child(self.context_panel)
"""

# 3. Add methods:
"""
    def toggle_context(self) -> None:
        if hasattr(self, 'context_panel'):
            self.context_panel.toggle()

    async def _load_memories(self):
        memories = await self.app.store.fetch_memories(self.app.store.current_session_id)
        if hasattr(self, 'context_panel'):
            self.context_panel.update_memories(memories)
"""

# 4. In full_refresh(), add: self.run_worker(self._load_memories(), exclusive=True)

# 5. In handle_ws_event for memory.stored, add: self.run_worker(self._load_memories(), exclusive=True)

# 6. For spinner: In stream.delta handler, call self.chat.show_spinner() before creating bubble, hide after
#    In stream.done and stream.error handlers, call self.chat.hide_spinner()
