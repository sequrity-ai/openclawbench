"""File manipulation benchmark scenario.

Tasks (9):
    Easy:
       - Task 1 (File Organization): Create user directories and profile.txt files from data.json
       - Task 2 (File Modification): Count action items from notes and update profile.txt files
       - Task 3 (File Consolidation): Aggregate profile data into users_summary.csv

    Medium:
       - Task 4 (Recursive File Search): Find all .log files and create log_summary.txt
       - Task 5 (Data Transformation): Transform sales_data.csv to sales_report.json with aggregations
       - Task 6 (File Comparison): Compare config_v1.ini and config_v2.ini, create config_diff.txt

    Hard:
       - Task 7 (Multi-Step Data Pipeline): Merge employees.csv, departments.json, projects.xml into department_report.json
       - Task 8 (Advanced Log Analysis): Parse application.log and generate log_analysis.json with error statistics
       - Task 9 (Data Validation Report): Validate inventory.csv data quality and create validation_report.json

Setup:
    Creates test workspace at /tmp/openclaw_benchmark/ with structured data files
    including JSON, CSV, XML, INI, and log files. All files are created fresh on
    each run and removed during cleanup.

Required Skills:
    None (built-in file system tools)
"""

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
        """Define the 9 file manipulation tasks with progressive complexity."""

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
                validates_files=True,
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
                validates_files=True,
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
                validates_files=True,
            )
        )

        # Task 4: Recursive File Search - Find files matching pattern
        self.add_task(
            BenchmarkTask(
                name="Recursive File Search",
                prompt=(
                    f"Find all .log files recursively under {self.file_setup.workspace_dir}/logs/. "
                    f"Create a summary file named 'log_summary.txt' in {self.file_setup.workspace_dir} "
                    "that lists each log file with its path and size. "
                    "The summary should include all .log files found in any subdirectory."
                ),
                expected_output_description="log_summary.txt listing all .log files with paths",
                validation_fn=self.validator.validate_recursive_search,
                timeout=90.0,
                metadata={"difficulty": "medium", "category": "file_search"},
                validates_files=True,
            )
        )

        # Task 5: Data Transformation Pipeline - Transform CSV to JSON with aggregations
        self.add_task(
            BenchmarkTask(
                name="Data Transformation",
                prompt=(
                    f"Read {self.file_setup.workspace_dir}/sales_data.csv. "
                    f"Transform the data by grouping by product and calculate: "
                    "1) total_quantity (sum of quantities), 2) total_revenue (quantity * price summed). "
                    f"Create a JSON file named 'sales_report.json' in {self.file_setup.workspace_dir} "
                    "containing an array or object with these aggregated product totals."
                ),
                expected_output_description="sales_report.json with aggregated product totals",
                validation_fn=self.validator.validate_data_transformation,
                timeout=90.0,
                metadata={"difficulty": "medium", "category": "data_transformation"},
                validates_files=True,
            )
        )

        # Task 6: File Comparison - Identify differences between files
        self.add_task(
            BenchmarkTask(
                name="File Comparison",
                prompt=(
                    f"Compare {self.file_setup.workspace_dir}/config_v1.ini and "
                    f"{self.file_setup.workspace_dir}/config_v2.ini. "
                    f"Create a file named 'config_diff.txt' in {self.file_setup.workspace_dir} "
                    "that identifies all the differences between the two config files. "
                    "Include changes in values and new settings added in v2."
                ),
                expected_output_description="config_diff.txt identifying all differences",
                validation_fn=self.validator.validate_file_comparison,
                timeout=90.0,
                metadata={"difficulty": "medium", "category": "file_comparison"},
                validates_files=True,
            )
        )

        # Task 7: Multi-Step Data Pipeline - Merge multiple data sources
        self.add_task(
            BenchmarkTask(
                name="Multi-Step Data Pipeline",
                prompt=(
                    f"Merge data from three sources in {self.file_setup.reports_dir}: "
                    "1) employees.csv (emp_id, name, dept_id, salary), "
                    "2) departments.json (id, name, location), "
                    "3) projects.xml (id, name, dept_id, budget). "
                    f"Create a JSON file named 'department_report.json' in {self.file_setup.workspace_dir} "
                    "with department-level aggregations containing: department name, employee_count, "
                    "total_salary, and total_project_budget. Join the data on dept_id."
                ),
                expected_output_description="department_report.json merging all three data sources",
                validation_fn=self.validator.validate_multi_step_pipeline,
                timeout=120.0,
                metadata={"difficulty": "hard", "category": "data_pipeline"},
                validates_files=True,
            )
        )

        # Task 8: Advanced Log Analysis - Parse and analyze log file
        self.add_task(
            BenchmarkTask(
                name="Advanced Log Analysis",
                prompt=(
                    f"Parse {self.file_setup.workspace_dir}/application.log and generate statistics. "
                    f"Create a JSON file named 'log_analysis.json' in {self.file_setup.workspace_dir} "
                    "with the following metrics: "
                    "1) error_count (number of ERROR entries), "
                    "2) warn_count (number of WARN entries), "
                    "3) info_count (number of INFO entries), "
                    "4) total_entries (total log lines), "
                    "5) hourly_distribution (count of entries per hour if you can extract timestamps). "
                    "Parse the log file line by line and count entries by level."
                ),
                expected_output_description="log_analysis.json with error rates and hourly distribution",
                validation_fn=self.validator.validate_log_analysis,
                timeout=120.0,
                metadata={"difficulty": "hard", "category": "log_analysis"},
                validates_files=True,
            )
        )

        # Task 9: Data Validation Report - Identify data quality issues
        self.add_task(
            BenchmarkTask(
                name="Data Validation Report",
                prompt=(
                    f"Validate the data quality in {self.file_setup.workspace_dir}/inventory.csv. "
                    f"Create a JSON file named 'validation_report.json' in {self.file_setup.workspace_dir} "
                    "that identifies all data quality issues including: "
                    "1) missing_values (items with empty/null name, price, or category fields), "
                    "2) invalid_quantities (negative quantities), "
                    "3) duplicate_items (items with the same name appearing multiple times). "
                    "For each issue type, list the item_ids affected and count the total issues."
                ),
                expected_output_description="validation_report.json with data quality issues",
                validation_fn=self.validator.validate_data_validation,
                timeout=120.0,
                metadata={"difficulty": "hard", "category": "data_validation"},
                validates_files=True,
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        local_mode = self.remote_manager is None
        checks = check_skills(self.required_skills, local_mode=local_mode, remote_manager=self.remote_manager)

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
