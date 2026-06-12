from pydantic import BaseModel


class ToolCallResponse(BaseModel):
    id: str
    tool_name: str
    args_json: str = "{}"
    result: str | None = None
    status: str = "pending"


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
    parent_id: str | None = None
    created_at: str
    updated_at: str


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]


class TaskRecordResponse(BaseModel):
    id: str
    parent_session_id: str
    parent_message_id: str | None = None
    subagent_type: str = ""
    description: str = ""
    status: str = "running"
    background: bool = False
    result_preview: str | None = None
    created_at: str = ""
    completed_at: str | None = None


class SessionStats(BaseModel):
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    context_tokens: int = 0
    message_count: int = 0


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
    tool_calls: list[ToolCallResponse] = []


def map_message(msg: dict, tool_calls: list[dict] | None = None) -> MessageResponse:
    tc_list = []
    if tool_calls:
        for tc in tool_calls:
            tc_list.append(ToolCallResponse(
                id=tc["id"],
                tool_name=tc["tool_name"],
                args_json=tc.get("args_json", "{}"),
                result=tc.get("result"),
                status=tc.get("status", "pending"),
            ))
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
        tool_calls=tc_list,
    )


class SessionDetailResponse(BaseModel):
    id: str
    title: str
    model_id: str
    system_prompt: str
    parent_id: str | None = None
    created_at: str
    updated_at: str
    messages: list[MessageResponse]
    stats: SessionStats = SessionStats()
    task_records: list[TaskRecordResponse] = []
