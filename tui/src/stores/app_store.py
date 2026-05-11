import httpx

API_BASE = "http://localhost:8000/api"


class AppStore:
    def __init__(self):
        self.sessions: list[dict] = []
        self.current_session_id: str = ""
        self.current_model: str = "claude-sonnet"
        self.models: list[dict] = []
        self.memory_count: int = 0
        self.messages: list[dict] = []
        self.connection_status: str = "disconnected"

    async def fetch_sessions(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/sessions")
            data = resp.json()
            self.sessions = data.get("sessions", [])
            return self.sessions

    async def create_session(self, title: str = "New Chat", model_id: str = "claude-sonnet") -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{API_BASE}/sessions", json={"title": title, "model_id": model_id})
            session = resp.json()
            self.sessions.insert(0, session)
            return session

    async def get_session(self, session_id: str) -> dict | None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/sessions/{session_id}")
            if resp.status_code == 404:
                return None
            return resp.json()

    async def delete_session(self, session_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(f"{API_BASE}/sessions/{session_id}")
            if resp.status_code == 204:
                self.sessions = [s for s in self.sessions if s["id"] != session_id]
                return True
            return False

    async def update_session(self, session_id: str, **kwargs) -> dict | None:
        async with httpx.AsyncClient() as client:
            resp = await client.patch(f"{API_BASE}/sessions/{session_id}", json=kwargs)
            if resp.status_code == 404:
                return None
            updated = resp.json()
            for i, s in enumerate(self.sessions):
                if s["id"] == session_id:
                    self.sessions[i] = updated
                    break
            return updated

    async def fetch_models(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/models")
            data = resp.json()
            self.models = data.get("models", [])
            return self.models

    async def fetch_memories(self, session_id: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{API_BASE}/memory/{session_id}")
            data = resp.json()
            memories = data.get("memories", [])
            self.memory_count = len(memories)
            return memories

    async def delete_memory(self, memory_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(f"{API_BASE}/memory/item/{memory_id}")
            return resp.status_code == 204

    def get_current_session(self) -> dict | None:
        for s in self.sessions:
            if s["id"] == self.current_session_id:
                return s
        return None
