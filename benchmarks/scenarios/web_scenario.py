"""Web research benchmark scenario."""

import logging

from benchmarks.base import (
    BenchmarkTask,
    CheckStatus,
    HealthCheckResult,
    ScenarioBase,
    SetupResult,
)
from benchmarks.setup.web_setup import WebSetup
from benchmarks.skill_checker import check_skills
from benchmarks.validators.web_validator import WebValidator

logger = logging.getLogger(__name__)


class WebScenario(ScenarioBase):
    """Benchmark scenario for web research capabilities."""

    def __init__(self):
        """Initialize web research scenario."""
        super().__init__(
            name="Web Research",
            description="Tests agent's ability to browse web pages, extract information, and cite sources",
            required_skills=[],  # Uses built-in web_search/web_fetch/browser tools
        )

        self.web_setup = WebSetup()
        self.validator = WebValidator()

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 3 web research tasks."""

        # Task 1: Factual Extraction
        self.add_task(
            BenchmarkTask(
                name="Factual Extraction",
                prompt=(
                    f"Go to {self.web_setup.wikipedia_url} and tell me: "
                    "1) The exact year Python was first released. "
                    "2) The full name of its creator. "
                    "Give me specific facts, not general statements."
                ),
                expected_output_description="Year 1991 and Guido van Rossum",
                validation_fn=self.validator.validate_factual_extraction,
                timeout=90.0,
                metadata={"difficulty": "low", "category": "factual_extraction"},
            )
        )

        # Task 2: Repository Analysis
        self.add_task(
            BenchmarkTask(
                name="Repository Analysis",
                prompt=(
                    f"Analyze the GitHub repository at {self.web_setup.github_repo_url}. "
                    "Tell me: 1) What organization owns it, 2) What is its main purpose, "
                    "and 3) What programming language or format are the examples in."
                ),
                expected_output_description="Anthropic-owned cookbook with code examples/notebooks",
                validation_fn=self.validator.validate_repo_analysis,
                timeout=90.0,
                metadata={"difficulty": "medium", "category": "code_analysis"},
            )
        )

        # Task 3: Multi-Source Research
        self.add_task(
            BenchmarkTask(
                name="Multi-Source Research",
                prompt=(
                    f"Research '{self.web_setup.search_topic}' and give me 3 popular Python web "
                    "frameworks. For each one, provide: the framework name, a one-sentence description, "
                    "and a source URL where you found the information."
                ),
                expected_output_description="3 Python web frameworks (e.g. Django, Flask, FastAPI) with URLs",
                validation_fn=self.validator.validate_multi_source_research,
                timeout=120.0,
                metadata={"difficulty": "medium", "category": "research_synthesis"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        checks = check_skills(self.required_skills)

        # Check URL accessibility
        accessible, message = self.web_setup.verify_urls_accessible()
        status = CheckStatus.PASS if accessible else CheckStatus.FAIL
        checks.append(
            HealthCheckResult(
                check_name="URL Accessibility",
                status=status,
                message=message,
                details={
                    "wikipedia_url": self.web_setup.wikipedia_url,
                    "github_url": self.web_setup.github_repo_url,
                },
            )
        )

        return checks

    def setup(self) -> SetupResult:
        """Set up the web research scenario.

        Returns:
            Setup result with test URLs
        """
        try:
            logger.info("Preparing test URLs and topics...")
            setup_data = self.web_setup.prepare_test_urls()

            logger.info(f"Test URLs prepared:")
            logger.info(f"  - Wikipedia: {setup_data['wikipedia_url']}")
            logger.info(f"  - GitHub: {setup_data['github_repo_url']}")
            logger.info(f"  - Research topic: {setup_data['search_topic']}")

            return SetupResult(
                status=CheckStatus.PASS,
                message="Web research URLs prepared successfully",
                setup_data=setup_data,
            )

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return SetupResult(
                status=CheckStatus.FAIL,
                message=f"Failed to prepare URLs: {str(e)}",
                error=str(e),
            )

    def cleanup(self) -> bool:
        """Clean up the web research scenario.

        Returns:
            True (no cleanup needed for web research)
        """
        logger.info("No cleanup needed for web research scenario")
        return True
