#!/usr/bin/env python3
"""Setup workspace for fetch-and-compare task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

thresholds_file = os.path.join(workspace, "thresholds.txt")
with open(thresholds_file, "w") as f:
    f.write("BTC minimum: 10000\n")

print(f"Workspace ready: {workspace}")
print(f"Created: {thresholds_file}")
