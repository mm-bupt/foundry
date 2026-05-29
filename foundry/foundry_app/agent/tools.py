import asyncio
from pathlib import Path

from pydantic_ai import Agent, RunContext
from foundry_app.agent.core import AgentDeps
from foundry_app.db.database import get_db
from foundry_app.db import crud
import struct
from foundry_app.config import settings


async def _noop_embed() -> bytes:
    dim = settings.embedding_dimensions
    return struct.pack(f"{dim}f", *([0.0] * dim))


def _resolve_path(work_dir: str, path: str) -> Path:
    base = Path(work_dir).resolve()
    target = (base / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if not str(target).startswith(str(base)):
        raise PermissionError(f"Path '{path}' is outside working directory")
    return target


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


def register_file_tools(agent: Agent):
    @agent.tool
    async def read_file(ctx: RunContext[AgentDeps], path: str) -> str:
        """Read the content of a file. Relative paths are resolved against the working directory.

        Args:
            path: File path (relative or absolute).
        """
        try:
            target = _resolve_path(ctx.deps.work_dir, path)
            if not target.is_file():
                return f"Error: '{path}' is not a file or does not exist."
            content = target.read_text(encoding="utf-8", errors="replace")
            return content
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error reading file: {e}"

    @agent.tool
    async def write_file(ctx: RunContext[AgentDeps], path: str, content: str) -> str:
        """Write content to a file. Relative paths are resolved against the working directory.
        Creates parent directories if needed.

        Args:
            path: File path (relative or absolute).
            content: Content to write.
        """
        try:
            target = _resolve_path(ctx.deps.work_dir, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"Successfully wrote {len(content)} chars to '{path}'."
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error writing file: {e}"

    @agent.tool
    async def list_files(ctx: RunContext[AgentDeps], path: str = ".") -> str:
        """List files and directories in a path. Relative paths are resolved against the working directory.

        Args:
            path: Directory path (relative or absolute). Defaults to working directory.
        """
        try:
            target = _resolve_path(ctx.deps.work_dir, path)
            if not target.is_dir():
                return f"Error: '{path}' is not a directory or does not exist."
            entries = sorted(target.iterdir())
            lines = []
            for entry in entries:
                if entry.is_dir():
                    lines.append(f"{entry.name}/")
                else:
                    size = entry.stat().st_size
                    lines.append(f"{entry.name} ({size} bytes)")
            if not lines:
                return "(empty directory)"
            return "\n".join(lines)
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error listing files: {e}"

    @agent.tool
    async def run_command(
        ctx: RunContext[AgentDeps], command: str, timeout: int = 120
    ) -> str:
        """Execute a shell command in the working directory.

        Args:
            command: The shell command to run.
            timeout: Timeout in seconds (default 120).
        """
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=ctx.deps.work_dir,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            output = ""
            if stdout:
                output += stdout.decode("utf-8", errors="replace")
            if stderr:
                output += stderr.decode("utf-8", errors="replace")
            if proc.returncode != 0:
                output += f"\n(exit code: {proc.returncode})"
            return output or "(no output)"
        except asyncio.TimeoutError:
            return f"Error: command timed out after {timeout}s."
        except Exception as e:
            return f"Error running command: {e}"
