from dataclasses import dataclass


@dataclass
class ModelInfo:
    id: str
    name: str
    provider: str
    provider_prefix: str
    context_window: int
    max_output_tokens: int


MODEL_REGISTRY: dict[str, ModelInfo] = {
    "gpt-4o": ModelInfo(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        provider_prefix="openai:gpt-4o",
        context_window=128000,
        max_output_tokens=16384,
    ),
    "gpt-4o-mini": ModelInfo(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        provider_prefix="openai:gpt-4o-mini",
        context_window=128000,
        max_output_tokens=16384,
    ),
    "claude-sonnet": ModelInfo(
        id="claude-sonnet",
        name="Claude Sonnet 4",
        provider="anthropic",
        provider_prefix="anthropic:claude-sonnet-4-20250514",
        context_window=200000,
        max_output_tokens=8192,
    ),
    "claude-haiku": ModelInfo(
        id="claude-haiku",
        name="Claude Haiku 4",
        provider="anthropic",
        provider_prefix="anthropic:claude-haiku-4-20250414",
        context_window=200000,
        max_output_tokens=8192,
    ),
}


def get_model_info(model_id: str) -> ModelInfo | None:
    return MODEL_REGISTRY.get(model_id)


def list_models() -> list[ModelInfo]:
    return list(MODEL_REGISTRY.values())


def get_provider_prefix(model_id: str) -> str:
    info = MODEL_REGISTRY.get(model_id)
    if not info:
        raise ValueError(f"Unknown model: {model_id}")
    return info.provider_prefix
