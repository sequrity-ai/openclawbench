"""Validation utilities for file manipulation tasks."""

import csv
import json
import re
from pathlib import Path
from typing import Any

from benchmarks.base import TaskResult


class FileValidator:
    """Validates file manipulation task results."""

    @staticmethod
    def validate_file_creation(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: File creation with markdown list.

        Expected: File named 'summary.md' with bullet list of Python, JavaScript, Rust
        """
        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))
        summary_file = workspace_dir / "summary.md"

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check if file exists
            if not summary_file.exists():
                error_message = "File summary.md not found"
            else:
                content = summary_file.read_text()
                validation_details["file_content"] = content

                # Check for required items
                required_items = ["Python", "JavaScript", "Rust"]
                found_items = []

                for item in required_items:
                    # Look for bullet points (-, *, or numbered)
                    pattern = rf"(?:^|\n)[\s]*(?:[-*]|\d+\.)\s*{item}"
                    if re.search(pattern, content, re.IGNORECASE):
                        found_items.append(item)
                        accuracy_score += 33.33

                validation_details["found_items"] = found_items
                validation_details["required_items"] = required_items

                if len(found_items) == len(required_items):
                    success = True
                    accuracy_score = 100.0
                else:
                    error_message = f"Missing items: {set(required_items) - set(found_items)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="File Creation",
            prompt="Create a file named 'summary.md' with a bullet list of: Python, JavaScript, Rust",
            success=success,
            latency=0.0,  # Will be set by runner
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_json_to_csv(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: JSON to CSV transformation.

        Expected: CSV file with names and emails from data.json
        """
        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))
        expected_users = setup_data.get("expected_users", [])

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Check for the specific expected file
            csv_file = workspace_dir / "data.csv"

            if not csv_file.exists():
                # Fall back to any CSV file
                csv_files = list(workspace_dir.glob("*.csv"))
                if not csv_files:
                    error_message = "No CSV file found (expected data.csv)"
                else:
                    csv_file = csv_files[0]

            if not error_message:
                validation_details["csv_file"] = str(csv_file)

                with open(csv_file, "r") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                validation_details["num_rows"] = len(rows)
                validation_details["expected_rows"] = len(expected_users)

                # Check if correct number of rows
                if len(rows) == len(expected_users):
                    accuracy_score += 30.0

                # Check if has name and email columns
                if rows and "name" in rows[0] and "email" in rows[0]:
                    accuracy_score += 30.0
                else:
                    error_message = "CSV missing 'name' or 'email' columns"

                # Check if data matches
                matched_records = 0
                for user in expected_users:
                    for row in rows:
                        if (
                            row.get("name", "").lower() == user["name"].lower()
                            and row.get("email", "").lower() == user["email"].lower()
                        ):
                            matched_records += 1
                            break

                record_accuracy = (matched_records / len(expected_users)) * 40.0
                accuracy_score += record_accuracy

                validation_details["matched_records"] = matched_records

                if accuracy_score >= 90.0:
                    success = True
                    accuracy_score = 100.0

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="JSON to CSV Transformation",
            prompt="Read data.json and create a CSV file with just names and emails",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_text_extraction(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: Text extraction and reporting.

        Expected: File in reports/ with extracted action items from notes.txt
        """
        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))
        reports_dir = workspace_dir / "reports"

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            # Look for files in reports directory
            if not reports_dir.exists():
                error_message = "Reports directory not found"
            else:
                report_files = list(reports_dir.glob("*.txt"))

                if not report_files:
                    error_message = "No report file found in reports/"
                else:
                    report_file = report_files[0]
                    validation_details["report_file"] = str(report_file)

                    content = report_file.read_text()
                    validation_details["file_content"] = content

                    # Expected action items (name + task description)
                    expected_actions = [
                        ("Alice", "development environment"),
                        ("Bob", "design mockups"),
                        ("Carol", "follow-up meeting"),
                        ("Everyone", "requirements document"),
                    ]

                    content_lower = content.lower()
                    found_actions = []
                    for name, task_fragment in expected_actions:
                        if name.lower() in content_lower and task_fragment in content_lower:
                            found_actions.append(name)

                    validation_details["found_actions"] = found_actions
                    validation_details["expected_count"] = len(expected_actions)

                    # Score: 20% per found action item (max 80%)
                    accuracy_score += len(found_actions) * 20.0

                    # Bonus 20%: non-action text is excluded
                    non_action_terms = ["Discussion Points", "Next Steps", "Attendees"]
                    excluded_count = sum(1 for term in non_action_terms if term not in content)
                    accuracy_score += (excluded_count / len(non_action_terms)) * 20.0

                    validation_details["excluded_non_actions"] = excluded_count

                    if len(found_actions) >= 3 and excluded_count >= 2:
                        success = True
                    if len(found_actions) == len(expected_actions) and excluded_count == len(non_action_terms):
                        accuracy_score = 100.0

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Text Extraction and Reporting",
            prompt="Extract all action items from notes.txt and save them to reports/actions.txt",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
