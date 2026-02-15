"""Validation utilities for Summarize benchmark tasks."""

import logging
from typing import Any

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)


class SummarizeValidator:
    """Validates Summarize task results."""

    @staticmethod
    def validate_url_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: URL summarization."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for summary-related keywords
            summary_keywords = ["summary", "article", "content", "main", "key", "points"]
            has_summary = any(kw in response.lower() for kw in summary_keywords)
            
            # Check reasonable length (not just echoing URL)
            has_content = len(response) > 50
            
            validation_details["has_summary_keywords"] = has_summary
            validation_details["has_content"] = has_content
            
            if has_summary and has_content:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Summary missing keywords or insufficient content"
                
        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="URL Summary",
            prompt="Summarize content from URL",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_youtube_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: YouTube video summarization."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for video/youtube related content
            video_keywords = ["video", "youtube", "content", "describes", "about"]
            has_video_ref = any(kw in response.lower() for kw in video_keywords)
            
            has_content = len(response) > 50
            
            validation_details["has_video_reference"] = has_video_ref
            validation_details["has_content"] = has_content
            
            if has_video_ref and has_content:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "YouTube summary missing or insufficient"
                
        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="YouTube Summary",
            prompt="Summarize YouTube video content",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_comparison_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: Compare summaries from multiple sources."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for comparison indicators
            comparison_keywords = ["both", "compare", "differ", "similar", "whereas", "while", "however"]
            has_comparison = any(kw in response.lower() for kw in comparison_keywords)
            
            has_content = len(response) > 100  # Longer for comparison
            
            validation_details["has_comparison"] = has_comparison
            validation_details["has_content"] = has_content
            
            if has_comparison and has_content:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Comparison missing or insufficient"
                
        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Comparison Summary",
            prompt="Compare summaries from multiple sources",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
