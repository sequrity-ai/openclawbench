"""Validation utilities for web research tasks."""

import re
from typing import Any

from benchmarks.base import TaskResult


class WebValidator:
    """Validates web research task results."""

    @staticmethod
    def validate_factual_extraction(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Factual extraction from Wikipedia.

        Expected: Year 1991 and creator Guido van Rossum.
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}

        response_lower = response.lower()

        # Check for year 1991 (Python's first release)
        found_year = bool(re.search(r"1991", response))
        validation_details["found_year"] = found_year
        if found_year:
            accuracy_score += 50.0

        # Check for Guido van Rossum (require both first and last name)
        found_creator = "guido" in response_lower and "rossum" in response_lower
        validation_details["found_creator"] = found_creator
        if found_creator:
            accuracy_score += 50.0

        if found_year and found_creator:
            success = True
            accuracy_score = 100.0

        error_message = None
        if not success:
            missing = []
            if not found_year:
                missing.append("year 1991")
            if not found_creator:
                missing.append("Guido van Rossum")
            error_message = f"Missing: {', '.join(missing)}"

        return TaskResult(
            task_name="Factual Extraction",
            prompt=f"Extract Python creation year and creator from {setup_data.get('wikipedia_url', 'Wikipedia')}",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_repo_analysis(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: GitHub repository analysis.

        Expected: Anthropic-owned cookbook with examples/guides.
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}

        response_lower = response.lower()

        # Check for organization identification (Anthropic)
        found_org = "anthropic" in response_lower
        validation_details["found_org"] = found_org
        if found_org:
            accuracy_score += 35.0

        # Check for purpose (cookbook / examples / guides)
        purpose_keywords = ["cookbook", "example", "recipe", "guide", "tutorial", "notebook", "sample"]
        found_purpose = any(kw in response_lower for kw in purpose_keywords)
        validation_details["found_purpose"] = found_purpose
        if found_purpose:
            accuracy_score += 35.0

        # Check for language/format mention (Python, Jupyter, notebook)
        lang_keywords = ["python", "jupyter", "notebook", "ipynb"]
        found_lang = any(kw in response_lower for kw in lang_keywords)
        validation_details["found_lang"] = found_lang
        if found_lang:
            accuracy_score += 30.0

        if found_org and found_purpose:
            success = True
        if found_org and found_purpose and found_lang:
            accuracy_score = 100.0

        error_message = None
        if not success:
            missing = []
            if not found_org:
                missing.append("organization (Anthropic)")
            if not found_purpose:
                missing.append("purpose description")
            if not found_lang:
                missing.append("language/format")
            error_message = f"Missing: {', '.join(missing)}"

        return TaskResult(
            task_name="Repository Analysis",
            prompt=f"Analyze {setup_data.get('github_repo_url', 'the repository')}",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_multi_source_research(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: Multi-source research on Python web frameworks.

        Expected: 3 frameworks (e.g. Django, Flask, FastAPI) with source URLs.
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}

        response_lower = response.lower()

        # Check for known Python web frameworks
        frameworks = [
            "django", "flask", "fastapi", "tornado", "bottle",
            "pyramid", "falcon", "starlette", "sanic", "aiohttp",
            "cherrypy", "hug", "quart", "litestar",
        ]
        found_frameworks = [fw for fw in frameworks if fw in response_lower]
        validation_details["found_frameworks"] = found_frameworks

        if len(found_frameworks) >= 3:
            accuracy_score += 50.0
        elif len(found_frameworks) == 2:
            accuracy_score += 30.0
        elif len(found_frameworks) == 1:
            accuracy_score += 15.0

        # Check for source URLs
        url_pattern = r"https?://[^\s<>\"{}|\\^`\[\]]+"
        urls = re.findall(url_pattern, response)
        validation_details["url_count"] = len(urls)
        validation_details["urls"] = urls[:10]

        if len(urls) >= 3:
            accuracy_score += 50.0
        elif len(urls) >= 2:
            accuracy_score += 30.0
        elif len(urls) >= 1:
            accuracy_score += 15.0

        if len(found_frameworks) >= 3 and len(urls) >= 3:
            success = True
            accuracy_score = 100.0

        error_message = None
        if not success:
            parts = []
            if len(found_frameworks) < 3:
                parts.append(f"only {len(found_frameworks)} frameworks (need 3)")
            if len(urls) < 3:
                parts.append(f"only {len(urls)} source URLs (need 3)")
            error_message = "Incomplete: " + ", ".join(parts)

        return TaskResult(
            task_name="Multi-Source Research",
            prompt=f"Research '{setup_data.get('search_topic', 'the topic')}' and provide 3 frameworks with sources",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
