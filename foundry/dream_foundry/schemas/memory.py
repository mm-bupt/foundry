from pydantic import BaseModel


class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 5


class MemoryResponse(BaseModel):
    id: str
    session_id: str
    content: str
    category: str
    created_at: str
    relevance_score: float | None = None


class MemoryListResponse(BaseModel):
    memories: list[MemoryResponse]


class MemorySearchResponse(BaseModel):
    memories: list[MemoryResponse]
