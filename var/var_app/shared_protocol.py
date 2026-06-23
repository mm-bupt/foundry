import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatMessageCmd:
    type: str = "chat.message"
    message_id: str = ""
    content: str = ""
    model_id: str = ""


@dataclass
class StreamDelta:
    type: str = "stream.delta"
    message_id: str = ""
    part_id: str = ""
    text: str = ""


@dataclass
class StreamDone:
    type: str = "stream.done"
    message_id: str = ""
    usage: dict = field(default_factory=dict)
    duration_ms: int = 0


@dataclass
class StreamError:
    type: str = "stream.error"
    message_id: str = ""
    error: dict = field(default_factory=dict)


@dataclass
class ToolCallEvent:
    type: str = "tool.call"
    tool_call_id: str = ""
    tool_name: str = ""
    args: dict = field(default_factory=dict)


@dataclass
class ToolResultEvent:
    type: str = "tool.result"
    tool_call_id: str = ""
    tool_name: str = ""
    result: str = ""
    duration_ms: int = 0


@dataclass
class ThinkingDelta:
    type: str = "thinking.delta"
    message_id: str = ""
    text: str = ""


@dataclass
class MemoryStored:
    type: str = "memory.stored"
    memory_id: str = ""
    content: str = ""
    category: str = ""


@dataclass
class Ping:
    type: str = "ping"


@dataclass
class Pong:
    type: str = "pong"


@dataclass
class SessionTitleUpdated:
    type: str = "session.title_updated"
    session_id: str = ""
    title: str = ""


@dataclass
class TaskStarted:
    type: str = "task.started"
    task_id: str = ""
    subagent_type: str = ""
    description: str = ""
    background: bool = False


@dataclass
class TaskCompleted:
    type: str = "task.completed"
    task_id: str = ""
    subagent_type: str = ""
    result_preview: str = ""
    duration_ms: int = 0


@dataclass
class TaskError:
    type: str = "task.error"
    task_id: str = ""
    subagent_type: str = ""
    error: str = ""


@dataclass
class CompactCmd:
    type: str = "chat.compact"
    session_id: str = ""


@dataclass
class CompactionDone:
    type: str = "compaction.done"
    session_id: str = ""
    summary_message_id: str = ""


@dataclass
class TodoUpdated:
    type: str = "todo.updated"
    session_id: str = ""
    todos: list = field(default_factory=list)


@dataclass
class QuestionAsked:
    type: str = "question.asked"
    question_id: str = ""
    questions: list = field(default_factory=list)


def parse_command(data: dict) -> ChatMessageCmd | CompactCmd | dict | None:
    msg_type = data.get("type", "")
    if msg_type == "chat.message":
        return ChatMessageCmd(
            message_id=data.get("message_id", str(uuid.uuid4())),
            content=data.get("content", ""),
            model_id=data.get("model_id", ""),
        )
    if msg_type == "chat.compact":
        return CompactCmd(
            session_id=data.get("session_id", ""),
        )
    if msg_type in ("question.reply", "question.reject"):
        return data
    return None


def to_dict(event: Any) -> dict:
    if hasattr(event, "__dataclass_fields__"):
        return {
            k: v
            for k, v in event.__dict__.items()
            if v is not None and v != "" and v != {} and v != []
        }
    if isinstance(event, dict):
        return event
    return {"type": "unknown"}
