from pathlib import Path
from pydantic_settings import BaseSettings

from var_app.yaml_config import var_config


class Settings(BaseSettings):
    app_name: str = "Var"
    app_version: str = "0.1.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    db_path: Path = Path.home() / ".var" / "var.db"
    work_dir: Path = Path.cwd()

    openai_api_key: str = ""
    anthropic_api_key: str = ""

    default_model: str = "claude-sonnet"
    embedding_model: str = "openai:text-embedding-3-small"
    embedding_dimensions: int = 1536

    ws_heartbeat_interval: int = 30
    ws_heartbeat_timeout: int = 60
    context_window_threshold: float = 0.8

    auto_compaction: bool = True
    compaction_prune: bool = True
    compaction_tail_turns: int = 2
    compaction_reserved: int = 20_000

    cors_origins: list[str] = ["*"]

    model_config = {
        "env_prefix": "VAR_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
settings.work_dir = settings.work_dir.resolve()

if var_config.work_dir:
    settings.work_dir = Path(var_config.work_dir).resolve()

if var_config.providers:
    if var_config.default_model_id:
        settings.default_model = var_config.default_model_id

    for _name, prov in var_config.providers.items():
        api_key = prov.options.apiKey
        if not api_key:
            continue
        if prov.type == "openai" and not settings.openai_api_key:
            settings.openai_api_key = api_key
        elif prov.type == "anthropic" and not settings.anthropic_api_key:
            settings.anthropic_api_key = api_key
