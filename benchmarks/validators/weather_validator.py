"""Validation utilities for weather skill tasks."""

import re
from typing import Any

from benchmarks.base import TaskResult


class WeatherValidator:
    """Validates weather skill task results."""

    @staticmethod
    def validate_current_weather(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Current weather for a city.

        Expected: Temperature value and a weather condition.
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}

        response_lower = response.lower()

        # Check for temperature (number followed by °C, °F, C, F, celsius, fahrenheit)
        temp_pattern = r"-?\d+\.?\d*\s*(?:°[CF]|degrees?|celsius|fahrenheit|[CF]\b)"
        found_temp = bool(re.search(temp_pattern, response, re.IGNORECASE))
        validation_details["found_temperature"] = found_temp
        if found_temp:
            accuracy_score += 50.0

        # Check for weather condition words
        conditions = [
            "sunny", "cloudy", "overcast", "rain", "snow", "clear",
            "fog", "mist", "drizzle", "storm", "thunder", "wind",
            "haze", "partly", "scattered", "humid", "dry", "warm",
            "cold", "cool", "hot", "freezing", "mild",
        ]
        found_condition = any(c in response_lower for c in conditions)
        validation_details["found_condition"] = found_condition
        if found_condition:
            accuracy_score += 30.0

        # Check that London is mentioned
        found_city = "london" in response_lower
        validation_details["found_city"] = found_city
        if found_city:
            accuracy_score += 20.0

        if found_temp and found_condition:
            success = True
        if found_temp and found_condition and found_city:
            accuracy_score = 100.0

        error_message = None
        if not success:
            missing = []
            if not found_temp:
                missing.append("temperature value")
            if not found_condition:
                missing.append("weather condition")
            error_message = f"Missing: {', '.join(missing)}"

        return TaskResult(
            task_name="Current Weather",
            prompt="What's the current weather in London?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_forecast_comparison(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: Forecast comparison between two cities.

        Expected: Both cities mentioned with multiple temperatures and day references.
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}

        response_lower = response.lower()

        # Check both cities are mentioned
        found_tokyo = "tokyo" in response_lower
        found_ny = "new york" in response_lower or "nyc" in response_lower
        validation_details["found_tokyo"] = found_tokyo
        validation_details["found_new_york"] = found_ny
        if found_tokyo:
            accuracy_score += 20.0
        if found_ny:
            accuracy_score += 20.0

        # Check for multiple temperature values (at least 3 for comparison)
        temp_pattern = r"-?\d+\.?\d*\s*(?:°[CF]|degrees?|celsius|fahrenheit|[CF]\b)"
        temps = re.findall(temp_pattern, response, re.IGNORECASE)
        validation_details["temperature_count"] = len(temps)
        if len(temps) >= 4:
            accuracy_score += 30.0
        elif len(temps) >= 2:
            accuracy_score += 15.0

        # Check for day/date references
        day_keywords = [
            "monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday", "sunday", "today", "tomorrow", "day 1", "day 2",
            "day 3", "next",
        ]
        found_days = sum(1 for d in day_keywords if d in response_lower)
        validation_details["day_references"] = found_days
        if found_days >= 3:
            accuracy_score += 30.0
        elif found_days >= 1:
            accuracy_score += 15.0

        if found_tokyo and found_ny and len(temps) >= 2:
            success = True
        if accuracy_score >= 100.0:
            accuracy_score = 100.0

        error_message = None
        if not success:
            missing = []
            if not found_tokyo:
                missing.append("Tokyo")
            if not found_ny:
                missing.append("New York")
            if len(temps) < 2:
                missing.append("temperature comparisons")
            error_message = f"Missing: {', '.join(missing)}"

        return TaskResult(
            task_name="Forecast Comparison",
            prompt="Compare weather forecast for Tokyo and New York for 3 days",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
