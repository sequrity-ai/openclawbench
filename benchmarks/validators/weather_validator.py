"""Validation utilities for Weather benchmark tasks."""

import logging
from typing import Any

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)


class WeatherValidator:
    """Validates Weather task results."""

    @staticmethod
    def validate_current_weather(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Current weather query.

        Expected: Bot reports current weather for a specific city

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including city name
        """
        city = setup_data.get("city", "San Francisco")

        success = False
        accuracy_score = 0.0
        validation_details = {"city": city}
        error_message = None

        try:
            # Check if bot mentioned the city and weather-related terms
            city_mentioned = city.lower() in response.lower()

            # Check for weather-related keywords
            weather_keywords = ["temperature", "temp", "degrees", "°", "weather", "sunny", "cloudy", "rain", "wind"]
            weather_mentioned = any(keyword in response.lower() for keyword in weather_keywords)

            validation_details["city_mentioned"] = city_mentioned
            validation_details["weather_mentioned"] = weather_mentioned

            # Binary scoring: city AND weather info must be present
            if city_mentioned and weather_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                accuracy_score = 0.0
                missing_parts = []
                if not city_mentioned:
                    missing_parts.append(f"city '{city}'")
                if not weather_mentioned:
                    missing_parts.append("weather information")
                error_message = f"Missing: {', '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Current Weather",
            prompt="Get current weather for a city",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_weather_forecast(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: Weather forecast query.

        Expected: Bot reports multi-day forecast

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including city and forecast days
        """
        city = setup_data.get("city", "New York")
        days = setup_data.get("forecast_days", 3)

        success = False
        accuracy_score = 0.0
        validation_details = {"city": city, "forecast_days": days}
        error_message = None

        try:
            # Check for city mention
            city_mentioned = city.lower() in response.lower()

            # Check for forecast-related keywords
            forecast_keywords = ["forecast", "tomorrow", "next", "day", "week", "upcoming"]
            forecast_mentioned = any(keyword in response.lower() for keyword in forecast_keywords)

            validation_details["city_mentioned"] = city_mentioned
            validation_details["forecast_mentioned"] = forecast_mentioned

            # Binary scoring
            if city_mentioned and forecast_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                accuracy_score = 0.0
                missing_parts = []
                if not city_mentioned:
                    missing_parts.append(f"city '{city}'")
                if not forecast_mentioned:
                    missing_parts.append("forecast information")
                error_message = f"Missing: {', '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Weather Forecast",
            prompt="Get weather forecast for multiple days",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_weather_comparison(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: Compare weather across cities.

        Expected: Bot compares weather between two cities

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including two cities
        """
        city1 = setup_data.get("city1", "London")
        city2 = setup_data.get("city2", "Tokyo")

        success = False
        accuracy_score = 0.0
        validation_details = {"city1": city1, "city2": city2}
        error_message = None

        try:
            # Check for both cities
            city1_mentioned = city1.lower() in response.lower()
            city2_mentioned = city2.lower() in response.lower()

            # Check for comparison keywords
            comparison_keywords = ["warmer", "colder", "compared", "difference", "than", "versus", "vs"]
            comparison_mentioned = any(keyword in response.lower() for keyword in comparison_keywords)

            validation_details["city1_mentioned"] = city1_mentioned
            validation_details["city2_mentioned"] = city2_mentioned
            validation_details["comparison_mentioned"] = comparison_mentioned

            # Binary scoring: both cities AND comparison must be present
            if city1_mentioned and city2_mentioned and comparison_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                accuracy_score = 0.0
                missing_parts = []
                if not city1_mentioned:
                    missing_parts.append(f"city '{city1}'")
                if not city2_mentioned:
                    missing_parts.append(f"city '{city2}'")
                if not comparison_mentioned:
                    missing_parts.append("comparison")
                error_message = f"Missing: {', '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Weather Comparison",
            prompt="Compare weather between two cities",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
