"""Configuration for the OpenClaw benchmark runner."""

import os
import tempfile

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BenchmarkConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Local backend
    bot_workspace_path: str = Field(
        default_factory=lambda: os.path.join(tempfile.gettempdir(), "openclaw_benchmark"),
        description="Local workspace path for benchmark tasks",
    )

    # Agent
    agent_id: str = Field(
        default="main",
        description="OpenClaw agent ID to use",
    )
    timeout_multiplier: float = Field(
        default=1.0,
        description="Multiply all task timeouts by this factor",
    )

    # Gateway
    gateway_port: int = Field(
        default=18789,
        description="openclaw gateway port",
    )

    # Daytona sandbox backend (optional)
    daytona_api_key: str = Field(default="", description="Daytona API key")
    daytona_api_url: str = Field(
        default="https://app.daytona.io/api",
        description="Daytona API URL",
    )
    daytona_image: str = Field(
        default="node:22-bookworm",
        description="Docker image for Daytona sandbox",
    )


def load_config(**cli_overrides) -> BenchmarkConfig:
    """Load config from env/.env, then apply CLI overrides."""
    cfg = BenchmarkConfig()
    filtered = {k: v for k, v in cli_overrides.items() if v is not None}
    if filtered:
        cfg = cfg.model_copy(update=filtered)
    return cfg
