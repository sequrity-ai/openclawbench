#!/bin/bash
set -e
WORKSPACE="/workspace"
REWARD_DIR="/logs/verifier"
mkdir -p "$REWARD_DIR"

FILE="$WORKSPACE/log_analysis.json"
if [ ! -f "$FILE" ]; then
    echo 0 > "$REWARD_DIR/reward.txt"
    exit 0
fi

python3 << 'PYEOF' > "$REWARD_DIR/reward.txt"
import json
with open("/workspace/log_analysis.json") as f:
    data = json.load(f)
ok = (data.get("error_count") == 32 and
      data.get("warn_count") == 32 and
      data.get("total_entries") == 250)
print(1 if ok else 0)
PYEOF
