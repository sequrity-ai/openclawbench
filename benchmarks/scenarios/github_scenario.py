"""GitHub skill benchmark scenario."""

import logging

from benchmarks.base import (
    BenchmarkTask,
    HealthCheckResult,
    ScenarioBase,
    SetupResult,
    CheckStatus,
)
from benchmarks.skill_checker import check_skills
from benchmarks.validators.github_validator import GitHubValidator

logger = logging.getLogger(__name__)


class GitHubScenario(ScenarioBase):
    """Benchmark scenario for the GitHub skill (gh CLI)."""

    def __init__(self):
        super().__init__(
            name="GitHub",
            description="Tests the GitHub skill: repository info and issue listing via gh CLI",
            required_skills=["github"],
        )

        self.validator = GitHubValidator()
        self.test_repo = "anthropics/anthropic-cookbook"
        self._define_tasks()

    def _define_tasks(self) -> None:
        self.add_task(
            BenchmarkTask(
                name="Repo Info",
                prompt=(
                    f"Use the GitHub CLI to get info about the {self.test_repo} repository. "
                    "Tell me the description, star count, and primary language."
                ),
                expected_output_description="Repo description, star count, and primary language",
                validation_fn=self.validator.validate_repo_info,
                timeout=60.0,
            )
        )

        self.add_task(
            BenchmarkTask(
                name="List Issues",
                prompt=(
                    f"Use the GitHub CLI to list the 3 most recent open issues from the "
                    f"{self.test_repo} repository. Include issue numbers and titles."
                ),
                expected_output_description="3 recent issues with #numbers and titles",
                validation_fn=self.validator.validate_list_issues,
                timeout=60.0,
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        return check_skills(self.required_skills)

    def setup(self) -> SetupResult:
        return SetupResult(
            status=CheckStatus.PASS,
            message="No setup needed for GitHub scenario",
            setup_data={"test_repo": self.test_repo},
        )

    def cleanup(self) -> bool:
        return True
