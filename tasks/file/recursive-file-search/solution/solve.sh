#!/bin/bash
# Reference solution for: Recursive File Search
cd /workspace

python3 << 'PYEOF'
import os

results = []
for root, dirs, files in os.walk("logs"):
    for f in files:
        if f.endswith(".log"):
            path = os.path.join(root, f)
            size = os.path.getsize(path)
            results.append(f"{path} ({size} bytes)")

with open("log_summary.txt", "w") as out:
    out.write("Log File Summary\n")
    out.write("=" * 40 + "\n")
    for r in results:
        out.write(r + "\n")
PYEOF
