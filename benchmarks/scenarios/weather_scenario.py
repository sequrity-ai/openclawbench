"""Weather benchmark scenario.

Tasks (9) — all require REAL-TIME weather data via API (not parametric knowledge):
    Easy:
       - Task 1 (Today's High): Today's forecasted high temperature in Reykjavik, Iceland
       - Task 2 (Specific Date High/Low): High and low temps in Dubai, UAE on Feb 20, 2026
       - Task 3 (Tomorrow's Precipitation): Will it rain in Singapore tomorrow?

    Medium:
       - Task 4 (Two-City Today): Which city has higher temp today — Oslo or Helsinki?
       - Task 5 (Specific Date Average): Average temperature in Auckland, NZ on Feb 22, 2026
       - Task 6 (Tomorrow's Wind): Forecasted max wind speed for Chicago tomorrow

    Hard:
       - Task 7 (Next 3 Days Warmest): Which of next 3 days has highest temp in Vancouver?
       - Task 8 (Three-City Ranking): Rank Tokyo, Seoul, Beijing by high temp on Feb 23, 2026
       - Task 9 (Two-City Range Diff): Difference between Moscow and Cairo temp ranges on Feb 23, 2026

Setup:
    No special setup required. All tasks require live weather API queries.
    Validators independently fetch ground truth from Open-Meteo API.

Required Skills:
    steipete/weather

IMPORTANT: All tasks require real-time data that changes daily.
Models CANNOT answer from parametric knowledge and MUST use the weather tool.
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
            description="Tests agent's ability to retrieve historical and climate facts using the weather skill",
            required_skills=["weather"],
        )

        self.validator = WeatherValidator()
        self.remote_manager = remote_manager
        self.setup_data = {}

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 9 Weather tasks with progressive complexity."""

        # Task 1: Today's High Temperature
        self.add_task(
            BenchmarkTask(
                name="Today's High Temperature",
                prompt="What is today's forecasted high temperature in Reykjavik, Iceland?",
                expected_output_description="Bot reports today's forecasted high temp for Reykjavik using weather API",
                validation_fn=self.validator.validate_today_high_temp,
                timeout=45.0,
                metadata={"difficulty": "easy", "category": "current_forecast"},
            )
        )

        # Task 2: Specific Date High/Low
        self.add_task(
            BenchmarkTask(
                name="Specific Date High/Low",
                prompt="What were the high and low temperatures in Dubai, UAE on February 20, 2026?",
                expected_output_description="Bot reports high and low temps for Dubai on Feb 20, 2026",
                validation_fn=self.validator.validate_specific_date_high_low,
                timeout=45.0,
                metadata={"difficulty": "easy", "category": "specific_date"},
            )
        )

        # Task 3: Tomorrow's Precipitation
        self.add_task(
            BenchmarkTask(
                name="Tomorrow's Precipitation",
                prompt="Will it rain in Singapore tomorrow?",
                expected_output_description="Bot checks tomorrow's forecast for Singapore and reports if rain is expected",
                validation_fn=self.validator.validate_tomorrow_precipitation,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "precipitation_forecast"},
            )
        )

        # Task 4: Two-City Comparison Today
        self.add_task(
            BenchmarkTask(
                name="Two-City Comparison Today",
                prompt="Which city has a higher forecasted temperature today — Oslo, Norway or Helsinki, Finland?",
                expected_output_description="Bot compares today's forecasted temps for Oslo and Helsinki",
                validation_fn=self.validator.validate_two_city_today,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "multi_city_comparison"},
            )
        )

        # Task 5: Specific Date Average Temperature
        self.add_task(
            BenchmarkTask(
                name="Specific Date Average",
                prompt="What was the average temperature in Auckland, New Zealand on February 22, 2026?",
                expected_output_description="Bot reports average temp for Auckland on Feb 22, 2026",
                validation_fn=self.validator.validate_specific_date_average,
                timeout=45.0,
                metadata={"difficulty": "medium", "category": "average_temp"},
            )
        )

        # Task 6: Tomorrow's Wind Speed
        self.add_task(
            BenchmarkTask(
                name="Tomorrow's Wind Speed",
                prompt="What is the forecasted maximum wind speed for Chicago, Illinois tomorrow?",
                expected_output_description="Bot reports tomorrow's max wind speed for Chicago",
                validation_fn=self.validator.validate_tomorrow_wind,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "wind_forecast"},
            )
        )

        # Task 7: Next 3 Days Warmest
        self.add_task(
            BenchmarkTask(
                name="Next 3 Days Warmest",
                prompt="Over the next 3 days, which day will have the highest temperature in Vancouver, Canada?",
                expected_output_description="Bot analyzes 3-day forecast for Vancouver and identifies warmest day",
                validation_fn=self.validator.validate_next_3_days_warmest,
                timeout=75.0,
                metadata={"difficulty": "hard", "category": "multi_day_analysis"},
            )
        )

        # Task 8: Three-City Ranking Specific Date
        self.add_task(
            BenchmarkTask(
                name="Three-City Ranking",
                prompt="On February 23, 2026, rank Tokyo, Seoul, and Beijing from warmest to coldest by their high temperatures.",
                expected_output_description="Bot fetches Feb 23 temps for Tokyo, Seoul, Beijing and ranks them",
                validation_fn=self.validator.validate_three_city_ranking,
                timeout=75.0,
                metadata={"difficulty": "hard", "category": "multi_city_ranking"},
            )
        )

        # Task 9: Two-City Temperature Range Difference
        self.add_task(
            BenchmarkTask(
                name="Two-City Range Difference",
                prompt=(
                    "On February 23, 2026, what is the difference between Moscow, Russia's temperature range "
                    "and Cairo, Egypt's temperature range? (Temperature range = high temp - low temp for each city)"
                ),
                expected_output_description="Bot calculates temp ranges for both cities and finds the difference",
                validation_fn=self.validator.validate_two_city_range_diff,
                timeout=75.0,
                metadata={"difficulty": "hard", "category": "range_calculation"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        # Check for weather skill
        local_mode = self.remote_manager is None
        checks = check_skills(self.required_skills, local_mode=local_mode, remote_manager=self.remote_manager)

        # CRITICAL: Check OpenAI API key (required for AI agent)
        checks.append(self._check_openai_api_key())

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

            # Store location coordinates for Open-Meteo API validation
            self.setup_data = {
                # Task 1: Today's high in Reykjavik
                "reykjavik": {"lat": 64.13, "lon": -21.90, "city": "Reykjavik", "country": "Iceland"},
                # Task 2: Specific date high/low in Dubai
                "dubai": {"lat": 25.27, "lon": 55.30, "city": "Dubai", "country": "UAE", "date": "2026-02-20"},
                # Task 3: Tomorrow's precipitation in Singapore
                "singapore": {"lat": 1.29, "lon": 103.85, "city": "Singapore", "country": "Singapore"},
                # Task 4: Two-city comparison today
                "oslo": {"lat": 59.91, "lon": 10.75, "city": "Oslo", "country": "Norway"},
                "helsinki": {"lat": 60.17, "lon": 24.94, "city": "Helsinki", "country": "Finland"},
                # Task 5: Specific date average in Auckland
                "auckland": {"lat": -36.85, "lon": 174.76, "city": "Auckland", "country": "New Zealand", "date": "2026-02-22"},
                # Task 6: Tomorrow's wind in Chicago
                "chicago": {"lat": 41.88, "lon": -87.63, "city": "Chicago", "country": "USA"},
                # Task 7: Next 3 days warmest in Vancouver
                "vancouver": {"lat": 49.28, "lon": -123.12, "city": "Vancouver", "country": "Canada"},
                # Task 8: Three-city ranking on specific date
                "tokyo": {"lat": 35.68, "lon": 139.65, "city": "Tokyo", "country": "Japan", "date": "2026-02-23"},
                "seoul": {"lat": 37.57, "lon": 126.98, "city": "Seoul", "country": "South Korea", "date": "2026-02-23"},
                "beijing": {"lat": 39.90, "lon": 116.41, "city": "Beijing", "country": "China", "date": "2026-02-23"},
                # Task 9: Two-city range difference on specific date
                "moscow": {"lat": 55.75, "lon": 37.62, "city": "Moscow", "country": "Russia", "date": "2026-02-23"},
                "cairo": {"lat": 30.04, "lon": 31.24, "city": "Cairo", "country": "Egypt", "date": "2026-02-23"},
            }

            logger.info("Setup complete - location coordinates configured for Open-Meteo validation")

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
