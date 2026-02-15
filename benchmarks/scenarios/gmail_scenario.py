"""Gmail benchmark scenario.

Architecture:
    This scenario uses TWO separate Gmail accounts for realistic testing:

    1. Bot's Gmail Account (e.g., openclaw-bot@gmail.com):
       - Configured in OpenClaw via the `gmail` skill
       - Bot reads emails sent to this account
       - Bot sends emails from this account

    2. Benchmark Gmail Account (e.g., openclaw-benchmark@gmail.com):
       - Separate Gmail account with OAuth2 credentials
       - Benchmark sends test emails FROM this account TO the bot
       - Benchmark receives test emails FROM the bot
       - Used to validate bot's email operations

    Task Flow:
       - Task 1 (Search): Benchmark sends email to bot → bot searches its inbox
       - Task 2 (Send): Bot sends email to benchmark → validate in benchmark's inbox
       - Task 3 (Parse): Benchmark sends email to bot → bot extracts data

    This two-account design mirrors real-world email communication between parties.
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
    ):
        """Initialize Gmail scenario.

        Args:
            client_id: OAuth2 client ID for the BENCHMARK Gmail account
            client_secret: OAuth2 client secret for the BENCHMARK Gmail account
            refresh_token: OAuth2 refresh token for the BENCHMARK Gmail account
            benchmark_email: Benchmark's Gmail address (has OAuth2 credentials)
            bot_email: Bot's Gmail address (configured in OpenClaw)

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
        self.setup_data = {}

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 3 Gmail tasks with progressive complexity."""

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

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        checks = check_skills(self.required_skills)

        # Check Gmail API access
        if self.gmail_setup.verify_api_access():
            checks.append(
                HealthCheckResult(
                    check_name="Gmail API Access",
                    status=CheckStatus.PASS,
                    message="Gmail API is accessible with provided credentials",
                    details={"base_url": self.gmail_setup.BASE_URL},
                )
            )
        else:
            checks.append(
                HealthCheckResult(
                    check_name="Gmail API Access",
                    status=CheckStatus.FAIL,
                    message="Cannot access Gmail API - check OAuth2 credentials",
                    details={"base_url": self.gmail_setup.BASE_URL},
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
            search_subject = f"[BENCHMARK TEST] Project Alpha Updates"
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

            # Wait a moment for emails to propagate
            logger.info("Waiting 3 seconds for Gmail to index emails...")
            time.sleep(3)

            # Store setup data for validation
            self.setup_data = {
                "test_id": test_id,
                "search_subject": search_subject,
                "search_email_id": search_email_id,
                "send_subject": "[BENCHMARK TEST] Automated Test Email",
                "benchmark_email": self.benchmark_email,
                "bot_email": self.bot_email,
                "parsing_subject": parsing_subject,
                "parsing_email_id": parsing_email_id,
                "expected_extracted_data": parsing_data,
                "gmail_setup": self.gmail_setup,  # Pass for validation
            }

            logger.info(f"Setup complete - sent {len(self.gmail_setup.test_email_ids)} test emails")
            logger.info(f"  - Search email: {search_subject} (ID: {search_email_id})")
            logger.info(f"  - Parsing email: {parsing_subject} (ID: {parsing_email_id})")

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
        """Clean up the Gmail scenario by deleting test emails.

        Returns:
            True if cleanup succeeded
        """
        try:
            logger.info("Cleaning up Gmail test emails...")
            deleted_count = self.gmail_setup.cleanup_test_emails()
            logger.info(f"Cleaned up {deleted_count} test emails successfully")
            return True
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return False
