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
