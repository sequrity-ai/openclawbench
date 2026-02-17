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

    @staticmethod
    def validate_count_unread(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 4: Count unread emails.

        Expected: Bot reports a numeric count of unread emails and uses
        relevant terms ("unread", "emails", a number or "no").
        """
        success = False
        accuracy_score = 0.0
        validation_details: dict[str, Any] = {}
        error_message = None

        try:
            response_lower = response.lower()

            # Must mention "unread" and "email" (or "inbox")
            has_unread = "unread" in response_lower
            has_email_ref = "email" in response_lower or "inbox" in response_lower
            # Must contain a digit or explicit "no" / "zero" / "none"
            has_count = bool(re.search(r"\d+", response_lower)) or any(
                word in response_lower for word in ("no unread", "zero", "none", "0")
            )

            validation_details["has_unread_keyword"] = has_unread
            validation_details["has_email_reference"] = has_email_ref
            validation_details["has_count"] = has_count

            if has_unread and has_email_ref and has_count:
                success = True
                accuracy_score = 100.0
            elif has_unread and has_email_ref:
                accuracy_score = 60.0
                error_message = "Response mentions unread emails but does not include a count"
            elif has_unread:
                accuracy_score = 30.0
                error_message = "Response mentions 'unread' but lacks email context and count"
            else:
                accuracy_score = 0.0
                error_message = "Response does not mention 'unread' emails"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Count Unread",
            prompt="How many unread emails do I have?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_search_by_sender(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 5: Search emails by sender.

        Expected: Bot found the test email sent from support@example.com and
        reports at least the sender address or subject in its response.
        """
        sender_email = setup_data.get("sender_search_email", "support@example.com")
        sender_subject = setup_data.get("sender_search_subject", "")

        success = False
        accuracy_score = 0.0
        validation_details: dict[str, Any] = {
            "expected_sender": sender_email,
            "expected_subject": sender_subject,
        }
        error_message = None

        try:
            response_lower = response.lower()

            has_sender = sender_email.lower() in response_lower
            has_subject = sender_subject and sender_subject.lower() in response_lower
            has_email_ref = "email" in response_lower or "message" in response_lower or "found" in response_lower

            validation_details["has_sender"] = has_sender
            validation_details["has_subject"] = bool(has_subject)
            validation_details["has_email_reference"] = has_email_ref

            if has_sender and has_subject:
                success = True
                accuracy_score = 100.0
            elif has_sender and has_email_ref:
                success = True
                accuracy_score = 80.0
            elif has_sender:
                accuracy_score = 50.0
                error_message = "Found sender address but response lacks email context"
            else:
                accuracy_score = 0.0
                error_message = f"Response does not mention expected sender '{sender_email}'"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Search by Sender",
            prompt="Find emails from support@example.com",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_label_management(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 6: Create a Gmail label.

        Expected: Bot confirms the label "Important Projects" was created,
        using relevant terms like "label", "created", "Important Projects".
        """
        expected_label = setup_data.get("new_label_name", "Important Projects")

        success = False
        accuracy_score = 0.0
        validation_details: dict[str, Any] = {"expected_label": expected_label}
        error_message = None

        try:
            response_lower = response.lower()
            expected_label_lower = expected_label.lower()

            has_label_keyword = "label" in response_lower
            has_label_name = expected_label_lower in response_lower
            has_created_keyword = any(
                word in response_lower
                for word in ("created", "added", "made", "successfully", "new label")
            )

            validation_details["has_label_keyword"] = has_label_keyword
            validation_details["has_label_name"] = has_label_name
            validation_details["has_created_keyword"] = has_created_keyword

            if has_label_name and has_created_keyword:
                success = True
                accuracy_score = 100.0
            elif has_label_name and has_label_keyword:
                success = True
                accuracy_score = 80.0
            elif has_label_keyword and has_created_keyword:
                accuracy_score = 40.0
                error_message = f"Mentions label creation but does not name '{expected_label}'"
            else:
                accuracy_score = 0.0
                error_message = f"Response does not confirm creation of label '{expected_label}'"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Label Management",
            prompt="Create a label called 'Important Projects'",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_email_with_attachment(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 7: Find emails with PDF attachments from last week.

        Expected: Bot reports at least the test email containing a PDF attachment
        and uses relevant terms: "pdf", "attachment", a recent date or "last week".
        """
        attachment_subject = setup_data.get("attachment_email_subject", "")

        success = False
        accuracy_score = 0.0
        validation_details: dict[str, Any] = {"expected_subject": attachment_subject}
        error_message = None

        try:
            response_lower = response.lower()

            has_pdf = "pdf" in response_lower
            has_attachment = "attachment" in response_lower or "attached" in response_lower
            has_subject = attachment_subject and attachment_subject.lower() in response_lower
            has_result = any(
                word in response_lower
                for word in ("found", "email", "message", "result", "here")
            )

            validation_details["has_pdf_keyword"] = has_pdf
            validation_details["has_attachment_keyword"] = has_attachment
            validation_details["has_subject"] = bool(has_subject)
            validation_details["has_result_context"] = has_result

            if has_pdf and has_attachment and has_subject:
                success = True
                accuracy_score = 100.0
            elif has_pdf and has_attachment and has_result:
                success = True
                accuracy_score = 80.0
            elif has_pdf and has_attachment:
                accuracy_score = 50.0
                error_message = "Mentions PDF attachment but result context is unclear"
            elif has_pdf or has_attachment:
                accuracy_score = 20.0
                error_message = "Partial mention of PDF/attachment but incomplete response"
            else:
                accuracy_score = 0.0
                error_message = "Response does not mention PDF attachments"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Email with Attachment",
            prompt="Find emails with PDF attachments from last week",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_draft_email(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 8: Draft an email about Q1 results.

        Expected: Bot confirms a draft was created/saved, mentioning
        the recipient (team@example.com) and subject or "Q1".
        """
        draft_recipient = setup_data.get("draft_recipient", "team@example.com")

        success = False
        accuracy_score = 0.0
        validation_details: dict[str, Any] = {"expected_recipient": draft_recipient}
        error_message = None

        try:
            response_lower = response.lower()

            has_draft = "draft" in response_lower
            has_recipient = draft_recipient.lower() in response_lower
            has_q1 = "q1" in response_lower or "quarter" in response_lower or "results" in response_lower
            has_created = any(
                word in response_lower
                for word in ("created", "saved", "drafted", "composed", "written")
            )

            validation_details["has_draft_keyword"] = has_draft
            validation_details["has_recipient"] = has_recipient
            validation_details["has_q1_reference"] = has_q1
            validation_details["has_created_keyword"] = has_created

            if has_draft and has_recipient and has_q1:
                success = True
                accuracy_score = 100.0
            elif has_draft and (has_recipient or has_q1) and has_created:
                success = True
                accuracy_score = 80.0
            elif has_draft and has_created:
                accuracy_score = 50.0
                error_message = "Draft confirmed but missing recipient or Q1 reference"
            elif has_draft:
                accuracy_score = 25.0
                error_message = "Mentions draft but lacks confirmation of creation"
            else:
                accuracy_score = 0.0
                error_message = "Response does not confirm draft creation"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Draft Email",
            prompt="Draft an email to team@example.com about Q1 results",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_email_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 9: Summarize the last 5 emails.

        Expected: Bot provides a summary referencing multiple emails and
        uses terms like "summary", "inbox", "email(s)", and ideally
        mentions at least one of the seeded test subjects.
        """
        summary_subjects = setup_data.get("summary_email_subjects", [])

        success = False
        accuracy_score = 0.0
        validation_details: dict[str, Any] = {"expected_subjects": summary_subjects}
        error_message = None

        try:
            response_lower = response.lower()

            has_summary = any(
                word in response_lower
                for word in ("summary", "summarize", "overview", "here are", "below are")
            )
            has_email_ref = "email" in response_lower or "inbox" in response_lower or "message" in response_lower
            # Check if response mentions a numeric count (5, four, three, etc.)
            has_count = bool(re.search(r"\b[1-9]\b|\bfive\b|\bfour\b|\bthree\b|\btwo\b|\bone\b", response_lower))
            # Count how many seeded subjects appear in the response
            matched_subjects = [s for s in summary_subjects if s.lower() in response_lower]

            validation_details["has_summary_keyword"] = has_summary
            validation_details["has_email_reference"] = has_email_ref
            validation_details["has_count"] = has_count
            validation_details["matched_subjects"] = matched_subjects
            validation_details["matched_subjects_count"] = len(matched_subjects)

            if has_summary and has_email_ref and len(matched_subjects) >= 1:
                success = True
                accuracy_score = 100.0
            elif has_summary and has_email_ref and has_count:
                success = True
                accuracy_score = 80.0
            elif has_summary and has_email_ref:
                accuracy_score = 50.0
                error_message = "Provides a summary but does not reference expected email content"
            elif has_email_ref:
                accuracy_score = 20.0
                error_message = "References emails but does not appear to summarize them"
            else:
                accuracy_score = 0.0
                error_message = "Response does not summarize inbox emails"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Email Summary",
            prompt="Summarize the last 5 emails in my inbox",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
