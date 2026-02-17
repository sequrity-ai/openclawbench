"""Factory for creating benchmark scenario instances with proper configuration.

This module centralizes scenario instantiation logic, making it easy to add new
scenarios without modifying CLI code.
"""

import logging
from typing import Any

from benchmarks.base import ScenarioBase
from config import TelegramConfig

logger = logging.getLogger(__name__)


class ScenarioConfig:
    """Configuration for a specific scenario type."""

    def __init__(
        self,
        scenario_class: type[ScenarioBase],
        requires_remote_manager: bool = False,
        config_keys: dict[str, str] | None = None,
    ):
        """Initialize scenario configuration.

        Args:
            scenario_class: The scenario class to instantiate
            requires_remote_manager: Whether this scenario needs remote_manager for validation
            config_keys: Mapping of init parameter names to config attribute names
                        Example: {"github_token": "github_token", "test_repo_owner": "github_test_repo_owner"}
        """
        self.scenario_class = scenario_class
        self.requires_remote_manager = requires_remote_manager
        self.config_keys = config_keys or {}


# Registry of scenario configurations
SCENARIO_CONFIGS: dict[str, ScenarioConfig] = {}


def register_scenario(name: str, config: ScenarioConfig) -> None:
    """Register a scenario configuration.

    Args:
        name: Scenario name (matches SCENARIO_MAP keys)
        config: Scenario configuration
    """
    SCENARIO_CONFIGS[name] = config


def create_scenario(
    scenario_class: type[ScenarioBase],
    config: TelegramConfig,
    remote_manager: Any = None,
) -> ScenarioBase:
    """Create a scenario instance with appropriate configuration.

    Args:
        scenario_class: The scenario class to instantiate
        config: Telegram configuration
        remote_manager: Optional RemoteWorkspaceManager for remote validation

    Returns:
        Instantiated scenario
    """
    # Find the scenario configuration
    scenario_config = None
    for name, sc_config in SCENARIO_CONFIGS.items():
        if sc_config.scenario_class == scenario_class:
            scenario_config = sc_config
            break

    if not scenario_config:
        # Fallback: instantiate with remote_manager only
        logger.warning(f"No configuration found for {scenario_class.__name__}, using default instantiation")
        return scenario_class(remote_manager=remote_manager)

    # Build initialization parameters
    init_params = {}

    # Add config-based parameters
    for param_name, config_attr in scenario_config.config_keys.items():
        value = getattr(config, config_attr, None)
        if value is not None:
            init_params[param_name] = value

    # Add remote_manager if required
    if scenario_config.requires_remote_manager:
        init_params["remote_manager"] = remote_manager
    else:
        # Explicitly set to None for scenarios that don't need it
        init_params["remote_manager"] = None

    return scenario_class(**init_params)


# Register all scenarios
def _register_all_scenarios():
    """Register all known scenarios with their configurations."""
    from benchmarks.scenarios import (
        FileScenario,
        GmailScenario,
        GitHubScenario,
        SummarizeScenario,
        WeatherScenario,
        WebScenario,
    )

    # File scenario - needs remote_manager for file validation
    register_scenario(
        "file",
        ScenarioConfig(
            scenario_class=FileScenario,
            requires_remote_manager=True,
        ),
    )

    # Gmail scenario - validates via Gmail API, no remote files
    register_scenario(
        "gmail",
        ScenarioConfig(
            scenario_class=GmailScenario,
            requires_remote_manager=False,
            config_keys={
                "client_id": "google_client_id",
                "client_secret": "google_client_secret",
                "refresh_token": "google_refresh_token",
                "benchmark_email": "gmail_benchmark_email",
                "bot_email": "gmail_bot_email",
            },
        ),
    )

    # GitHub scenario - validates via GitHub API, no remote files
    register_scenario(
        "github",
        ScenarioConfig(
            scenario_class=GitHubScenario,
            requires_remote_manager=False,
            config_keys={
                "github_token": "github_token",
                "test_repo_owner": "github_test_repo_owner",
                "test_repo_name": "github_test_repo_name",
            },
        ),
    )

    # Web Search scenario - validates text responses only
    register_scenario(
        "web",
        ScenarioConfig(
            scenario_class=WebScenario,
            requires_remote_manager=False,
        ),
    )

    # Weather scenario - validates text responses only
    register_scenario(
        "weather",
        ScenarioConfig(
            scenario_class=WeatherScenario,
            requires_remote_manager=False,
        ),
    )

    # Summarize scenario - uploads seed documents to remote server via SFTP
    register_scenario(
        "summarize",
        ScenarioConfig(
            scenario_class=SummarizeScenario,
            requires_remote_manager=True,
        ),
    )


# Auto-register on module import
_register_all_scenarios()
