#!/bin/bash
# Test: gmail-live/count-unread
# Verifies the agent reports exactly 3 unread emails.

set -e

python3 - <<'PYEOF'
import json
import os
import re
import sys

reward_dir = os.environ.get("REWARD_DIR", "/tmp")
reward_file = os.path.join(reward_dir, "reward.txt")


def fail(reason=""):
    print(f"FAIL: {reason}", file=sys.stderr)
    with open(reward_file, "w") as f:
        f.write("0")
    sys.exit(0)


def pass_test(reason=""):
    print(f"PASS: {reason}")
    with open(reward_file, "w") as f:
        f.write("1")
    sys.exit(0)


# Read expected count from manifest
expected_unread = 3
manifest_path = "/workspace/.manifest.json"
if os.path.exists(manifest_path):
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    expected_unread = manifest.get("expected_unread", 3)

# Read agent response
try:
    with open("/logs/agent/response.txt", "r") as f:
        response = f.read()
except Exception as e:
    fail(f"Could not read response file: {e}")

# Check for the expected count
pattern = rf'\b{expected_unread}\b'
if re.search(pattern, response):
    pass_test(f"Response contains '{expected_unread}' (correct unread count)")
else:
    fail(f"Expected '{expected_unread}', got '{response.strip()}'")
PYEOF
