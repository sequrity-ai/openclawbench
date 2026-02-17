"""Validation utilities for GitHub benchmark tasks."""

import logging
from typing import Any

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)


class GitHubValidator:
    """Validates GitHub task results."""

    @staticmethod
    def validate_issue_creation(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Issue creation."""
        expected_title = setup_data.get("issue_title", "")
        
        success = False
        accuracy_score = 0.0
        validation_details = {"expected_title": expected_title}
        error_message = None

        try:
            # Check if bot mentioned issue creation
            creation_keywords = ["issue", "created", "opened", "#"]
            has_creation = any(kw in response.lower() for kw in creation_keywords)
            
            # Check if title is mentioned
            title_mentioned = expected_title.lower() in response.lower() if expected_title else True
            
            validation_details["has_creation_keywords"] = has_creation
            validation_details["title_mentioned"] = title_mentioned
            
            if has_creation and title_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Issue creation not confirmed or title not mentioned"
                
        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Issue Creation",
            prompt="Create a GitHub issue",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_issue_list(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: List issues."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for list-related keywords
            list_keywords = ["issue", "open", "list", "#"]
            has_list = any(kw in response.lower() for kw in list_keywords)
            
            # Check reasonable content
            has_content = len(response) > 30
            
            validation_details["has_list_keywords"] = has_list
            validation_details["has_content"] = has_content
            
            if has_list and has_content:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Issue list not provided or insufficient"
                
        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="List Issues",
            prompt="List open issues in repository",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_repo_info(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: Repository information."""
        repo_name = setup_data.get("repo_name", "")
        
        success = False
        accuracy_score = 0.0
        validation_details = {"repo_name": repo_name}
        error_message = None

        try:
            # Check for repo-related keywords
            repo_keywords = ["repository", "repo", "star", "fork", "description"]
            has_repo_info = any(kw in response.lower() for kw in repo_keywords)
            
            # Check repo name mentioned
            repo_mentioned = repo_name.lower() in response.lower() if repo_name else True
            
            validation_details["has_repo_info"] = has_repo_info
            validation_details["repo_mentioned"] = repo_mentioned
            
            if has_repo_info and repo_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Repository information not provided"
                
        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Repository Info",
            prompt="Get repository information",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_recent_commits(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 4: Recent commits."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            response_lower = response.lower()

            # Check for commit-related keywords
            commit_keywords = ["commit", "commits", "sha", "message", "author", "hash"]
            has_commits = any(kw in response_lower for kw in commit_keywords)

            # Check reasonable content length
            has_content = len(response) > 50

            # Detect empty/no-data responses - bot saying "no commits" or "repo is empty"
            empty_patterns = [
                "no commits", "zero commits", "empty", "no commit history",
                "repository is empty", "repo is empty", "hasn't been pushed",
                "has no commits", "no history", "not yet been committed",
            ]
            is_empty_response = any(pat in response_lower for pat in empty_patterns)

            validation_details["has_commit_keywords"] = has_commits
            validation_details["has_content"] = has_content
            validation_details["is_empty_response"] = is_empty_response

            if has_commits and has_content and not is_empty_response:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Commit list not provided or repo is empty (no actual commits found)"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Recent Commits",
            prompt="Show me the last 5 commits in the repo",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_pull_request_list(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 5: Pull request list."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            response_lower = response.lower()

            # Check for pull request-related keywords
            pr_keywords = ["pull request", "pull requests", "pr", "open", "merged", "draft"]
            has_pr_info = any(kw in response_lower for kw in pr_keywords)

            # Check reasonable content length
            has_content = len(response) > 30

            # Detect empty/no-data responses
            empty_patterns = [
                "no open pull requests", "no pull requests", "no prs",
                "empty", "repository is empty", "repo is empty",
                "there are no", "0 pull requests", "zero pull requests",
            ]
            is_empty_response = any(pat in response_lower for pat in empty_patterns)

            validation_details["has_pr_keywords"] = has_pr_info
            validation_details["has_content"] = has_content
            validation_details["is_empty_response"] = is_empty_response

            if has_pr_info and has_content and not is_empty_response:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Pull request list not provided or repo has no open PRs"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Pull Request List",
            prompt="List all open pull requests",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_issue_labels(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 6: Issue labels."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for label-related keywords
            label_keywords = ["label", "labels", "tag", "tags", "bug", "enhancement", "documentation"]
            has_labels = any(kw in response.lower() for kw in label_keywords)

            # Check reasonable content length
            has_content = len(response) > 30

            validation_details["has_label_keywords"] = has_labels
            validation_details["has_content"] = has_content

            if has_labels and has_content:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Label list not provided or insufficient content"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Issue Labels",
            prompt="What labels are available in this repo?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_contributor_stats(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 7: Contributor stats."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            response_lower = response.lower()

            # Check for contributor-related keywords
            contributor_keywords = ["contributor", "contributors", "commit", "commits", "author", "top"]
            has_contributors = any(kw in response_lower for kw in contributor_keywords)

            # Check reasonable content length
            has_content = len(response) > 50

            # Detect empty/no-data responses
            empty_patterns = [
                "no contributors", "has no contributors", "zero contributors",
                "empty", "repository is empty", "repo is empty",
                "no contribution data", "no commits", "zero commits",
            ]
            is_empty_response = any(pat in response_lower for pat in empty_patterns)

            validation_details["has_contributor_keywords"] = has_contributors
            validation_details["has_content"] = has_content
            validation_details["is_empty_response"] = is_empty_response

            if has_contributors and has_content and not is_empty_response:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Contributor stats not provided or repo has no contributors"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Contributor Stats",
            prompt="Who are the top 3 contributors to this repo?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_file_contents(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 8: File contents retrieval."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            response_lower = response.lower()

            # Check for file content-related keywords (functions defined in src/utils.js)
            content_keywords = ["fetchdata", "processitems", "async function", "function", "utils.js", "utils"]
            has_file_content = any(kw in response_lower for kw in content_keywords)

            # Check reasonable content length
            has_content = len(response) > 30

            # Detect error/not-found responses
            error_patterns = [
                "not found", "does not exist", "file not found", "404",
                "no such file", "cannot find", "unable to find",
                "error retrieving", "failed to get",
            ]
            is_error_response = any(pat in response_lower for pat in error_patterns)

            validation_details["has_file_content_keywords"] = has_file_content
            validation_details["has_content"] = has_content
            validation_details["is_error_response"] = is_error_response

            if has_file_content and has_content and not is_error_response:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "File contents not retrieved or function names not mentioned"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="File Contents",
            prompt="Get the contents of src/utils.js and identify the functions it defines",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_release_info(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 9: Release info."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            response_lower = response.lower()

            # Check for release-related keywords
            release_keywords = ["release", "releases", "version", "tag", "published", "date", "latest"]
            has_release_info = any(kw in response_lower for kw in release_keywords)

            # Check reasonable content length
            has_content = len(response) > 30

            # Detect empty/no-data responses
            empty_patterns = [
                "no releases", "there are no releases", "no release",
                "empty", "repository is empty", "repo is empty",
                "has no releases", "no tags", "0 releases",
            ]
            is_empty_response = any(pat in response_lower for pat in empty_patterns)

            validation_details["has_release_keywords"] = has_release_info
            validation_details["has_content"] = has_content
            validation_details["is_empty_response"] = is_empty_response

            if has_release_info and has_content and not is_empty_response:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Release information not provided or repo has no releases"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Release Info",
            prompt="What was the latest release and when?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
