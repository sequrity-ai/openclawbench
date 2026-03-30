#!/usr/bin/env python3
"""Setup workspace for transform-and-report task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

# Widget Pro appears 4 times, amounts: 80, 120, 95, 155 = 450
rows = [
    ("date", "product", "amount"),
    ("2026-01-03", "Gadget Basic", "75"),
    ("2026-01-05", "Widget Pro", "80"),
    ("2026-01-07", "SuperTool", "200"),
    ("2026-01-09", "Widget Pro", "120"),
    ("2026-01-11", "Gadget Basic", "60"),
    ("2026-01-13", "MegaKit", "320"),
    ("2026-01-15", "Widget Pro", "95"),
    ("2026-01-17", "SuperTool", "185"),
    ("2026-01-19", "Gadget Basic", "90"),
    ("2026-01-21", "Widget Pro", "155"),
]

sales_file = os.path.join(workspace, "sales.csv")
with open(sales_file, "w") as f:
    for row in rows:
        f.write(",".join(row) + "\n")

widget_total = sum(int(r[2]) for r in rows[1:] if r[1] == "Widget Pro")
print(f"Workspace ready: {workspace}")
print(f"Created: {sales_file} (Widget Pro total: {widget_total})")
