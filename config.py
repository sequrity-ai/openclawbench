"""Configuration management for Telegram client."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramConfig(BaseSettings):
    """Telegram client configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Mode selection
    local_mode: bool = Field(
        default=False,
        description="Use local OpenClaw gateway via 'openclaw agent' CLI instead of Telegram",
    )

    # Telegram settings
    telegram_bot_token: str = Field(
        default="",
        description="Telegram bot token from BotFather (required for Telegram mode)",
    )
    openclaw_bot_username: str = Field(
        default="openclaw_bot",
        description="Username of the OpenClaw bot to interact with",
    )

    # Local mode settings
    agent_id: str = Field(
        default="main",
        description="OpenClaw agent ID to use in local mode",
    )

    # Performance settings
    async_mode: bool = Field(
        default=True,
        description="Enable async mode for performance (True) or sync mode for debugging (False)",
    )

    # API settings
    telegram_api_base_url: str = Field(
        default="https://api.telegram.org",
        description="Telegram API base URL",
    )
    request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
    )
    polling_timeout: int = Field(
        default=10,
        description="Long polling timeout in seconds",
    )
    polling_interval: float = Field(
        default=1.0,
        description="Interval between polling attempts in seconds",
    )

    # Benchmark settings
    timeout_multiplier: float = Field(
        default=1.0,
        description="Multiply all task timeouts by this factor (useful for slower systems)",
    )
    max_concurrent_sessions: int = Field(
        default=10,
        description="Maximum concurrent sessions for benchmarking (async mode only)",
    )
    default_session_timeout: int = Field(
        default=300,
        description="Default session timeout in seconds",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    debug_mode: bool = Field(
        default=False,
        description="Enable detailed debug logging",
    )

    @property
    def telegram_api_url(self) -> str:
        """Get the full Telegram API URL with bot token."""
        return f"{self.telegram_api_base_url}/bot{self.telegram_bot_token}"


def load_config() -> TelegramConfig:
    """Load configuration from environment variables and .env file."""
    return TelegramConfig()
