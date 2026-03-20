#!/bin/bash
set -e
WORKSPACE="/workspace"
REWARD_DIR="/logs/verifier"
mkdir -p "$REWARD_DIR"

FILE="$WORKSPACE/sales_report.json"
if [ ! -f "$FILE" ]; then
    echo 0 > "$REWARD_DIR/reward.txt"
    exit 0
fi

python3 << 'PYEOF' > "$REWARD_DIR/reward.txt"
import json
with open("/workspace/sales_report.json") as f:
    data = json.load(f)
if isinstance(data, dict):
    if "products" in data:
        items = data["products"]
    else:
        items = [{"product": k, **v} if isinstance(v, dict) else {"product": k} for k, v in data.items()]
else:
    items = data
expected = {"Laptop": (15, 18000), "Mouse": (35, 875), "Keyboard": (18, 1350), "Monitor": (7, 2100)}
matched = 0
for name, (qty, rev) in expected.items():
    for item in items:
        pname = item.get("product", item.get("name", ""))
        if pname == name and item.get("total_quantity") == qty and item.get("total_revenue") == rev:
            matched += 1
            break
print(1 if matched == 4 else 0)
PYEOF
