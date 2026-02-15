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
            # Check for topic mention
            topic_found = topic.lower() in response.lower()
            validation_details["topic_found"] = topic_found

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
