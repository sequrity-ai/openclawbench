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
        f"Email: {user['email']}\nRole: {user['role']}\nAction Items: 0\n"
    )

# Log files
logs_dir = workspace_dir / "logs"
logs_dir.mkdir(exist_ok=True)
(logs_dir / "app.log").write_text("INFO: Application started\nERROR: Connection failed\nWARN: Retry attempt 1\n" * 50)
(logs_dir / "error.log").write_text("ERROR: Database timeout\nERROR: Invalid query\n" * 100)
api_logs = logs_dir / "api"
api_logs.mkdir(exist_ok=True)
(api_logs / "requests.log").write_text("GET /api/users 200\nPOST /api/data 201\n" * 75)
(api_logs / "access.log").write_text("192.168.1.1 - [GET /api/status]\n" * 60)

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
(workspace_dir / "application.log").write_text("\n".join(log_entries) + "\n")

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
