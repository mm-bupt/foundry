from dataclasses import dataclass
from typing import Callable, Awaitable


@dataclass
class AgentDeps:
    session_id: str
    model_id: str
    work_dir: str = ""
    send_event: Callable[[dict], Awaitable[None]] | None = None
    is_subagent: bool = False
    parent_session_id: str | None = None
    task_id: str | None = None
