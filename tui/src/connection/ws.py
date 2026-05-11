import asyncio
import json
import uuid
from typing import Callable, Awaitable

import websockets


class WSClient:
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.ws = None
        self.session_id: str = ""
        self.connected: bool = False
        self._on_event: Callable[[dict], Awaitable[None]] | None = None
        self._recv_task: asyncio.Task | None = None

    def set_event_handler(self, handler: Callable[[dict], Awaitable[None]]):
        self._on_event = handler

    async def connect(self, session_id: str) -> bool:
        self.session_id = session_id
        url = f"{self.base_url}/ws/{session_id}"
        try:
            self.ws = await websockets.connect(url, ping_interval=30, ping_timeout=60)
            self.connected = True
            self._recv_task = asyncio.create_task(self._recv_loop())
            return True
        except Exception:
            self.connected = False
            return False

    async def _recv_loop(self):
        try:
            async for raw in self.ws:
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if self._on_event:
                    await self._on_event(event)
        except websockets.ConnectionClosed:
            pass
        except Exception:
            pass
        finally:
            self.connected = False
            if self._on_event:
                await self._on_event({"type": "connection.lost"})

    async def send_message(self, content: str):
        if not self.ws or not self.connected:
            return
        msg = {
            "type": "chat.message",
            "message_id": str(uuid.uuid4()),
            "content": content,
        }
        await self.ws.send(json.dumps(msg))

    async def interrupt(self):
        if not self.ws or not self.connected:
            return
        await self.ws.send(json.dumps({"type": "chat.interrupt"}))

    async def ping(self):
        if not self.ws or not self.connected:
            return
        await self.ws.send(json.dumps({"type": "ping"}))

    async def disconnect(self):
        if self._recv_task:
            self._recv_task.cancel()
            self._recv_task = None
        if self.ws:
            await self.ws.close()
            self.ws = None
        self.connected = False

    async def reconnect(self) -> bool:
        await self.disconnect()
        if self.session_id:
            return await self.connect(self.session_id)
        return False
