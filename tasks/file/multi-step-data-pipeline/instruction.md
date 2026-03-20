# Multi-Step Data Pipeline

Merge data from three sources in /workspace/reports: 1) employees.csv (emp_id, name, dept_id, salary), 2) departments.json (id, name, location), 3) projects.xml (id, name, dept_id, budget). Create a JSON file named 'department_report.json' in /workspace with department-level aggregations containing: department name, employee_count, total_salary, and total_project_budget. Join the data on dept_id.
