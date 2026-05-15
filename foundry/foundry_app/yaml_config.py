from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ProviderOptions:
    api: str = ""
    apiKey: str = ""


@dataclass
class ProviderConfig:
    type: str = "openai"
    options: ProviderOptions = field(default_factory=ProviderOptions)
    models: list[str] = field(default_factory=list)


@dataclass
class FoundryConfig:
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    default_model: str = ""
    default_provider_name: str = ""
    default_model_id: str = ""

    def get_default_model(self) -> str:
        if self.default_model_id:
            return self.default_model_id
        for prov in self.providers.values():
            if prov.models:
                return prov.models[0]
        return ""


def _parse_options(raw: list | dict | None) -> ProviderOptions:
    if raw is None:
        return ProviderOptions()
    if isinstance(raw, dict):
        return ProviderOptions(api=raw.get("api", ""), apiKey=raw.get("apiKey", ""))
    if isinstance(raw, list):
        merged: dict[str, str] = {}
        for item in raw:
            if isinstance(item, dict):
                merged.update(item)
        return ProviderOptions(
            api=merged.get("api", ""), apiKey=merged.get("apiKey", "")
        )
    return ProviderOptions()


def _parse_provider(name: str, data: dict) -> ProviderConfig:
    ptype = str(data.get("type", "openai")).rstrip(",")
    options = _parse_options(data.get("options"))
    models = data.get("models", [])
    if isinstance(models, str):
        models = [models]
    return ProviderConfig(type=ptype, options=options, models=models)


def load_yaml_config(config_path: str | Path | None = None) -> FoundryConfig:
    if config_path is None:
        config_path = Path.home() / ".config" / "foundry" / "config.yaml"
    config_path = Path(config_path)

    if not config_path.exists():
        return FoundryConfig()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = f.read()
        import re

        raw = re.sub(r",(\s*\n)", r"\1", raw)
        data = yaml.safe_load(raw)
    except Exception:
        return FoundryConfig()

    if not data or not isinstance(data, dict):
        return FoundryConfig()

    providers: dict[str, ProviderConfig] = {}
    raw_providers = data.get("provider", {})
    if isinstance(raw_providers, dict):
        for name, pdata in raw_providers.items():
            if isinstance(pdata, dict):
                providers[name] = _parse_provider(name, pdata)

    default_model = str(data.get("model", ""))
    default_provider_name = ""
    default_model_id = ""

    if default_model and ":" in default_model:
        parts = default_model.split(":", 1)
        default_provider_name = parts[0]
        default_model_id = parts[1]

    return FoundryConfig(
        providers=providers,
        default_model=default_model,
        default_provider_name=default_provider_name,
        default_model_id=default_model_id,
    )


foundry_config = load_yaml_config()
