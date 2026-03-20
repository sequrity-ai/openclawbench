#!/bin/bash
# Reference solution for: Advanced Log Analysis
cd /workspace

python3 << 'PYEOF'
import json
import re
from collections import defaultdict

with open("application.log") as f:
    lines = [l.strip() for l in f if l.strip()]

error_count = 0
warn_count = 0
info_count = 0
hourly = defaultdict(int)

for line in lines:
    if "] ERROR:" in line:
        error_count += 1
    elif "] WARN:" in line:
        warn_count += 1
    elif "] INFO:" in line:
        info_count += 1

    m = re.search(r"\[\d{4}-\d{2}-\d{2} (\d{2}):\d{2}:\d{2}\]", line)
    if m:
        hourly[m.group(1)] += 1

result = {
    "error_count": error_count,
    "warn_count": warn_count,
    "info_count": info_count,
    "total_entries": len(lines),
    "hourly_distribution": dict(sorted(hourly.items())),
}

with open("log_analysis.json", "w") as f:
    json.dump(result, f, indent=2)
PYEOF
