# 06 — Database Design

## SQLite + sqlite-vec

### Why SQLite

- Zero external dependencies (no Postgres server needed)
- Single file, easy backup/transfer
- sqlite-vec extension for vector similarity search
- Swappable to PostgreSQL later via SQLModel abstraction

### Database File

```
~/.dream-foundry/dream-foundry.db
```

Configurable via `DREAM_FOUNDRY_DB_PATH` environment variable.

## Tables

### `sessions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT (UUID) | PK | Session ID |
| `title` | TEXT | NOT NULL | Session display title |
| `model_id` | TEXT | NOT NULL, DEFAULT 'claude-sonnet' | Active model ID |
| `system_prompt` | TEXT | DEFAULT '' | Custom system prompt |
| `created_at` | TEXT (ISO 8601) | NOT NULL | Creation timestamp |
| `updated_at` | TEXT (ISO 8601) | NOT NULL | Last update timestamp |

### `messages`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT (UUID) | PK | Message ID |
| `session_id` | TEXT (UUID) | FK → sessions.id, NOT NULL | Parent session |
| `role` | TEXT | NOT NULL, CHECK IN ('user','assistant','system') | Message role |
| `content` | TEXT | NOT NULL | Message text content |
| `model_id` | TEXT | NULLABLE | Model used (assistant messages only) |
| `duration_ms` | INTEGER | DEFAULT 0 | Generation duration (assistant only) |
| `input_tokens` | INTEGER | DEFAULT 0 | Input token count |
| `output_tokens` | INTEGER | DEFAULT 0 | Output token count |
| `model_messages_json` | TEXT | DEFAULT '[]' | Serialized Pydantic AI ModelMessage list |
| `created_at` | TEXT (ISO 8601) | NOT NULL | Creation timestamp |

**`model_messages_json`**: Stores the full Pydantic AI `ModelMessage` history as JSON. This is the serialized form of `result.all_messages()` used to restore conversation state across runs.

### `memory_vectors`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT (UUID) | PK | Memory entry ID |
| `session_id` | TEXT (UUID) | FK → sessions.id, NOT NULL | Parent session |
| `content` | TEXT | NOT NULL | Memory text content |
| `category` | TEXT | NOT NULL, DEFAULT 'note' | Category (preference/fact/decision/project/note) |
| `embedding` | BLOB | NOT NULL | sqlite-vec vector (float32 array) |
| `created_at` | TEXT (ISO 8601) | NOT NULL | Creation timestamp |

### `tool_calls`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT (UUID) | PK | Tool call ID |
| `message_id` | TEXT (UUID) | FK → messages.id, NOT NULL | Parent message |
| `tool_name` | TEXT | NOT NULL | Tool function name |
| `args_json` | TEXT | DEFAULT '{}' | Tool arguments as JSON |
| `result` | TEXT | NULLABLE | Tool result text |
| `duration_ms` | INTEGER | DEFAULT 0 | Execution duration |
| `status` | TEXT | NOT NULL, DEFAULT 'pending' | pending/running/completed/error |
| `created_at` | TEXT (ISO 8601) | NOT NULL | Creation timestamp |

## Indexes

```sql
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_memory_vectors_session_id ON memory_vectors(session_id);
CREATE INDEX idx_memory_vectors_category ON memory_vectors(category);
CREATE INDEX idx_tool_calls_message_id ON tool_calls(message_id);
CREATE INDEX idx_sessions_updated_at ON sessions(updated_at);
```

## sqlite-vec Setup

```sql
-- Create a virtual table for vector similarity search
CREATE VIRTUAL TABLE vec_memory USING vec0(
    id TEXT PRIMARY KEY,
    embedding float[1536]  -- OpenAI text-embedding-3-small dimension
);
```

### Similarity Search Query

```sql
SELECT
    mv.id,
    mv.content,
    mv.category,
    mv.created_at,
    vec.distance
FROM vec_memory vm
JOIN memory_vectors mv ON mv.id = vm.id
WHERE mv.session_id = ?
ORDER BY vm.embedding <-> ?  -- cosine distance
LIMIT ?;
```

## SQLModel Definitions

```python
# foundry/app/db/models.py

import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from typing import Optional

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
    role: str  # "user" | "assistant" | "system"
    content: str
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
    embedding: bytes  # sqlite-vec float32 blob
    created_at: str = Field(default_factory=utcnow)

class ToolCall(SQLModel, table=True):
    __tablename__ = "tool_calls"
    id: str = Field(default_factory=new_id, primary_key=True)
    message_id: str = Field(foreign_key="messages.id")
    tool_name: str
    args_json: str = Field(default="{}")
    result: Optional[str] = Field(default=None)
    duration_ms: int = Field(default=0)
    status: str = Field(default="pending")
    created_at: str = Field(default_factory=utcnow)
```

## Database Initialization

```python
# foundry/app/db/database.py

import aiosqlite
from pathlib import Path

DB_PATH = Path.home() / ".dream-foundry" / "dream-foundry.db"

async def get_db() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db

async def init_db(db: aiosqlite.Connection):
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (...);
        CREATE TABLE IF NOT EXISTS messages (...);
        CREATE TABLE IF NOT EXISTS memory_vectors (...);
        CREATE TABLE IF NOT EXISTS tool_calls (...);
        -- indexes
        -- vec virtual table
    """)
    await db.commit()
```

## CRUD Operations

### Sessions

```python
async def create_session(db, title="New Chat", model_id="claude-sonnet") -> Session
async def get_session(db, session_id: str) -> Session | None
async def list_sessions(db) -> list[Session]
async def update_session(db, session_id: str, **kwargs) -> Session
async def delete_session(db, session_id: str) -> bool
```

### Messages

```python
async def create_message(db, session_id, role, content, **kwargs) -> Message
async def list_messages(db, session_id: str) -> list[Message]
async def get_message(db, message_id: str) -> Message | None
async def update_message(db, message_id: str, **kwargs) -> Message
```

### Memory

```python
async def store_memory(db, session_id, content, category, embedding) -> MemoryVector
async def search_memory(db, session_id, query_embedding, limit=5) -> list[MemoryVector]
async def list_memory(db, session_id) -> list[MemoryVector]
async def delete_memory(db, memory_id: str) -> bool
```

### Tool Calls

```python
async def create_tool_call(db, message_id, tool_name, args) -> ToolCall
async def update_tool_call(db, tool_call_id, result, status) -> ToolCall
async def list_tool_calls(db, message_id: str) -> list[ToolCall]
```
