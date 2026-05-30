from pydantic import BaseModel


class SessionCreate(BaseModel):
    title: str = "New Chat"
    model_id: str = "claude-sonnet"


class SessionUpdate(BaseModel):
    title: str | None = None
    model_id: str | None = None
    system_prompt: str | None = None


class SessionResponse(BaseModel):
    id: str
    title: str
    model_id: str
    system_prompt: str
    created_at: str
    updated_at: str


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    thinking_content: str = ""
    model_id: str | None = None
    duration_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    created_at: str


def map_message(msg: dict) -> MessageResponse:
    return MessageResponse(
        id=msg["id"],
        session_id=msg["session_id"],
        role=msg["role"],
        content=msg["content"],
        thinking_content=msg.get("thinking_content", ""),
        model_id=msg.get("model_id"),
        duration_ms=msg.get("duration_ms", 0),
        tokens_in=msg.get("input_tokens", 0),
        tokens_out=msg.get("output_tokens", 0),
        created_at=msg["created_at"],
    )


class SessionDetailResponse(BaseModel):
    id: str
    title: str
    model_id: str
    system_prompt: str
    created_at: str
    updated_at: str
    messages: list[MessageResponse]
