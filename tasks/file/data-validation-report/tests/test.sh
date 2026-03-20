#!/bin/bash
set -e
WORKSPACE="/workspace"
REWARD_DIR="/logs/verifier"
mkdir -p "$REWARD_DIR"

FILE="$WORKSPACE/validation_report.json"
if [ ! -f "$FILE" ]; then
    echo 0 > "$REWARD_DIR/reward.txt"
    exit 0
fi

python3 << 'PYEOF' > "$REWARD_DIR/reward.txt"
import json
with open("/workspace/validation_report.json") as f:
    data = json.load(f)
s = json.dumps(data).lower()
missing_name = "1004" in s or "1015" in s
neg_qty = "1003" in s or "1012" in s
dup = "widget a" in s
print(1 if (missing_name and neg_qty and dup) else 0)
PYEOF
