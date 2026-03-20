#!/bin/bash
# Reference solution for: Data Transformation
cd /workspace

python3 << 'PYEOF'
import csv
import json

with open("sales_data.csv") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

products = {}
for r in rows:
    name = r["product"]
    qty = int(r["quantity"])
    price = float(r["price"])
    if name not in products:
        products[name] = {"product": name, "total_quantity": 0, "total_revenue": 0}
    products[name]["total_quantity"] += qty
    products[name]["total_revenue"] += int(qty * price)

result = {"products": list(products.values())}

with open("sales_report.json", "w") as f:
    json.dump(result, f, indent=2)
PYEOF
