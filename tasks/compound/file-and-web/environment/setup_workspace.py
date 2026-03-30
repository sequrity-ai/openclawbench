#!/usr/bin/env python3
"""Setup workspace for file-and-web task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

cities_file = os.path.join(workspace, "cities.txt")
with open(cities_file, "w") as f:
    f.write("Paris\nTokyo\nSydney\n")

print(f"Workspace ready: {workspace}")
print(f"Created: {cities_file}")
