"""Validation utilities for Gmail benchmark tasks.

All tasks are pinned to dynamically-seeded email data sent during setup().
Ground-truth values (subjects, codes, invoice numbers, amounts) are generated
fresh each run and stored in setup_data — no hardcoded facts.

Validators use binary success (100.0 or 0.0) — no partial credit paths.
"""

import logging
import re
from typing import Any

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)


class GmailValidator:
    """Validates Gmail task results against seeded email content."""

    @staticmethod
    def validate_email_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Email search (EASY).

        Expected: Bot found the seeded '[BENCHMARK TEST] Project Alpha Updates' email
        and reported the unique confirmation code from its body.

        Conditions:
          1. search_subject phrase appears in response
          2. confirmation_code (unique random per-run code) appears in response
        """
        expected_subject = setup_data.get("search_subject", "")
        expected_code = setup_data.get("expected_extracted_data", {}).get("confirmation_code", "")

        success = False
        accuracy_score = 0.0
        validation_details = {
            "expected_subject": expected_subject,
            "expected_confirmation_code": expected_code,
        }
        error_message = None

        try:
            response_lower = response.lower()

            subject_found = expected_subject.lower() in response_lower
            code_found = bool(expected_code) and expected_code.lower() in response_lower

            validation_details["subject_found"] = subject_found
            validation_details["code_found"] = code_found

            if subject_found and code_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not subject_found:
                    missing_parts.append(f"email subject '{expected_subject}'")
                if not code_found:
                    missing_parts.append(f"confirmation code '{expected_code}'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Email Search",
            prompt="Search for '[BENCHMARK TEST] Project Alpha Updates' and report the confirmation code",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_email_send(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: Email send (EASY).

        Expected: Email from bot exists in benchmark's Gmail inbox.
        Validation uses Gmail API to check — not just response keywords.

        Conditions:
          1. Gmail API confirms email received from bot with expected subject
        """
        gmail_setup = setup_data.get("gmail_setup")
        expected_subject = setup_data.get("send_subject", "")
        benchmark_email = setup_data.get("benchmark_email", "")
        bot_email = setup_data.get("bot_email", "")

        success = False
        accuracy_score = 0.0
        validation_details = {
            "expected_subject": expected_subject,
            "benchmark_email": benchmark_email,
            "bot_email": bot_email,
        }
        error_message = None

        try:
            if not gmail_setup:
                error_message = "Gmail setup not available for validation"
            else:
                query = f"subject:{expected_subject} from:{bot_email} in:inbox"
                received_emails = gmail_setup.search_emails(query, max_results=5)

                validation_details["found_count"] = len(received_emails)

                if received_emails:
                    success = True
                    accuracy_score = 100.0
                    validation_details["email_id"] = received_emails[0]["id"]
                else:
                    error_message = (
                        f"No email received from bot with subject '{expected_subject}' "
                        f"from '{bot_email}' — Gmail API check found 0 matching emails"
                    )

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Email Send",
            prompt=f"Send email to benchmark account with subject '{expected_subject}'",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_email_parsing(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: Email data extraction (EASY).

        Expected: Bot extracted invoice_number, total_amount, and due_date
        from the seeded invoice email. All three values are random per run.

        Conditions:
          1. invoice_number (e.g. "INV-7342") appears in response
          2. total_amount (e.g. "$7842.00") appears in response
          3. due_date ("2026-03-15") appears in response
        """
        expected_data = setup_data.get("expected_extracted_data", {})
        # Exclude confirmation_code — that's for Task 1 only
        relevant_data = {k: v for k, v in expected_data.items() if k != "confirmation_code"}

        success = False
        accuracy_score = 0.0
        validation_details = {"expected_data": relevant_data}
        error_message = None

        try:
            extracted_correctly = []
            missing_values = []

            for key, expected_value in relevant_data.items():
                if str(expected_value).lower() in response.lower():
                    extracted_correctly.append(key)
                else:
                    missing_values.append(f"{key}='{expected_value}'")

            validation_details["extracted_correctly"] = extracted_correctly
            validation_details["missing_values"] = missing_values

            if len(extracted_correctly) == len(relevant_data):
                success = True
                accuracy_score = 100.0
            else:
                error_message = f"Missing extracted values: {', '.join(missing_values)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Email Data Extraction",
            prompt="Find invoice email and extract invoice number, total amount, and due date",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_count_unread(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 4: Count unread emails (MEDIUM).

        Expected: Bot reports how many unread emails are in the inbox.
        Count is live (not pinned), so we check structural correctness:
        response must mention "unread" AND contain a number (or "no"/"zero"/"none").

        Conditions:
          1. "unread" appears in response
          2. A digit OR "no unread"/"zero"/"none" appears (explicit count or zero-state)
        """
        success = False
        accuracy_score = 0.0
        validation_details: dict[str, Any] = {}
        error_message = None

        try:
            response_lower = response.lower()

            has_unread = "unread" in response_lower
            has_count = bool(re.search(r"\d+", response_lower)) or any(
                phrase in response_lower for phrase in ("no unread", "zero", "none", "0 unread")
            )

            validation_details["has_unread_keyword"] = has_unread
            validation_details["has_count"] = has_count

            if has_unread and has_count:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not has_unread:
                    missing_parts.append("keyword 'unread'")
                if not has_count:
                    missing_parts.append("a count (digit or 'no unread'/'zero'/'none')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

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
        """Validate Task 5: Search emails by subject (MEDIUM).

        The task asks the bot to find the '[BENCHMARK TEST] Support Request' email
        and report who it appears to be from + the subject line.

        Note: The email is sent with from_display_name="support@example.com" but Gmail
        API ignores the MIME From override, so the email's actual sender in Gmail search
        is the benchmark account — not support@example.com. We validate on subject only.

        Conditions:
          1. sender_search_subject ('[BENCHMARK TEST] Support Request') appears in response
          2. "support" appears in response (the from display name is visible in the email body)
        """
        sender_subject = setup_data.get("sender_search_subject", "")

        success = False
        accuracy_score = 0.0
        validation_details: dict[str, Any] = {
            "expected_subject": sender_subject,
        }
        error_message = None

        try:
            response_lower = response.lower()

            has_subject = bool(sender_subject) and sender_subject.lower() in response_lower
            # "support" covers "support@example.com" or "support request" in the response
            has_support = "support" in response_lower

            validation_details["has_subject"] = has_subject
            validation_details["has_support"] = has_support

            if has_subject and has_support:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not has_subject:
                    missing_parts.append(f"seeded subject '{sender_subject}'")
                if not has_support:
                    missing_parts.append("'support' reference in response")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Search by Sender",
            prompt="Find the '[BENCHMARK TEST] Support Request' email and report who it's from",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_label_management(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 6: Create Gmail label (MEDIUM).

        Expected: Bot created the label "Important Projects" and confirmed it.

        Conditions:
          1. "important projects" appears in response (label name)
          2. A creation-confirmation word appears ("created", "added", "successfully", etc.)
        """
        expected_label = setup_data.get("new_label_name", "Important Projects")

        success = False
        accuracy_score = 0.0
        validation_details: dict[str, Any] = {"expected_label": expected_label}
        error_message = None

        try:
            response_lower = response.lower()

            has_label_name = expected_label.lower() in response_lower
            has_created = any(
                word in response_lower
                for word in ("created", "added", "made", "successfully", "new label")
            )

            validation_details["has_label_name"] = has_label_name
            validation_details["has_created_keyword"] = has_created

            if has_label_name and has_created:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not has_label_name:
                    missing_parts.append(f"label name '{expected_label}'")
                if not has_created:
                    missing_parts.append("creation confirmation ('created', 'added', 'successfully')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

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
        """Validate Task 7: Find emails with PDF attachments (HARD).

        Expected: Bot found the seeded Q4 Financial Report email and reported
        the subject plus mentioned PDF/attachment.

        Conditions:
          1. attachment_email_subject appears in response (seeded email subject)
          2. "pdf" appears in response (the attachment type mentioned in email body)
        """
        attachment_subject = setup_data.get("attachment_email_subject", "")

        success = False
        accuracy_score = 0.0
        validation_details: dict[str, Any] = {"expected_subject": attachment_subject}
        error_message = None

        try:
            response_lower = response.lower()

            has_subject = bool(attachment_subject) and attachment_subject.lower() in response_lower
            has_pdf = "pdf" in response_lower

            validation_details["has_subject"] = has_subject
            validation_details["has_pdf"] = has_pdf

            if has_subject and has_pdf:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not has_subject:
                    missing_parts.append(f"seeded email subject '{attachment_subject}'")
                if not has_pdf:
                    missing_parts.append("keyword 'pdf'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

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
        """Validate Task 8: Draft an email (HARD).

        Expected: Bot created a draft to team@example.com about Q1 results
        and confirmed the draft was saved.

        Conditions:
          1. "team@example.com" appears in response (draft recipient)
          2. "draft" appears in response (confirms a draft was created, not sent)
          3. "q1" OR "quarter" OR "results" appears (draft subject matter)
        """
        draft_recipient = setup_data.get("draft_recipient", "team@example.com")

        success = False
        accuracy_score = 0.0
        validation_details: dict[str, Any] = {"expected_recipient": draft_recipient}
        error_message = None

        try:
            response_lower = response.lower()

            has_recipient = draft_recipient.lower() in response_lower
            has_draft = "draft" in response_lower
            has_q1 = any(kw in response_lower for kw in ("q1", "quarter", "results"))

            validation_details["has_recipient"] = has_recipient
            validation_details["has_draft_keyword"] = has_draft
            validation_details["has_q1_reference"] = has_q1

            if has_recipient and has_draft and has_q1:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not has_recipient:
                    missing_parts.append(f"recipient '{draft_recipient}'")
                if not has_draft:
                    missing_parts.append("keyword 'draft'")
                if not has_q1:
                    missing_parts.append("Q1/quarter/results reference")
                error_message = f"Missing: {'; '.join(missing_parts)}"

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
        """Validate Task 9: Summarize last 5 emails (HARD).

        Expected: Bot summarized multiple inbox emails and mentioned at least
        2 of the 5 seeded subject topics in its response.
        Seeded subjects include "Team Meeting Notes", "Budget Approval", etc.

        Conditions:
          1. At least 3 of the 5 seeded summary_subjects appear in response
          2. "summary" OR "summarize" OR "here are" OR "overview" appears
        """
        summary_subjects = setup_data.get("summary_email_subjects", [])

        success = False
        accuracy_score = 0.0
        validation_details: dict[str, Any] = {"expected_subjects": summary_subjects}
        error_message = None

        try:
            response_lower = response.lower()

            matched_subjects = [s for s in summary_subjects if s.lower() in response_lower]
            has_summary_keyword = any(
                kw in response_lower
                for kw in ("summary", "summarize", "here are", "overview", "below are")
            )

            validation_details["matched_subjects"] = matched_subjects
            validation_details["matched_count"] = len(matched_subjects)
            validation_details["has_summary_keyword"] = has_summary_keyword

            if len(matched_subjects) >= 3 and has_summary_keyword:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if len(matched_subjects) < 3:
                    missing_parts.append(
                        f"at least 3 seeded email subjects (found {len(matched_subjects)}: {matched_subjects})"
                    )
                if not has_summary_keyword:
                    missing_parts.append("summary keyword ('summary', 'here are', 'overview')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

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
