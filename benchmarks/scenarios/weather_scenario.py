"""Weather benchmark scenario.

Tasks (9) — all pinned to historical/climate ground-truth facts:
    Easy:
       - Task 1 (Record High): SF all-time record high temp — 106°F, set in 2017
       - Task 2 (Rainfall Comparison): Miami vs Seattle annual rainfall — Miami wins (~62" vs ~39")
       - Task 3 (City Comparison): London vs Tokyo average January temp — Tokyo is warmer

    Medium:
       - Task 4 (Multi-City Ranking): Paris/Berlin/Rome — Rome has hottest average July temp (~25-26°C)
       - Task 5 (Monthly Extreme): Seattle's wettest month — November, ~6.5 inches
       - Task 6 (Snowfall Fact): Chicago average annual snowfall — ~36-37 inches

    Hard:
       - Task 7 (National Record): UK all-time record high temperature — 40.3°C, July 2022
       - Task 8 (Rainfall Comparison): NYC vs London annual rainfall — NYC wetter (~50" vs ~27")
       - Task 9 (Global Extreme): Coldest capital city by avg annual temp — Ulaanbaatar, Mongolia

Setup:
    No special setup required. Tasks use weather skill + web search for historical/climate facts.

Required Skills:
    steipete/weather
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
            required_skills=["steipete/weather"],
        )

        self.validator = WeatherValidator()
        self.remote_manager = remote_manager
        self.setup_data = {}

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 9 Weather tasks with progressive complexity."""

        # Task 1: SF All-Time Record High
        self.add_task(
            BenchmarkTask(
                name="Current Weather",
                prompt=(
                    "What is San Francisco's all-time record high temperature, "
                    "and what year was it set?"
                ),
                expected_output_description="Bot reports SF all-time record high is 106°F set in 2017",
                validation_fn=self.validator.validate_current_weather,
                timeout=45.0,
                metadata={"difficulty": "easy", "category": "weather_record"},
            )
        )

        # Task 2: Miami vs Seattle Annual Rainfall
        self.add_task(
            BenchmarkTask(
                name="Weather Forecast",
                prompt=(
                    "Which city gets more annual rainfall — Miami or Seattle? "
                    "How much does each city receive per year in inches?"
                ),
                expected_output_description="Bot reports Miami gets ~62 inches vs Seattle ~39 inches, Miami wins",
                validation_fn=self.validator.validate_weather_forecast,
                timeout=45.0,
                metadata={"difficulty": "easy", "category": "weather_comparison"},
            )
        )

        # Task 3: London vs Tokyo January Temperature
        self.add_task(
            BenchmarkTask(
                name="Weather Comparison",
                prompt=(
                    "Compare the average January temperatures in London and Tokyo. "
                    "Which city is warmer in January, and what are their average January temperatures?"
                ),
                expected_output_description="Bot reports Tokyo (~6°C/43°F) is warmer than London (near freezing) in January",
                validation_fn=self.validator.validate_weather_comparison,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "weather_comparison"},
            )
        )

        # Task 4: Hottest July — Rome vs Paris vs Berlin
        self.add_task(
            BenchmarkTask(
                name="Multi-City Weather",
                prompt=(
                    "Among Paris, Berlin, and Rome, which city has the highest average July temperature? "
                    "What is that city's average July temperature?"
                ),
                expected_output_description="Bot identifies Rome as hottest in July (~25-26°C / 77-79°F)",
                validation_fn=self.validator.validate_multi_city_weather,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "weather_ranking"},
            )
        )

        # Task 5: Seattle Wettest Month
        self.add_task(
            BenchmarkTask(
                name="Weather Alerts",
                prompt=(
                    "What is Seattle's wettest month of the year, "
                    "and how many inches of rain does it typically receive that month?"
                ),
                expected_output_description="Bot identifies November as Seattle's wettest month with ~6.5 inches",
                validation_fn=self.validator.validate_weather_alerts,
                timeout=45.0,
                metadata={"difficulty": "medium", "category": "weather_monthly"},
            )
        )

        # Task 6: Chicago Annual Snowfall
        self.add_task(
            BenchmarkTask(
                name="Temperature Trend",
                prompt=(
                    "How much snow does Chicago receive on average per year? "
                    "Give me the average annual snowfall in inches."
                ),
                expected_output_description="Bot reports Chicago averages ~36-37 inches of snow per year",
                validation_fn=self.validator.validate_temperature_trend,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "weather_snowfall"},
            )
        )

        # Task 7: UK All-Time Record High
        self.add_task(
            BenchmarkTask(
                name="Travel Weather Planning",
                prompt=(
                    "What is the highest temperature ever recorded in the United Kingdom, "
                    "and what year did it occur?"
                ),
                expected_output_description="Bot reports UK all-time record is 40.3°C (104.5°F) set in 2022",
                validation_fn=self.validator.validate_travel_weather,
                timeout=75.0,
                metadata={"difficulty": "hard", "category": "weather_record"},
            )
        )

        # Task 8: NYC vs London Annual Rainfall
        self.add_task(
            BenchmarkTask(
                name="Best Weather Day",
                prompt=(
                    "Which city receives more annual rainfall — New York City or London? "
                    "How many inches does each city get per year?"
                ),
                expected_output_description="Bot reports NYC (~50 inches) is wetter than London (~27 inches)",
                validation_fn=self.validator.validate_best_weather_day,
                timeout=75.0,
                metadata={"difficulty": "hard", "category": "weather_comparison"},
            )
        )

        # Task 9: Coldest Capital City
        self.add_task(
            BenchmarkTask(
                name="Severe Weather Risk",
                prompt=(
                    "What is the coldest capital city in the world by average annual temperature? "
                    "What country is it in?"
                ),
                expected_output_description="Bot identifies Ulaanbaatar, Mongolia as the coldest capital city",
                validation_fn=self.validator.validate_severe_weather_risk,
                timeout=75.0,
                metadata={"difficulty": "hard", "category": "weather_extreme"},
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

            # Store expected data for validation — all historical ground truths
            self.setup_data = {
                # Task 1: SF all-time record high
                "sf_record": {
                    "temperature_f": "106",
                    "year": "2017",
                    "city": "San Francisco",
                },
                # Task 2: Miami vs Seattle annual rainfall
                "rainfall_comparison": {
                    "winner": "Miami",
                    "miami_inches": "62",   # ~61.7 inches
                    "seattle_inches": "39",
                },
                # Task 3: London vs Tokyo January temperature
                "january_comparison": {
                    "warmer_city": "Tokyo",
                    "tokyo_jan_c": "6",     # ~6°C average
                    "london_jan_c": "4",    # ~4°C average
                },
                # Task 4: Hottest July — Rome
                "july_ranking": {
                    "hottest_city": "Rome",
                    "rome_july_c": "25",    # ~25-26°C average
                },
                # Task 5: Seattle wettest month
                "seattle_wettest": {
                    "month": "November",
                    "inches": "6.5",
                },
                # Task 6: Chicago annual snowfall
                "chicago_snowfall": {
                    "inches_low": "36",
                    "inches_high": "37",
                    "city": "Chicago",
                },
                # Task 7: UK all-time record high
                "uk_record": {
                    "temperature_c": "40.3",
                    "year": "2022",
                    "location": "Coningsby",
                },
                # Task 8: NYC vs London annual rainfall
                "nyc_london_rainfall": {
                    "winner": "New York City",
                    "nyc_inches": "50",    # ~49.9 inches
                    "london_inches": "27", # ~27.2 inches
                },
                # Task 9: Coldest capital city
                "coldest_capital": {
                    "city": "Ulaanbaatar",
                    "country": "Mongolia",
                    "avg_temp_c": "-0.8",
                },
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
