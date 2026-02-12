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

    def __init__(self):
        """Initialize file manipulation scenario."""
        super().__init__(
            name="File Manipulation",
            description="Tests agent's ability to create, read, transform, and extract data from files",
            required_skills=[],  # Uses built-in read/write/exec tools only
        )

        self.file_setup = FileSetup()
        self.validator = FileValidator()

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 3 file manipulation tasks."""

        # Task 1: File Creation
        self.add_task(
            BenchmarkTask(
                name="File Creation",
                prompt=(
                    f"Create a file named 'summary.md' in {self.file_setup.workspace_dir} "
                    "with a bullet list of the following programming languages: "
                    "Python, JavaScript, Rust"
                ),
                expected_output_description="Markdown file with bullet list of 3 languages",
                validation_fn=self.validator.validate_file_creation,
                timeout=40.0,
                metadata={"difficulty": "low", "category": "file_creation"},
            )
        )

        # Task 2: JSON to CSV Transformation
        self.add_task(
            BenchmarkTask(
                name="JSON to CSV Transformation",
                prompt=(
                    f"Read the file {self.file_setup.data_json_path} and create a CSV file "
                    f"named 'data.csv' in {self.file_setup.workspace_dir} with just the "
                    "names and emails. The CSV should have columns: name, email"
                ),
                expected_output_description="CSV file named data.csv with name and email columns",
                validation_fn=self.validator.validate_json_to_csv,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "data_transformation"},
            )
        )

        # Task 3: Text Extraction
        self.add_task(
            BenchmarkTask(
                name="Text Extraction and Reporting",
                prompt=(
                    f"Read {self.file_setup.notes_txt_path} and extract all the action items. "
                    "Action items are lines in the 'Action Items:' section that start with "
                    "'- Name: task description'. "
                    f"Save them to a new file at {self.file_setup.reports_dir}/actions.txt. "
                    "Only include the action items, not the discussion points or other notes."
                ),
                expected_output_description="Text file with extracted action items only",
                validation_fn=self.validator.validate_text_extraction,
                timeout=50.0,
                metadata={"difficulty": "medium", "category": "text_extraction"},
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
            logger.info("Cleaning up test workspace...")
            success = self.file_setup.cleanup_workspace()
            if success:
                logger.info("Workspace cleaned up successfully")
            return success
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return False
