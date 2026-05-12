from __future__ import annotations

from dataclasses import dataclass, field

from dream_foundry.yaml_config import foundry_config


@dataclass
class ModelInfo:
    id: str
    name: str
    provider: str
    provider_prefix: str
    context_window: int
    max_output_tokens: int
    api_base: str = ""
    api_key: str = ""


_BUILTIN_MODELS: dict[str, ModelInfo] = {
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

MODEL_REGISTRY: dict[str, ModelInfo] = {}


def _build_registry_from_yaml() -> dict[str, ModelInfo]:
    if not foundry_config.providers:
        return dict(_BUILTIN_MODELS)

    registry: dict[str, ModelInfo] = {}
    for prov_name, prov in foundry_config.providers.items():
        for model_id in prov.models:
            provider_prefix = f"{prov.type}:{model_id}"
            display_name = model_id
            api_base = prov.options.api
            api_key = prov.options.apiKey

            registry[model_id] = ModelInfo(
                id=model_id,
                name=display_name,
                provider=prov.type,
                provider_prefix=provider_prefix,
                context_window=128000,
                max_output_tokens=16384,
                api_base=api_base,
                api_key=api_key,
            )
    return registry


def init_registry() -> None:
    global MODEL_REGISTRY
    MODEL_REGISTRY = _build_registry_from_yaml()


init_registry()


def get_model_info(model_id: str) -> ModelInfo | None:
    return MODEL_REGISTRY.get(model_id)


def list_models() -> list[ModelInfo]:
    return list(MODEL_REGISTRY.values())


def get_provider_prefix(model_id: str) -> str:
    info = MODEL_REGISTRY.get(model_id)
    if not info:
        raise ValueError(f"Unknown model: {model_id}")
    return info.provider_prefix


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 3.5))


def get_context_budget(model_id: str) -> int:
    info = MODEL_REGISTRY.get(model_id)
    if not info:
        return 100000
    return int(info.context_window * 0.8) - info.max_output_tokens
