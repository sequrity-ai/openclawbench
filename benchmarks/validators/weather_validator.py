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
        # Use forecast_city key to avoid conflict with Task 1's city
        city = setup_data.get("forecast_city", setup_data.get("city", "New York"))
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

    @staticmethod
    def validate_multi_city_weather(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 4: Multi-City Weather (MEDIUM).

        Expected: Bot reports weather for three cities
        """
        cities = ["Paris", "Berlin", "Rome"]

        success = False
        accuracy_score = 0.0
        validation_details = {"cities": cities}
        error_message = None

        try:
            # Check if all three cities are mentioned
            cities_mentioned = sum(1 for city in cities if city.lower() in response.lower())
            validation_details["cities_mentioned"] = cities_mentioned

            # Check for weather keywords
            weather_keywords = ["temperature", "temp", "degrees", "°", "weather", "sunny", "cloudy", "rain"]
            weather_mentioned = any(keyword in response.lower() for keyword in weather_keywords)
            validation_details["weather_mentioned"] = weather_mentioned

            # Pass if at least 2 cities and weather info present
            if cities_mentioned >= 2 and weather_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                error_message = f"Found {cities_mentioned}/3 cities, weather_info={weather_mentioned}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Multi-City Weather",
            prompt="Get weather for multiple cities",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_weather_alerts(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 5: Weather Alerts (MEDIUM).

        Expected: Bot checks for weather alerts
        """
        city = "Miami"

        success = False
        accuracy_score = 0.0
        validation_details = {"city": city}
        error_message = None

        try:
            city_mentioned = city.lower() in response.lower()
            validation_details["city_mentioned"] = city_mentioned

            # Check for alert-related keywords
            alert_keywords = ["alert", "warning", "advisory", "watch", "severe", "no alerts", "no warnings"]
            alert_mentioned = any(keyword in response.lower() for keyword in alert_keywords)
            validation_details["alert_mentioned"] = alert_mentioned

            if city_mentioned and alert_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                error_message = f"city_mentioned={city_mentioned}, alert_mentioned={alert_mentioned}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Weather Alerts",
            prompt="Check weather alerts for city",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_temperature_trend(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 6: Temperature Trend (MEDIUM).

        Expected: Bot analyzes temperature trend
        """
        city = "Seattle"

        success = False
        accuracy_score = 0.0
        validation_details = {"city": city}
        error_message = None

        try:
            city_mentioned = city.lower() in response.lower()
            validation_details["city_mentioned"] = city_mentioned

            # Check for trend keywords
            trend_keywords = ["warmer", "colder", "increasing", "decreasing", "trend", "rising", "falling", "temperature"]
            trend_mentioned = any(keyword in response.lower() for keyword in trend_keywords)
            validation_details["trend_mentioned"] = trend_mentioned

            if city_mentioned and trend_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                error_message = f"city_mentioned={city_mentioned}, trend_mentioned={trend_mentioned}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Temperature Trend",
            prompt="Analyze temperature trend",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_travel_weather(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 7: Travel Weather Planning (HARD).

        Expected: Bot provides packing recommendations
        """
        city = "Barcelona"

        success = False
        accuracy_score = 0.0
        validation_details = {"city": city}
        error_message = None

        try:
            city_mentioned = city.lower() in response.lower()
            validation_details["city_mentioned"] = city_mentioned

            # Check for packing/travel keywords
            packing_keywords = ["pack", "bring", "wear", "jacket", "umbrella", "clothes", "clothing", "recommend"]
            packing_mentioned = any(keyword in response.lower() for keyword in packing_keywords)
            validation_details["packing_mentioned"] = packing_mentioned

            # Check for weather info
            weather_keywords = ["weather", "temperature", "rain", "sunny", "forecast"]
            weather_mentioned = any(keyword in response.lower() for keyword in weather_keywords)
            validation_details["weather_mentioned"] = weather_mentioned

            if city_mentioned and packing_mentioned and weather_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                error_message = f"city={city_mentioned}, packing={packing_mentioned}, weather={weather_mentioned}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Travel Weather Planning",
            prompt="Provide packing recommendations based on weather",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_best_weather_day(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 8: Best Weather Day (HARD).

        Expected: Bot recommends specific day
        """
        city = "Chicago"

        success = False
        accuracy_score = 0.0
        validation_details = {"city": city}
        error_message = None

        try:
            city_mentioned = city.lower() in response.lower()
            validation_details["city_mentioned"] = city_mentioned

            # Check for day recommendation
            day_keywords = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "best", "recommend"]
            day_mentioned = any(keyword in response.lower() for keyword in day_keywords)
            validation_details["day_mentioned"] = day_mentioned

            # Check for outdoor/activity keywords
            activity_keywords = ["outdoor", "activity", "activities", "weather", "conditions"]
            activity_mentioned = any(keyword in response.lower() for keyword in activity_keywords)
            validation_details["activity_mentioned"] = activity_mentioned

            if city_mentioned and day_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                error_message = f"city={city_mentioned}, day={day_mentioned}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Best Weather Day",
            prompt="Recommend best day for outdoor activities",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_severe_weather_risk(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 9: Severe Weather Risk (HARD).

        Expected: Bot assesses severe weather risks
        """
        city = "Houston"

        success = False
        accuracy_score = 0.0
        validation_details = {"city": city}
        error_message = None

        try:
            city_mentioned = city.lower() in response.lower()
            validation_details["city_mentioned"] = city_mentioned

            # Check for risk/severe weather keywords
            severe_keywords = ["severe", "storm", "extreme", "risk", "warning", "alert", "dangerous", "no risk", "unlikely"]
            severe_mentioned = any(keyword in response.lower() for keyword in severe_keywords)
            validation_details["severe_mentioned"] = severe_mentioned

            # Check for weekend mention
            weekend_keywords = ["weekend", "saturday", "sunday"]
            weekend_mentioned = any(keyword in response.lower() for keyword in weekend_keywords)
            validation_details["weekend_mentioned"] = weekend_mentioned

            if city_mentioned and severe_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                error_message = f"city={city_mentioned}, severe={severe_mentioned}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Severe Weather Risk",
            prompt="Assess severe weather risks",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
