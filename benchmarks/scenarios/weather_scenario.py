"""Weather skill benchmark scenario."""

import logging

from benchmarks.base import (
    BenchmarkTask,
    HealthCheckResult,
    ScenarioBase,
    SetupResult,
    CheckStatus,
)
from benchmarks.skill_checker import check_skills
from benchmarks.validators.weather_validator import WeatherValidator

logger = logging.getLogger(__name__)


class WeatherScenario(ScenarioBase):
    """Benchmark scenario for the weather skill."""

    def __init__(self):
        super().__init__(
            name="Weather",
            description="Tests the weather skill: current conditions and forecast comparison",
            required_skills=["weather"],
        )

        self.validator = WeatherValidator()
        self._define_tasks()

    def _define_tasks(self) -> None:
        self.add_task(
            BenchmarkTask(
                name="Current Weather",
                prompt="What's the current weather in London? Give me the temperature and conditions.",
                expected_output_description="Temperature and weather condition for London",
                validation_fn=self.validator.validate_current_weather,
                timeout=30.0,
            )
        )

        self.add_task(
            BenchmarkTask(
                name="Forecast Comparison",
                prompt=(
                    "Compare the weather forecast for Tokyo and New York for the next 3 days. "
                    "Show the temperature and conditions for each city and each day."
                ),
                expected_output_description="Side-by-side 3-day forecast for Tokyo and New York",
                validation_fn=self.validator.validate_forecast_comparison,
                timeout=60.0,
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        return check_skills(self.required_skills)

    def setup(self) -> SetupResult:
        return SetupResult(
            status=CheckStatus.PASS,
            message="No setup needed for weather scenario",
            setup_data={},
        )

    def cleanup(self) -> bool:
        return True
