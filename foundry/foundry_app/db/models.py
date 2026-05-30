import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(default_factory=new_id, primary_key=True)
    title: str = Field(default="New Chat")
    model_id: str = Field(default="claude-sonnet")
    system_prompt: str = Field(default="")
    created_at: str = Field(default_factory=utcnow)
    updated_at: str = Field(default_factory=utcnow)


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: str = Field(default_factory=new_id, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id")
    role: str
    content: str
    thinking_content: str = Field(default="")
    model_id: Optional[str] = Field(default=None)
    duration_ms: int = Field(default=0)
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    model_messages_json: str = Field(default="[]")
    created_at: str = Field(default_factory=utcnow)


class MemoryVector(SQLModel, table=True):
    __tablename__ = "memory_vectors"

    id: str = Field(default_factory=new_id, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id")
    content: str
    category: str = Field(default="note")
    embedding: bytes = Field(default=b"")
    created_at: str = Field(default_factory=utcnow)


class ToolCallRecord(SQLModel, table=True):
    __tablename__ = "tool_calls"

    id: str = Field(default_factory=new_id, primary_key=True)
    message_id: str = Field(foreign_key="messages.id")
    tool_name: str
    args_json: str = Field(default="{}")
    result: Optional[str] = Field(default=None)
    duration_ms: int = Field(default=0)
    status: str = Field(default="pending")
    created_at: str = Field(default_factory=utcnow)
