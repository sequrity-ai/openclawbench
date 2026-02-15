"""Weather benchmark scenario.

Architecture:
    This scenario tests the bot's ability to retrieve weather information
    using the steipete/weather skill. No API keys required.

    Task Flow:
       - Task 1: Get current weather for a specific city
       - Task 2: Get weather forecast for multiple days
       - Task 3: Compare weather between two cities
"""

import logging

from benchmarks.base import (
    BenchmarkTask,
    CheckStatus,
    HealthCheckResult,
    ScenarioBase,
    SetupResult,
)
from benchmarks.skill_checker import check_skills
from benchmarks.validators.weather_validator import WeatherValidator

logger = logging.getLogger(__name__)


class WeatherScenario(ScenarioBase):
    """Benchmark scenario for weather information retrieval."""

    def __init__(self, remote_manager=None):
        """Initialize Weather scenario.

        Args:
            remote_manager: Optional RemoteWorkspaceManager (not used for weather)

        Note:
            - Requires the steipete/weather skill to be installed
            - No API keys required
        """
        super().__init__(
            name="Weather",
            description="Tests agent's ability to retrieve and compare weather information",
            required_skills=["steipete/weather"],
        )

        self.validator = WeatherValidator()
        self.setup_data = {}

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 3 Weather tasks."""

        # Task 1: Current Weather
        self.add_task(
            BenchmarkTask(
                name="Current Weather",
                prompt="What's the current weather in San Francisco?",
                expected_output_description="Bot reports current weather conditions for San Francisco",
                validation_fn=self.validator.validate_current_weather,
                timeout=45.0,
                metadata={"difficulty": "easy", "category": "weather_current"},
            )
        )

        # Task 2: Weather Forecast
        self.add_task(
            BenchmarkTask(
                name="Weather Forecast",
                prompt="Can you get me the weather forecast for New York for the next 3 days?",
                expected_output_description="Bot provides multi-day forecast for New York",
                validation_fn=self.validator.validate_weather_forecast,
                timeout=45.0,
                metadata={"difficulty": "easy", "category": "weather_forecast"},
            )
        )

        # Task 3: Weather Comparison
        self.add_task(
            BenchmarkTask(
                name="Weather Comparison",
                prompt="Compare the current weather in London versus Tokyo. Which city is warmer?",
                expected_output_description="Bot compares weather between London and Tokyo",
                validation_fn=self.validator.validate_weather_comparison,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "weather_comparison"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        # Check for weather skill
        checks = check_skills(self.required_skills)

        checks.append(
            HealthCheckResult(
                check_name="Weather API Note",
                status=CheckStatus.PASS,
                message="Weather skill requires no API key configuration",
                details={"required_skill": "steipete/weather"},
            )
        )

        return checks

    def setup(self) -> SetupResult:
        """Set up the Weather scenario.

        Returns:
            Setup result with expected validation data
        """
        try:
            logger.info("Setting up Weather benchmark...")

            # Store expected data for validation
            self.setup_data = {
                # Task 1: Current Weather
                "city": "San Francisco",
                # Task 2: Weather Forecast
                "forecast_days": 3,
                # Task 3: Weather Comparison
                "city1": "London",
                "city2": "Tokyo",
            }

            logger.info("Setup complete - validation criteria configured")

            return SetupResult(
                status=CheckStatus.PASS,
                message="Weather scenario configured successfully",
                setup_data=self.setup_data,
            )

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return SetupResult(
                status=CheckStatus.FAIL,
                message=f"Failed to set up Weather scenario: {str(e)}",
                error=str(e),
            )

    def cleanup(self) -> bool:
        """Clean up the Weather scenario.

        Returns:
            True (no cleanup needed for weather queries)
        """
        logger.info("Weather scenario cleanup (no action needed)")
        return True
