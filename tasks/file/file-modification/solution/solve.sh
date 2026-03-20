#!/bin/bash
# Reference solution for: File Modification
cd /workspace

python3 << 'PYEOF'
import re
from pathlib import Path

with open("notes.txt") as f:
    content = f.read()

counts = {}
for line in content.split("\n"):
    m = re.match(r"^- (\w+):", line)
    if m:
        name = m.group(1)
        if name != "Everyone":
            counts[name] = counts.get(name, 0) + 1

name_map = {
    "Alice": "Alice Johnson",
    "Bob": "Bob Smith",
    "Carol": "Carol White",
}

for first, full in name_map.items():
    profile = Path(f"users/{full}/profile.txt")
    if profile.exists():
        text = profile.read_text()
        count = counts.get(first, 0)
        text = re.sub(r"Action Items: \d+", f"Action Items: {count}", text)
        profile.write_text(text)
PYEOF
