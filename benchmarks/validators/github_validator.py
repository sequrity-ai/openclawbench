"""Validation utilities for GitHub skill tasks."""

import re
from typing import Any

from benchmarks.base import TaskResult


class GitHubValidator:
    """Validates GitHub skill task results."""

    @staticmethod
    def validate_repo_info(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Repository information via gh CLI.

        Expected: Description, star count, and primary language.
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}

        response_lower = response.lower()

        # Check for repo/org identification
        found_repo = "anthropic" in response_lower and "cookbook" in response_lower
        validation_details["found_repo"] = found_repo
        if found_repo:
            accuracy_score += 30.0

        # Check for star count (a number near "star")
        star_pattern = r"(\d[\d,]*)\s*(?:star|⭐)"
        star_match = re.search(star_pattern, response_lower)
        if not star_match:
            # Also check "stars: 1234" or "1234 stars"
            star_pattern2 = r"(?:star[s]?[:\s]+)(\d[\d,]*)|(\d[\d,]*)\s*star"
            star_match = re.search(star_pattern2, response_lower)
        found_stars = star_match is not None
        validation_details["found_stars"] = found_stars
        if found_stars:
            accuracy_score += 35.0

        # Check for primary language
        lang_keywords = [
            "python", "jupyter", "notebook", "javascript", "typescript",
            "markdown", "shell", "go", "rust",
        ]
        found_lang = any(kw in response_lower for kw in lang_keywords)
        validation_details["found_language"] = found_lang
        if found_lang:
            accuracy_score += 35.0

        if found_repo and found_stars and found_lang:
            success = True
            accuracy_score = 100.0
        elif found_repo and (found_stars or found_lang):
            success = True

        error_message = None
        if not success:
            missing = []
            if not found_repo:
                missing.append("repository identification")
            if not found_stars:
                missing.append("star count")
            if not found_lang:
                missing.append("primary language")
            error_message = f"Missing: {', '.join(missing)}"

        return TaskResult(
            task_name="Repo Info",
            prompt="Get info about anthropics/anthropic-cookbook via gh CLI",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_list_issues(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: List recent open issues via gh CLI.

        Expected: At least 2 issue numbers (#NNN) with titles.
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}

        # Check for issue numbers (#NNN pattern)
        issue_pattern = r"#(\d+)"
        issues = re.findall(issue_pattern, response)
        unique_issues = list(set(issues))
        validation_details["issue_numbers"] = unique_issues[:10]
        validation_details["issue_count"] = len(unique_issues)

        if len(unique_issues) >= 3:
            accuracy_score += 50.0
        elif len(unique_issues) >= 2:
            accuracy_score += 35.0
        elif len(unique_issues) >= 1:
            accuracy_score += 15.0

        # Check for issue titles (non-trivial text near issue numbers)
        # Look for lines that contain both a number and substantial text
        lines = response.split("\n")
        titled_lines = 0
        for line in lines:
            if re.search(r"#\d+", line) and len(line.strip()) > 15:
                titled_lines += 1
        validation_details["titled_lines"] = titled_lines

        if titled_lines >= 3:
            accuracy_score += 50.0
        elif titled_lines >= 2:
            accuracy_score += 35.0
        elif titled_lines >= 1:
            accuracy_score += 15.0

        if len(unique_issues) >= 2 and titled_lines >= 2:
            success = True
        if len(unique_issues) >= 3 and titled_lines >= 3:
            accuracy_score = 100.0

        error_message = None
        if not success:
            parts = []
            if len(unique_issues) < 2:
                parts.append(f"only {len(unique_issues)} issue numbers (need 2+)")
            if titled_lines < 2:
                parts.append(f"only {titled_lines} issues with titles (need 2+)")
            error_message = "Incomplete: " + ", ".join(parts)

        return TaskResult(
            task_name="List Issues",
            prompt="List 3 most recent open issues from anthropics/anthropic-cookbook",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
