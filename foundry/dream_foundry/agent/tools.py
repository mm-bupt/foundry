from pydantic_ai import Agent, RunContext
from dream_foundry.agent.core import AgentDeps
from dream_foundry.db.database import get_db
from dream_foundry.db import crud
from dream_foundry.agent.memory import embed_text


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
            await crud.store_memory(
                db, ctx.deps.session_id, content, category, embedding
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
        try:
            embedding = await embed_text(query)
            db = await get_db()
            results = await crud.search_memory(
                db, ctx.deps.session_id, embedding, limit
            )
            if not results:
                return "No relevant memories found."
            lines = [f"- [{r['category']}] {r['content']}" for r in results]
            return "\n".join(lines)
        except Exception as e:
            return f"Memory search failed: {e}"

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
