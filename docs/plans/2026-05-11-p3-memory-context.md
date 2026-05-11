# P3: Memory + Context Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace brute-force vector search with sqlite-vec, add LLM-based history summarization, add token-aware context trimming, and emit MemoryStored events to clients.

**Architecture:** sqlite-vec virtual table for fast cosine similarity search. Token-counting context trimmer using model context windows from registry. LLM summarizer that calls a lightweight model to compress old messages. Tool events emitted through the existing WS/SSE send_event callback.

**Tech Stack:** sqlite-vec, aiosqlite, pydantic-ai, openai (embeddings + summarization)

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `foundry/dream_foundry/config.py` | Add `summary_model` setting |
| Modify | `foundry/dream_foundry/db/database.py` | Add vec_memory virtual table to schema |
| Modify | `foundry/dream_foundry/db/crud.py` | Replace brute-force search with sqlite-vec query |
| Modify | `foundry/dream_foundry/agent/memory.py` | Add caching, improve error handling |
| Modify | `foundry/dream_foundry/agent/context.py` | Token-aware trimming + LLM summarization |
| Modify | `foundry/dream_foundry/agent/core.py` | Pass send_event to deps, emit MemoryStored |
| Modify | `foundry/dream_foundry/agent/tools.py` | Emit MemoryStored event via callback |
| Modify | `foundry/dream_foundry/agent/registry.py` | Add token estimate helper |
| Modify | `foundry/pyproject.toml` | Add sqlite-vec dependency |

---

## Chunk 1: sqlite-vec Integration

### Task 1: Add sqlite-vec dependency

**Files:**
- Modify: `foundry/pyproject.toml`

- [ ] **Step 1: Add sqlite-vec to dependencies**

Add `sqlite-vec>=0.1` to the dependencies list in `foundry/pyproject.toml`.

- [ ] **Step 2: Install dependency**

Run: `pip install sqlite-vec`

- [ ] **Step 3: Commit**

```bash
git add foundry/pyproject.toml
git commit -m "chore: add sqlite-vec dependency"
```

### Task 2: Update database schema with vec_memory virtual table

**Files:**
- Modify: `foundry/dream_foundry/db/database.py`

- [ ] **Step 1: Add sqlite-vec initialization to database.py**

In `foundry/dream_foundry/db/database.py`, update `_connect()` to load the sqlite-vec extension and update `_SCHEMA` to create the `vec_memory` virtual table.

Add after `import aiosqlite`:
```python
import sqlite_vec
```

Update `_connect()` to load the extension after connecting:
```python
async def _connect() -> aiosqlite.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(settings.db_path))
    db.row_factory = aiosqlite.Row
    await db.enable_load_extension(True)
    await db.load_extension(sqlite_vec.loadable_path())
    await db.enable_load_extension(False)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db
```

Append to `_SCHEMA` string (after existing indexes):
```sql
CREATE VIRTUAL TABLE IF NOT EXISTS vec_memory USING vec0(
    id TEXT PRIMARY KEY,
    embedding float[1536]
);
```

- [ ] **Step 2: Commit**

```bash
git add foundry/dream_foundry/db/database.py
git commit -m "feat: add sqlite-vec virtual table for vector search"
```

### Task 3: Replace brute-force memory search with sqlite-vec query

**Files:**
- Modify: `foundry/dream_foundry/db/crud.py`

- [ ] **Step 1: Update store_memory to also insert into vec_memory**

In `foundry/dream_foundry/db/crud.py`, update `store_memory()` to insert into both `memory_vectors` and `vec_memory`:

```python
async def store_memory(
    db: aiosqlite.Connection,
    session_id: str,
    content: str,
    category: str,
    embedding: bytes,
) -> dict:
    mid = new_id()
    now = utcnow()
    await db.execute(
        "INSERT INTO memory_vectors (id, session_id, content, category, embedding, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (mid, session_id, content, category, embedding, now),
    )
    await db.execute(
        "INSERT INTO vec_memory (id, embedding) VALUES (?, ?)",
        (mid, embedding),
    )
    await db.commit()
    return {
        "id": mid,
        "session_id": session_id,
        "content": content,
        "category": category,
        "created_at": now,
    }
```

- [ ] **Step 2: Replace search_memory with sqlite-vec query**

Replace the entire `search_memory()` function with:

```python
async def search_memory(
    db: aiosqlite.Connection, session_id: str, query_embedding: bytes, limit: int = 5
) -> list[dict]:
    try:
        cursor = await db.execute(
            """
            SELECT mv.id, mv.session_id, mv.content, mv.category, mv.created_at, vm.distance
            FROM vec_memory vm
            JOIN memory_vectors mv ON mv.id = vm.id
            WHERE mv.session_id = ?
            ORDER BY vm.embedding <-> ?
            LIMIT ?
            """,
            (session_id, query_embedding, limit),
        )
        rows = await cursor.fetchall()
        results = []
        for row in rows:
            r = dict(row)
            results.append(
                {
                    "id": r["id"],
                    "session_id": r["session_id"],
                    "content": r["content"],
                    "category": r["category"],
                    "created_at": r["created_at"],
                    "relevance_score": round(1.0 - r["distance"], 4),
                }
            )
        return results
    except Exception:
        return await _fallback_search(db, session_id, query_embedding, limit)
```

Add the fallback function for when sqlite-vec is unavailable:

```python
async def _fallback_search(
    db: aiosqlite.Connection, session_id: str, query_embedding: bytes, limit: int
) -> list[dict]:
    import struct
    from dream_foundry.config import settings

    dim = len(query_embedding) // 4
    cursor = await db.execute(
        "SELECT id, session_id, content, category, created_at, embedding FROM memory_vectors WHERE session_id = ?",
        (session_id,),
    )
    rows = await cursor.fetchall()

    def cosine_sim(a: bytes, b: bytes) -> float:
        va = struct.unpack(f"{dim}f", a)
        vb = struct.unpack(f"{dim}f", b)
        dot = sum(x * y for x, y in zip(va, vb))
        na = sum(x * x for x in va) ** 0.5
        nb = sum(x * x for x in vb) ** 0.5
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    scored = []
    for row in rows:
        r = dict(row)
        if not r["embedding"] or len(r["embedding"]) < 4:
            continue
        sim = cosine_sim(query_embedding, r["embedding"])
        scored.append((sim, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for sim, r in scored[:limit]:
        results.append(
            {
                "id": r["id"],
                "session_id": r["session_id"],
                "content": r["content"],
                "category": r["category"],
                "created_at": r["created_at"],
                "relevance_score": round(sim, 4),
            }
        )
    return results
```

- [ ] **Step 3: Update delete_memory to also delete from vec_memory**

```python
async def delete_memory(db: aiosqlite.Connection, memory_id: str) -> bool:
    await db.execute("DELETE FROM vec_memory WHERE id = ?", (memory_id,))
    cursor = await db.execute("DELETE FROM memory_vectors WHERE id = ?", (memory_id,))
    await db.commit()
    return cursor.rowcount > 0
```

- [ ] **Step 4: Commit**

```bash
git add foundry/dream_foundry/db/crud.py
git commit -m "feat: use sqlite-vec for vector similarity search"
```

---

## Chunk 2: Context Management — Token-Aware Trimming + LLM Summarization

### Task 4: Add token estimation helper to registry

**Files:**
- Modify: `foundry/dream_foundry/agent/registry.py`

- [ ] **Step 1: Add estimate_tokens function**

Append to `foundry/dream_foundry/agent/registry.py`:

```python
def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 3.5))


def get_context_budget(model_id: str) -> int:
    info = MODEL_REGISTRY.get(model_id)
    if not info:
        return 100000
    return int(info.context_window * 0.8) - info.max_output_tokens
```

- [ ] **Step 2: Commit**

```bash
git add foundry/dream_foundry/agent/registry.py
git commit -m "feat: add token estimation and context budget helpers"
```

### Task 5: Add summary_model config setting

**Files:**
- Modify: `foundry/dream_foundry/config.py`

- [ ] **Step 1: Add summary_model field**

Add to the `Settings` class in `foundry/dream_foundry/config.py`:

```python
    summary_model: str = "openai:gpt-4o-mini"
```

- [ ] **Step 2: Commit**

```bash
git add foundry/dream_foundry/config.py
git commit -m "feat: add summary_model config setting"
```

### Task 6: Rewrite context.py with token-aware trimming + LLM summarization

**Files:**
- Modify: `foundry/dream_foundry/agent/context.py`

- [ ] **Step 1: Replace entire file**

Replace `foundry/dream_foundry/agent/context.py` with:

```python
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    UserPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
)

from dream_foundry.agent.registry import estimate_tokens


async def trim_and_summarize(messages: list[ModelMessage]) -> list[ModelMessage]:
    if len(messages) <= 10:
        return messages

    total_tokens = sum(_count_msg_tokens(m) for m in messages)

    if total_tokens < 40000:
        return messages

    recent_keep = 15
    recent = messages[-recent_keep:]
    old = messages[:-recent_keep]

    summary = await _generate_summary(old)

    summary_part = SystemPromptPart(content=f"[Conversation Summary]\n{summary}")
    summary_msg = ModelRequest(parts=[summary_part])

    return [summary_msg] + recent


def _count_msg_tokens(msg: ModelMessage) -> int:
    total = 0
    if isinstance(msg, ModelRequest):
        for part in msg.parts:
            if isinstance(part, UserPromptPart):
                content = part.content
                if isinstance(content, str):
                    total += estimate_tokens(content)
                elif isinstance(content, list):
                    total += estimate_tokens(" ".join(str(c) for c in content))
    elif isinstance(msg, ModelResponse):
        for part in msg.parts:
            if isinstance(part, TextPart):
                total += estimate_tokens(part.content)
    return total


async def _generate_summary(messages: list[ModelMessage]) -> str:
    text = _build_compact_summary(messages)
    if not text:
        return "Previous conversation occurred."

    try:
        from dream_foundry.config import settings

        agent = Agent(
            settings.summary_model,
            instructions="Summarize concisely. Preserve key decisions, preferences, and technical details. Use bullet points.",
        )
        result = await agent.run(
            f"Summarize this conversation in under 300 words:\n\n{text}"
        )
        return str(result.output)
    except Exception:
        return text[:2000]


def _build_compact_summary(messages: list[ModelMessage]) -> str:
    lines = []
    for msg in messages:
        try:
            if isinstance(msg, ModelRequest):
                for part in msg.parts:
                    if isinstance(part, UserPromptPart):
                        content = part.content
                        if isinstance(content, str):
                            text = content[:300]
                        elif isinstance(content, list):
                            text = " ".join(str(c)[:150] for c in content)[:300]
                        else:
                            text = str(content)[:300]
                        lines.append(f"User: {text}")
            elif isinstance(msg, ModelResponse):
                for part in msg.parts:
                    if isinstance(part, TextPart):
                        lines.append(f"Assistant: {part.content[:300]}")
                    elif isinstance(part, ToolCallPart):
                        lines.append(f"Tool call: {part.tool_name}")
                    elif isinstance(part, ToolReturnPart):
                        lines.append(f"Tool result: {str(part.content)[:150]}")
        except Exception:
            pass

    if not lines:
        return ""

    return "\n".join(lines)
```

- [ ] **Step 2: Commit**

```bash
git add foundry/dream_foundry/agent/context.py
git commit -m "feat: token-aware context trimming with LLM summarization"
```

---

## Chunk 3: Embedding Pipeline + MemoryStored Events

### Task 7: Improve embedding pipeline with caching

**Files:**
- Modify: `foundry/dream_foundry/agent/memory.py`

- [ ] **Step 1: Replace with cached embedding function**

Replace `foundry/dream_foundry/agent/memory.py` with:

```python
import hashlib
import struct

from dream_foundry.config import settings

_cache: dict[str, bytes] = {}


def _cache_key(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


async def embed_text(text: str) -> bytes:
    key = _cache_key(text)
    if key in _cache:
        return _cache[key]

    try:
        import openai

        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            dimensions=settings.embedding_dimensions,
        )
        embedding = response.data[0].embedding
        result = struct.pack(f"{len(embedding)}f", *embedding)
    except Exception:
        dim = settings.embedding_dimensions
        result = struct.pack(f"{dim}f", *([0.0] * dim))

    _cache[key] = result
    return result
```

- [ ] **Step 2: Commit**

```bash
git add foundry/dream_foundry/agent/memory.py
git commit -m "feat: add embedding cache to avoid redundant API calls"
```

### Task 8: Emit MemoryStored events from agent tools

**Files:**
- Modify: `foundry/dream_foundry/agent/core.py`
- Modify: `foundry/dream_foundry/agent/tools.py`

- [ ] **Step 1: Update AgentDeps to include event callback**

In `foundry/dream_foundry/agent/core.py`, update `AgentDeps`:

```python
@dataclass
class AgentDeps:
    session_id: str
    model_id: str
    send_event: Callable[[dict], Awaitable[None]] | None = None
```

Update `stream_chat()` to pass `send_event` to deps:

```python
    deps = AgentDeps(session_id=session_id, model_id=model_id, send_event=send_event)
```

- [ ] **Step 2: Update tools.py to emit MemoryStored event**

In `foundry/dream_foundry/agent/tools.py`, update `store_memory`:

```python
def register_memory_tools(agent: Agent):
    @agent.tool
    async def store_memory(
        ctx: RunContext[AgentDeps], content: str, category: str = "note"
    ) -> str:
        """Store important information to long-term memory.

        Args:
            content: The information to store.
            category: One of "preference", "fact", "decision", "project", "note".
        """
        try:
            embedding = await embed_text(content)
            db = await get_db()
            mem = await crud.store_memory(
                db, ctx.deps.session_id, content, category, embedding
            )
            if ctx.deps.send_event:
                await ctx.deps.send_event(
                    {
                        "type": "memory.stored",
                        "memory_id": mem["id"],
                        "content": content,
                        "category": category,
                    }
                )
            return f"Stored in memory (category: {category})."
        except Exception as e:
            return f"Failed to store memory: {e}"
```

The `recall_memory` and `list_all_memories` functions remain unchanged.

- [ ] **Step 3: Commit**

```bash
git add foundry/dream_foundry/agent/core.py foundry/dream_foundry/agent/tools.py
git commit -m "feat: emit MemoryStored events via WS/SSE when agent stores memory"
```

### Task 9: Install and verify

- [ ] **Step 1: Reinstall backend**

Run: `pip install -e foundry`

- [ ] **Step 2: Start server and test health**

Run: `python -m uvicorn dream_foundry.main:app --host 0.0.0.0 --port 8000`

Verify: GET http://localhost:8000/api/health returns `{"status":"ok","version":"0.1.0"}`

- [ ] **Step 3: Commit all remaining changes**

```bash
git add -A
git commit -m "feat: complete P3 memory and context system"
```
