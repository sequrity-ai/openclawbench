"""Validation utilities for Weather benchmark tasks.

All tasks are pinned to historical/climate ground-truth facts — no live data required.
"""

import logging
from typing import Any

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)


class WeatherValidator:
    """Validates Weather task results against historical/climate ground-truth facts."""

    @staticmethod
    def validate_current_weather(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: SF all-time record high temperature (EASY).

        Expected: Bot reports San Francisco's all-time record high is 106°F, set in 2017.

        Conditions:
          1. "106" appears in the response (the temperature)
          2. "2017" appears in the response (the year)
        """
        sf_record = setup_data.get("sf_record", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"sf_record": sf_record}
        error_message = None

        try:
            response_lower = response.lower()

            temp_found = "106" in response_lower
            year_found = "2017" in response_lower
            validation_details["temp_106_found"] = temp_found
            validation_details["year_2017_found"] = year_found

            if temp_found and year_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not temp_found:
                    missing_parts.append("record temperature '106'°F")
                if not year_found:
                    missing_parts.append("record year '2017'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Current Weather",
            prompt="What is San Francisco's all-time record high temperature, and what year was it set?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_weather_forecast(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: Miami vs Seattle annual rainfall comparison (EASY).

        Expected: Bot reports Miami gets more rain than Seattle (~62" vs ~39").

        Conditions:
          1. "miami" appears (correct winner identified)
          2. "61" OR "62" appears (Miami's approximate annual rainfall in inches)
        """
        rainfall = setup_data.get("rainfall_comparison", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"rainfall_comparison": rainfall}
        error_message = None

        try:
            response_lower = response.lower()

            miami_found = "miami" in response_lower
            # Accept 61 or 62 inches (sources vary slightly: 61.7–62 inches)
            amount_found = "61" in response_lower or "62" in response_lower
            validation_details["miami_found"] = miami_found
            validation_details["amount_found"] = amount_found

            if miami_found and amount_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not miami_found:
                    missing_parts.append("'Miami' as the wetter city")
                if not amount_found:
                    missing_parts.append("Miami annual rainfall '61' or '62' inches")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Weather Forecast",
            prompt="Which city gets more annual rainfall — Miami or Seattle? How much does each get?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_weather_comparison(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: London vs Tokyo average January temperature (EASY).

        Expected: Bot reports Tokyo is warmer than London in January.
        Tokyo averages ~6°C (43°F) in January; London is near or below freezing (~4°C).

        Conditions:
          1. "tokyo" appears in response
          2. "warmer" OR "higher" OR "milder" appears (indicating Tokyo is the warmer city)
        """
        jan_comparison = setup_data.get("january_comparison", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"january_comparison": jan_comparison}
        error_message = None

        try:
            response_lower = response.lower()

            tokyo_found = "tokyo" in response_lower
            # Check Tokyo is identified as warmer
            warmer_signal = (
                "tokyo" in response_lower
                and any(kw in response_lower for kw in ["warmer", "higher", "milder", "warmer than london"])
            )
            validation_details["tokyo_found"] = tokyo_found
            validation_details["warmer_signal_found"] = warmer_signal

            if tokyo_found and warmer_signal:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not tokyo_found:
                    missing_parts.append("'Tokyo'")
                if not warmer_signal:
                    missing_parts.append("Tokyo identified as warmer ('warmer', 'higher', or 'milder')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Weather Comparison",
            prompt="Compare average January temperatures in London vs Tokyo — which is warmer?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_multi_city_weather(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 4: Hottest July — Rome vs Paris vs Berlin (MEDIUM).

        Expected: Bot identifies Rome as having the highest average July temperature (~25-26°C / 77-79°F).

        Conditions:
          1. "rome" appears in response (correct winner named)
          2. A temperature in the 25–30°C range OR 77–86°F range for Rome
             — accept "25", "26", "77", "78", "79", "80"
        """
        july_ranking = setup_data.get("july_ranking", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"july_ranking": july_ranking}
        error_message = None

        try:
            response_lower = response.lower()

            rome_found = "rome" in response_lower
            # Accept any representative temperature for Rome in July
            temp_signals = ["25", "26", "77", "78", "79", "80"]
            temp_found = any(t in response_lower for t in temp_signals)
            matched_temps = [t for t in temp_signals if t in response_lower]
            validation_details["rome_found"] = rome_found
            validation_details["temp_found"] = temp_found
            validation_details["matched_temps"] = matched_temps

            if rome_found and temp_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not rome_found:
                    missing_parts.append("'Rome' as the hottest city")
                if not temp_found:
                    missing_parts.append("Rome July temperature (e.g. 25°C, 26°C, 77-80°F)")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Multi-City Weather",
            prompt="Among Paris, Berlin, and Rome — which has the highest average July temperature?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_weather_alerts(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 5: Seattle's wettest month (MEDIUM).

        Expected: Bot reports November is Seattle's wettest month, with ~6.5 inches.

        Conditions:
          1. "november" appears in response
          2. "6" appears in response (representing ~6 or 6.5 inches)
        """
        seattle_wettest = setup_data.get("seattle_wettest", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"seattle_wettest": seattle_wettest}
        error_message = None

        try:
            response_lower = response.lower()

            november_found = "november" in response_lower
            # Accept "6" as in "6.5 inches" or "6 inches"
            amount_found = "6" in response_lower
            validation_details["november_found"] = november_found
            validation_details["amount_6_found"] = amount_found

            if november_found and amount_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not november_found:
                    missing_parts.append("wettest month 'November'")
                if not amount_found:
                    missing_parts.append("rainfall amount (~6 or 6.5 inches)")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Weather Alerts",
            prompt="What is Seattle's wettest month and how many inches does it receive?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_temperature_trend(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 6: Chicago average annual snowfall (MEDIUM).

        Expected: Bot reports Chicago averages ~36-37 inches of snow per year.

        Conditions:
          1. "chicago" appears in response
          2. "36" OR "37" appears in response (annual snowfall in inches)
        """
        chicago_snowfall = setup_data.get("chicago_snowfall", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"chicago_snowfall": chicago_snowfall}
        error_message = None

        try:
            response_lower = response.lower()

            chicago_found = "chicago" in response_lower
            # Accept 35, 36, or 37 (sources vary: BestPlaces says 35, NWS says 36, Choose Chicago says 37)
            amount_found = "35" in response_lower or "36" in response_lower or "37" in response_lower
            matched_amounts = [a for a in ["35", "36", "37"] if a in response_lower]
            validation_details["chicago_found"] = chicago_found
            validation_details["amount_found"] = amount_found
            validation_details["matched_amounts"] = matched_amounts

            if chicago_found and amount_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not chicago_found:
                    missing_parts.append("'Chicago'")
                if not amount_found:
                    missing_parts.append("annual snowfall amount (35, 36, or 37 inches)")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Temperature Trend",
            prompt="How much snow does Chicago receive on average per year?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_travel_weather(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 7: UK all-time record high temperature (HARD).

        Expected: Bot reports the UK record is 40.3°C (104.5°F), set in 2022.

        Conditions:
          1. "40" appears in response (the 40.3°C temperature)
          2. "2022" appears in response (the year)
        """
        uk_record = setup_data.get("uk_record", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"uk_record": uk_record}
        error_message = None

        try:
            response_lower = response.lower()

            temp_found = "40" in response_lower
            year_found = "2022" in response_lower
            validation_details["temp_40_found"] = temp_found
            validation_details["year_2022_found"] = year_found

            if temp_found and year_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not temp_found:
                    missing_parts.append("UK record temperature '40'(.3)°C")
                if not year_found:
                    missing_parts.append("record year '2022'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Travel Weather Planning",
            prompt="What is the highest temperature ever recorded in the United Kingdom and what year?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_best_weather_day(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 8: NYC vs London annual rainfall (HARD).

        Expected: Bot reports NYC receives more rain than London (~27 inches).
        NYC figures vary by source and period:
          - NOAA 1991-2020 normals: ~46.6 inches (Central Park)
          - Older datasets: ~49-50 inches
        Accept any figure in the 46-50 range.

        Conditions:
          1. "new york" appears in response (correct winner named)
          2. Any of "46", "47", "48", "49", "50" appears (NYC annual rainfall)
        """
        nyc_london = setup_data.get("nyc_london_rainfall", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"nyc_london_rainfall": nyc_london}
        error_message = None

        try:
            response_lower = response.lower()

            nyc_found = "new york" in response_lower
            # Accept 46-50 inches: NOAA 1991-2020 normals give ~46.6"; older sources say ~49.9-50"
            accepted = ["46", "47", "48", "49", "50"]
            amount_found = any(a in response_lower for a in accepted)
            matched_amounts = [a for a in accepted if a in response_lower]
            validation_details["new_york_found"] = nyc_found
            validation_details["amount_found"] = amount_found
            validation_details["matched_amounts"] = matched_amounts

            if nyc_found and amount_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not nyc_found:
                    missing_parts.append("'New York' as the wetter city")
                if not amount_found:
                    missing_parts.append("NYC annual rainfall (46-50 inches)")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Best Weather Day",
            prompt="Which city receives more annual rainfall — New York City or London?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_severe_weather_risk(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 9: Coldest capital city in the world (HARD).

        Expected: Bot identifies Ulaanbaatar, Mongolia as the coldest capital city by average annual temperature.

        Conditions:
          1. "ulaanbaatar" appears in response (the city — unique, unambiguous)
          2. "mongolia" appears in response (the country)
        """
        coldest = setup_data.get("coldest_capital", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"coldest_capital": coldest}
        error_message = None

        try:
            response_lower = response.lower()

            ulaanbaatar_found = "ulaanbaatar" in response_lower
            mongolia_found = "mongolia" in response_lower
            validation_details["ulaanbaatar_found"] = ulaanbaatar_found
            validation_details["mongolia_found"] = mongolia_found

            if ulaanbaatar_found and mongolia_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not ulaanbaatar_found:
                    missing_parts.append("coldest capital city 'Ulaanbaatar'")
                if not mongolia_found:
                    missing_parts.append("country 'Mongolia'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Severe Weather Risk",
            prompt="What is the coldest capital city in the world by average annual temperature?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
