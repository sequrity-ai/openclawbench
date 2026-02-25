"""Gmail benchmark scenario.

Architecture:
    This scenario uses TWO separate Gmail accounts for realistic testing:

    1. Bot's Gmail Account: Configured in OpenClaw via the `gog` skill.
       The bot reads, sends, and manages emails using this account.

    2. Benchmark Gmail Account: A separate account with OAuth2 credentials
       used by the benchmark harness to send test emails and validate results.

Tasks (9):
    Easy:
       - Task 1 (Email Search): Find the most recent '[BENCHMARK TEST] Project Alpha Updates' email
       - Task 2 (Email Send): Send a test email to the benchmark address
       - Task 3 (Email Data Extraction): Find '[BENCHMARK TEST] Invoice' email and extract the amount

    Medium:
       - Task 4 (Count Unread): How many unread emails do I have?
       - Task 5 (Search by Sender): Find emails from support@example.com
       - Task 6 (Label Management): Create a label called 'Important Projects'

    Hard:
       - Task 7 (Email with Attachment): Find emails with PDF attachments from last week
       - Task 8 (Draft Email): Draft an email to team@example.com about Q1 results
       - Task 9 (Email Summary): Summarize the last 5 emails in my inbox

Setup:
    Sends 3 benchmark test emails to the bot's inbox (project update, invoice, newsletter)
    so that Tasks 1 and 3 have real data to find. Cleanup closes seeded issues/emails.

Required Skills:
    gog (Gmail skill)

Config:
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN — bot's Gmail OAuth
    GMAIL_BENCHMARK_EMAIL — benchmark account address (sends/receives test emails)
    GMAIL_BOT_EMAIL — bot's Gmail address
"""

import logging
import secrets
import time

from benchmarks.base import (
    BenchmarkTask,
    CheckStatus,
    HealthCheckResult,
    ScenarioBase,
    SetupResult,
)
from benchmarks.setup.gmail_setup import GmailSetup
from benchmarks.skill_checker import check_skills
from benchmarks.validators.gmail_validator import GmailValidator

logger = logging.getLogger(__name__)


class GmailScenario(ScenarioBase):
    """Benchmark scenario for Gmail email capabilities."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        benchmark_email: str,
        bot_email: str,
        remote_manager=None,
    ):
        """Initialize Gmail scenario.

        Args:
            client_id: OAuth2 client ID for the BENCHMARK Gmail account
            client_secret: OAuth2 client secret for the BENCHMARK Gmail account
            refresh_token: OAuth2 refresh token for the BENCHMARK Gmail account
            benchmark_email: Benchmark's Gmail address (has OAuth2 credentials)
            bot_email: Bot's Gmail address (configured in OpenClaw)
            remote_manager: Optional RemoteWorkspaceManager for remote validation

        Note:
            - OAuth credentials are for the benchmark's Gmail account
            - Benchmark sends test emails TO bot_email
            - Bot sends test emails TO benchmark_email
            - Validation checks benchmark's inbox for emails FROM bot
        """
        super().__init__(
            name="Gmail Email",
            description="Tests agent's ability to search, send, and parse emails via Gmail",
            required_skills=["gog"],
        )

        self.gmail_setup = GmailSetup(client_id, client_secret, refresh_token)
        self.validator = GmailValidator()
        self.benchmark_email = benchmark_email
        self.bot_email = bot_email
        self.remote_manager = remote_manager
        self.setup_data = {}

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 9 Gmail tasks with progressive complexity."""

        # Task 1: Email Search - Find specific email by subject
        self.add_task(
            BenchmarkTask(
                name="Email Search",
                prompt=(
                    "Search my Gmail inbox for the MOST RECENT email with the subject "
                    "'[BENCHMARK TEST] Project Alpha Updates'. "
                    "Tell me what the subject is and the confirmation code from the email body."
                ),
                expected_output_description="Bot finds and reports the email subject and confirmation code",
                validation_fn=self.validator.validate_email_search,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "email_search"},
            )
        )

        # Task 2: Email Send - Bot sends email to benchmark account
        self.add_task(
            BenchmarkTask(
                name="Email Send",
                prompt=(
                    f"Send an email to {self.benchmark_email} with the subject "
                    "'[BENCHMARK TEST] Automated Test Email' and body "
                    "'This is an automated test email from the OpenClaw bot. "
                    "Please disregard.'"
                ),
                expected_output_description="Email sent successfully to benchmark account",
                validation_fn=self.validator.validate_email_send,
                timeout=90.0,
                metadata={"difficulty": "easy", "category": "email_send"},
            )
        )

        # Task 3: Email Parsing - Extract data from email
        self.add_task(
            BenchmarkTask(
                name="Email Data Extraction",
                prompt=(
                    "Find the MOST RECENT email with subject starting with '[BENCHMARK TEST] Invoice'. "
                    "Extract and tell me the following information: "
                    "invoice number, total amount, and due date."
                ),
                expected_output_description="Bot extracts invoice number, amount, and due date from latest invoice email",
                validation_fn=self.validator.validate_email_parsing,
                timeout=90.0,
                metadata={"difficulty": "easy", "category": "email_parsing"},
            )
        )

        # Task 4: Count Unread - Report how many unread emails exist
        self.add_task(
            BenchmarkTask(
                name="Count Unread",
                prompt="How many unread emails do I have?",
                expected_output_description="Bot reports the number of unread emails in the inbox",
                validation_fn=self.validator.validate_count_unread,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "email_count"},
            )
        )

        # Task 5: Search by Sender - Find the seeded support email by subject
        self.add_task(
            BenchmarkTask(
                name="Search by Sender",
                prompt=(
                    "Search my Gmail inbox for the email with subject "
                    "'[BENCHMARK TEST] Support Request'. "
                    "Tell me who it appears to be from and what the subject line is."
                ),
                expected_output_description="Bot finds and reports the support request email subject",
                validation_fn=self.validator.validate_search_by_sender,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "email_search"},
            )
        )

        # Task 6: Label Management - Create a new label
        self.add_task(
            BenchmarkTask(
                name="Label Management",
                prompt="Create a label called 'Important Projects'",
                expected_output_description="Bot creates the Gmail label 'Important Projects' and confirms creation",
                validation_fn=self.validator.validate_label_management,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "label_management"},
            )
        )

        # Task 7: Email with Attachment - Find PDF emails from last week
        self.add_task(
            BenchmarkTask(
                name="Email with Attachment",
                prompt="Find emails with PDF attachments from last week",
                expected_output_description="Bot finds and reports emails that contain PDF attachments from the past week",
                validation_fn=self.validator.validate_email_with_attachment,
                timeout=90.0,
                metadata={"difficulty": "hard", "category": "email_search"},
            )
        )

        # Task 8: Draft Email - Compose a draft to team@example.com
        self.add_task(
            BenchmarkTask(
                name="Draft Email",
                prompt="Draft an email to team@example.com about Q1 results",
                expected_output_description="Bot drafts (saves as draft) an email to team@example.com regarding Q1 results",
                validation_fn=self.validator.validate_draft_email,
                timeout=90.0,
                metadata={"difficulty": "hard", "category": "email_draft"},
            )
        )

        # Task 9: Email Summary - Summarize the last 5 inbox emails
        self.add_task(
            BenchmarkTask(
                name="Email Summary",
                prompt="Summarize the last 5 emails in my inbox",
                expected_output_description="Bot retrieves and summarizes the 5 most recent inbox emails",
                validation_fn=self.validator.validate_email_summary,
                timeout=120.0,
                metadata={"difficulty": "hard", "category": "email_summary"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        local_mode = self.remote_manager is None
        checks = check_skills(self.required_skills, local_mode=local_mode, remote_manager=self.remote_manager)

        # CRITICAL: Check OpenAI API key (required for AI agent)
        checks.append(self._check_openai_api_key())

        # Check Gmail API access
        if self.gmail_setup.verify_api_access():
            checks.append(
                HealthCheckResult(
                    check_name="Gmail API Access (Benchmark)",
                    status=CheckStatus.PASS,
                    message="Gmail API is accessible with provided credentials",
                    details={"base_url": self.gmail_setup.BASE_URL},
                )
            )
        else:
            checks.append(
                HealthCheckResult(
                    check_name="Gmail API Access (Benchmark)",
                    status=CheckStatus.FAIL,
                    message="Cannot access Gmail API - check OAuth2 credentials (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN)",
                    details={
                        "base_url": self.gmail_setup.BASE_URL,
                        "error": "Gmail scenario requires OAuth2 credentials for validation",
                        "fix": "Configure Google OAuth2 credentials in .env file",
                    },
                )
            )

        return checks

    def setup(self) -> SetupResult:
        """Set up the Gmail scenario by sending test emails.

        Returns:
            Setup result with test email metadata
        """
        try:
            logger.info("Setting up Gmail benchmark - sending test emails...")

            # Generate unique identifiers to avoid conflicts and ensure fresh data
            test_id = secrets.token_hex(4)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            random_number = secrets.randbelow(10000)

            # Task 1: Send searchable email TO BOT with random content
            search_subject = "[BENCHMARK TEST] Project Alpha Updates"
            search_random_code = f"CODE-{secrets.token_hex(3).upper()}"
            search_email_id = self.gmail_setup.send_test_email(
                to=self.bot_email,
                subject=search_subject,
                body=(
                    "This is a test email for the OpenClaw benchmark.\n\n"
                    "Project Alpha Status:\n"
                    "- Phase 1: Completed\n"
                    "- Phase 2: In Progress\n"
                    "- Phase 3: Planned\n\n"
                    f"Confirmation Code: {search_random_code}\n"
                    f"Timestamp: {timestamp}\n"
                    f"Test ID: {test_id}"
                ),
            )

            # Task 3: Send email with structured data to parse TO BOT
            # Use random invoice number and amount to prevent caching
            invoice_num = random_number
            invoice_amount = f"${random_number + 500:,}.00"
            parsing_subject = f"[BENCHMARK TEST] Invoice #{invoice_num}"
            parsing_data = {
                "invoice_number": f"INV-{invoice_num}",
                "total_amount": invoice_amount,
                "due_date": "2026-03-15",
                "confirmation_code": search_random_code,  # Link to Task 1
            }
            parsing_email_id = self.gmail_setup.send_test_email(
                to=self.bot_email,
                subject=parsing_subject,
                body=(
                    "Thank you for your business!\n\n"
                    "Invoice Details:\n"
                    f"Invoice Number: {parsing_data['invoice_number']}\n"
                    f"Total Amount: {parsing_data['total_amount']}\n"
                    f"Due Date: {parsing_data['due_date']}\n\n"
                    "Please remit payment by the due date.\n\n"
                    f"Timestamp: {timestamp}\n"
                    f"Test ID: {test_id}"
                ),
            )

            # Task 5: Send email FROM support@example.com address (spoofed sender display name)
            # We send it with the benchmark account but label the from field so the bot can find it
            sender_search_subject = "[BENCHMARK TEST] Support Request"
            sender_email_id = self.gmail_setup.send_test_email(
                to=self.bot_email,
                subject=sender_search_subject,
                body=(
                    "Hello,\n\n"
                    "This is a test support request for the OpenClaw benchmark.\n\n"
                    "Please note this email was sent as part of an automated test.\n\n"
                    f"From: support@example.com\n"
                    f"Test ID: {test_id}\n"
                    f"Timestamp: {timestamp}"
                ),
                from_display_name="support@example.com",
            )

            # Task 7: Send email with a simulated PDF attachment notice TO BOT
            attachment_subject = "[BENCHMARK TEST] Q4 Financial Report"
            attachment_email_id = self.gmail_setup.send_test_email(
                to=self.bot_email,
                subject=attachment_subject,
                body=(
                    "Please find attached the Q4 Financial Report.\n\n"
                    "Attachment: Q4_Financial_Report.pdf\n"
                    "File size: 2.4 MB\n"
                    "Type: PDF document\n\n"
                    "This report contains a summary of Q4 performance metrics.\n\n"
                    f"Test ID: {test_id}\n"
                    f"Timestamp: {timestamp}"
                ),
            )

            # Tasks 9: Send 5 summary seed emails TO BOT so there is content to summarize
            summary_subjects = []
            summary_email_ids = []
            summary_topics = [
                ("Team Meeting Notes", "Notes from today's standup: discussed sprint progress and blockers."),
                ("Budget Approval", "Your budget request for Q2 has been approved. See attached breakdown."),
                ("New Feature Release", "Version 2.3 is now live. Key changes: improved search and dark mode."),
                ("Customer Feedback", "We received positive feedback from Acme Corp regarding the new dashboard."),
                ("Action Items", "Following up on action items from last week's review. Deadline is Friday."),
            ]
            for topic_subject, topic_body in summary_topics:
                full_subject = f"[BENCHMARK TEST] {topic_subject}"
                summary_subjects.append(full_subject)
                eid = self.gmail_setup.send_test_email(
                    to=self.bot_email,
                    subject=full_subject,
                    body=(
                        f"{topic_body}\n\n"
                        f"Test ID: {test_id}\n"
                        f"Timestamp: {timestamp}"
                    ),
                )
                summary_email_ids.append(eid)

            # Wait a moment for emails to propagate
            logger.info("Waiting 3 seconds for Gmail to index emails...")
            time.sleep(3)

            # Store setup data for validation
            self.setup_data = {
                "test_id": test_id,
                # Task 1
                "search_subject": search_subject,
                "search_email_id": search_email_id,
                # Task 2
                "send_subject": "[BENCHMARK TEST] Automated Test Email",
                "benchmark_email": self.benchmark_email,
                "bot_email": self.bot_email,
                # Task 3
                "parsing_subject": parsing_subject,
                "parsing_email_id": parsing_email_id,
                "expected_extracted_data": parsing_data,
                # Task 4 (no pre-seeded data needed — bot queries live unread count)
                # Task 5
                "sender_search_email": "support@example.com",
                "sender_search_subject": sender_search_subject,
                "sender_email_id": sender_email_id,
                # Task 6 (no pre-seeded data — bot creates the label on demand)
                "new_label_name": "Important Projects",
                # Task 7
                "attachment_email_subject": attachment_subject,
                "attachment_email_id": attachment_email_id,
                # Task 8 (no pre-seeded data — bot creates the draft on demand)
                "draft_recipient": "team@example.com",
                # Task 9
                "summary_email_subjects": summary_subjects,
                "summary_email_ids": summary_email_ids,
                # Shared
                "gmail_setup": self.gmail_setup,  # Pass for validation
            }

            total_sent = len(self.gmail_setup.test_email_ids)
            logger.info(f"Setup complete - sent {total_sent} test emails")
            logger.info(f"  - Search email: {search_subject} (ID: {search_email_id})")
            logger.info(f"  - Parsing email: {parsing_subject} (ID: {parsing_email_id})")
            logger.info(f"  - Sender search email: {sender_search_subject} (ID: {sender_email_id})")
            logger.info(f"  - Attachment email: {attachment_subject} (ID: {attachment_email_id})")
            logger.info(f"  - Summary seed emails: {len(summary_email_ids)} sent")

            return SetupResult(
                status=CheckStatus.PASS,
                message="Gmail test emails created successfully",
                setup_data=self.setup_data,
            )

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return SetupResult(
                status=CheckStatus.FAIL,
                message=f"Failed to create test emails: {str(e)}",
                error=str(e),
            )

    def cleanup(self) -> bool:
        """Clean up the Gmail scenario by deleting test emails and labels.

        Returns:
            True if cleanup succeeded
        """
        try:
            logger.info("Cleaning up Gmail test emails...")
            deleted_count = self.gmail_setup.cleanup_test_emails()
            logger.info(f"Cleaned up {deleted_count} test emails successfully")

            # Delete the 'Important Projects' label created by Task 6 so the next
            # run starts clean and the bot can create it fresh (not find it pre-existing)
            label_name = self.setup_data.get("new_label_name", "Important Projects")
            try:
                deleted = self.gmail_setup.delete_label_by_name(label_name)
                if deleted:
                    logger.info(f"Deleted label '{label_name}' from prior run")
            except Exception as e:
                logger.warning(f"Could not delete label '{label_name}': {e}")

            return True
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return False
