import uuid
from datetime import datetime, timezone

import aiosqlite

from foundry_app.db.models import Session, Message, MemoryVector, ToolCallRecord, TaskRecord


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


# ── Sessions ──────────────────────────────────────────────────────────


async def create_session(
    db: aiosqlite.Connection,
    title: str = "New Chat",
    model_id: str = "claude-sonnet",
    parent_id: str | None = None,
) -> dict:
    sid = new_id()
    now = utcnow()
    await db.execute(
        "INSERT INTO sessions (id, title, model_id, parent_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (sid, title, model_id, parent_id, now, now),
    )
    await db.commit()
    return {
        "id": sid,
        "title": title,
        "model_id": model_id,
        "system_prompt": "",
        "parent_id": parent_id,
        "created_at": now,
        "updated_at": now,
    }


async def get_session(db: aiosqlite.Connection, session_id: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def list_sessions(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def update_session(
    db: aiosqlite.Connection, session_id: str, **kwargs
) -> dict | None:
    session = await get_session(db, session_id)
    if not session:
        return None
    now = utcnow()
    sets = []
    vals = []
    for k, v in kwargs.items():
        if k in ("title", "model_id", "system_prompt", "parent_id"):
            sets.append(f"{k} = ?")
            vals.append(v)
    if not sets:
        return session
    sets.append("updated_at = ?")
    vals.append(now)
    vals.append(session_id)
    await db.execute(f"UPDATE sessions SET {', '.join(sets)} WHERE id = ?", vals)
    await db.commit()
    return await get_session(db, session_id)


async def delete_session(db: aiosqlite.Connection, session_id: str) -> bool:
    cursor = await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    await db.commit()
    return cursor.rowcount > 0


# ── Messages ──────────────────────────────────────────────────────────


async def create_message(
    db: aiosqlite.Connection,
    session_id: str,
    role: str,
    content: str,
    model_id: str | None = None,
    duration_ms: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    model_messages_json: str = "[]",
    is_compaction: bool = False,
    is_summary: bool = False,
    tail_start_id: str | None = None,
) -> dict:
    mid = new_id()
    now = utcnow()
    await db.execute(
        """INSERT INTO messages
           (id, session_id, role, content, model_id, duration_ms,
            input_tokens, output_tokens, model_messages_json,
            is_compaction, is_summary, tail_start_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            mid,
            session_id,
            role,
            content,
            model_id,
            duration_ms,
            input_tokens,
            output_tokens,
            model_messages_json,
            int(is_compaction),
            int(is_summary),
            tail_start_id,
            now,
        ),
    )
    now2 = utcnow()
    await db.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?", (now2, session_id)
    )
    await db.commit()
    return {
        "id": mid,
        "session_id": session_id,
        "role": role,
        "content": content,
        "model_id": model_id,
        "duration_ms": duration_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "model_messages_json": model_messages_json,
        "is_compaction": is_compaction,
        "is_summary": is_summary,
        "tail_start_id": tail_start_id,
        "created_at": now,
    }


async def list_messages(db: aiosqlite.Connection, session_id: str) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_message(db: aiosqlite.Connection, message_id: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_message(
    db: aiosqlite.Connection, message_id: str, **kwargs
) -> dict | None:
    msg = await get_message(db, message_id)
    if not msg:
        return None
    sets = []
    vals = []
    for k, v in kwargs.items():
        if k in (
            "content",
            "thinking_content",
            "model_id",
            "duration_ms",
            "input_tokens",
            "output_tokens",
            "model_messages_json",
            "is_compaction",
            "is_summary",
            "tail_start_id",
            "compacted_at",
        ):
            sets.append(f"{k} = ?")
            vals.append(v)
    if not sets:
        return msg
    vals.append(message_id)
    await db.execute(f"UPDATE messages SET {', '.join(sets)} WHERE id = ?", vals)
    await db.commit()
    return await get_message(db, message_id)


# ── Memory ────────────────────────────────────────────────────────────


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


async def list_memory(db: aiosqlite.Connection, session_id: str) -> list[dict]:
    cursor = await db.execute(
        "SELECT id, session_id, content, category, created_at FROM memory_vectors WHERE session_id = ? ORDER BY created_at DESC",
        (session_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def delete_memory(db: aiosqlite.Connection, memory_id: str) -> bool:
    await db.execute("DELETE FROM vec_memory WHERE id = ?", (memory_id,))
    cursor = await db.execute("DELETE FROM memory_vectors WHERE id = ?", (memory_id,))
    await db.commit()
    return cursor.rowcount > 0


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


async def _fallback_search(
    db: aiosqlite.Connection, session_id: str, query_embedding: bytes, limit: int
) -> list[dict]:
    import struct
    from foundry_app.config import settings

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


# ── Tool Calls ────────────────────────────────────────────────────────


async def create_tool_call(
    db: aiosqlite.Connection, message_id: str, tool_name: str, args_json: str = "{}"
) -> dict:
    tid = new_id()
    now = utcnow()
    await db.execute(
        "INSERT INTO tool_calls (id, message_id, tool_name, args_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (tid, message_id, tool_name, args_json, now),
    )
    await db.commit()
    return {
        "id": tid,
        "message_id": message_id,
        "tool_name": tool_name,
        "args_json": args_json,
        "status": "pending",
        "created_at": now,
    }


async def update_tool_call(
    db: aiosqlite.Connection,
    tool_call_id: str,
    result: str | None = None,
    status: str | None = None,
    duration_ms: int | None = None,
) -> dict | None:
    sets = []
    vals = []
    if result is not None:
        sets.append("result = ?")
        vals.append(result)
    if status is not None:
        sets.append("status = ?")
        vals.append(status)
    if duration_ms is not None:
        sets.append("duration_ms = ?")
        vals.append(duration_ms)
    if not sets:
        cursor = await db.execute(
            "SELECT * FROM tool_calls WHERE id = ?", (tool_call_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    vals.append(tool_call_id)
    await db.execute(f"UPDATE tool_calls SET {', '.join(sets)} WHERE id = ?", vals)
    await db.commit()
    cursor = await db.execute("SELECT * FROM tool_calls WHERE id = ?", (tool_call_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def list_tool_calls(db: aiosqlite.Connection, message_id: str) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM tool_calls WHERE message_id = ? ORDER BY created_at ASC",
        (message_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_session_stats(db: aiosqlite.Connection, session_id: str) -> dict:
    cursor = await db.execute(
        """
        SELECT
            COALESCE(SUM(input_tokens), 0) as total_input_tokens,
            COALESCE(SUM(output_tokens), 0) as total_output_tokens,
            COUNT(*) as message_count
        FROM messages
        WHERE session_id = ?
        """,
        (session_id,),
    )
    row = await cursor.fetchone()
    if not row:
        return {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "context_tokens": 0,
            "message_count": 0,
        }
    total_input = row[0] or 0
    total_output = row[1] or 0
    return {
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_input + total_output,
        "context_tokens": total_input,
        "message_count": row[2] or 0,
    }


# ── Task Records ─────────────────────────────────────────────────────


async def create_task_record(
    db: aiosqlite.Connection,
    parent_session_id: str,
    subagent_type: str,
    description: str = "",
    parent_message_id: str | None = None,
    background: bool = False,
) -> dict:
    tid = new_id()
    now = utcnow()
    await db.execute(
        """INSERT INTO task_records
           (id, parent_session_id, parent_message_id, subagent_type, description, status, background, created_at)
           VALUES (?, ?, ?, ?, ?, 'running', ?, ?)""",
        (tid, parent_session_id, parent_message_id, subagent_type, description, int(background), now),
    )
    await db.commit()
    return {
        "id": tid,
        "parent_session_id": parent_session_id,
        "parent_message_id": parent_message_id,
        "subagent_type": subagent_type,
        "description": description,
        "status": "running",
        "background": background,
        "result_preview": None,
        "created_at": now,
        "completed_at": None,
    }


async def get_task_record(db: aiosqlite.Connection, task_id: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM task_records WHERE id = ?", (task_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_task_record(
    db: aiosqlite.Connection,
    task_id: str,
    status: str | None = None,
    result_preview: str | None = None,
) -> dict | None:
    sets = []
    vals = []
    if status is not None:
        sets.append("status = ?")
        vals.append(status)
    if result_preview is not None:
        sets.append("result_preview = ?")
        vals.append(result_preview)
    if status in ("completed", "error", "cancelled"):
        sets.append("completed_at = ?")
        vals.append(utcnow())
    if not sets:
        return await get_task_record(db, task_id)
    vals.append(task_id)
    await db.execute(f"UPDATE task_records SET {', '.join(sets)} WHERE id = ?", vals)
    await db.commit()
    return await get_task_record(db, task_id)


async def list_task_records(
    db: aiosqlite.Connection, parent_session_id: str
) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM task_records WHERE parent_session_id = ? ORDER BY created_at ASC",
        (parent_session_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_child_sessions(
    db: aiosqlite.Connection, parent_session_id: str
) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM sessions WHERE parent_id = ? ORDER BY created_at ASC",
        (parent_session_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# ── Todos ─────────────────────────────────────────────────────────────


async def update_todos(
    db: aiosqlite.Connection, session_id: str, todos: list[dict]
) -> None:
    await db.execute("DELETE FROM todos WHERE session_id = ?", (session_id,))
    now = utcnow()
    for position, todo in enumerate(todos):
        await db.execute(
            "INSERT INTO todos (session_id, content, status, priority, position, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, todo["content"], todo["status"], todo["priority"], position, now),
        )
    await db.commit()


async def get_todos(db: aiosqlite.Connection, session_id: str) -> list[dict]:
    cursor = await db.execute(
        "SELECT content, status, priority FROM todos WHERE session_id = ? ORDER BY position ASC",
        (session_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]
