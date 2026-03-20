#!/bin/bash
set -e
WORKSPACE="/workspace"
REWARD_DIR="/logs/verifier"
mkdir -p "$REWARD_DIR"

FILE="$WORKSPACE/department_report.json"
if [ ! -f "$FILE" ]; then
    echo 0 > "$REWARD_DIR/reward.txt"
    exit 0
fi

python3 << 'PYEOF' > "$REWARD_DIR/reward.txt"
import json
with open("/workspace/department_report.json") as f:
    data = json.load(f)
if isinstance(data, list):
    depts = data
elif "departments" in data:
    depts = data["departments"]
else:
    depts = [{"department": k, **v} if isinstance(v, dict) else {"department": k} for k, v in data.items()]
expected = {
    "Engineering": (2, 200000, 120000),
    "Design": (2, 166000, 50000),
    "Marketing": (1, 82000, 75000),
}
matched = 0
for name, (emp, sal, bud) in expected.items():
    for d in depts:
        dname = d.get("department", d.get("name", ""))
        if dname == name:
            if (d.get("employee_count") == emp and
                d.get("total_salary") == sal and
                d.get("total_project_budget", d.get("project_budget")) == bud):
                matched += 1
            break
print(1 if matched == 3 else 0)
PYEOF
