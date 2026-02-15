"""GitHub benchmark scenario.

Architecture:
    This scenario uses a test GitHub repository for benchmark validation.

    Similar to Gmail, this requires:
    1. Bot's GitHub Account: Configured in OpenClaw via steipete/github skill
    2. Benchmark GitHub Account: With personal access token for validation

    Task Flow:
       - Task 1: Create a test issue
       - Task 2: List open issues
       - Task 3: Get repository information
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
from benchmarks.setup.github_setup import GitHubSetup
from benchmarks.skill_checker import check_skills
from benchmarks.validators.github_validator import GitHubValidator

logger = logging.getLogger(__name__)


class GitHubScenario(ScenarioBase):
    """Benchmark scenario for GitHub operations."""

    def __init__(self, github_token: str, test_repo_owner: str, test_repo_name: str):
        """Initialize GitHub scenario.

        Args:
            github_token: Personal access token for benchmark GitHub account
            test_repo_owner: Owner of test repository
            test_repo_name: Name of test repository

        Note:
            - Requires bot to have steipete/github skill installed
            - Benchmark creates/closes issues in test repo for validation
        """
        super().__init__(
            name="GitHub",
            description="Tests agent's ability to interact with GitHub repos, issues, and PRs",
            required_skills=["steipete/github"],
        )

        self.github_setup = GitHubSetup(github_token)
        self.validator = GitHubValidator()
        self.test_repo_owner = test_repo_owner
        self.test_repo_name = test_repo_name
        self.setup_data = {}

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 3 GitHub tasks."""

        # Task 1: Create Issue
        self.add_task(
            BenchmarkTask(
                name="Issue Creation",
                prompt=(
                    f"Create a new issue in the repository {self.test_repo_owner}/{self.test_repo_name} "
                    f"with the title '[BENCHMARK TEST] Test Issue' and body 'This is a test issue created by the benchmark.'"
                ),
                expected_output_description="Bot creates issue and reports success",
                validation_fn=self.validator.validate_issue_creation,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "issue_create"},
            )
        )

        # Task 2: List Issues
        self.add_task(
            BenchmarkTask(
                name="List Issues",
                prompt=(
                    f"List all open issues in the repository {self.test_repo_owner}/{self.test_repo_name}. "
                    f"Show me the issue titles."
                ),
                expected_output_description="Bot lists open issues",
                validation_fn=self.validator.validate_issue_list,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "issue_list"},
            )
        )

        # Task 3: Repository Info
        self.add_task(
            BenchmarkTask(
                name="Repository Info",
                prompt=(
                    f"Get information about the repository {self.test_repo_owner}/{self.test_repo_name}. "
                    f"Tell me the description, number of stars, and number of forks."
                ),
                expected_output_description="Bot provides repository metadata",
                validation_fn=self.validator.validate_repo_info,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "repo_info"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        checks = check_skills(self.required_skills)

        # Check GitHub API access
        if self.github_setup.verify_api_access(self.test_repo_owner, self.test_repo_name):
            checks.append(
                HealthCheckResult(
                    check_name="GitHub API Access",
                    status=CheckStatus.PASS,
                    message=f"GitHub API is accessible for {self.test_repo_owner}/{self.test_repo_name}",
                    details={"test_repo": f"{self.test_repo_owner}/{self.test_repo_name}"},
                )
            )
        else:
            checks.append(
                HealthCheckResult(
                    check_name="GitHub API Access",
                    status=CheckStatus.FAIL,
                    message="Cannot access GitHub API - check personal access token and repository permissions",
                    details={"test_repo": f"{self.test_repo_owner}/{self.test_repo_name}"},
                )
            )

        return checks

    def setup(self) -> SetupResult:
        """Set up the GitHub scenario.

        Returns:
            Setup result with test data
        """
        try:
            logger.info("Setting up GitHub benchmark...")

            # Generate unique identifier for this test run
            test_id = secrets.token_hex(4)

            # Store setup data for validation
            self.setup_data = {
                "test_id": test_id,
                "issue_title": "[BENCHMARK TEST] Test Issue",
                "repo_owner": self.test_repo_owner,
                "repo_name": self.test_repo_name,
                "github_setup": self.github_setup,  # Pass for validation
            }

            logger.info(f"Setup complete for {self.test_repo_owner}/{self.test_repo_name}")

            return SetupResult(
                status=CheckStatus.PASS,
                message="GitHub scenario configured successfully",
                setup_data=self.setup_data,
            )

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return SetupResult(
                status=CheckStatus.FAIL,
                message=f"Failed to set up GitHub scenario: {str(e)}",
                error=str(e),
            )

    def cleanup(self) -> bool:
        """Clean up the GitHub scenario by closing test issues.

        Returns:
            True if cleanup succeeded
        """
        try:
            logger.info("Cleaning up GitHub test issues...")
            closed_count = self.github_setup.cleanup_test_issues(self.test_repo_owner, self.test_repo_name)
            logger.info(f"Cleaned up {closed_count} test issues successfully")
            return True
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return False
