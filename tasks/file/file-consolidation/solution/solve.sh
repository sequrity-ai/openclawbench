#!/bin/bash
# Reference solution for: File Consolidation
cd /workspace

python3 << 'PYEOF'
import csv
import re
from pathlib import Path

users = []
for profile in sorted(Path("users").rglob("profile.txt")):
    name = profile.parent.name
    text = profile.read_text()
    email = re.search(r"Email: (.+)", text).group(1).strip()
    role = re.search(r"Role: (.+)", text).group(1).strip()
    action = int(re.search(r"Action Items: (\d+)", text).group(1))
    users.append({"name": name, "email": email, "role": role, "action_count": action})

users.sort(key=lambda x: x["action_count"], reverse=True)

with open("users_summary.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "email", "role", "action_count"])
    writer.writeheader()
    for u in users:
        writer.writerow(u)
PYEOF
