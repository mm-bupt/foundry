from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Dream Foundry"
    app_version: str = "0.1.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    db_path: Path = Path.home() / ".dream-foundry" / "dream-foundry.db"

    openai_api_key: str = ""
    anthropic_api_key: str = ""

    default_model: str = "claude-sonnet"
    embedding_model: str = "openai:text-embedding-3-small"
    embedding_dimensions: int = 1536

    ws_heartbeat_interval: int = 30
    ws_heartbeat_timeout: int = 60
    context_window_threshold: float = 0.8

    cors_origins: list[str] = ["*"]

    model_config = {
        "env_prefix": "DREAM_FOUNDRY_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
