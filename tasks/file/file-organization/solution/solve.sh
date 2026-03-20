#!/bin/bash
# Reference solution for: File Organization
cd /workspace

python3 << 'PYEOF'
import csv
import os

with open("sales_data.csv") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

regions = set(r["region"] for r in rows)
for region in regions:
    os.makedirs(f"by_region/{region}", exist_ok=True)
    with open(f"by_region/{region}/sales.csv", "w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=["product", "quantity", "price", "region"])
        writer.writeheader()
        for r in rows:
            if r["region"] == region:
                writer.writerow(r)
PYEOF
