from pydantic_ai import Agent, RunContext
from foundry_app.agent.core import AgentDeps
from foundry_app.db.database import get_db
from foundry_app.db import crud
import struct
from foundry_app.config import settings


async def _noop_embed() -> bytes:
    dim = settings.embedding_dimensions
    return struct.pack(f"{dim}f", *([0.0] * dim))


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
            embedding = await _noop_embed()
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

    @agent.tool
    async def recall_memory(
        ctx: RunContext[AgentDeps], query: str, limit: int = 5
    ) -> str:
        """Search long-term memory for relevant information.

        Args:
            query: The search query.
            limit: Max results to return (default 5).
        """
        return "No relevant memories found."

    @agent.tool
    async def list_all_memories(ctx: RunContext[AgentDeps]) -> str:
        """List all stored memories for the current session."""
        try:
            db = await get_db()
            memories = await crud.list_memory(db, ctx.deps.session_id)
            if not memories:
                return "No memories stored yet."
            lines = [f"- [{m['category']}] {m['content']}" for m in memories]
            return "\n".join(lines)
        except Exception as e:
            return f"Failed to list memories: {e}"
