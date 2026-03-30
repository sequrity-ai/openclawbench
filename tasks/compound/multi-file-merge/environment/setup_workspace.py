#!/usr/bin/env python3
"""Setup workspace for multi-file-merge task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

# Q1=120000, Q2=135000, Q3=148000, Total=403000
quarters = {
    "q1.txt": ("Q1 Revenue", 120000),
    "q2.txt": ("Q2 Revenue", 135000),
    "q3.txt": ("Q3 Revenue", 148000),
}

for filename, (label, amount) in quarters.items():
    filepath = os.path.join(workspace, filename)
    with open(filepath, "w") as f:
        f.write(f"{label}: {amount}\n")
    print(f"Created: {filepath}")

total = sum(v[1] for v in quarters.values())
print(f"Workspace ready: {workspace}")
print(f"Total revenue: {total}")
