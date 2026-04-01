#!/bin/bash
# Reference solution for gmail-live/count-unread.
# Uses `gog` CLI to count unread emails with the test label.

mkdir -p /workspace/.logs/agent

python3 - <<'PYEOF'
import json
import os
import subprocess
import sys

# Read the test label
with open("/workspace/test_label.txt", "r") as f:
    label = f.read().strip()

# Search for unread messages with that label
result = subprocess.run(
    ["gog", "gmail", "search", f"label:{label} is:unread", "--json"],
    capture_output=True, text=True, timeout=30
)

if result.returncode != 0:
    print(f"Error: {result.stderr}", file=sys.stderr)
    sys.exit(1)

messages = json.loads(result.stdout)
count = len(messages) if isinstance(messages, list) else 0

with open("/workspace/.logs/agent/response.txt", "w") as f:
    f.write(str(count))

print(f"Unread emails with label '{label}': {count}")
PYEOF
