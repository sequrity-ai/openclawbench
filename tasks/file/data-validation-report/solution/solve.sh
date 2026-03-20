#!/bin/bash
# Reference solution for: Data Validation Report
cd /workspace

python3 << 'PYEOF'
import csv
import json
from collections import defaultdict

with open("inventory.csv") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

missing_values = []
invalid_quantities = []
name_counts = defaultdict(list)

for row in rows:
    item_id = row["item_id"]

    if not row["name"].strip():
        missing_values.append({"item_id": item_id, "field": "name"})
    if not row["price"].strip():
        missing_values.append({"item_id": item_id, "field": "price"})
    if not row["category"].strip():
        missing_values.append({"item_id": item_id, "field": "category"})

    if row["quantity"].strip():
        qty = int(row["quantity"])
        if qty < 0:
            invalid_quantities.append({"item_id": item_id, "quantity": qty})

    if row["name"].strip():
        name_counts[row["name"].strip()].append(item_id)

duplicate_items = []
for name, ids in name_counts.items():
    if len(ids) > 1:
        duplicate_items.append({"name": name, "item_ids": ids, "count": len(ids)})

report = {
    "missing_values": {
        "items": missing_values,
        "total": len(missing_values),
    },
    "invalid_quantities": {
        "items": invalid_quantities,
        "total": len(invalid_quantities),
    },
    "duplicate_items": {
        "items": duplicate_items,
        "total": len(duplicate_items),
    },
}

with open("validation_report.json", "w") as f:
    json.dump(report, f, indent=2)
PYEOF
