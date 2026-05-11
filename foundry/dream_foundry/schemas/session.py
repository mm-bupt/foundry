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


class SessionDetailResponse(BaseModel):
    id: str
    title: str
    model_id: str
    system_prompt: str
    created_at: str
    updated_at: str
    messages: list[dict]
