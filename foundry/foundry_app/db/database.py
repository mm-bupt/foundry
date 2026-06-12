import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager

import aiosqlite
import sqlite_vec

from foundry_app.config import settings

_db: aiosqlite.Connection | None = None


def _get_vec_extension_path() -> str:
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
        dll = base / "sqlite_vec" / "vec0.dll"
        if dll.exists():
            return str(dll)
    return sqlite_vec.loadable_path()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New Chat',
    model_id TEXT NOT NULL DEFAULT 'claude-sonnet',
    system_prompt TEXT NOT NULL DEFAULT '',
    parent_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    thinking_content TEXT NOT NULL DEFAULT '',
    model_id TEXT,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    model_messages_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_vectors (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'note',
    embedding BLOB NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    args_json TEXT NOT NULL DEFAULT '{}',
    result TEXT,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_records (
    id TEXT PRIMARY KEY,
    parent_session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    parent_message_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
    subagent_type TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'running',
    background INTEGER NOT NULL DEFAULT 0,
    result_preview TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_memory_vectors_session_id ON memory_vectors(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_vectors_category ON memory_vectors(category);
CREATE INDEX IF NOT EXISTS idx_tool_calls_message_id ON tool_calls(message_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions(updated_at);
CREATE INDEX IF NOT EXISTS idx_sessions_parent_id ON sessions(parent_id);
CREATE INDEX IF NOT EXISTS idx_task_records_parent ON task_records(parent_session_id);

CREATE VIRTUAL TABLE IF NOT EXISTS vec_memory USING vec0(
    id TEXT PRIMARY KEY,
    embedding float[1536]
);
"""


async def _connect() -> aiosqlite.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(settings.db_path))
    db.row_factory = aiosqlite.Row
    await db.enable_load_extension(True)
    await db.load_extension(_get_vec_extension_path())
    await db.enable_load_extension(False)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


_MIGRATIONS = [
    "ALTER TABLE messages ADD COLUMN thinking_content TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE sessions ADD COLUMN parent_id TEXT",
]


async def init_db(db: aiosqlite.Connection):
    for migration in _MIGRATIONS:
        try:
            await db.execute(migration)
            await db.commit()
        except Exception:
            await db.rollback()
    await db.executescript(_SCHEMA)
    await db.commit()


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await _connect()
        await init_db(_db)
    return _db


async def close_db():
    global _db
    if _db is not None:
        await _db.close()
        _db = None


@asynccontextmanager
async def db_connection():
    db = await get_db()
    try:
        yield db
    except Exception:
        await db.rollback()
        raise
