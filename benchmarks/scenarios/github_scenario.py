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

    def __init__(self, github_token: str, test_repo_owner: str, test_repo_name: str, remote_manager=None):
        """Initialize GitHub scenario.

        Args:
            github_token: Personal access token for benchmark GitHub account
            test_repo_owner: Owner of test repository
            test_repo_name: Name of test repository
            remote_manager: Optional RemoteWorkspaceManager for remote validation

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
        self.remote_manager = remote_manager
        self.setup_data = {}

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 9 GitHub tasks."""

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

        # Task 4: Recent Commits
        self.add_task(
            BenchmarkTask(
                name="Recent Commits",
                prompt=(
                    f"Show me the last 5 commits in the repository {self.test_repo_owner}/{self.test_repo_name}."
                ),
                expected_output_description="Bot lists the 5 most recent commits with messages and authors",
                validation_fn=self.validator.validate_recent_commits,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "commits"},
            )
        )

        # Task 5: Pull Request List
        self.add_task(
            BenchmarkTask(
                name="Pull Request List",
                prompt=(
                    f"List all open pull requests in the repository {self.test_repo_owner}/{self.test_repo_name}."
                ),
                expected_output_description="Bot lists all open pull requests",
                validation_fn=self.validator.validate_pull_request_list,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "pull_requests"},
            )
        )

        # Task 6: Issue Labels
        self.add_task(
            BenchmarkTask(
                name="Issue Labels",
                prompt=(
                    f"What labels are available in the repository {self.test_repo_owner}/{self.test_repo_name}?"
                ),
                expected_output_description="Bot lists all available labels in the repository",
                validation_fn=self.validator.validate_issue_labels,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "labels"},
            )
        )

        # Task 7: Contributor Stats
        self.add_task(
            BenchmarkTask(
                name="Contributor Stats",
                prompt=(
                    f"Who are the top 3 contributors to the repository {self.test_repo_owner}/{self.test_repo_name}?"
                ),
                expected_output_description="Bot identifies the top 3 contributors with commit counts",
                validation_fn=self.validator.validate_contributor_stats,
                timeout=90.0,
                metadata={"difficulty": "hard", "category": "contributors"},
            )
        )

        # Task 8: File Contents (replaces Code Search which has GitHub search index delay)
        self.add_task(
            BenchmarkTask(
                name="File Contents",
                prompt=(
                    f"Get the contents of the file `src/utils.js` in the repository "
                    f"{self.test_repo_owner}/{self.test_repo_name}. "
                    f"What functions does it define?"
                ),
                expected_output_description="Bot retrieves and displays the file contents, identifying the async functions defined in it",
                validation_fn=self.validator.validate_file_contents,
                timeout=90.0,
                metadata={"difficulty": "hard", "category": "file_contents"},
            )
        )

        # Task 9: Release Info
        self.add_task(
            BenchmarkTask(
                name="Release Info",
                prompt=(
                    f"What was the latest release in the repository {self.test_repo_owner}/{self.test_repo_name} and when was it published?"
                ),
                expected_output_description="Bot provides the latest release tag name and publication date",
                validation_fn=self.validator.validate_release_info,
                timeout=90.0,
                metadata={"difficulty": "hard", "category": "releases"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        local_mode = self.remote_manager is None
        checks = check_skills(self.required_skills, local_mode=local_mode, remote_manager=self.remote_manager)

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

            # Seed the repo with commits, a PR branch, and a release
            logger.info(f"Seeding repository {self.test_repo_owner}/{self.test_repo_name}...")
            seed_info = self.github_setup.seed_repo_data(self.test_repo_owner, self.test_repo_name)
            logger.info(f"Seeding complete: {seed_info}")

            # Store setup data for validation
            self.setup_data = {
                "test_id": test_id,
                "issue_title": "[BENCHMARK TEST] Test Issue",
                "repo_owner": self.test_repo_owner,
                "repo_name": self.test_repo_name,
                "github_setup": self.github_setup,  # Pass for validation
                "seed_info": seed_info,
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
        """Clean up the GitHub scenario by closing test issues and removing seeded data.

        Returns:
            True if cleanup succeeded
        """
        try:
            logger.info("Cleaning up GitHub test issues...")
            closed_count = self.github_setup.cleanup_test_issues(self.test_repo_owner, self.test_repo_name)
            logger.info(f"Cleaned up {closed_count} test issues successfully")

            logger.info("Cleaning up seeded repository data...")
            self.github_setup.cleanup_seeded_data(self.test_repo_owner, self.test_repo_name)
            logger.info("Seeded data cleanup complete")
            return True
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return False
