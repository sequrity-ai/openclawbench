#!/usr/bin/env python3
"""Setup workspace for filter-and-save task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

# 15 employees, exactly 5 in Engineering
employees = [
    ("name", "department", "salary"),
    ("Alice Johnson", "Engineering", "95000"),
    ("Bob Martinez", "Marketing", "72000"),
    ("Carol White", "Engineering", "88000"),
    ("David Chen", "HR", "65000"),
    ("Emma Davis", "Engineering", "102000"),
    ("Frank Wilson", "Finance", "78000"),
    ("Grace Lee", "Marketing", "69000"),
    ("Henry Brown", "Engineering", "91000"),
    ("Iris Taylor", "HR", "62000"),
    ("James Anderson", "Finance", "83000"),
    ("Karen Thomas", "Engineering", "97000"),
    ("Leo Jackson", "Marketing", "74000"),
    ("Maria Garcia", "HR", "67000"),
    ("Nathan Harris", "Finance", "81000"),
    ("Olivia Clark", "Marketing", "71000"),
]

csv_file = os.path.join(workspace, "employees.csv")
with open(csv_file, "w") as f:
    for row in employees:
        f.write(",".join(row) + "\n")

eng_count = sum(1 for e in employees[1:] if e[1] == "Engineering")
print(f"Workspace ready: {workspace}")
print(f"Created: {csv_file} ({len(employees) - 1} employees, {eng_count} in Engineering)")
