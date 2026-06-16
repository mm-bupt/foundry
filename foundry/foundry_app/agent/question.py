import asyncio
import uuid
from typing import Any

from foundry_app.logger import get_logger

logger = get_logger("agent.question")

_pending: dict[str, asyncio.Future] = {}


def create_pending(question_id: str | None = None) -> tuple[str, asyncio.Future]:
    qid = question_id or f"que_{uuid.uuid4().hex[:12]}"
    future: asyncio.Future = asyncio.get_running_loop().create_future()
    _pending[qid] = future
    logger.debug("question pending | id=%s total=%d", qid, len(_pending))
    return qid, future


def resolve(question_id: str, answers: list[list[str]]) -> bool:
    future = _pending.pop(question_id, None)
    if future is None or future.done():
        logger.debug("question resolve not found | id=%s", question_id)
        return False
    future.set_result(answers)
    logger.debug("question resolved | id=%s answers=%s", question_id, answers)
    return True


def reject(question_id: str) -> bool:
    future = _pending.pop(question_id, None)
    if future is None or future.done():
        return False
    future.set_exception(QuestionRejectedError(question_id))
    logger.debug("question rejected | id=%s", question_id)
    return True


def list_pending() -> list[dict[str, Any]]:
    return [{"question_id": qid} for qid in _pending if not _pending[qid].done()]


class QuestionRejectedError(Exception):
    def __init__(self, question_id: str):
        self.question_id = question_id
        super().__init__(f"Question '{question_id}' was rejected by user")
