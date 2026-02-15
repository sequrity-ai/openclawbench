"""File manipulation benchmark scenario."""

import logging

from benchmarks.base import (
    BenchmarkTask,
    CheckStatus,
    HealthCheckResult,
    ScenarioBase,
    SetupResult,
)
from benchmarks.setup.file_setup import FileSetup
from benchmarks.skill_checker import check_skills
from benchmarks.validators.file_validator import FileValidator

logger = logging.getLogger(__name__)


class FileScenario(ScenarioBase):
    """Benchmark scenario for file manipulation capabilities."""

    def __init__(self, remote_manager=None):
        """Initialize file manipulation scenario.

        Args:
            remote_manager: Optional RemoteWorkspaceManager for remote setup/validation
        """
        super().__init__(
            name="File Manipulation",
            description="Tests agent's ability to create, read, transform, and extract data from files",
            required_skills=[],  # Uses built-in read/write/exec tools only
        )

        self.file_setup = FileSetup()
        self.validator = FileValidator()
        self.remote_manager = remote_manager

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 3 file manipulation tasks with progressive complexity."""

        # Task 1: File Organization - Create directory structure
        self.add_task(
            BenchmarkTask(
                name="File Organization",
                prompt=(
                    f"Read the user data from {self.file_setup.data_json_path}. "
                    f"For each user, create a directory named 'users/{{name}}/' under {self.file_setup.workspace_dir}, "
                    "where {{name}} is the user's name (e.g., 'Alice Johnson'). "
                    "In each user directory, create a file called 'profile.txt' containing their email and role, "
                    "formatted as:\n"
                    "Email: {{email}}\n"
                    "Role: {{role}}"
                ),
                expected_output_description="Directory structure: users/{name}/profile.txt for each user",
                validation_fn=self.validator.validate_file_organization,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "file_organization"},
            )
        )

        # Task 2: File Modification - Update existing files
        self.add_task(
            BenchmarkTask(
                name="File Modification",
                prompt=(
                    f"Read {self.file_setup.notes_txt_path} to count how many action items each person has. "
                    "Count ONLY action items explicitly assigned to each person by their name (e.g., 'Alice:', 'Bob:', 'Carol:'). "
                    "Do NOT count action items assigned to 'Everyone' or group names. "
                    f"Then update each profile.txt file in the users/ directories to add a new line at the end: "
                    "'Action Items: X' where X is the count of action items for that specific person. "
                    "If a user has no action items explicitly assigned to them by name, use 0."
                ),
                expected_output_description="Updated profile.txt files with action item counts",
                validation_fn=self.validator.validate_file_modification,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "file_modification"},
            )
        )

        # Task 3: File Consolidation - Aggregate data from multiple files
        self.add_task(
            BenchmarkTask(
                name="File Consolidation",
                prompt=(
                    f"Find all profile.txt files in the users/ directories under {self.file_setup.workspace_dir}. "
                    f"Read each profile and create a CSV file named 'users_summary.csv' in {self.file_setup.workspace_dir} "
                    "with columns: name, email, role, action_count. "
                    "Sort the rows by action_count in descending order (highest first)."
                ),
                expected_output_description="CSV file with aggregated user data sorted by action count",
                validation_fn=self.validator.validate_file_consolidation,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "file_consolidation"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        checks = check_skills(self.required_skills)

        # Check workspace access
        if self.file_setup.verify_workspace_access():
            checks.append(
                HealthCheckResult(
                    check_name="Workspace Access",
                    status=CheckStatus.PASS,
                    message=f"Can read/write to {self.file_setup.workspace_dir}",
                    details={"workspace_dir": str(self.file_setup.workspace_dir)},
                )
            )
        else:
            checks.append(
                HealthCheckResult(
                    check_name="Workspace Access",
                    status=CheckStatus.FAIL,
                    message=f"Cannot access workspace directory: {self.file_setup.workspace_dir}",
                    details={"workspace_dir": str(self.file_setup.workspace_dir)},
                )
            )

        return checks

    def setup(self) -> SetupResult:
        """Set up the file manipulation scenario.

        Returns:
            Setup result with paths to created files
        """
        try:
            if self.remote_manager:
                # Remote setup via SSH
                logger.info("Creating remote workspace and seed files...")
                return self.remote_manager.remote_setup()
            else:
                # Local setup
                logger.info("Creating test workspace and seed files...")
                setup_data = self.file_setup.create_workspace()

                logger.info(f"Workspace created at: {setup_data['workspace_dir']}")
                logger.info(f"  - data.json: {setup_data['data_json']}")
                logger.info(f"  - notes.txt: {setup_data['notes_txt']}")
                logger.info(f"  - reports/: {setup_data['reports_dir']}")

                return SetupResult(
                    status=CheckStatus.PASS,
                    message="File workspace created successfully",
                    setup_data=setup_data,
                )

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return SetupResult(
                status=CheckStatus.FAIL,
                message=f"Failed to create workspace: {str(e)}",
                error=str(e),
            )

    def cleanup(self) -> bool:
        """Clean up the file manipulation scenario.

        Returns:
            True if cleanup succeeded
        """
        try:
            if self.remote_manager:
                # Remote cleanup via SSH
                logger.info("Cleaning up remote workspace...")
                return self.remote_manager.remote_cleanup()
            else:
                # Local cleanup
                logger.info("Cleaning up test workspace...")
                success = self.file_setup.cleanup_workspace()
                if success:
                    logger.info("Workspace cleaned up successfully")
                return success
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return False
