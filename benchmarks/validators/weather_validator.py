"""Validation utilities for Weather benchmark tasks.

All tasks require real-time weather data via API.
Validators fetch ground truth from Open-Meteo API and compare against bot responses.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any

import requests

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)


class WeatherValidator:
    """Validates Weather task results by fetching ground truth from Open-Meteo API."""

    OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
    TOLERANCE_TEMP = 2.0  # ±2°C tolerance for temperature comparisons
    TOLERANCE_WIND = 5.0  # ±5 km/h tolerance for wind speed

    @staticmethod
    def _fetch_weather(lat: float, lon: float, start_date: str, end_date: str) -> dict | None:
        """Fetch weather data from Open-Meteo API.

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            API response dict or None if fetch fails
        """
        try:
            url = (
                f"{WeatherValidator.OPEN_METEO_BASE}?"
                f"latitude={lat}&longitude={lon}"
                f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max"
                f"&timezone=auto"
                f"&start_date={start_date}&end_date={end_date}"
            )
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch weather data: {e}")
            return None

    @staticmethod
    def _extract_number(text: str, pattern: str = r"-?\d+\.?\d*") -> float | None:
        """Extract first number from text."""
        match = re.search(pattern, text)
        return float(match.group()) if match else None

    @staticmethod
    def validate_today_high_temp(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Today's high temperature in Reykjavik (EASY).

        Expected: Bot reports today's forecasted high temp for Reykjavik.

        Validation:
          1. Fetch today's weather for Reykjavik from Open-Meteo
          2. Check bot's response contains a temperature within ±2°C of actual high
        """
        reykjavik = setup_data.get("reykjavik", {})
        today = datetime.now().strftime("%Y-%m-%d")

        success = False
        accuracy_score = 0.0
        validation_details = {"location": reykjavik, "date": today}
        error_message = None

        try:
            # Fetch ground truth from Open-Meteo
            weather_data = WeatherValidator._fetch_weather(
                reykjavik["lat"], reykjavik["lon"], today, today
            )

            if not weather_data or "daily" not in weather_data:
                error_message = "Failed to fetch weather data from Open-Meteo"
            else:
                actual_high = weather_data["daily"]["temperature_2m_max"][0]
                validation_details["actual_high_temp"] = actual_high

                # Extract temperature from bot response
                bot_temp = WeatherValidator._extract_number(response)
                validation_details["bot_temp"] = bot_temp

                if bot_temp is not None:
                    temp_diff = abs(bot_temp - actual_high)
                    validation_details["temp_diff"] = temp_diff

                    if temp_diff <= WeatherValidator.TOLERANCE_TEMP:
                        success = True
                        accuracy_score = 100.0
                    else:
                        error_message = (
                            f"Temperature mismatch: bot reported {bot_temp}°C, "
                            f"actual is {actual_high}°C (diff: {temp_diff:.1f}°C)"
                        )
                else:
                    error_message = "Could not extract temperature from bot response"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Today's High Temperature",
            prompt="What is today's forecasted high temperature in Reykjavik, Iceland?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_specific_date_high_low(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: High and low temps in Dubai on Feb 20, 2026 (EASY).

        Expected: Bot reports both high and low temps for Dubai on specific date.

        Validation:
          1. Fetch Feb 20, 2026 weather for Dubai from Open-Meteo
          2. Check bot's response contains both temps within ±2°C tolerance
        """
        dubai = setup_data.get("dubai", {})
        date = dubai.get("date", "2026-02-20")

        success = False
        accuracy_score = 0.0
        validation_details = {"location": dubai, "date": date}
        error_message = None

        try:
            weather_data = WeatherValidator._fetch_weather(dubai["lat"], dubai["lon"], date, date)

            if not weather_data or "daily" not in weather_data:
                error_message = "Failed to fetch weather data from Open-Meteo"
            else:
                actual_high = weather_data["daily"]["temperature_2m_max"][0]
                actual_low = weather_data["daily"]["temperature_2m_min"][0]
                validation_details["actual_high"] = actual_high
                validation_details["actual_low"] = actual_low

                # Extract all numbers from response
                numbers = re.findall(r"-?\d+\.?\d*", response)
                temps = [float(n) for n in numbers]
                validation_details["extracted_temps"] = temps

                if len(temps) >= 2:
                    # Check if any two temps match high and low
                    high_matches = [t for t in temps if abs(t - actual_high) <= WeatherValidator.TOLERANCE_TEMP]
                    low_matches = [t for t in temps if abs(t - actual_low) <= WeatherValidator.TOLERANCE_TEMP]

                    if high_matches and low_matches:
                        success = True
                        accuracy_score = 100.0
                    else:
                        error_message = (
                            f"Temperature mismatch: expected high ~{actual_high}°C and low ~{actual_low}°C"
                        )
                else:
                    error_message = f"Expected 2 temperatures, found {len(temps)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Specific Date High/Low",
            prompt="What were the high and low temperatures in Dubai, UAE on February 20, 2026?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_tomorrow_precipitation(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: Will it rain in Singapore tomorrow? (EASY).

        Expected: Bot checks tomorrow's forecast for Singapore and reports yes/no.

        Validation:
          1. Fetch tomorrow's weather for Singapore from Open-Meteo
          2. Check bot's yes/no matches actual precipitation forecast
        """
        singapore = setup_data.get("singapore", {})
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        success = False
        accuracy_score = 0.0
        validation_details = {"location": singapore, "date": tomorrow}
        error_message = None

        try:
            weather_data = WeatherValidator._fetch_weather(
                singapore["lat"], singapore["lon"], tomorrow, tomorrow
            )

            if not weather_data or "daily" not in weather_data:
                error_message = "Failed to fetch weather data from Open-Meteo"
            else:
                actual_precip = weather_data["daily"]["precipitation_sum"][0]
                will_rain = actual_precip > 0.1  # >0.1mm counts as rain
                validation_details["actual_precipitation_mm"] = actual_precip
                validation_details["will_rain"] = will_rain

                response_lower = response.lower()
                bot_says_yes = any(word in response_lower for word in ["yes", "will rain", "rain", "rainfall"])
                bot_says_no = any(word in response_lower for word in ["no", "won't rain", "no rain", "not rain"])
                validation_details["bot_says_yes"] = bot_says_yes
                validation_details["bot_says_no"] = bot_says_no

                if will_rain and bot_says_yes:
                    success = True
                    accuracy_score = 100.0
                elif not will_rain and bot_says_no:
                    success = True
                    accuracy_score = 100.0
                else:
                    error_message = (
                        f"Precipitation mismatch: actual {actual_precip}mm (will_rain={will_rain}), "
                        f"bot says yes={bot_says_yes}, no={bot_says_no}"
                    )

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Tomorrow's Precipitation",
            prompt="Will it rain in Singapore tomorrow?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_two_city_today(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 4: Which city is warmer today — Oslo or Helsinki? (MEDIUM).

        Expected: Bot compares today's temps for both cities.

        Validation:
          1. Fetch today's weather for both cities from Open-Meteo
          2. Determine which city is actually warmer
          3. Check bot identified correct city
        """
        oslo = setup_data.get("oslo", {})
        helsinki = setup_data.get("helsinki", {})
        today = datetime.now().strftime("%Y-%m-%d")

        success = False
        accuracy_score = 0.0
        validation_details = {"date": today}
        error_message = None

        try:
            oslo_data = WeatherValidator._fetch_weather(oslo["lat"], oslo["lon"], today, today)
            helsinki_data = WeatherValidator._fetch_weather(helsinki["lat"], helsinki["lon"], today, today)

            if not oslo_data or not helsinki_data:
                error_message = "Failed to fetch weather data from Open-Meteo"
            else:
                oslo_temp = oslo_data["daily"]["temperature_2m_max"][0]
                helsinki_temp = helsinki_data["daily"]["temperature_2m_max"][0]
                validation_details["oslo_temp"] = oslo_temp
                validation_details["helsinki_temp"] = helsinki_temp

                warmer_city = "Oslo" if oslo_temp > helsinki_temp else "Helsinki"
                validation_details["warmer_city"] = warmer_city

                response_lower = response.lower()
                if warmer_city.lower() in response_lower:
                    success = True
                    accuracy_score = 100.0
                else:
                    error_message = f"Wrong city: expected {warmer_city}, not found in response"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Two-City Comparison Today",
            prompt="Which city has a higher forecasted temperature today — Oslo, Norway or Helsinki, Finland?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_specific_date_average(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 5: Average temperature in Auckland on Feb 22, 2026 (MEDIUM).

        Expected: Bot reports average temp (high + low) / 2.

        Validation:
          1. Fetch Feb 22, 2026 weather for Auckland from Open-Meteo
          2. Calculate average: (max + min) / 2
          3. Check bot's temperature within ±2°C
        """
        auckland = setup_data.get("auckland", {})
        date = auckland.get("date", "2026-02-22")

        success = False
        accuracy_score = 0.0
        validation_details = {"location": auckland, "date": date}
        error_message = None

        try:
            weather_data = WeatherValidator._fetch_weather(auckland["lat"], auckland["lon"], date, date)

            if not weather_data or "daily" not in weather_data:
                error_message = "Failed to fetch weather data from Open-Meteo"
            else:
                actual_high = weather_data["daily"]["temperature_2m_max"][0]
                actual_low = weather_data["daily"]["temperature_2m_min"][0]
                actual_avg = (actual_high + actual_low) / 2
                validation_details["actual_high"] = actual_high
                validation_details["actual_low"] = actual_low
                validation_details["actual_avg"] = actual_avg

                bot_temp = WeatherValidator._extract_number(response)
                validation_details["bot_temp"] = bot_temp

                if bot_temp is not None:
                    temp_diff = abs(bot_temp - actual_avg)
                    validation_details["temp_diff"] = temp_diff

                    if temp_diff <= WeatherValidator.TOLERANCE_TEMP:
                        success = True
                        accuracy_score = 100.0
                    else:
                        error_message = (
                            f"Average temperature mismatch: bot reported {bot_temp}°C, "
                            f"actual average is {actual_avg:.1f}°C (diff: {temp_diff:.1f}°C)"
                        )
                else:
                    error_message = "Could not extract temperature from bot response"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Specific Date Average",
            prompt="What was the average temperature in Auckland, New Zealand on February 22, 2026?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_tomorrow_wind(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 6: Tomorrow's max wind speed in Chicago (MEDIUM).

        Expected: Bot reports tomorrow's max wind speed.

        Validation:
          1. Fetch tomorrow's weather for Chicago from Open-Meteo
          2. Check bot's wind speed within ±5 km/h tolerance
        """
        chicago = setup_data.get("chicago", {})
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        success = False
        accuracy_score = 0.0
        validation_details = {"location": chicago, "date": tomorrow}
        error_message = None

        try:
            weather_data = WeatherValidator._fetch_weather(
                chicago["lat"], chicago["lon"], tomorrow, tomorrow
            )

            if not weather_data or "daily" not in weather_data:
                error_message = "Failed to fetch weather data from Open-Meteo"
            else:
                actual_wind = weather_data["daily"]["windspeed_10m_max"][0]
                validation_details["actual_wind_kmh"] = actual_wind

                bot_wind = WeatherValidator._extract_number(response)
                validation_details["bot_wind"] = bot_wind

                if bot_wind is not None:
                    wind_diff = abs(bot_wind - actual_wind)
                    validation_details["wind_diff"] = wind_diff

                    if wind_diff <= WeatherValidator.TOLERANCE_WIND:
                        success = True
                        accuracy_score = 100.0
                    else:
                        error_message = (
                            f"Wind speed mismatch: bot reported {bot_wind} km/h, "
                            f"actual is {actual_wind} km/h (diff: {wind_diff:.1f} km/h)"
                        )
                else:
                    error_message = "Could not extract wind speed from bot response"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Tomorrow's Wind Speed",
            prompt="What is the forecasted maximum wind speed for Chicago, Illinois tomorrow?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_next_3_days_warmest(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 7: Which of next 3 days is warmest in Vancouver? (HARD).

        Expected: Bot analyzes 3-day forecast and identifies warmest day.

        Validation:
          1. Fetch next 3 days weather for Vancouver from Open-Meteo
          2. Determine which day has highest temp
          3. Check bot identified correct day (today/tomorrow/day after)
        """
        vancouver = setup_data.get("vancouver", {})
        today = datetime.now()
        dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]
        start_date = dates[0]
        end_date = dates[2]

        success = False
        accuracy_score = 0.0
        validation_details = {"location": vancouver, "dates": dates}
        error_message = None

        try:
            weather_data = WeatherValidator._fetch_weather(
                vancouver["lat"], vancouver["lon"], start_date, end_date
            )

            if not weather_data or "daily" not in weather_data:
                error_message = "Failed to fetch weather data from Open-Meteo"
            else:
                temps = weather_data["daily"]["temperature_2m_max"]
                validation_details["temps"] = temps

                max_temp_idx = temps.index(max(temps))
                warmest_date = dates[max_temp_idx]
                validation_details["warmest_date"] = warmest_date
                validation_details["warmest_temp"] = temps[max_temp_idx]

                # Check if bot mentions the correct date or relative day
                response_lower = response.lower()
                day_names = ["today", "tomorrow", "day after tomorrow"]
                expected_day = day_names[max_temp_idx] if max_temp_idx < 3 else warmest_date

                if warmest_date in response or expected_day in response_lower:
                    success = True
                    accuracy_score = 100.0
                else:
                    error_message = f"Wrong day: expected {expected_day} ({warmest_date}), not found in response"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Next 3 Days Warmest",
            prompt="Over the next 3 days, which day will have the highest temperature in Vancouver, Canada?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_three_city_ranking(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 8: Rank Tokyo, Seoul, Beijing by temp on Feb 23, 2026 (HARD).

        Expected: Bot fetches all 3 cities and ranks them warmest to coldest.

        Validation:
          1. Fetch Feb 23, 2026 weather for all 3 cities from Open-Meteo
          2. Determine correct ranking
          3. Check bot's ranking matches
        """
        tokyo = setup_data.get("tokyo", {})
        seoul = setup_data.get("seoul", {})
        beijing = setup_data.get("beijing", {})
        date = "2026-02-23"

        success = False
        accuracy_score = 0.0
        validation_details = {"date": date}
        error_message = None

        try:
            tokyo_data = WeatherValidator._fetch_weather(tokyo["lat"], tokyo["lon"], date, date)
            seoul_data = WeatherValidator._fetch_weather(seoul["lat"], seoul["lon"], date, date)
            beijing_data = WeatherValidator._fetch_weather(beijing["lat"], beijing["lon"], date, date)

            if not tokyo_data or not seoul_data or not beijing_data:
                error_message = "Failed to fetch weather data from Open-Meteo"
            else:
                tokyo_temp = tokyo_data["daily"]["temperature_2m_max"][0]
                seoul_temp = seoul_data["daily"]["temperature_2m_max"][0]
                beijing_temp = beijing_data["daily"]["temperature_2m_max"][0]

                cities_temps = [
                    ("Tokyo", tokyo_temp),
                    ("Seoul", seoul_temp),
                    ("Beijing", beijing_temp),
                ]
                cities_temps.sort(key=lambda x: x[1], reverse=True)
                ranking = [city for city, temp in cities_temps]

                validation_details["tokyo_temp"] = tokyo_temp
                validation_details["seoul_temp"] = seoul_temp
                validation_details["beijing_temp"] = beijing_temp
                validation_details["correct_ranking"] = ranking

                # Check if bot's ranking matches
                response_lower = response.lower()
                # Simple check: correct order of city names in response
                tokyo_pos = response_lower.find("tokyo")
                seoul_pos = response_lower.find("seoul")
                beijing_pos = response_lower.find("beijing")

                positions = [
                    (ranking[0].lower(), tokyo_pos if ranking[0] == "Tokyo" else seoul_pos if ranking[0] == "Seoul" else beijing_pos),
                    (ranking[1].lower(), tokyo_pos if ranking[1] == "Tokyo" else seoul_pos if ranking[1] == "Seoul" else beijing_pos),
                    (ranking[2].lower(), tokyo_pos if ranking[2] == "Tokyo" else seoul_pos if ranking[2] == "Seoul" else beijing_pos),
                ]

                # Check if all cities mentioned
                if tokyo_pos > -1 and seoul_pos > -1 and beijing_pos > -1:
                    # Check rough ordering (first ranked appears before last ranked)
                    first_city_pos = response_lower.find(ranking[0].lower())
                    last_city_pos = response_lower.find(ranking[2].lower())

                    if first_city_pos < last_city_pos:
                        success = True
                        accuracy_score = 100.0
                    else:
                        error_message = f"Ranking order incorrect: expected {' > '.join(ranking)}"
                else:
                    error_message = "Not all cities mentioned in response"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Three-City Ranking",
            prompt="On February 23, 2026, rank Tokyo, Seoul, and Beijing from warmest to coldest by their high temperatures.",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_two_city_range_diff(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 9: Difference between Moscow and Cairo temp ranges on Feb 23, 2026 (HARD).

        Expected: Bot calculates temp range (high - low) for each city, then finds difference.

        Validation:
          1. Fetch Feb 23, 2026 weather for both cities from Open-Meteo
          2. Calculate Moscow range and Cairo range
          3. Calculate difference between ranges
          4. Check bot's answer within ±1°C
        """
        moscow = setup_data.get("moscow", {})
        cairo = setup_data.get("cairo", {})
        date = "2026-02-23"

        success = False
        accuracy_score = 0.0
        validation_details = {"date": date}
        error_message = None

        try:
            moscow_data = WeatherValidator._fetch_weather(moscow["lat"], moscow["lon"], date, date)
            cairo_data = WeatherValidator._fetch_weather(cairo["lat"], cairo["lon"], date, date)

            if not moscow_data or not cairo_data:
                error_message = "Failed to fetch weather data from Open-Meteo"
            else:
                moscow_max = moscow_data["daily"]["temperature_2m_max"][0]
                moscow_min = moscow_data["daily"]["temperature_2m_min"][0]
                moscow_range = moscow_max - moscow_min

                cairo_max = cairo_data["daily"]["temperature_2m_max"][0]
                cairo_min = cairo_data["daily"]["temperature_2m_min"][0]
                cairo_range = cairo_max - cairo_min

                actual_diff = abs(moscow_range - cairo_range)

                validation_details["moscow_max"] = moscow_max
                validation_details["moscow_min"] = moscow_min
                validation_details["moscow_range"] = moscow_range
                validation_details["cairo_max"] = cairo_max
                validation_details["cairo_min"] = cairo_min
                validation_details["cairo_range"] = cairo_range
                validation_details["actual_difference"] = actual_diff

                bot_diff = WeatherValidator._extract_number(response)
                validation_details["bot_difference"] = bot_diff

                if bot_diff is not None:
                    diff_error = abs(bot_diff - actual_diff)
                    validation_details["diff_error"] = diff_error

                    if diff_error <= 1.0:  # ±1°C tolerance for difference
                        success = True
                        accuracy_score = 100.0
                    else:
                        error_message = (
                            f"Range difference mismatch: bot reported {bot_diff}°C, "
                            f"actual difference is {actual_diff:.1f}°C (error: {diff_error:.1f}°C)"
                        )
                else:
                    error_message = "Could not extract difference value from bot response"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Two-City Range Difference",
            prompt=(
                "On February 23, 2026, what is the difference between Moscow, Russia's temperature range "
                "and Cairo, Egypt's temperature range? (Temperature range = high temp - low temp for each city)"
            ),
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
