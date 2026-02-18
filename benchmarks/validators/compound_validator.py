"""Validation utilities for Compound benchmark tasks.

Compound tasks chain 2-3 skills. Validators are pinned to:
  - Specific cities/topics named in the task prompts (weather, T1/T4/T6)
  - Specific GitHub issue title phrases from the prompts (T4/T5/T8/T9)
  - Seeded file content from the GitHub test repo (T3/T7)
  - Topic-specific keywords for web/summarize tasks (T2)

Tasks involving GitHub issue creation (T4/T5/T8/T9) require both the
issue title phrase AND a "#" (issue number) — confirming the issue was created.
"""

import logging
from typing import Any

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)


class CompoundValidator:
    """Validates compound multi-skill task results."""

    @staticmethod
    def validate_weather_then_web(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Weather + Web Research — Tokyo weather + travel tips (EASY).

        Expected: Bot checked Tokyo weather AND searched for relevant travel/packing tips.

        Conditions:
          1. "tokyo" appears (correct city)
          2. A temperature marker appears ("°", "celsius", "fahrenheit", "degrees")
          3. A packing/travel tip word appears ("pack", "bring", "umbrella", "jacket",
             "sunscreen", "clothing", "recommend")
        """
        success = False
        accuracy_score = 0.0
        validation_details = {"city": "tokyo"}
        error_message = None

        try:
            response_lower = response.lower()

            tokyo_found = "tokyo" in response_lower
            temp_found = any(kw in response_lower for kw in ("°", "celsius", "fahrenheit", "degrees", "temperature"))
            packing_found = any(kw in response_lower for kw in (
                "pack", "bring", "umbrella", "jacket", "sunscreen", "clothing", "recommend", "tip", "wear"
            ))

            validation_details["tokyo_found"] = tokyo_found
            validation_details["temp_found"] = temp_found
            validation_details["packing_found"] = packing_found

            if tokyo_found and temp_found and packing_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not tokyo_found:
                    missing_parts.append("city 'tokyo'")
                if not temp_found:
                    missing_parts.append("temperature data ('°', 'celsius', 'degrees')")
                if not packing_found:
                    missing_parts.append("packing/travel tip ('pack', 'bring', 'jacket', 'umbrella')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Weather + Web Research",
            prompt="Check weather in Tokyo then search for travel/packing tips",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_web_then_summarize(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: Web Search + Summarize — Python async article (EASY).

        Expected: Bot found an article about Python async programming and summarized it.

        Conditions:
          1. "python" appears (correct topic)
          2. "async" appears (correct subtopic)
          3. A summary word appears ("summary", "key point", "main", "takeaway",
             "discusses", "covers", "explains")
        """
        success = False
        accuracy_score = 0.0
        validation_details = {"topic": "python async programming"}
        error_message = None

        try:
            response_lower = response.lower()

            python_found = "python" in response_lower
            async_found = "async" in response_lower
            summary_found = any(kw in response_lower for kw in (
                "summary", "key point", "main", "takeaway", "discusses",
                "covers", "explains", "article", "according to"
            ))

            validation_details["python_found"] = python_found
            validation_details["async_found"] = async_found
            validation_details["summary_found"] = summary_found

            if python_found and async_found and summary_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not python_found:
                    missing_parts.append("topic 'python'")
                if not async_found:
                    missing_parts.append("subtopic 'async'")
                if not summary_found:
                    missing_parts.append("summary language ('key point', 'main', 'discusses')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Web Search + Summarize",
            prompt="Search for Python async article then summarize key points",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_github_then_summarize(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: GitHub + Summarize — read src/utils.js and summarize (EASY).

        Expected: Bot read the seeded src/utils.js file and summarized its purpose.
        The file defines fetchData() and processItems() — both must be mentioned.

        Conditions:
          1. "fetchdata" appears (function from seeded file)
          2. "processitems" appears (function from seeded file)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {
            "seeded_function_1": "fetchData",
            "seeded_function_2": "processItems",
        }
        error_message = None

        try:
            response_lower = response.lower()

            fetchdata_found = "fetchdata" in response_lower
            processitems_found = "processitems" in response_lower

            validation_details["fetchdata_found"] = fetchdata_found
            validation_details["processitems_found"] = processitems_found

            if fetchdata_found and processitems_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not fetchdata_found:
                    missing_parts.append("seeded function 'fetchData'")
                if not processitems_found:
                    missing_parts.append("seeded function 'processItems'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="GitHub + Summarize",
            prompt="Read src/utils.js from repo and summarize its purpose",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_weather_then_github(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 4: Weather + GitHub Issue — London weather + file issue (MEDIUM).

        Expected: Bot checked London weather AND created a GitHub issue titled
        '[BENCHMARK TEST] Weather Report' containing the weather data.

        Conditions:
          1. "london" appears (correct city)
          2. "weather report" appears (issue title phrase)
          3. "#" appears (issue number — confirming issue was created)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {
            "city": "london",
            "issue_title_phrase": "weather report",
        }
        error_message = None

        try:
            response_lower = response.lower()

            london_found = "london" in response_lower
            title_found = "weather report" in response_lower
            number_found = "#" in response

            validation_details["london_found"] = london_found
            validation_details["title_found"] = title_found
            validation_details["number_found"] = number_found

            if london_found and title_found and number_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not london_found:
                    missing_parts.append("city 'london'")
                if not title_found:
                    missing_parts.append("issue title phrase 'weather report'")
                if not number_found:
                    missing_parts.append("issue number ('#')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Weather + GitHub Issue",
            prompt="Check London weather then file GitHub issue '[BENCHMARK TEST] Weather Report'",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_web_then_github(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 5: Web Research + GitHub Issue — async best practices + file issue (MEDIUM).

        Expected: Bot researched Python async best practices AND created a GitHub issue
        titled '[BENCHMARK TEST] Async Research' with findings.

        Conditions:
          1. "async" appears (correct topic researched)
          2. "async research" appears (issue title phrase)
          3. "#" appears (issue number — confirming issue was created)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {
            "topic": "async",
            "issue_title_phrase": "async research",
        }
        error_message = None

        try:
            response_lower = response.lower()

            async_found = "async" in response_lower
            title_found = "async research" in response_lower
            number_found = "#" in response

            validation_details["async_found"] = async_found
            validation_details["title_found"] = title_found
            validation_details["number_found"] = number_found

            if async_found and title_found and number_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not async_found:
                    missing_parts.append("topic 'async'")
                if not title_found:
                    missing_parts.append("issue title phrase 'async research'")
                if not number_found:
                    missing_parts.append("issue number ('#')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Web Research + GitHub Issue",
            prompt="Research Python async best practices then file GitHub issue '[BENCHMARK TEST] Async Research'",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_weather_web_compare(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 6: Multi-City Weather + Context — London, Tokyo, Paris (MEDIUM).

        Expected: Bot retrieved weather for all three cities and compared them.

        Conditions:
          1. "london" appears (city 1)
          2. "tokyo" appears (city 2)
          3. "paris" appears (city 3)
          4. A comparison word appears ("warmer", "cooler", "hotter", "colder",
             "compared", "versus", "whereas", "while", "difference")
        """
        success = False
        accuracy_score = 0.0
        validation_details = {"cities": ["london", "tokyo", "paris"]}
        error_message = None

        try:
            response_lower = response.lower()

            london_found = "london" in response_lower
            tokyo_found = "tokyo" in response_lower
            paris_found = "paris" in response_lower
            comparison_found = any(kw in response_lower for kw in (
                "warmer", "cooler", "hotter", "colder", "compared",
                "versus", "whereas", "while", "difference", "warmest", "coolest"
            ))

            validation_details["london_found"] = london_found
            validation_details["tokyo_found"] = tokyo_found
            validation_details["paris_found"] = paris_found
            validation_details["comparison_found"] = comparison_found

            if london_found and tokyo_found and paris_found and comparison_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not london_found:
                    missing_parts.append("city 'london'")
                if not tokyo_found:
                    missing_parts.append("city 'tokyo'")
                if not paris_found:
                    missing_parts.append("city 'paris'")
                if not comparison_found:
                    missing_parts.append("comparison word ('warmer', 'cooler', 'compared')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Multi-City Weather + Context",
            prompt="Check weather in London, Tokyo, Paris and compare all three",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_github_web_research(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 7: GitHub Repo + Web Research — repo info + tech research (HARD).

        Expected: Bot retrieved info from the seeded GitHub repo (README mentions
        "Benchmark Test Repository" and "openclaw-sandbox") AND did web research.

        Conditions:
          1. "benchmark test repository" appears (seeded README heading)
          2. "openclaw-sandbox" appears (seeded repo reference)
          3. A web research signal appears ("search", "found", "article", "according",
             "online", "javascript")
        """
        success = False
        accuracy_score = 0.0
        validation_details = {
            "seeded_readme_heading": "benchmark test repository",
            "seeded_repo_ref": "openclaw-sandbox",
        }
        error_message = None

        try:
            response_lower = response.lower()

            heading_found = "benchmark test repository" in response_lower
            repo_ref_found = "openclaw-sandbox" in response_lower
            web_found = any(kw in response_lower for kw in (
                "search", "found", "article", "according", "online", "javascript", "js", "web"
            ))

            validation_details["heading_found"] = heading_found
            validation_details["repo_ref_found"] = repo_ref_found
            validation_details["web_research_found"] = web_found

            if heading_found and repo_ref_found and web_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not heading_found:
                    missing_parts.append("seeded README heading 'benchmark test repository'")
                if not repo_ref_found:
                    missing_parts.append("seeded repo reference 'openclaw-sandbox'")
                if not web_found:
                    missing_parts.append("web research signal ('search', 'found', 'article')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="GitHub Repo + Web Research",
            prompt="Get repo info then research the technology stack online",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_three_skill_chain(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 8: Web + Weather + GitHub Chain — 3-skill chain (HARD).

        Expected: Bot searched AI news, checked San Francisco weather, and created
        a GitHub issue titled '[BENCHMARK TEST] Daily Briefing'.

        Conditions:
          1. "san francisco" appears (correct weather city)
          2. "daily briefing" appears (issue title phrase)
          3. "#" appears (issue number — confirming issue was created)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {
            "weather_city": "san francisco",
            "issue_title_phrase": "daily briefing",
        }
        error_message = None

        try:
            response_lower = response.lower()

            sf_found = "san francisco" in response_lower
            title_found = "daily briefing" in response_lower
            number_found = "#" in response

            validation_details["san_francisco_found"] = sf_found
            validation_details["title_found"] = title_found
            validation_details["number_found"] = number_found

            if sf_found and title_found and number_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not sf_found:
                    missing_parts.append("weather city 'san francisco'")
                if not title_found:
                    missing_parts.append("issue title phrase 'daily briefing'")
                if not number_found:
                    missing_parts.append("issue number ('#')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Web + Weather + GitHub Chain",
            prompt="Search AI news + SF weather, then file GitHub issue '[BENCHMARK TEST] Daily Briefing'",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_summarize_then_github(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 9: Research + Summarize + GitHub — ML healthcare + file issue (HARD).

        Expected: Bot researched ML in healthcare, summarized findings, and created
        a GitHub issue titled '[BENCHMARK TEST] ML Healthcare Research'.

        Conditions:
          1. "healthcare" appears (correct research topic)
          2. "ml healthcare research" appears (issue title phrase)
          3. "#" appears (issue number — confirming issue was created)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {
            "topic": "healthcare",
            "issue_title_phrase": "ml healthcare research",
        }
        error_message = None

        try:
            response_lower = response.lower()

            healthcare_found = "healthcare" in response_lower
            title_found = "ml healthcare research" in response_lower
            number_found = "#" in response

            validation_details["healthcare_found"] = healthcare_found
            validation_details["title_found"] = title_found
            validation_details["number_found"] = number_found

            if healthcare_found and title_found and number_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not healthcare_found:
                    missing_parts.append("topic 'healthcare'")
                if not title_found:
                    missing_parts.append("issue title phrase 'ml healthcare research'")
                if not number_found:
                    missing_parts.append("issue number ('#')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Research + Summarize + GitHub",
            prompt="Research ML in healthcare, summarize, file '[BENCHMARK TEST] ML Healthcare Research'",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
