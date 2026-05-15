from pydantic import BaseModel


class ChatRequest(BaseModel):
    content: str
    message_id: str | None = None


class ChatMessage(BaseModel):
    type: str = "chat.message"
    message_id: str = ""
    content: str = ""
