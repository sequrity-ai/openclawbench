#!/usr/bin/env python3
"""Export openclawbench scenarios as Harbor-compatible task directories.

Generates one Harbor task directory per benchmark task, with:
  - instruction.md: task prompt
  - task.toml: configuration and metadata
  - environment/Dockerfile: sandbox with seed files
  - tests/test.sh: validation script that produces reward.txt
  - solution/solve.sh: placeholder reference solution

Usage:
    uv run python scripts/export_harbor.py [--output-dir harbor_tasks]
"""

import argparse
import os
import sys
import textwrap
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.scenarios.file_scenario import FileScenario
from benchmarks.setup.file_setup import FileSetup


def slugify(name: str) -> str:
    """Convert a task name to a filesystem-safe slug."""
    return name.lower().replace(" ", "-").replace("_", "-")


def get_difficulty_timeout(difficulty: str) -> tuple[int, int]:
    """Return (agent_timeout, verifier_timeout) based on difficulty."""
    if difficulty == "easy":
        return 120, 60
    elif difficulty == "medium":
        return 180, 90
    else:  # hard
        return 300, 120


def generate_task_toml(task_name: str, difficulty: str, category: str) -> str:
    """Generate task.toml content."""
    agent_timeout, verifier_timeout = get_difficulty_timeout(difficulty)

    return textwrap.dedent(f"""\
        version = "1.0"

        [metadata]
        author_name = "openclawbench"
        difficulty = "{difficulty}"
        category = "{category}"
        tags = ["file-manipulation", "{category}", "{difficulty}"]

        [agent]
        timeout_sec = {agent_timeout}

        [verifier]
        timeout_sec = {verifier_timeout}

        [environment]
        cpus = 1
        memory_mb = 2048
        storage_mb = 10240
        allow_internet = false
    """)


def generate_dockerfile(workspace_path: str = "/workspace") -> str:
    """Generate Dockerfile that sets up the seed files."""
    return textwrap.dedent(f"""\
        FROM python:3.12-slim

        RUN apt-get update && apt-get install -y --no-install-recommends \\
            coreutils diffutils findutils && \\
            rm -rf /var/lib/apt/lists/*

        WORKDIR {workspace_path}

        # Seed files are created by the setup script
        COPY setup_workspace.py /setup_workspace.py
        RUN python3 /setup_workspace.py "{workspace_path}"
    """)


def generate_setup_workspace_script() -> str:
    """Generate the Python script that creates seed files inside the Docker image.

    This is a standalone script (no project dependencies) that reproduces
    the same seed data as FileSetup.create_workspace().
    """
    # Read the file_setup.py source and extract the create_workspace logic
    # For simplicity, we embed the seed data directly
    return textwrap.dedent('''\
        #!/usr/bin/env python3
        """Create benchmark seed files in the workspace directory."""
        import json
        import os
        import sys
        from datetime import datetime, timedelta
        from pathlib import Path

        workspace_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
        workspace_dir.mkdir(parents=True, exist_ok=True)

        reports_dir = workspace_dir / "reports"
        reports_dir.mkdir(exist_ok=True)

        # data.json
        sample_data = {
            "users": [
                {"name": "Alice Johnson", "email": "alice@example.com", "role": "Engineer"},
                {"name": "Bob Smith", "email": "bob@example.com", "role": "Designer"},
                {"name": "Carol White", "email": "carol@example.com", "role": "Manager"},
            ]
        }
        with open(workspace_dir / "data.json", "w") as f:
            json.dump(sample_data, f, indent=2)

        # notes.txt
        (workspace_dir / "notes.txt").write_text("""Project Kickoff Meeting Notes
Date: 2026-02-11

Attendees: Alice, Bob, Carol

Discussion Points:
- Project timeline and milestones
- Resource allocation
- Communication protocols

Action Items:
- Alice: Set up development environment by Friday
- Bob: Create initial design mockups for review
- Carol: Schedule follow-up meeting for next week
- Everyone: Review project requirements document

Next Steps:
The team will reconvene next Tuesday to review progress and address
any blockers that have come up.
""")

        # Pre-create user profiles
        for user in sample_data["users"]:
            user_dir = workspace_dir / "users" / user["name"]
            user_dir.mkdir(parents=True, exist_ok=True)
            (user_dir / "profile.txt").write_text(
                f"Email: {user[\'email\']}\\nRole: {user[\'role\']}\\nAction Items: 0\\n"
            )

        # Log files
        logs_dir = workspace_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        (logs_dir / "app.log").write_text("INFO: Application started\\nERROR: Connection failed\\nWARN: Retry attempt 1\\n" * 50)
        (logs_dir / "error.log").write_text("ERROR: Database timeout\\nERROR: Invalid query\\n" * 100)
        api_logs = logs_dir / "api"
        api_logs.mkdir(exist_ok=True)
        (api_logs / "requests.log").write_text("GET /api/users 200\\nPOST /api/data 201\\n" * 75)
        (api_logs / "access.log").write_text("192.168.1.1 - [GET /api/status]\\n" * 60)

        # sales_data.csv
        (workspace_dir / "sales_data.csv").write_text("""product,quantity,price,region
Laptop,5,1200,North
Mouse,15,25,South
Keyboard,8,75,East
Monitor,3,300,West
Laptop,7,1200,South
Mouse,20,25,North
Keyboard,10,75,West
Monitor,4,300,East
Laptop,3,1200,East
""")

        # Config files
        (workspace_dir / "config_v1.ini").write_text("""[database]
host = localhost
port = 5432
name = mydb
timeout = 30

[cache]
enabled = true
ttl = 300

[logging]
level = INFO
""")
        (workspace_dir / "config_v2.ini").write_text("""[database]
host = prod-db.example.com
port = 5432
name = mydb
timeout = 60
pool_size = 10

[cache]
enabled = true
ttl = 600

[logging]
level = DEBUG
format = json
""")

        # Data pipeline files
        (reports_dir / "employees.csv").write_text("""emp_id,name,dept_id,salary
101,Alice Johnson,1,95000
102,Bob Smith,2,78000
103,Carol White,1,105000
104,Dave Brown,3,82000
105,Eve Davis,2,88000
""")
        (reports_dir / "departments.json").write_text(json.dumps({
            "departments": [
                {"id": 1, "name": "Engineering", "location": "Building A"},
                {"id": 2, "name": "Design", "location": "Building B"},
                {"id": 3, "name": "Marketing", "location": "Building C"},
            ]
        }, indent=2))
        (reports_dir / "projects.xml").write_text("""<?xml version="1.0"?>
<projects>
  <project><id>1</id><name>Website Redesign</name><dept_id>2</dept_id><budget>50000</budget></project>
  <project><id>2</id><name>Mobile App</name><dept_id>1</dept_id><budget>120000</budget></project>
  <project><id>3</id><name>Brand Campaign</name><dept_id>3</dept_id><budget>75000</budget></project>
</projects>
""")

        # application.log
        base_time = datetime(2024, 2, 15, 9, 0, 0)
        log_entries = []
        for i in range(250):
            timestamp = base_time + timedelta(minutes=i * 2)
            ts = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if i % 10 == 0:
                log_entries.append(f"[{ts}] ERROR: Database connection timeout after 30s")
            elif i % 7 == 0:
                log_entries.append(f"[{ts}] WARN: High memory usage detected: 87%")
            elif i % 15 == 0:
                log_entries.append(f"[{ts}] ERROR: Failed to process request ID {i}: invalid payload")
            else:
                log_entries.append(f"[{ts}] INFO: Request processed successfully ID={i}")
        (workspace_dir / "application.log").write_text("\\n".join(log_entries) + "\\n")

        # inventory.csv (with intentional data quality issues)
        (workspace_dir / "inventory.csv").write_text("""item_id,name,quantity,price,category,last_updated
1001,Widget A,50,19.99,Electronics,2024-02-10
1002,Gadget B,0,45.50,Electronics,2024-02-11
1003,Tool C,-5,12.99,Hardware,2024-02-09
1004,,25,8.99,Office,2024-02-12
1005,Device D,100,299.99,Electronics,2024-02-13
1006,Part E,15,,Hardware,2024-02-11
1007,Supply F,200,5.99,Office,2024-02-10
1008,Widget A,30,19.99,Electronics,2024-02-14
1009,Component G,75,150.00,Electronics,
1010,Material H,0,22.50,Building,2024-02-12
1011,Widget X,50,19.99,Electronics,2024-02-09
1012,Tool Y,-10,15.99,Hardware,2024-02-11
1013,Device Z,5,9999.99,Electronics,2024-02-13
1014,Part A,25,7.50,Hardware,2024-02-10
1015,,40,12.00,Office,2024-02-11
1016,Supply B,100,3.99,Office,2024-02-12
1017,Gadget C,0,55.00,Electronics,2024-02-09
1018,Component D,,89.99,Electronics,2024-02-13
1019,Material E,150,18.75,Building,2024-02-10
1020,Widget A,45,19.99,Electronics,2024-02-14
1021,Tool F,30,25.50,,2024-02-11
1022,Device G,200,449.99,Electronics,2024-02-12
1023,Part H,-3,9.99,Hardware,2024-02-13
1024,Supply C,80,6.50,Office,2024-02-10
1025,Widget B,60,22.99,Electronics,2024-02-11
1026,,15,11.99,Hardware,2024-02-09
1027,Component E,90,175.00,Electronics,2024-02-12
1028,Material F,0,30.00,Building,2024-02-13
1029,Gadget D,35,65.00,Electronics,2024-02-10
1030,Tool G,50,,Hardware,2024-02-11
1031,Device H,120,349.99,Electronics,2024-02-12
1032,Part I,25,14.99,Hardware,2024-02-09
1033,Supply D,150,4.50,Office,2024-02-13
1034,Widget C,-8,24.99,Electronics,2024-02-10
1035,Component F,200,225.00,,2024-02-11
1036,Material G,75,45.00,Building,2024-02-12
1037,,100,8.50,Office,2024-02-13
1038,Gadget E,0,75.00,Electronics,2024-02-09
1039,Tool H,40,19.50,Hardware,2024-02-10
1040,Device I,85,399.99,Electronics,2024-02-11
1041,Part J,-2,16.99,Hardware,2024-02-12
1042,Supply E,110,5.25,Office,2024-02-13
1043,Widget D,55,27.99,Electronics,2024-02-09
1044,Component G,130,,Electronics,2024-02-10
1045,Material H,0,38.50,Building,2024-02-11
1046,Gadget F,20,85.00,Electronics,2024-02-12
1047,Tool I,65,22.50,Hardware,2024-02-13
1048,Device J,95,299.99,,2024-02-09
1049,Part K,30,12.50,Hardware,2024-02-10
1050,Supply F,140,7.99,Office,2024-02-11
""")

        print(f"Workspace created at {workspace_dir}")
    ''')


# Test scripts for each task — maps task name to shell script content
# Each script checks the agent's output and writes 1 or 0 to /logs/verifier/reward.txt
TEST_SCRIPTS = {
    "File Organization": textwrap.dedent("""\
        #!/bin/bash
        set -e
        WORKSPACE="/workspace"
        REWARD_DIR="/logs/verifier"
        mkdir -p "$REWARD_DIR"

        PASS=1
        for region in North South East West; do
            FILE="$WORKSPACE/by_region/$region/sales.csv"
            if [ ! -f "$FILE" ]; then
                echo "FAIL: Missing $FILE"
                PASS=0
            fi
        done

        echo $PASS > "$REWARD_DIR/reward.txt"
    """),

    "File Modification": textwrap.dedent("""\
        #!/bin/bash
        set -e
        WORKSPACE="/workspace"
        REWARD_DIR="/logs/verifier"
        mkdir -p "$REWARD_DIR"

        PASS=1
        for user in "Alice Johnson" "Bob Smith" "Carol White"; do
            FILE="$WORKSPACE/users/$user/profile.txt"
            if [ ! -f "$FILE" ]; then
                echo "FAIL: Missing $FILE"
                PASS=0
                continue
            fi
            if ! grep -q "Action Items: 1" "$FILE"; then
                echo "FAIL: $user profile missing 'Action Items: 1'"
                PASS=0
            fi
        done

        echo $PASS > "$REWARD_DIR/reward.txt"
    """),

    "File Consolidation": textwrap.dedent("""\
        #!/bin/bash
        set -e
        WORKSPACE="/workspace"
        REWARD_DIR="/logs/verifier"
        mkdir -p "$REWARD_DIR"

        FILE="$WORKSPACE/users_summary.csv"
        if [ ! -f "$FILE" ]; then
            echo "FAIL: users_summary.csv not found"
            echo 0 > "$REWARD_DIR/reward.txt"
            exit 0
        fi

        # Check columns and data
        PASS=1
        if ! head -1 "$FILE" | grep -qi "name"; then
            PASS=0
        fi
        LINES=$(wc -l < "$FILE")
        if [ "$LINES" -lt 4 ]; then
            PASS=0
        fi

        echo $PASS > "$REWARD_DIR/reward.txt"
    """),

    "Recursive File Search": textwrap.dedent("""\
        #!/bin/bash
        set -e
        WORKSPACE="/workspace"
        REWARD_DIR="/logs/verifier"
        mkdir -p "$REWARD_DIR"

        FILE="$WORKSPACE/log_summary.txt"
        if [ ! -f "$FILE" ]; then
            echo 0 > "$REWARD_DIR/reward.txt"
            exit 0
        fi

        PASS=1
        for logfile in app.log error.log requests.log access.log; do
            if ! grep -q "$logfile" "$FILE"; then
                echo "FAIL: Missing $logfile in summary"
                PASS=0
            fi
        done

        echo $PASS > "$REWARD_DIR/reward.txt"
    """),

    "Data Transformation": textwrap.dedent("""\
        #!/bin/bash
        set -e
        WORKSPACE="/workspace"
        REWARD_DIR="/logs/verifier"
        mkdir -p "$REWARD_DIR"

        FILE="$WORKSPACE/sales_report.json"
        if [ ! -f "$FILE" ]; then
            echo 0 > "$REWARD_DIR/reward.txt"
            exit 0
        fi

        python3 << 'PYEOF' > "$REWARD_DIR/reward.txt"
        import json
        with open("/workspace/sales_report.json") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if "products" in data:
                items = data["products"]
            else:
                items = [{"product": k, **v} if isinstance(v, dict) else {"product": k} for k, v in data.items()]
        else:
            items = data
        expected = {"Laptop": (15, 18000), "Mouse": (35, 875), "Keyboard": (18, 1350), "Monitor": (7, 2100)}
        matched = 0
        for name, (qty, rev) in expected.items():
            for item in items:
                pname = item.get("product", item.get("name", ""))
                if pname == name and item.get("total_quantity") == qty and item.get("total_revenue") == rev:
                    matched += 1
                    break
        print(1 if matched == 4 else 0)
        PYEOF
    """),

    "File Comparison": textwrap.dedent("""\
        #!/bin/bash
        set -e
        WORKSPACE="/workspace"
        REWARD_DIR="/logs/verifier"
        mkdir -p "$REWARD_DIR"

        FILE="$WORKSPACE/config_diff.txt"
        if [ ! -f "$FILE" ]; then
            echo 0 > "$REWARD_DIR/reward.txt"
            exit 0
        fi

        CONTENT=$(cat "$FILE" | tr '[:upper:]' '[:lower:]')
        PASS=1
        # Check key differences are mentioned
        echo "$CONTENT" | grep -q "localhost" || PASS=0
        echo "$CONTENT" | grep -q "prod-db" || PASS=0
        echo "$CONTENT" | grep -q "pool" || PASS=0
        echo "$CONTENT" | grep -q "debug" || PASS=0

        echo $PASS > "$REWARD_DIR/reward.txt"
    """),

    "Multi-Step Data Pipeline": textwrap.dedent("""\
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
    """),

    "Advanced Log Analysis": textwrap.dedent("""\
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
    """),

    "Data Validation Report": textwrap.dedent("""\
        #!/bin/bash
        set -e
        WORKSPACE="/workspace"
        REWARD_DIR="/logs/verifier"
        mkdir -p "$REWARD_DIR"

        FILE="$WORKSPACE/validation_report.json"
        if [ ! -f "$FILE" ]; then
            echo 0 > "$REWARD_DIR/reward.txt"
            exit 0
        fi

        python3 << 'PYEOF' > "$REWARD_DIR/reward.txt"
        import json
        with open("/workspace/validation_report.json") as f:
            data = json.load(f)
        s = json.dumps(data).lower()
        missing_name = "1004" in s or "1015" in s
        neg_qty = "1003" in s or "1012" in s
        dup = "widget a" in s
        print(1 if (missing_name and neg_qty and dup) else 0)
        PYEOF
    """),
}


def export_task(task, output_dir: Path, workspace_path: str = "/workspace") -> Path:
    """Export a single BenchmarkTask as a Harbor task directory."""
    difficulty = task.metadata.get("difficulty", "medium")
    category = task.metadata.get("category", "general")
    task_slug = slugify(task.name)
    task_dir = output_dir / task_slug

    # Create directory structure
    for subdir in ["environment", "tests", "solution"]:
        (task_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Rewrite prompt to use /workspace instead of /tmp/openclaw_benchmark
    prompt = task.prompt.replace("/tmp/openclaw_benchmark", workspace_path)

    # instruction.md
    (task_dir / "instruction.md").write_text(
        f"# {task.name}\n\n{prompt}\n"
    )

    # task.toml
    (task_dir / "task.toml").write_text(
        generate_task_toml(task.name, difficulty, category)
    )

    # environment/Dockerfile
    (task_dir / "environment" / "Dockerfile").write_text(
        generate_dockerfile(workspace_path)
    )

    # environment/setup_workspace.py
    setup_script = generate_setup_workspace_script()
    # The script is generated with consistent 8-space indent; strip it
    lines = setup_script.split("\n")
    stripped = []
    for line in lines:
        if line and line[:8] == "        ":
            stripped.append(line[8:])
        else:
            stripped.append(line)
    (task_dir / "environment" / "setup_workspace.py").write_text("\n".join(stripped))

    # tests/test.sh
    test_script = TEST_SCRIPTS.get(task.name, "#!/bin/bash\necho 0 > /logs/verifier/reward.txt\n")
    (task_dir / "tests" / "test.sh").write_text(test_script)
    os.chmod(task_dir / "tests" / "test.sh", 0o755)

    # solution/solve.sh (placeholder)
    (task_dir / "solution" / "solve.sh").write_text(
        f"#!/bin/bash\n# Reference solution for: {task.name}\n# TODO: implement\nexit 0\n"
    )
    os.chmod(task_dir / "solution" / "solve.sh", 0o755)

    return task_dir


def main():
    parser = argparse.ArgumentParser(description="Export openclawbench scenarios as Harbor tasks")
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("tasks/file"),
        help="Output directory for Harbor task directories (default: tasks/file/)",
    )
    parser.add_argument(
        "--workspace-path",
        default="/workspace",
        help="Workspace path inside the Harbor container (default: /workspace)",
    )
    args = parser.parse_args()

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build file scenario to get task definitions
    scenario = FileScenario(remote_manager=None)

    print(f"Exporting {len(scenario.tasks)} tasks to {output_dir}/\n")

    for task in scenario.tasks:
        task_dir = export_task(task, output_dir, args.workspace_path)
        difficulty = task.metadata.get("difficulty", "?")
        print(f"  [{difficulty}] {task.name} -> {task_dir}")

    print(f"\nDone. {len(scenario.tasks)} Harbor tasks exported to {output_dir}/")
    print(f"\nRun a task with:")
    print(f"  harbor run -p \"{output_dir}/<task-name>\" -a \"<agent>\" -m \"<model>\"")


if __name__ == "__main__":
    main()
