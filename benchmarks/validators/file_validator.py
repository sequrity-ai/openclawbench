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

    @staticmethod
    def validate_recursive_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate MEDIUM Task 1: Recursive File Search with Filtering.

        Expected: log_summary.txt with all .log files (path and size)
        """
        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            summary_file = workspace_dir / "log_summary.txt"

            if not summary_file.exists():
                error_message = "log_summary.txt not found"
            else:
                content = summary_file.read_text()

                # Expected log files (hardcoded to match seed data in file_setup.py and remote_workspace.py)
                # logs/app.log, logs/error.log, logs/api/requests.log, logs/api/access.log
                expected_log_names = ["app.log", "error.log", "requests.log", "access.log"]
                validation_details["expected_files"] = len(expected_log_names)

                # Check if all log files are mentioned in the summary
                found_files = []
                missing_files = []

                for log_name in expected_log_names:
                    # Check if file name is mentioned in the summary
                    if log_name in content:
                        found_files.append(log_name)
                    else:
                        missing_files.append(log_name)

                validation_details["found_files"] = len(found_files)
                validation_details["missing_files"] = missing_files

                # Binary scoring: pass only if ALL log files are mentioned
                if len(missing_files) == 0:
                    success = True
                    accuracy_score = 100.0
                else:
                    accuracy_score = 0.0
                    error_message = f"Missing {len(missing_files)} log files in summary: {', '.join(missing_files)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Recursive File Search",
            prompt="Find all .log files recursively and create log_summary.txt",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_data_transformation(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate MEDIUM Task 2: Data Transformation Pipeline.

        Expected: sales_report.json with aggregated product totals (total_quantity, total_revenue)
        """
        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            report_file = workspace_dir / "sales_report.json"

            if not report_file.exists():
                error_message = "sales_report.json not found"
            else:
                with open(report_file, "r") as f:
                    report_data = json.load(f)

                # Expected aggregations from sales_data.csv
                # Laptop: 5+7+3=15, revenue: 15*1200=18000
                # Mouse: 15+20=35, revenue: 35*25=875
                # Keyboard: 8+10=18, revenue: 18*75=1350
                # Monitor: 3+4=7, revenue: 7*300=2100
                expected_products = {
                    "Laptop": {"total_quantity": 15, "total_revenue": 18000},
                    "Mouse": {"total_quantity": 35, "total_revenue": 875},
                    "Keyboard": {"total_quantity": 18, "total_revenue": 1350},
                    "Monitor": {"total_quantity": 7, "total_revenue": 2100},
                }

                validation_details["expected_products"] = list(expected_products.keys())

                # Check if data is structured correctly
                if not isinstance(report_data, (list, dict)):
                    error_message = "Invalid JSON structure"
                else:
                    # Handle three formats:
                    # 1. List of dicts: [{"product": "Laptop", "total_quantity": 15, ...}, ...]
                    # 2. Dict with "products" key: {"products": [...]}
                    # 3. Dict keyed by product name: {"Laptop": {"total_quantity": 15, ...}, ...}
                    if isinstance(report_data, list):
                        products_list = report_data
                    elif "products" in report_data:
                        products_list = report_data.get("products", [])
                    else:
                        # Dict-keyed format: convert to list-of-dicts
                        products_list = [
                            {"product": k, **v} if isinstance(v, dict) else {"product": k}
                            for k, v in report_data.items()
                        ]

                    matched_products = 0
                    mismatched_products = []

                    for expected_name, expected_values in expected_products.items():
                        found = False
                        for product in products_list:
                            product_name = product.get("product", product.get("name", ""))
                            if product_name == expected_name:
                                # Check quantities and revenue
                                qty = product.get("total_quantity", 0)
                                rev = product.get("total_revenue", 0)

                                if qty == expected_values["total_quantity"] and rev == expected_values["total_revenue"]:
                                    matched_products += 1
                                    found = True
                                    break
                                else:
                                    mismatched_products.append(f"{expected_name}: expected qty={expected_values['total_quantity']}, rev={expected_values['total_revenue']}, got qty={qty}, rev={rev}")
                                    found = True
                                    break

                        if not found:
                            mismatched_products.append(f"{expected_name}: not found in report")

                    validation_details["matched_products"] = matched_products
                    validation_details["mismatched_products"] = mismatched_products

                    # Binary scoring: pass only if ALL products have correct aggregations
                    if matched_products == len(expected_products):
                        success = True
                        accuracy_score = 100.0
                    else:
                        accuracy_score = 0.0
                        error_message = f"Product aggregations incorrect: {', '.join(mismatched_products)}"

        except json.JSONDecodeError as e:
            error_message = f"Invalid JSON format: {str(e)}"
        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Data Transformation",
            prompt="Transform sales_data.csv into sales_report.json with aggregations",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_file_comparison(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate MEDIUM Task 3: File Comparison and Merge.

        Expected: config_diff.txt identifying all differences between config versions
        """
        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            diff_file = workspace_dir / "config_diff.txt"

            if not diff_file.exists():
                error_message = "config_diff.txt not found"
            else:
                content = diff_file.read_text().lower()

                # Key differences to detect between config_v1 and config_v2:
                # 1. database.host: localhost -> prod-db.example.com
                # 2. database.timeout: 30 -> 60
                # 3. database.pool_size: added in v2
                # 4. cache.ttl: 300 -> 600
                # 5. logging.level: INFO -> DEBUG
                # 6. logging.format: added in v2

                expected_diffs = [
                    ("host", ["localhost", "prod-db.example.com", "database"]),
                    ("timeout", ["30", "60", "database"]),
                    ("pool_size", ["pool", "10"]),
                    ("ttl", ["300", "600", "cache"]),
                    ("level", ["info", "debug", "logging"]),
                    ("format", ["json", "logging"]),
                ]

                found_diffs = []
                missing_diffs = []

                for diff_name, keywords in expected_diffs:
                    # Check if diff is mentioned (all keywords should appear)
                    if all(keyword in content for keyword in keywords):
                        found_diffs.append(diff_name)
                    else:
                        missing_diffs.append(diff_name)

                validation_details["expected_diffs"] = len(expected_diffs)
                validation_details["found_diffs"] = found_diffs
                validation_details["missing_diffs"] = missing_diffs

                # Binary scoring: pass only if ALL 6 diffs are found
                if len(found_diffs) == 6:
                    success = True
                    accuracy_score = 100.0
                else:
                    accuracy_score = 0.0
                    error_message = f"Missing key differences: {', '.join(missing_diffs)} (found {len(found_diffs)}/6)"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="File Comparison",
            prompt="Compare config_v1.ini and config_v2.ini, create config_diff.txt",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_multi_step_pipeline(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate HARD Task 2: Multi-Step Data Pipeline.

        Expected: department_report.json merging employees.csv, departments.json, projects.xml
        with department name, employee count, total salary, total project budget
        """
        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            report_file = workspace_dir / "department_report.json"

            if not report_file.exists():
                error_message = "department_report.json not found"
            else:
                with open(report_file, "r") as f:
                    report_data = json.load(f)

                # Expected aggregations:
                # Engineering (dept_id=1): 2 employees (Alice 95k, Carol 105k), 1 project (Mobile App 120k)
                # Design (dept_id=2): 2 employees (Bob 78k, Eve 88k), 1 project (Website Redesign 50k)
                # Marketing (dept_id=3): 1 employee (Dave 82k), 1 project (Brand Campaign 75k)
                expected_depts = {
                    "Engineering": {
                        "employee_count": 2,
                        "total_salary": 200000,  # 95k + 105k
                        "total_project_budget": 120000,
                    },
                    "Design": {
                        "employee_count": 2,
                        "total_salary": 166000,  # 78k + 88k
                        "total_project_budget": 50000,
                    },
                    "Marketing": {
                        "employee_count": 1,
                        "total_salary": 82000,
                        "total_project_budget": 75000,
                    },
                }

                validation_details["expected_departments"] = list(expected_depts.keys())

                # Handle three formats:
                # 1. List of dicts: [{"department": "Engineering", "employee_count": 2, ...}, ...]
                # 2. Dict with "departments" key: {"departments": [...]}
                # 3. Dict keyed by dept name: {"Engineering": {"employee_count": 2, ...}, ...}
                if isinstance(report_data, list):
                    depts_list = report_data
                elif "departments" in report_data:
                    depts_list = report_data.get("departments", [])
                else:
                    # Dict-keyed format: convert to list-of-dicts
                    depts_list = [
                        {"department": k, **v} if isinstance(v, dict) else {"department": k}
                        for k, v in report_data.items()
                    ]

                matched_depts = 0
                mismatched_depts = []

                for expected_name, expected_values in expected_depts.items():
                    found = False
                    for dept in depts_list:
                        dept_name = dept.get("department", dept.get("name", ""))
                        if dept_name == expected_name:
                            # Check all aggregations
                            emp_count = dept.get("employee_count", 0)
                            total_salary = dept.get("total_salary", 0)
                            total_budget = dept.get("total_project_budget", dept.get("project_budget", 0))

                            if (
                                emp_count == expected_values["employee_count"]
                                and total_salary == expected_values["total_salary"]
                                and total_budget == expected_values["total_project_budget"]
                            ):
                                matched_depts += 1
                                found = True
                                break
                            else:
                                mismatched_depts.append(
                                    f"{expected_name}: expected emp={expected_values['employee_count']}, "
                                    f"salary={expected_values['total_salary']}, budget={expected_values['total_project_budget']}, "
                                    f"got emp={emp_count}, salary={total_salary}, budget={total_budget}"
                                )
                                found = True
                                break

                    if not found:
                        mismatched_depts.append(f"{expected_name}: not found in report")

                validation_details["matched_departments"] = matched_depts
                validation_details["mismatched_departments"] = mismatched_depts

                # Binary scoring: pass only if ALL departments have correct aggregations
                if matched_depts == len(expected_depts):
                    success = True
                    accuracy_score = 100.0
                else:
                    accuracy_score = 0.0
                    error_message = f"Department aggregations incorrect: {', '.join(mismatched_depts)}"

        except json.JSONDecodeError as e:
            error_message = f"Invalid JSON format: {str(e)}"
        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Multi-Step Data Pipeline",
            prompt="Merge employees.csv, departments.json, projects.xml into department_report.json",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_log_analysis(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate HARD Task 8: Advanced Log Analysis.

        Expected: log_analysis.json with error rates, hourly distribution, top errors
        """
        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            analysis_file = workspace_dir / "log_analysis.json"

            if not analysis_file.exists():
                error_message = "log_analysis.json not found"
            else:
                with open(analysis_file, "r") as f:
                    analysis_data = json.load(f)

                # Check for required metrics
                required_keys = ["error_count", "warn_count", "info_count", "total_entries"]
                has_all_keys = all(key in analysis_data for key in required_keys)

                validation_details["has_required_keys"] = has_all_keys
                validation_details["found_keys"] = list(analysis_data.keys())

                # Seeded log: 250 entries (i=0..249)
                # i%10==0 → ERROR: 25 entries (0,10,...,240)
                # elif i%7==0 → WARN: 32 entries
                # elif i%15==0 (not %10 or %7) → ERROR: 8 entries (15,30,45,75,135,165,195,225)
                # Total ERRORs = 25 + 8 = 33, WARNs = 32, total = 250
                if has_all_keys:
                    error_count = analysis_data.get("error_count", 0)
                    warn_count = analysis_data.get("warn_count", 0)
                    total = analysis_data.get("total_entries", 0)

                    if error_count == 33 and warn_count == 32 and total == 250:
                        success = True
                        accuracy_score = 100.0
                    else:
                        error_message = f"Incorrect counts: errors={error_count} (expected 33), warns={warn_count} (expected 32), total={total} (expected 250)"
                        validation_details["expected_error_count"] = 33
                        validation_details["expected_warn_count"] = 32
                        validation_details["expected_total_entries"] = 250
                else:
                    error_message = f"Missing required keys: {set(required_keys) - set(analysis_data.keys())}"

        except json.JSONDecodeError as e:
            error_message = f"Invalid JSON format: {str(e)}"
        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Advanced Log Analysis",
            prompt="Parse application.log and generate statistical analysis",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_data_validation(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate HARD Task 9: Data Validation Report.

        Expected: validation_report.json identifying data quality issues
        """
        workspace_dir = Path(setup_data.get("workspace_dir", "/tmp/openclaw_benchmark"))

        success = False
        accuracy_score = 0.0
        validation_details = {}
        error_message = None

        try:
            report_file = workspace_dir / "validation_report.json"

            if not report_file.exists():
                error_message = "validation_report.json not found"
            else:
                with open(report_file, "r") as f:
                    report_data = json.load(f)

                # Expected issues in inventory.csv:
                # - Missing names: 1004, 1015, 1026, 1037 (4 items)
                # - Missing prices: 1006, 1018, 1030, 1044 (4 items)
                # - Missing categories: 1021, 1035, 1048 (3 items)
                # - Missing dates: 1009 (1 item)
                # - Negative quantities: 1003, 1012, 1023, 1034, 1041 (5 items)
                # - Zero quantities: 1002, 1010, 1017, 1028, 1038, 1045 (6 items)
                # - Duplicate names: Widget A (1001, 1008, 1020) (3 occurrences)

                # Pin to specific seeded data quality issues in inventory.csv:
                # - Missing names: items 1004, 1015 (empty name field)
                # - Negative quantities: items 1003 (qty=-5), 1012 (qty=-10)
                # - Duplicate name "Widget A": items 1001, 1008, 1020
                report_str = json.dumps(report_data).lower()

                # Check 1: item 1004 or 1015 flagged for missing name
                missing_name_found = "1004" in report_str or "1015" in report_str
                # Check 2: item 1003 or 1012 flagged for negative quantity
                negative_qty_found = "1003" in report_str or "1012" in report_str
                # Check 3: "widget a" flagged as duplicate
                duplicate_found = "widget a" in report_str

                validation_details["missing_name_item_found"] = missing_name_found
                validation_details["negative_qty_item_found"] = negative_qty_found
                validation_details["duplicate_name_found"] = duplicate_found

                # Binary scoring: pass only if ALL 3 issue categories identified with pinned items
                if missing_name_found and negative_qty_found and duplicate_found:
                    success = True
                    accuracy_score = 100.0
                else:
                    missing_parts = []
                    if not missing_name_found:
                        missing_parts.append("missing-name items (1004 or 1015)")
                    if not negative_qty_found:
                        missing_parts.append("negative-quantity items (1003 or 1012)")
                    if not duplicate_found:
                        missing_parts.append("duplicate name 'Widget A'")
                    error_message = f"Missing issue categories: {'; '.join(missing_parts)}"

        except json.JSONDecodeError as e:
            error_message = f"Invalid JSON format: {str(e)}"
        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Data Validation Report",
            prompt="Validate inventory.csv and generate quality issues report",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
