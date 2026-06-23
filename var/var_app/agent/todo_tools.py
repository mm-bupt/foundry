from pydantic_ai import Agent, RunContext
from var_app.agent.deps import AgentDeps
from var_app.db.database import get_db
from var_app.db import crud
from var_app.logger import get_logger

logger = get_logger("agent.todo_tools")

TODOWRITE_DESCRIPTION = """\
Create and maintain a structured task list for the current coding session. Tracks progress, organizes multi-step work, and surfaces status to the user.

## When to use
Use proactively when:
- The task requires 3+ distinct steps or actions (not just 3 tool calls for a single conceptual step)
- The work is non-trivial and benefits from planning
- The user provides multiple tasks (numbered or comma-separated) or explicitly asks for a todo list
- New instructions arrive - capture them as todos
- You start a task - mark it `in_progress` (only one at a time) before working
- You finish a task - mark it `completed` and add any follow-ups discovered during the work

## When NOT to use
Skip when:
- The work is a single, straightforward task (or <3 trivial steps)
- The request is purely informational or conversational
- Tracking adds no organizational value

## States
- `pending` - not started
- `in_progress` - actively working (exactly ONE at a time)
- `completed` - finished successfully
- `cancelled` - no longer needed

## Rules
- Update status in real time; don't batch completions
- Mark `completed` only after the required work is actually done, including any required verification. Never based on intent.
- Keep exactly one `in_progress` while work remains
- If blocked or partial, keep it `in_progress` and add a follow-up todo describing the blocker
- Preserve user-provided commands verbatim (flags, args, order)
- Items should be specific and actionable; break large work into smaller steps

## Examples

Use it:
- "Add a dark mode toggle and run the tests" -> multi-step feature + explicit verification
- "Rename getCwd -> getCurrentWorkingDirectory across the repo" -> grep reveals 15 occurrences in 8 files
- "Implement registration, catalog, cart, checkout" -> multiple complex features

Skip it:
- "How do I print Hello World in Python?" -> informational
- "Add a comment to calculateTotal" -> single edit
- "Run npm install and tell me what happened" -> one command

When in doubt, use it.\
"""


def register_todo_tools(agent: Agent):
    @agent.tool
    async def todowrite(
        ctx: RunContext[AgentDeps],
        todos: list[dict],
    ) -> str:
        """Create and maintain a structured task list for the current coding session. Tracks progress, organizes multi-step work, and surfaces status to the user.

        Args:
            todos: The updated todo list. Each item has:
                - content (str): Brief description of the task
                - status (str): Current status: pending, in_progress, completed, cancelled
                - priority (str): Priority level: high, medium, low
        """
        session_id = ctx.deps.session_id
        db = await get_db()

        validated = []
        for t in todos:
            validated.append({
                "content": str(t.get("content", "")),
                "status": t.get("status", "pending") if t.get("status") in ("pending", "in_progress", "completed", "cancelled") else "pending",
                "priority": t.get("priority", "medium") if t.get("priority") in ("high", "medium", "low") else "medium",
            })

        await crud.update_todos(db, session_id, validated)

        if ctx.deps.send_event:
            await ctx.deps.send_event({
                "type": "todo.updated",
                "session_id": session_id,
                "todos": validated,
            })

        active = sum(1 for t in validated if t["status"] != "completed")
        logger.debug("todowrite | session=%s total=%d active=%d", session_id, len(validated), active)
        return f"Updated {len(validated)} todos ({active} active)"
