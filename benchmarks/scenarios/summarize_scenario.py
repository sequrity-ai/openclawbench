"""Summarize benchmark scenario.

Architecture:
    This scenario tests the bot's ability to summarize content from various sources
    using the steipete/summarize skill. No API keys required.

    Task Flow:
       - Task 1: Summarize a web article
       - Task 2: Summarize a YouTube video
       - Task 3: Compare summaries from multiple sources
"""

import logging

from benchmarks.base import (
    BenchmarkTask,
    CheckStatus,
    HealthCheckResult,
    ScenarioBase,
    SetupResult,
)
from benchmarks.skill_checker import check_skills
from benchmarks.validators.summarize_validator import SummarizeValidator

logger = logging.getLogger(__name__)


class SummarizeScenario(ScenarioBase):
    """Benchmark scenario for content summarization."""

    def __init__(self, remote_manager=None):
        """Initialize Summarize scenario.

        Args:
            remote_manager: Optional RemoteWorkspaceManager (not used for summarize)

        Note:
            - Requires the steipete/summarize skill to be installed
            - No API keys required
        """
        super().__init__(
            name="Summarize",
            description="Tests agent's ability to summarize content from web, PDFs, videos",
            required_skills=["steipete/summarize"],
        )

        self.validator = SummarizeValidator()
        self.setup_data = {}

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 3 Summarize tasks."""

        # Task 1: Web Article Summary
        self.add_task(
            BenchmarkTask(
                name="URL Summary",
                prompt="Can you summarize this article for me? https://en.wikipedia.org/wiki/Python_(programming_language)",
                expected_output_description="Bot provides a concise summary of the Python Wikipedia article",
                validation_fn=self.validator.validate_url_summary,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "url_summary"},
            )
        )

        # Task 2: YouTube Video Summary
        self.add_task(
            BenchmarkTask(
                name="YouTube Summary",
                prompt="Summarize this YouTube video: https://www.youtube.com/watch?v=x7X9w_GIm1s (Python in 100 Seconds)",
                expected_output_description="Bot summarizes the YouTube video content",
                validation_fn=self.validator.validate_youtube_summary,
                timeout=90.0,
                metadata={"difficulty": "easy", "category": "video_summary"},
            )
        )

        # Task 3: Multiple Source Comparison
        self.add_task(
            BenchmarkTask(
                name="Comparison Summary",
                prompt=(
                    "Compare and summarize these two articles about Python: "
                    "1) https://en.wikipedia.org/wiki/Python_(programming_language) "
                    "2) https://www.python.org/about/ "
                    "What are the key differences in how they describe Python?"
                ),
                expected_output_description="Bot compares and contrasts summaries from both sources",
                validation_fn=self.validator.validate_comparison_summary,
                timeout=120.0,
                metadata={"difficulty": "easy", "category": "comparison_summary"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        # Check for summarize skill
        checks = check_skills(self.required_skills)

        checks.append(
            HealthCheckResult(
                check_name="Summarize API Note",
                status=CheckStatus.PASS,
                message="Summarize skill requires no API key configuration",
                details={"required_skill": "steipete/summarize"},
            )
        )

        return checks

    def setup(self) -> SetupResult:
        """Set up the Summarize scenario.

        Returns:
            Setup result with expected validation data
        """
        try:
            logger.info("Setting up Summarize benchmark...")

            # Store expected data for validation
            self.setup_data = {
                # No specific setup data needed - URLs are in task prompts
            }

            logger.info("Setup complete - validation criteria configured")

            return SetupResult(
                status=CheckStatus.PASS,
                message="Summarize scenario configured successfully",
                setup_data=self.setup_data,
            )

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return SetupResult(
                status=CheckStatus.FAIL,
                message=f"Failed to set up Summarize scenario: {str(e)}",
                error=str(e),
            )

    def cleanup(self) -> bool:
        """Clean up the Summarize scenario.

        Returns:
            True (no cleanup needed for summarization)
        """
        logger.info("Summarize scenario cleanup (no action needed)")
        return True
