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

    # Telegram settings (Client API - for user-based client)
    telegram_api_id: int = Field(
        default=0,
        description="Telegram API ID from https://my.telegram.org (required for Telegram mode)",
    )
    telegram_api_hash: str = Field(
        default="",
        description="Telegram API Hash from https://my.telegram.org (required for Telegram mode)",
    )
    telegram_phone: str = Field(
        default="",
        description="Your Telegram phone number (with country code, e.g. +1234567890)",
    )
    telegram_session_name: str = Field(
        default="openclaw_benchmark",
        description="Session name for storing authentication data",
    )
    openclaw_bot_username: str = Field(
        default="openclaw_bot",
        description="Username of the OpenClaw bot to interact with",
    )

    # Deprecated Bot API settings (kept for backwards compatibility)
    telegram_bot_token: str = Field(
        default="",
        description="[DEPRECATED] Telegram bot token - use Client API instead",
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

    # Remote setup settings
    bot_ssh_host: str = Field(
        default="localhost",
        description="SSH host for remote bot setup and validation",
    )
    bot_ssh_port: int = Field(
        default=22,
        description="SSH port for remote bot connection",
    )
    bot_ssh_user: str = Field(
        default="openclaw",
        description="SSH username for remote bot connection",
    )
    bot_workspace_path: str = Field(
        default="/tmp/openclaw_benchmark",
        description="Workspace path on remote bot for benchmark files",
    )
    bot_ssh_key_path: str = Field(
        default="",
        description="Path to SSH private key for remote bot authentication (e.g. ~/.ssh/id_rsa)",
    )
    bot_ssh_password: str = Field(
        default="",
        description="SSH password for remote bot authentication (use key_path if possible)",
    )
    bot_ssh_key_passphrase: str = Field(
        default="",
        description="Passphrase for encrypted SSH private key (if applicable)",
    )

    # Daytona sandbox settings
    daytona_api_key: str = Field(
        default="",
        description="Daytona API key for sandbox creation (from app.daytona.io)",
    )
    daytona_api_url: str = Field(
        default="https://app.daytona.io/api",
        description="Daytona API URL",
    )
    daytona_image: str = Field(
        default="ubuntu:22.04",
        description="Docker image for Daytona sandbox",
    )

    # Bot model switching (remote mode only)
    bot_model: str = Field(
        default="",
        description="OpenClaw bot model to switch to before benchmarking (e.g. anthropic/claude-opus-4-5). Empty = use bot's current model.",
    )

    # Bot workspace / custom prompt injection
    bot_workspace_dir: str = Field(
        default="~/.openclaw/workspace",
        description="Path to the OpenClaw bot workspace directory (where SOUL.md lives)",
    )
    custom_bot_prompt_file: str = Field(
        default="",
        description="Path to a file whose contents will be injected as SOUL.md in the bot workspace before benchmarking. Empty = leave SOUL.md unchanged.",
    )

    # AI agent settings
    ai_agent_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model for AI agent user simulation",
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for AI agent",
    )

    # Conversation settings
    max_conversation_turns: int = Field(
        default=10,
        description="Maximum number of conversation turns per task",
    )
    conversation_timeout: float = Field(
        default=300.0,
        description="Maximum time for entire conversation in seconds",
    )

    # Gmail API settings (for Gmail scenario - requires TWO Gmail accounts)
    google_client_id: str = Field(
        default="",
        description="OAuth2 client ID for BENCHMARK Gmail account",
    )
    google_client_secret: str = Field(
        default="",
        description="OAuth2 client secret for BENCHMARK Gmail account",
    )
    google_refresh_token: str = Field(
        default="",
        description="OAuth2 refresh token for BENCHMARK Gmail account",
    )
    gmail_benchmark_email: str = Field(
        default="",
        description="Benchmark Gmail address (account that has OAuth2 credentials)",
    )
    gmail_bot_email: str = Field(
        default="",
        description="Bot's Gmail address (configured in OpenClaw bot)",
    )

    # Tavily API settings (for Web Search scenario)
    tavily_api_key: str = Field(
        default="",
        description="Tavily API key for web search capabilities",
    )

    # GitHub API settings (for GitHub scenario)
    github_token: str = Field(
        default="",
        description="GitHub personal access token for benchmark validation",
    )
    github_test_repo_owner: str = Field(
        default="",
        description="Owner of test repository for GitHub benchmarks",
    )
    github_test_repo_name: str = Field(
        default="",
        description="Name of test repository for GitHub benchmarks",
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


Config = TelegramConfig


def load_config() -> TelegramConfig:
    """Load configuration from environment variables and .env file."""
    return TelegramConfig()
