"""Validation utilities for Web Search benchmark tasks."""

import logging
import re
from typing import Any

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)


class WebValidator:
    """Validates Web Search task results."""

    @staticmethod
    def validate_factual_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Factual web search.

        Expected: Bot found and reported correct factual information

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including expected facts
        """
        expected_facts = setup_data.get("expected_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"expected_facts": expected_facts}
        error_message = None

        try:
            # Check if bot mentioned all expected facts (case-insensitive)
            facts_found = []
            facts_missing = []

            for fact_name, fact_value in expected_facts.items():
                # Convert to lowercase for comparison
                if str(fact_value).lower() in response.lower():
                    facts_found.append(fact_name)
                else:
                    facts_missing.append(fact_name)

            validation_details["facts_found"] = facts_found
            validation_details["facts_missing"] = facts_missing

            # Binary scoring: ALL facts must be present
            if len(facts_found) == len(expected_facts):
                success = True
                accuracy_score = 100.0
            else:
                accuracy_score = 0.0
                error_message = f"Missing expected facts: {', '.join(facts_missing)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Factual Web Search",
            prompt="Search for factual information on the web",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_comparison_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: Comparison research.

        Expected: Bot provided comparison with key differences

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including comparison criteria
        """
        required_keywords = setup_data.get("required_keywords", [])
        comparison_topics = setup_data.get("comparison_topics", [])

        success = False
        accuracy_score = 0.0
        validation_details = {
            "required_keywords": required_keywords,
            "comparison_topics": comparison_topics,
        }
        error_message = None

        try:
            # Check for required keywords
            keywords_found = []
            keywords_missing = []

            for keyword in required_keywords:
                if keyword.lower() in response.lower():
                    keywords_found.append(keyword)
                else:
                    keywords_missing.append(keyword)

            # Check that both comparison topics are mentioned
            topics_found = []
            topics_missing = []

            for topic in comparison_topics:
                if topic.lower() in response.lower():
                    topics_found.append(topic)
                else:
                    topics_missing.append(topic)

            validation_details["keywords_found"] = keywords_found
            validation_details["keywords_missing"] = keywords_missing
            validation_details["topics_found"] = topics_found
            validation_details["topics_missing"] = topics_missing

            # Binary scoring: ALL keywords and topics must be present
            all_keywords_present = len(keywords_found) == len(required_keywords)
            all_topics_present = len(topics_found) == len(comparison_topics)

            if all_keywords_present and all_topics_present:
                success = True
                accuracy_score = 100.0
            else:
                accuracy_score = 0.0
                missing_items = []
                if keywords_missing:
                    missing_items.append(f"keywords: {', '.join(keywords_missing)}")
                if topics_missing:
                    missing_items.append(f"topics: {', '.join(topics_missing)}")
                error_message = f"Missing: {'; '.join(missing_items)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Comparison Research",
            prompt="Compare two concepts or technologies",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_current_events(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: Current events research.

        Expected: Bot found recent/current information with relevant details

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including topic and required elements
        """
        topic = setup_data.get("topic", "")
        required_elements = setup_data.get("required_elements", [])

        success = False
        accuracy_score = 0.0
        validation_details = {
            "topic": topic,
            "required_elements": required_elements,
        }
        error_message = None

        try:
            # Check for topic mention (with common variations/abbreviations)
            # For "artificial intelligence", also accept "AI", "A.I.", etc.
            topic_variations = [topic.lower()]
            if topic.lower() == "artificial intelligence":
                topic_variations.extend(["ai", "a.i.", "a i"])

            topic_found = any(variation in response.lower() for variation in topic_variations)
            validation_details["topic_found"] = topic_found
            validation_details["topic_variations_checked"] = topic_variations

            # Check for required elements
            elements_found = []
            elements_missing = []

            for element in required_elements:
                if element.lower() in response.lower():
                    elements_found.append(element)
                else:
                    elements_missing.append(element)

            validation_details["elements_found"] = elements_found
            validation_details["elements_missing"] = elements_missing

            # Binary scoring: topic AND all required elements must be present
            if topic_found and len(elements_found) == len(required_elements):
                success = True
                accuracy_score = 100.0
            else:
                accuracy_score = 0.0
                missing_parts = []
                if not topic_found:
                    missing_parts.append(f"topic '{topic}'")
                if elements_missing:
                    missing_parts.append(f"elements: {', '.join(elements_missing)}")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Current Events Research",
            prompt="Research current events and news",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_multi_query_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 4: Multi-Query Search (MEDIUM).

        Expected: Bot searched for both 'Python async programming' and 'FastAPI tutorials'
        and reported results containing Python, async, and FastAPI keywords.

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data (unused for this task)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for Python keyword
            python_mentioned = "python" in response.lower()
            validation_details["python_mentioned"] = python_mentioned

            # Check for async keyword
            async_mentioned = "async" in response.lower()
            validation_details["async_mentioned"] = async_mentioned

            # Check for FastAPI keyword (case-insensitive)
            fastapi_mentioned = "fastapi" in response.lower()
            validation_details["fastapi_mentioned"] = fastapi_mentioned

            if python_mentioned and async_mentioned and fastapi_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not python_mentioned:
                    missing_parts.append("Python")
                if not async_mentioned:
                    missing_parts.append("async")
                if not fastapi_mentioned:
                    missing_parts.append("FastAPI")
                error_message = f"Missing keywords: {', '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Multi-Query Search",
            prompt="Search for both 'Python async programming' and 'FastAPI tutorials'",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_domain_specific_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 5: Domain-Specific Search (MEDIUM).

        Expected: Bot found recent AI articles from techcrunch.com and reported
        results mentioning both TechCrunch and AI.

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data (unused for this task)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for techcrunch keyword
            techcrunch_mentioned = "techcrunch" in response.lower()
            validation_details["techcrunch_mentioned"] = techcrunch_mentioned

            # Check for AI keyword (various forms)
            ai_keywords = ["ai", "artificial intelligence", "a.i."]
            ai_mentioned = any(kw in response.lower() for kw in ai_keywords)
            validation_details["ai_mentioned"] = ai_mentioned

            if techcrunch_mentioned and ai_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not techcrunch_mentioned:
                    missing_parts.append("techcrunch")
                if not ai_mentioned:
                    missing_parts.append("AI")
                error_message = f"Missing keywords: {', '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Domain-Specific Search",
            prompt="Find recent articles about AI on techcrunch.com",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_news_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 6: News Search (MEDIUM).

        Expected: Bot retrieved and summarized recent news about climate change,
        mentioning 'climate' or 'news' in the response.

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data (unused for this task)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for climate keyword
            climate_mentioned = "climate" in response.lower()
            validation_details["climate_mentioned"] = climate_mentioned

            # Check for news keyword
            news_mentioned = "news" in response.lower()
            validation_details["news_mentioned"] = news_mentioned

            # Pass if either climate or news is mentioned
            if climate_mentioned or news_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Missing keywords: neither 'climate' nor 'news' found in response"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="News Search",
            prompt="What are the latest news about climate change?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_time_filtered_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 7: Time-Filtered Search (HARD).

        Expected: Bot found articles about OpenAI published recently, mentioning
        OpenAI and time-related keywords such as 'recent', 'week', or 'latest'.

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data (unused for this task)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for OpenAI keyword
            openai_mentioned = "openai" in response.lower()
            validation_details["openai_mentioned"] = openai_mentioned

            # Check for time-related keywords
            time_keywords = ["recent", "week", "latest", "last week", "past week", "new", "published"]
            time_mentioned = any(kw in response.lower() for kw in time_keywords)
            validation_details["time_mentioned"] = time_mentioned
            validation_details["time_keywords_checked"] = time_keywords

            if openai_mentioned and time_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not openai_mentioned:
                    missing_parts.append("OpenAI")
                if not time_mentioned:
                    missing_parts.append("time-related terms (recent/week/latest)")
                error_message = f"Missing keywords: {', '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Time-Filtered Search",
            prompt="Find articles about OpenAI published in the last week",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_search_comparison(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 8: Search Comparison (HARD).

        Expected: Bot searched for both React and Vue, compared results,
        and reported which has more results using comparison language.

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data (unused for this task)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for React keyword
            react_mentioned = "react" in response.lower()
            validation_details["react_mentioned"] = react_mentioned

            # Check for Vue keyword
            vue_mentioned = "vue" in response.lower()
            validation_details["vue_mentioned"] = vue_mentioned

            # Check for comparison keywords
            comparison_keywords = ["more", "less", "than", "compared", "versus", "vs", "higher", "lower", "results"]
            comparison_mentioned = any(kw in response.lower() for kw in comparison_keywords)
            validation_details["comparison_mentioned"] = comparison_mentioned

            if react_mentioned and vue_mentioned and comparison_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not react_mentioned:
                    missing_parts.append("React")
                if not vue_mentioned:
                    missing_parts.append("Vue")
                if not comparison_mentioned:
                    missing_parts.append("comparison language")
                error_message = f"Missing: {', '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Search Comparison",
            prompt="Search for 'React' vs 'Vue' and tell me which has more results",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_topic_analysis(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 9: Topic Analysis (HARD).

        Expected: Bot searched for 'machine learning', analyzed the top results,
        and summarized the main topics found using analysis/summary language.

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data (unused for this task)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for machine learning keyword
            ml_keywords = ["machine learning", "ml"]
            ml_mentioned = any(kw in response.lower() for kw in ml_keywords)
            validation_details["ml_mentioned"] = ml_mentioned

            # Check for analysis/summary keywords
            analysis_keywords = [
                "summary", "summarize", "summarized", "topic", "topics",
                "main", "key", "overview", "include", "covers", "focus",
                "analysis", "analyze", "analyzed",
            ]
            analysis_mentioned = any(kw in response.lower() for kw in analysis_keywords)
            validation_details["analysis_mentioned"] = analysis_mentioned
            validation_details["analysis_keywords_checked"] = analysis_keywords

            if ml_mentioned and analysis_mentioned:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not ml_mentioned:
                    missing_parts.append("machine learning")
                if not analysis_mentioned:
                    missing_parts.append("analysis/summary language")
                error_message = f"Missing: {', '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Topic Analysis",
            prompt="Search for 'machine learning' and summarize the main topics from the top results",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
