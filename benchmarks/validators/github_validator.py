"""Validation utilities for GitHub benchmark tasks.

All tasks are pinned to seeded repository data — no live/external facts required.

Seeded state (created by setup before any tasks run):
  - README.md: "Benchmark Test Repository" / "openclaw-sandbox"
  - 5 commits: "Add utility functions", "Add API client", "Add data processor",
                "Add configuration module", "Add main entry point"
  - src/utils.js: defines fetchData() and processItems()
  - Open PR: "[BENCHMARK] Add error handler feature"
  - Release: tag "v1.0.0-benchmark"
  - Label: "benchmark-seed"
  - 3 open issues (titles contain "fetchdata returns null" / "retry logic" / "update readme")
  - All commits authored by repo_owner
"""

import logging
from typing import Any

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)


class GitHubValidator:
    """Validates GitHub task results against seeded repository facts."""

    @staticmethod
    def validate_issue_creation(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Create issue (EASY).

        Expected: Bot creates an issue titled '[BENCHMARK TEST] Test Issue'
        and reports the new issue number.

        Conditions:
          1. "benchmark test" appears in response (the title phrase)
          2. "#" appears in response (issue number reported)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {"expected_title_phrase": "benchmark test"}
        error_message = None

        try:
            response_lower = response.lower()

            title_found = "benchmark test" in response_lower
            number_found = "#" in response

            validation_details["title_found"] = title_found
            validation_details["number_found"] = number_found

            if title_found and number_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not title_found:
                    missing_parts.append("issue title phrase 'benchmark test'")
                if not number_found:
                    missing_parts.append("issue number ('#')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Issue Creation",
            prompt=(
                "Create a new issue titled '[BENCHMARK TEST] Test Issue' "
                "and body 'This is a test issue created by the benchmark.'"
            ),
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_issue_list(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: List open issues (EASY).

        Expected: Bot lists open issues including the seeded ones.
        Seeded issue titles contain "fetchdata returns null" and "retry logic".

        Conditions:
          1. "fetchdata" appears (from "[BENCHMARK SEED] Bug: fetchData returns null on timeout")
          2. "retry" appears (from "[BENCHMARK SEED] Feature: add retry logic to processItems")
        """
        success = False
        accuracy_score = 0.0
        validation_details = {
            "seeded_issue_1": "fetchdata returns null on timeout",
            "seeded_issue_2": "retry logic to processitems",
        }
        error_message = None

        try:
            response_lower = response.lower()

            fetchdata_found = "fetchdata" in response_lower
            retry_found = "retry" in response_lower

            validation_details["fetchdata_found"] = fetchdata_found
            validation_details["retry_found"] = retry_found

            if fetchdata_found and retry_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not fetchdata_found:
                    missing_parts.append("seeded issue 'fetchData returns null' ('fetchdata')")
                if not retry_found:
                    missing_parts.append("seeded issue 'retry logic' ('retry')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="List Issues",
            prompt="List all open issues in the repository. Show me the issue titles.",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_repo_info(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: Repository info (EASY).

        Expected: Bot reads the repo and finds the seeded README description.
        README.md content: "# Benchmark Test Repository\n...openclaw-sandbox..."

        Conditions:
          1. "benchmark test repository" appears (README heading)
          2. "openclaw-sandbox" appears (repo name referenced in README)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {
            "readme_heading": "benchmark test repository",
            "repo_ref": "openclaw-sandbox",
        }
        error_message = None

        try:
            response_lower = response.lower()

            heading_found = "benchmark test repository" in response_lower
            repo_ref_found = "openclaw-sandbox" in response_lower

            validation_details["heading_found"] = heading_found
            validation_details["repo_ref_found"] = repo_ref_found

            if heading_found and repo_ref_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not heading_found:
                    missing_parts.append("README heading 'Benchmark Test Repository'")
                if not repo_ref_found:
                    missing_parts.append("repo reference 'openclaw-sandbox'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Repository Info",
            prompt="Get information about the repository. Tell me the description, number of stars, and number of forks.",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_recent_commits(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 4: Recent commits (MEDIUM).

        Expected: Bot lists recent commits including the two earliest seeded commits.
        Seeded commit messages: "Add utility functions", "Add API client",
        "Add data processor", "Add configuration module", "Add main entry point"

        Conditions:
          1. "add utility functions" appears in response (seeded commit 1)
          2. "add api client" appears in response (seeded commit 2)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {
            "seeded_commit_1": "add utility functions",
            "seeded_commit_2": "add api client",
        }
        error_message = None

        try:
            response_lower = response.lower()

            utility_found = "add utility functions" in response_lower
            api_client_found = "add api client" in response_lower

            validation_details["utility_commit_found"] = utility_found
            validation_details["api_client_commit_found"] = api_client_found

            if utility_found and api_client_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not utility_found:
                    missing_parts.append("seeded commit message 'Add utility functions'")
                if not api_client_found:
                    missing_parts.append("seeded commit message 'Add API client'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Recent Commits",
            prompt="Show me the last 5 commits in the repository.",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_pull_request_list(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 5: List open pull requests (MEDIUM).

        Expected: Bot lists open PRs and includes the seeded PR.
        Seeded PR title: "[BENCHMARK] Add error handler feature"

        Conditions:
          1. "error handler" appears in response (unique phrase from seeded PR title)
          2. "benchmark" appears in response (PR title prefix)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {"seeded_pr_title": "[BENCHMARK] Add error handler feature"}
        error_message = None

        try:
            response_lower = response.lower()

            error_handler_found = "error handler" in response_lower
            benchmark_found = "benchmark" in response_lower

            validation_details["error_handler_found"] = error_handler_found
            validation_details["benchmark_found"] = benchmark_found

            if error_handler_found and benchmark_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not error_handler_found:
                    missing_parts.append("seeded PR phrase 'error handler'")
                if not benchmark_found:
                    missing_parts.append("seeded PR prefix 'benchmark'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Pull Request List",
            prompt="List all open pull requests in the repository.",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_issue_labels(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 6: List repository labels (MEDIUM).

        Expected: Bot lists labels including the seeded 'benchmark-seed' label.

        Conditions:
          1. "benchmark-seed" appears in response (unique seeded label name)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {"seeded_label": "benchmark-seed"}
        error_message = None

        try:
            response_lower = response.lower()

            label_found = "benchmark-seed" in response_lower

            validation_details["benchmark_seed_label_found"] = label_found

            if label_found:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Missing: seeded label 'benchmark-seed'"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Issue Labels",
            prompt="What labels are available in this repository?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_contributor_stats(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 7: Contributor stats (HARD).

        Expected: Bot identifies contributors; all seeded commits are by repo_owner.
        repo_owner is stored in setup_data["repo_owner"].

        Conditions:
          1. repo_owner username appears in response (the sole contributor)
        """
        repo_owner = setup_data.get("repo_owner", "")

        success = False
        accuracy_score = 0.0
        validation_details = {"repo_owner": repo_owner}
        error_message = None

        try:
            response_lower = response.lower()

            owner_found = repo_owner.lower() in response_lower if repo_owner else False

            validation_details["owner_found"] = owner_found

            if owner_found:
                success = True
                accuracy_score = 100.0
            else:
                error_message = f"Missing: repo owner '{repo_owner}' not found in contributor list"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Contributor Stats",
            prompt="Who are the top 3 contributors to this repository?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_file_contents(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 8: File contents retrieval (HARD).

        Expected: Bot reads src/utils.js and identifies the two async functions.
        src/utils.js defines: async function fetchData(...) and async function processItems(...)

        Conditions:
          1. "fetchdata" appears in response (function name from file)
          2. "processitems" appears in response (function name from file)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {
            "function_1": "fetchData",
            "function_2": "processItems",
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
                    missing_parts.append("function 'fetchData'")
                if not processitems_found:
                    missing_parts.append("function 'processItems'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="File Contents",
            prompt="Get the contents of src/utils.js and identify the functions it defines.",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_release_info(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 9: Release info (HARD).

        Expected: Bot finds the seeded release and reports its tag.
        Seeded release tag: "v1.0.0-benchmark"

        Conditions:
          1. "v1.0.0-benchmark" appears in response (unique seeded release tag)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {"seeded_release_tag": "v1.0.0-benchmark"}
        error_message = None

        try:
            response_lower = response.lower()

            tag_found = "v1.0.0-benchmark" in response_lower

            validation_details["tag_found"] = tag_found

            if tag_found:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Missing: seeded release tag 'v1.0.0-benchmark'"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Release Info",
            prompt="What was the latest release in the repository and when was it published?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
