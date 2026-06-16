from pydantic_ai import Agent, RunContext
from foundry_app.agent.deps import AgentDeps
from foundry_app.agent.question import create_pending, QuestionRejectedError
from foundry_app.logger import get_logger

logger = get_logger("agent.question_tools")

QUESTION_DESCRIPTION = """\
Use this tool when you need to ask the user questions during execution. This allows you to:
1. Gather user preferences or requirements
2. Clarify ambiguous instructions
3. Get decisions on implementation choices as you work
4. Offer choices to the user about what direction to take.

Usage notes:
- The tool will block until the user answers or dismisses the question
- Answers are returned as arrays of labels; set `multiple: true` to allow selecting more than one
- If you recommend a specific option, make that the first option in the list and add "(Recommended)" at the end of the label
- Do NOT include "Other" or catch-all options — the user can always type their own answer
- Keep option labels concise (1-5 words); put explanation in the description
"""


def register_question_tools(agent: Agent):
    @agent.tool
    async def question(
        ctx: RunContext[AgentDeps],
        questions: list[dict],
    ) -> str:
        """Ask the user questions during execution. Blocks until the user replies or dismisses.

        Args:
            questions: Questions to ask. Each item has:
                - question (str): Complete question to ask the user
                - header (str): Very short label for the question (max 30 chars)
                - options (list): Available choices, each with:
                    - label (str): Display text (1-5 words, concise)
                    - description (str): Explanation of choice
                - multiple (bool, optional): Allow selecting multiple choices (default false)
        """
        send_event = ctx.deps.send_event
        if not send_event:
            return "Error: cannot ask question in this mode (no event channel)"

        question_id, future = create_pending()

        await send_event({
            "type": "question.asked",
            "question_id": question_id,
            "session_id": ctx.deps.session_id,
            "questions": questions,
        })
        logger.debug(
            "question asked | session=%s id=%s count=%d",
            ctx.deps.session_id, question_id, len(questions),
        )

        try:
            answers = await future
        except QuestionRejectedError:
            return "The user dismissed the question. Continue with your best judgment."

        formatted_parts = []
        for i, q in enumerate(questions):
            ans = answers[i] if i < len(answers) else []
            ans_text = ", ".join(ans) if ans else "Unanswered"
            formatted_parts.append(f'"{q.get("question", "")}"="{ans_text}"')

        return (
            f"User has answered your questions: {', '.join(formatted_parts)}. "
            "You can now continue with the user's answers in mind."
        )
