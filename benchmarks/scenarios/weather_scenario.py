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
        self.remote_manager = remote_manager
        self.setup_data = {}

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 9 Weather tasks with progressive complexity."""

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

        # Task 4: Multi-City Weather
        self.add_task(
            BenchmarkTask(
                name="Multi-City Weather",
                prompt="Tell me the current weather in Paris, Berlin, and Rome.",
                expected_output_description="Bot reports weather for three European cities",
                validation_fn=self.validator.validate_multi_city_weather,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "weather_multi_city"},
            )
        )

        # Task 5: Weather Alerts
        self.add_task(
            BenchmarkTask(
                name="Weather Alerts",
                prompt="Are there any weather alerts or warnings for Miami?",
                expected_output_description="Bot checks for weather alerts in Miami",
                validation_fn=self.validator.validate_weather_alerts,
                timeout=45.0,
                metadata={"difficulty": "medium", "category": "weather_alerts"},
            )
        )

        # Task 6: Temperature Trend
        self.add_task(
            BenchmarkTask(
                name="Temperature Trend",
                prompt="What's the temperature trend for Seattle over the next week? Is it getting warmer or colder?",
                expected_output_description="Bot analyzes temperature trend for Seattle",
                validation_fn=self.validator.validate_temperature_trend,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "weather_trend"},
            )
        )

        # Task 7: Travel Weather Planning
        self.add_task(
            BenchmarkTask(
                name="Travel Weather Planning",
                prompt="I'm planning a trip to Barcelona next week. What should I pack based on the weather forecast?",
                expected_output_description="Bot provides packing recommendations based on Barcelona weather",
                validation_fn=self.validator.validate_travel_weather,
                timeout=75.0,
                metadata={"difficulty": "hard", "category": "weather_travel"},
            )
        )

        # Task 8: Best Weather Day
        self.add_task(
            BenchmarkTask(
                name="Best Weather Day",
                prompt="Looking at the next 5 days in Chicago, which day would be best for outdoor activities?",
                expected_output_description="Bot recommends best day for outdoor activities in Chicago",
                validation_fn=self.validator.validate_best_weather_day,
                timeout=75.0,
                metadata={"difficulty": "hard", "category": "weather_recommendation"},
            )
        )

        # Task 9: Severe Weather Risk
        self.add_task(
            BenchmarkTask(
                name="Severe Weather Risk",
                prompt="Is there any risk of severe weather like storms or extreme temperatures in Houston this weekend?",
                expected_output_description="Bot assesses severe weather risks for Houston",
                validation_fn=self.validator.validate_severe_weather_risk,
                timeout=75.0,
                metadata={"difficulty": "hard", "category": "weather_severe"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        # Check for weather skill
        local_mode = self.remote_manager is None
        checks = check_skills(self.required_skills, local_mode=local_mode, remote_manager=self.remote_manager)

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
            # Note: Each validator uses different keys from this shared dict
            self.setup_data = {
                # Task 1: Current Weather - uses "city"
                "city": "San Francisco",
                # Task 2: Weather Forecast - uses "city" (different city!) and "forecast_days"
                # We need to set city for forecast separately, so Task 2 reads from forecast_city
                "forecast_city": "New York",
                "forecast_days": 3,
                # Task 3: Weather Comparison - uses "city1" and "city2"
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
