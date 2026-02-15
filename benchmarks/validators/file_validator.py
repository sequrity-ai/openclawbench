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
    def validate_file_organization(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: File Organization - Create directory structure.

        Expected: users/{name}/profile.txt for each user with email and role
        """
        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))
        expected_users = setup_data.get("expected_users", [])

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            users_dir = workspace_dir / "users"

            if not users_dir.exists():
                error_message = "users/ directory not found"
            else:
                # Check each user has their directory and profile.txt
                all_valid = True
                missing_items = []

                for user in expected_users:
                    user_name = user["name"]
                    user_dir = users_dir / user_name
                    profile_file = user_dir / "profile.txt"

                    if not user_dir.exists():
                        all_valid = False
                        missing_items.append(f"Directory users/{user_name}/")
                        continue

                    if not profile_file.exists():
                        all_valid = False
                        missing_items.append(f"File users/{user_name}/profile.txt")
                        continue

                    # Verify profile.txt content
                    content = profile_file.read_text()
                    has_email = user["email"] in content
                    has_role = user["role"] in content

                    if not (has_email and has_role):
                        all_valid = False
                        missing_items.append(f"Invalid content in users/{user_name}/profile.txt")

                validation_details["checked_users"] = len(expected_users)
                validation_details["missing_items"] = missing_items

                # Binary scoring: pass only if ALL users have valid directories and files
                if all_valid:
                    success = True
                    accuracy_score = 100.0
                else:
                    accuracy_score = 0.0
                    error_message = f"Missing or invalid items: {', '.join(missing_items)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="File Organization",
            prompt="Create users/{name}/profile.txt directories and files",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_file_modification(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: File Modification - Update profile.txt with action counts.

        Expected: Each profile.txt updated with "Action Items: X" line
        """
        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))
        expected_users = setup_data.get("expected_users", [])

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            users_dir = workspace_dir / "users"

            # Expected action item counts from notes.txt
            expected_counts = {
                "Alice Johnson": 1,  # Set up development environment
                "Bob Smith": 1,      # Create initial design mockups
                "Carol White": 1,    # Schedule follow-up meeting
            }

            if not users_dir.exists():
                error_message = "users/ directory not found"
            else:
                all_valid = True
                invalid_items = []

                for user in expected_users:
                    user_name = user["name"]
                    profile_file = users_dir / user_name / "profile.txt"

                    if not profile_file.exists():
                        all_valid = False
                        invalid_items.append(f"Missing users/{user_name}/profile.txt")
                        continue

                    content = profile_file.read_text()
                    expected_count = expected_counts.get(user_name, 0)

                    # Check for "Action Items: X" line
                    if f"Action Items: {expected_count}" not in content:
                        all_valid = False
                        invalid_items.append(f"users/{user_name}/profile.txt missing or incorrect action count")

                validation_details["checked_users"] = len(expected_users)
                validation_details["invalid_items"] = invalid_items
                validation_details["expected_counts"] = expected_counts

                # Binary scoring: pass only if ALL profiles updated correctly
                if all_valid:
                    success = True
                    accuracy_score = 100.0
                else:
                    accuracy_score = 0.0
                    error_message = f"Invalid or missing updates: {', '.join(invalid_items)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="File Modification",
            prompt="Update profile.txt files with action item counts",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_file_consolidation(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: File Consolidation - Aggregate profiles into CSV.

        Expected: users_summary.csv with name, email, role, action_count sorted by action_count desc
        """
        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))
        expected_users = setup_data.get("expected_users", [])

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            csv_file = workspace_dir / "users_summary.csv"

            if not csv_file.exists():
                error_message = "users_summary.csv not found"
            else:
                with open(csv_file, "r") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                validation_details["num_rows"] = len(rows)
                validation_details["expected_rows"] = len(expected_users)

                # Check columns exist
                required_columns = ["name", "email", "role", "action_count"]
                has_correct_columns = rows and all(col in rows[0] for col in required_columns)

                if not has_correct_columns:
                    error_message = f"CSV missing required columns: {required_columns}"
                else:
                    # Check row count matches
                    has_correct_rows = len(rows) == len(expected_users)

                    # Check all user data is present
                    matched_records = 0
                    for user in expected_users:
                        for row in rows:
                            if (
                                row.get("name", "").lower() == user["name"].lower()
                                and row.get("email", "").lower() == user["email"].lower()
                                and row.get("role", "").lower() == user["role"].lower()
                            ):
                                matched_records += 1
                                break

                    has_all_data = matched_records == len(expected_users)

                    # Check sorting by action_count descending
                    is_sorted = True
                    try:
                        action_counts = [int(row.get("action_count", 0)) for row in rows]
                        is_sorted = action_counts == sorted(action_counts, reverse=True)
                    except ValueError:
                        is_sorted = False

                    validation_details["matched_records"] = matched_records
                    validation_details["has_correct_rows"] = has_correct_rows
                    validation_details["has_all_data"] = has_all_data
                    validation_details["is_sorted"] = is_sorted

                    # Binary scoring: pass only if ALL requirements met
                    if has_correct_rows and has_correct_columns and has_all_data and is_sorted:
                        success = True
                        accuracy_score = 100.0
                    else:
                        accuracy_score = 0.0
                        error_message = f"Requirements not met: rows={has_correct_rows}, columns={has_correct_columns}, data={has_all_data}, sorted={is_sorted}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="File Consolidation",
            prompt="Create users_summary.csv with aggregated data sorted by action_count",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
