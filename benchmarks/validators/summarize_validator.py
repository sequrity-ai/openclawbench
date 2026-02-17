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

    @staticmethod
    def validate_executive_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 4: Executive summary of business article."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for executive/business summary keywords
            executive_keywords = ["executive", "revenue", "growth", "performance", "key highlights", "financial", "business"]
            has_executive_content = any(kw in response.lower() for kw in executive_keywords)

            # Check for summary indicators
            summary_keywords = ["summary", "overview", "key points", "highlights"]
            has_summary = any(kw in response.lower() for kw in summary_keywords)

            has_content = len(response) > 80

            validation_details["has_executive_content"] = has_executive_content
            validation_details["has_summary"] = has_summary
            validation_details["has_content"] = has_content

            if (has_executive_content or has_summary) and has_content:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Executive summary missing key elements or insufficient content"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Executive Summary",
            prompt="Create executive summary of business article",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_technical_abstract(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 5: Technical abstract/summary."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for technical content keywords
            technical_keywords = ["algorithm", "method", "approach", "technique", "model", "system", "results", "findings"]
            has_technical_content = any(kw in response.lower() for kw in technical_keywords)

            # Check for abstract/summary indicators
            summary_keywords = ["abstract", "summary", "overview", "key concepts", "main idea"]
            has_summary = any(kw in response.lower() for kw in summary_keywords)

            has_content = len(response) > 80

            validation_details["has_technical_content"] = has_technical_content
            validation_details["has_summary"] = has_summary
            validation_details["has_content"] = has_content

            if (has_technical_content or has_summary) and has_content:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Technical abstract missing key elements or insufficient content"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Technical Abstract",
            prompt="Summarize technical document focusing on key concepts",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_comparative_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 6: Comparative summary of two articles."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for comparison indicators
            comparison_keywords = ["compare", "contrast", "both", "whereas", "while", "however", "differ", "similar", "versus"]
            has_comparison = any(kw in response.lower() for kw in comparison_keywords)

            # Check for summary indicators
            summary_keywords = ["summary", "key points", "main difference", "overview"]
            has_summary = any(kw in response.lower() for kw in summary_keywords)

            # Should mention both articles/perspectives
            has_both_perspectives = response.lower().count("article") >= 2 or any(
                word in response.lower() for word in ["first", "second", "one", "other"]
            )

            has_content = len(response) > 120  # Longer for comparison

            validation_details["has_comparison"] = has_comparison
            validation_details["has_summary"] = has_summary
            validation_details["has_both_perspectives"] = has_both_perspectives
            validation_details["has_content"] = has_content

            if has_comparison and has_content and (has_summary or has_both_perspectives):
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Comparative summary missing key elements or insufficient content"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Comparative Summary",
            prompt="Compare two articles on same topic",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_multilevel_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 7: Multi-level summary (1-sentence, 1-paragraph, detailed)."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for multilevel structure indicators
            level_indicators = ["sentence", "paragraph", "detailed", "brief", "comprehensive", "one-sentence"]
            has_level_indicators = sum(1 for kw in level_indicators if kw in response.lower())

            # Check for summary keywords
            summary_keywords = ["summary", "overview", "key points", "main idea"]
            has_summary = any(kw in response.lower() for kw in summary_keywords)

            # Should have substantial content for multiple levels
            has_content = len(response) > 150

            # Check for structured formatting (bullets, numbers, sections)
            has_structure = any(char in response for char in ["-", "*", "1.", "2.", "•"])

            validation_details["level_indicators_count"] = has_level_indicators
            validation_details["has_summary"] = has_summary
            validation_details["has_content"] = has_content
            validation_details["has_structure"] = has_structure

            if has_content and (has_level_indicators >= 2 or has_summary) and has_structure:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Multi-level summary missing required structure or insufficient content"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Multi-Level Summary",
            prompt="Provide 1-sentence, 1-paragraph, and detailed summaries",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_qa_generation(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 8: Q&A generation from article."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for Q&A indicators
            qa_keywords = ["question", "answer", "q:", "a:", "what", "why", "how", "when", "where"]
            has_qa_format = sum(1 for kw in qa_keywords if kw in response.lower())

            # Check for question marks
            question_count = response.count("?")
            has_questions = question_count >= 2

            # Should have substantial content
            has_content = len(response) > 100

            # Check for structured formatting
            has_structure = any(char in response for char in ["-", "*", "1.", "Q:", "A:"])

            validation_details["qa_keywords_count"] = has_qa_format
            validation_details["question_count"] = question_count
            validation_details["has_content"] = has_content
            validation_details["has_structure"] = has_structure

            if has_questions and has_content and (has_qa_format >= 3 or has_structure):
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Q&A generation missing questions/answers or insufficient content"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Q&A Generation",
            prompt="Generate questions and answers from article",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_sentiment_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 9: Sentiment analysis summary."""
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for sentiment-related keywords
            sentiment_keywords = ["positive", "negative", "neutral", "sentiment", "tone", "optimistic", "pessimistic", "mixed"]
            has_sentiment = any(kw in response.lower() for kw in sentiment_keywords)

            # Check for summary keywords
            summary_keywords = ["summary", "overview", "key points", "main idea", "analysis"]
            has_summary = any(kw in response.lower() for kw in summary_keywords)

            # Should have substantial content
            has_content = len(response) > 80

            validation_details["has_sentiment"] = has_sentiment
            validation_details["has_summary"] = has_summary
            validation_details["has_content"] = has_content

            if has_sentiment and has_content and has_summary:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Sentiment analysis summary missing sentiment indicators or insufficient content"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Sentiment Analysis Summary",
            prompt="Summarize with sentiment analysis",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
