"""Configuration for the OpenClaw benchmark runner."""

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
        default="/tmp/openclaw_benchmark",
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

    # Daytona sandbox backend (optional)
    daytona_api_key: str = Field(default="", description="Daytona API key")
    daytona_api_url: str = Field(
        default="https://app.daytona.io/api",
        description="Daytona API URL",
    )
    daytona_image: str = Field(
        default="ubuntu:22.04",
        description="Docker image for Daytona sandbox",
    )


# Alias for run.py import compatibility
TelegramConfig = BenchmarkConfig


def load_config() -> BenchmarkConfig:
    return BenchmarkConfig()
