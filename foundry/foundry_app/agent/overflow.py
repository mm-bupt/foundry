from foundry_app.agent.registry import get_model_info

COMPACTION_BUFFER = 20_000


def usable_tokens(model_id: str) -> int:
    info = get_model_info(model_id)
    if not info:
        return 80_000
    context = info.context_window
    max_output = info.max_output_tokens
    reserved = COMPACTION_BUFFER
    return max(0, context - max_output - reserved)


def is_overflow(model_id: str, tokens_used: int) -> bool:
    from foundry_app.config import settings

    if not settings.auto_compaction:
        return False
    info = get_model_info(model_id)
    if info and info.context_window == 0:
        return False
    return tokens_used >= usable_tokens(model_id)
