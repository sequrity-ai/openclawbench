#!/usr/bin/env python3
"""Setup workspace for aggregate-and-report task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

# 20 transactions, 4 categories
# Housing: 5 transactions summing to 2750
# Food: 7 transactions
# Transport: 4 transactions
# Entertainment: 4 transactions
transactions = [
    ("id", "category", "amount"),
    ("1", "Housing", "800"),
    ("2", "Food", "120"),
    ("3", "Transport", "45"),
    ("4", "Food", "85"),
    ("5", "Entertainment", "60"),
    ("6", "Housing", "550"),
    ("7", "Food", "200"),
    ("8", "Transport", "30"),
    ("9", "Entertainment", "95"),
    ("10", "Housing", "600"),
    ("11", "Food", "150"),
    ("12", "Transport", "75"),
    ("13", "Entertainment", "110"),
    ("14", "Housing", "400"),
    ("15", "Food", "95"),
    ("16", "Transport", "55"),
    ("17", "Entertainment", "80"),
    ("18", "Housing", "400"),
    ("19", "Food", "175"),
    ("20", "Food", "110"),
]

csv_file = os.path.join(workspace, "transactions.csv")
with open(csv_file, "w") as f:
    for row in transactions:
        f.write(",".join(row) + "\n")

# Verify Housing total
housing_total = sum(int(r[2]) for r in transactions[1:] if r[1] == "Housing")
housing_count = sum(1 for r in transactions[1:] if r[1] == "Housing")
print(f"Workspace ready: {workspace}")
print(f"Created: {csv_file} ({len(transactions) - 1} transactions)")
print(f"Housing: {housing_count} transactions, total={housing_total}")
