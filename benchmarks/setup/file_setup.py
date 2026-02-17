"""Setup utilities for file manipulation benchmark scenario."""

import json
import os
import shutil
from pathlib import Path


class FileSetup:
    """Handles setup and cleanup for file manipulation benchmarks."""

    def __init__(self, workspace_dir: str = "/tmp/openclaw_benchmark"):
        """Initialize file setup.

        Args:
            workspace_dir: Directory for test files
        """
        self.workspace_dir = Path(workspace_dir)
        self.data_json_path = self.workspace_dir / "data.json"
        self.notes_txt_path = self.workspace_dir / "notes.txt"
        self.reports_dir = self.workspace_dir / "reports"

    def create_workspace(self) -> dict[str, str]:
        """Create test workspace with seed files.

        Returns:
            Dict with paths to created files
        """
        # Create directories
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)

        # Create data.json with sample user records
        sample_data = {
            "users": [
                {"name": "Alice Johnson", "email": "alice@example.com", "role": "Engineer"},
                {"name": "Bob Smith", "email": "bob@example.com", "role": "Designer"},
                {"name": "Carol White", "email": "carol@example.com", "role": "Manager"},
            ]
        }

        with open(self.data_json_path, "w") as f:
            json.dump(sample_data, f, indent=2)

        # Create notes.txt with meeting notes
        notes_content = """Project Kickoff Meeting Notes
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
"""

        with open(self.notes_txt_path, "w") as f:
            f.write(notes_content)

        # MEDIUM Task 1: Create nested log files for recursive search
        logs_dir = self.workspace_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        (logs_dir / "app.log").write_text("INFO: Application started\nERROR: Connection failed\nWARN: Retry attempt 1\n" * 50)
        (logs_dir / "error.log").write_text("ERROR: Database timeout\nERROR: Invalid query\n" * 100)

        api_logs = logs_dir / "api"
        api_logs.mkdir(exist_ok=True)
        (api_logs / "requests.log").write_text("GET /api/users 200\nPOST /api/data 201\n" * 75)
        (api_logs / "access.log").write_text("192.168.1.1 - [GET /api/status]\n" * 60)

        # MEDIUM Task 2: Create sales data CSV for transformation
        sales_csv = self.workspace_dir / "sales_data.csv"
        sales_csv.write_text("""product,quantity,price,region
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

        # MEDIUM Task 3: Create config files for comparison
        config_v1 = self.workspace_dir / "config_v1.ini"
        config_v1.write_text("""[database]
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

        config_v2 = self.workspace_dir / "config_v2.ini"
        config_v2.write_text("""[database]
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

        # HARD Task 2: Create multiple data sources for multi-step pipeline
        # CSV file
        employees_csv = self.reports_dir / "employees.csv"
        employees_csv.write_text("""emp_id,name,dept_id,salary
101,Alice Johnson,1,95000
102,Bob Smith,2,78000
103,Carol White,1,105000
104,Dave Brown,3,82000
105,Eve Davis,2,88000
""")

        # JSON file
        departments_json = self.reports_dir / "departments.json"
        departments_json.write_text("""{
  "departments": [
    {"id": 1, "name": "Engineering", "location": "Building A"},
    {"id": 2, "name": "Design", "location": "Building B"},
    {"id": 3, "name": "Marketing", "location": "Building C"}
  ]
}
""")

        # XML file
        projects_xml = self.reports_dir / "projects.xml"
        projects_xml.write_text("""<?xml version="1.0"?>
<projects>
  <project>
    <id>1</id>
    <name>Website Redesign</name>
    <dept_id>2</dept_id>
    <budget>50000</budget>
  </project>
  <project>
    <id>2</id>
    <name>Mobile App</name>
    <dept_id>1</dept_id>
    <budget>120000</budget>
  </project>
  <project>
    <id>3</id>
    <name>Brand Campaign</name>
    <dept_id>3</dept_id>
    <budget>75000</budget>
  </project>
</projects>
""")

        # HARD Task 8: Create application log for advanced analysis
        application_log = self.workspace_dir / "application.log"
        log_entries = []
        from datetime import datetime, timedelta
        base_time = datetime(2024, 2, 15, 9, 0, 0)

        # Generate 200+ log entries with various levels and timestamps
        for i in range(250):
            timestamp = base_time + timedelta(minutes=i*2)
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            if i % 10 == 0:
                log_entries.append(f"[{time_str}] ERROR: Database connection timeout after 30s")
            elif i % 7 == 0:
                log_entries.append(f"[{time_str}] WARN: High memory usage detected: 87%")
            elif i % 15 == 0:
                log_entries.append(f"[{time_str}] ERROR: Failed to process request ID {i}: invalid payload")
            else:
                log_entries.append(f"[{time_str}] INFO: Request processed successfully ID={i}")

        application_log.write_text("\n".join(log_entries) + "\n")

        # HARD Task 9: Create inventory CSV with data quality issues
        inventory_csv = self.workspace_dir / "inventory.csv"
        inventory_csv.write_text("""item_id,name,quantity,price,category,last_updated
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

        return {
            "workspace_dir": str(self.workspace_dir),
            "data_json": str(self.data_json_path),
            "notes_txt": str(self.notes_txt_path),
            "reports_dir": str(self.reports_dir),
            "expected_users": sample_data["users"],
            "logs_dir": str(logs_dir),
            "sales_csv": str(sales_csv),
            "config_v1": str(config_v1),
            "config_v2": str(config_v2),
            "employees_csv": str(employees_csv),
            "departments_json": str(departments_json),
            "projects_xml": str(projects_xml),
            "application_log": str(application_log),
            "inventory_csv": str(inventory_csv),
        }

    def cleanup_workspace(self) -> bool:
        """Remove test workspace.

        Returns:
            True if cleanup succeeded
        """
        try:
            if self.workspace_dir.exists():
                shutil.rmtree(self.workspace_dir)
            return True
        except Exception as e:
            print(f"Cleanup error: {e}")
            return False

    def verify_workspace_access(self) -> bool:
        """Verify we can read/write to workspace.

        Returns:
            True if workspace is accessible
        """
        try:
            # Try to create a test file
            test_file = self.workspace_dir / ".test"
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            test_file.write_text("test")
            test_file.unlink()
            return True
        except Exception:
            return False
