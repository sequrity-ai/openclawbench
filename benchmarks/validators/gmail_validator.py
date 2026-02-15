"""Validation utilities for Gmail benchmark tasks."""

import logging
import re
from typing import Any

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)


class GmailValidator:
    """Validates Gmail task results."""

    @staticmethod
    def validate_email_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Email search.

        Expected: Bot found and reported correct email subject and confirmation code

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including expected_subject and confirmation_code
        """
        expected_subject = setup_data.get("search_subject", "")
        expected_code = setup_data.get("expected_extracted_data", {}).get("confirmation_code", "")
        test_email_id = setup_data.get("search_email_id", "")

        success = False
        accuracy_score = 0.0
        validation_details = {
            "expected_subject": expected_subject,
            "expected_confirmation_code": expected_code,
        }
        error_message = None

        try:
            # Check if bot mentioned the correct subject AND confirmation code
            # This ensures bot is reading the LATEST email, not a cached old one
            subject_found = expected_subject.lower() in response.lower()
            code_found = expected_code and expected_code.lower() in response.lower()

            if subject_found and code_found:
                success = True
                accuracy_score = 100.0
                validation_details["found_subject"] = True
                validation_details["found_confirmation_code"] = True
            elif subject_found:
                # Found subject but not confirmation code - might be old email
                accuracy_score = 50.0
                error_message = f"Found subject but missing confirmation code: '{expected_code}'"
                validation_details["found_subject"] = True
                validation_details["found_confirmation_code"] = False
            else:
                accuracy_score = 0.0
                error_message = f"Bot did not mention expected subject: '{expected_subject}'"
                validation_details["found_subject"] = False
                validation_details["found_confirmation_code"] = False

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Email Search",
            prompt="Search for email with specific subject",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_email_send(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: Email send.

        Expected: Email from bot exists in benchmark's Gmail inbox
        (Bot sends TO benchmark account, so we check benchmark's inbox)
        """
        gmail_setup = setup_data.get("gmail_setup")
        expected_subject = setup_data.get("send_subject", "")
        benchmark_email = setup_data.get("benchmark_email", "")
        bot_email = setup_data.get("bot_email", "")

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            if not gmail_setup:
                error_message = "Gmail setup not available for validation"
            else:
                # Search for received email in benchmark's inbox from bot
                # Bot sends TO benchmark, so we check inbox (not sent folder)
                query = f"subject:{expected_subject} from:{bot_email} in:inbox"
                received_emails = gmail_setup.search_emails(query, max_results=5)

                validation_details["expected_subject"] = expected_subject
                validation_details["benchmark_email"] = benchmark_email
                validation_details["bot_email"] = bot_email
                validation_details["found_count"] = len(received_emails)

                if received_emails:
                    success = True
                    accuracy_score = 100.0
                    validation_details["email_id"] = received_emails[0]["id"]
                else:
                    accuracy_score = 0.0
                    error_message = f"No email received from bot with subject '{expected_subject}' from '{bot_email}'"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Email Send",
            prompt="Send email with specific subject and recipient",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_email_parsing(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: Email data extraction.

        Expected: Bot extracted correct data from email
        """
        expected_data = setup_data.get("expected_extracted_data", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"expected_data": expected_data}
        error_message = None

        try:
            # Check if bot extracted expected values
            # Exclude 'confirmation_code' which is only for Task 1
            relevant_data = {k: v for k, v in expected_data.items() if k != "confirmation_code"}
            extracted_correctly = []
            missing_values = []

            for key, expected_value in relevant_data.items():
                # Look for the value in bot's response (case-insensitive)
                if str(expected_value).lower() in response.lower():
                    extracted_correctly.append(key)
                else:
                    missing_values.append(key)

            validation_details["extracted_correctly"] = extracted_correctly
            validation_details["missing_values"] = missing_values

            # Binary scoring: ALL values must be extracted
            if len(extracted_correctly) == len(relevant_data):
                success = True
                accuracy_score = 100.0
            else:
                accuracy_score = 0.0
                error_message = f"Missing extracted values: {', '.join(missing_values)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Email Data Extraction",
            prompt="Extract specific data from email content",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
