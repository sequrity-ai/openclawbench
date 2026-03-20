"""Daytona sandbox workspace manager for benchmark setup and validation.

Drop-in replacement for RemoteWorkspaceManager that uses the Daytona SDK
instead of SSH/SFTP for sandbox lifecycle, file operations, and command execution.
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

from daytona_sdk import (
    Daytona,
    DaytonaConfig,
    CreateSandboxFromImageParams,
    FileUpload,
    Resources,
)

from benchmarks.base import TaskResult, SetupResult, CheckStatus

logger = logging.getLogger(__name__)


class DaytonaWorkspaceManager:
    """Manages sandbox workspace via Daytona SDK for benchmark setup and validation."""

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://app.daytona.io/api",
        image: str = "ubuntu:22.04",
        workspace_path: str = "/tmp/openclaw_benchmark",
        resources: Resources | None = None,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.image = image
        self.workspace_path = workspace_path
        self.resources = resources

        self._daytona: Daytona | None = None
        self._sandbox = None

    def _get_client(self) -> Daytona:
        if self._daytona is None:
            self._daytona = Daytona(DaytonaConfig(
                api_key=self.api_key,
                api_url=self.api_url,
            ))
        return self._daytona

    def connect(self) -> None:
        """Create and start a Daytona sandbox."""
        if self._sandbox is not None:
            return

        logger.info("Creating Daytona sandbox...")
        client = self._get_client()

        params = CreateSandboxFromImageParams(
            image=self.image,
            resources=self.resources,
            labels={"purpose": "openclawbench"},
        )

        self._sandbox = client.create(params, timeout=120)
        logger.info(f"Sandbox created: {self._sandbox.id}")

    def disconnect(self) -> None:
        """Stop and delete the Daytona sandbox."""
        if self._sandbox is not None:
            sandbox_id = self._sandbox.id
            try:
                client = self._get_client()
                client.delete(self._sandbox)
                logger.info(f"Sandbox deleted: {sandbox_id}")
            except Exception as e:
                logger.warning(f"Failed to delete sandbox {sandbox_id}: {e}")
            self._sandbox = None

    def _exec_command(self, command: str) -> tuple[int, str, str]:
        """Execute command in the sandbox.

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if self._sandbox is None:
            raise RuntimeError("Not connected. Call connect() first.")

        logger.debug(f"Executing sandbox command: {command}")
        result = self._sandbox.process.exec(command, timeout=60)

        exit_code = result.exit_code if hasattr(result, 'exit_code') else 0
        stdout = result.result if hasattr(result, 'result') else str(result)
        # Daytona exec returns combined output; separate stderr isn't always available
        stderr = ""

        if exit_code != 0:
            logger.warning(f"Command failed (exit {exit_code}): {stdout}")

        return exit_code, stdout, stderr

    def _upload_content(self, content: str, remote_path: str) -> None:
        """Upload string content to a file in the sandbox."""
        self._sandbox.fs.upload_file(content.encode("utf-8"), remote_path)
        logger.debug(f"Uploaded {len(content)} bytes to {remote_path}")

    def _upload_json(self, data: Any, remote_path: str) -> None:
        """Upload JSON data to a file in the sandbox."""
        self._upload_content(json.dumps(data, indent=2), remote_path)

    def remote_setup(self) -> SetupResult:
        """Setup workspace in the Daytona sandbox.

        Creates workspace directory structure and uploads seed files.
        """
        try:
            self.connect()

            # 1. Purge old workspace
            logger.info(f"Purging old workspace: {self.workspace_path}")
            self._exec_command(f"rm -rf {self.workspace_path}")

            # 2. Create workspace structure
            logger.info(f"Creating workspace structure: {self.workspace_path}")
            reports_dir = f"{self.workspace_path}/reports"
            exit_code, stdout, stderr = self._exec_command(f"mkdir -p {reports_dir}")
            if exit_code != 0:
                return SetupResult(
                    status=CheckStatus.FAIL,
                    message=f"Failed to create workspace: {stdout}",
                    error=stdout,
                )

            # 3. Upload data.json
            sample_data = {
                "users": [
                    {"name": "Alice Johnson", "email": "alice@example.com", "role": "Engineer"},
                    {"name": "Bob Smith", "email": "bob@example.com", "role": "Designer"},
                    {"name": "Carol White", "email": "carol@example.com", "role": "Manager"},
                ]
            }
            remote_data_json = f"{self.workspace_path}/data.json"
            self._upload_json(sample_data, remote_data_json)
            logger.info(f"Uploaded data.json to {remote_data_json}")

            # 4. Upload notes.txt
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
            remote_notes_txt = f"{self.workspace_path}/notes.txt"
            self._upload_content(notes_content, remote_notes_txt)
            logger.info(f"Uploaded notes.txt to {remote_notes_txt}")

            # 5. Create logs directory structure
            logs_dir = f"{self.workspace_path}/logs"
            api_logs_dir = f"{logs_dir}/api"
            self._exec_command(f"mkdir -p {api_logs_dir}")

            log_files = {
                f"{logs_dir}/app.log": "INFO: Application started\nERROR: Connection failed\nWARN: Retry attempt 1\n" * 50,
                f"{logs_dir}/error.log": "ERROR: Database timeout\nERROR: Invalid query\n" * 100,
                f"{api_logs_dir}/requests.log": "GET /api/users 200\nPOST /api/data 201\n" * 75,
                f"{api_logs_dir}/access.log": "192.168.1.1 - [GET /api/status]\n" * 60,
            }
            for remote_path, content in log_files.items():
                self._upload_content(content, remote_path)
                logger.info(f"Uploaded {remote_path}")

            # 6. Upload sales_data.csv
            sales_csv_content = """product,quantity,price,region
Laptop,5,1200,North
Mouse,15,25,South
Keyboard,8,75,East
Monitor,3,300,West
Laptop,7,1200,South
Mouse,20,25,North
Keyboard,10,75,West
Monitor,4,300,East
Laptop,3,1200,East
"""
            remote_sales_csv = f"{self.workspace_path}/sales_data.csv"
            self._upload_content(sales_csv_content, remote_sales_csv)
            logger.info(f"Uploaded sales_data.csv")

            # 7. Upload config files
            config_v1_content = """[database]
host = localhost
port = 5432
name = mydb
timeout = 30

[cache]
enabled = true
ttl = 300

[logging]
level = INFO
"""
            config_v2_content = """[database]
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
"""
            for filename, content in [("config_v1.ini", config_v1_content), ("config_v2.ini", config_v2_content)]:
                self._upload_content(content, f"{self.workspace_path}/{filename}")
                logger.info(f"Uploaded {filename}")

            # 8. Upload data pipeline files
            employees_csv_content = """emp_id,name,dept_id,salary
101,Alice Johnson,1,95000
102,Bob Smith,2,78000
103,Carol White,1,105000
104,Dave Brown,3,82000
105,Eve Davis,2,88000
"""
            departments_json_content = """{
  "departments": [
    {"id": 1, "name": "Engineering", "location": "Building A"},
    {"id": 2, "name": "Design", "location": "Building B"},
    {"id": 3, "name": "Marketing", "location": "Building C"}
  ]
}
"""
            projects_xml_content = """<?xml version="1.0"?>
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
"""
            self._upload_content(employees_csv_content, f"{reports_dir}/employees.csv")
            self._upload_json(json.loads(departments_json_content), f"{reports_dir}/departments.json")
            self._upload_content(projects_xml_content, f"{reports_dir}/projects.xml")
            logger.info("Uploaded data pipeline files")

            # 9. Upload application.log
            from datetime import datetime, timedelta
            base_time = datetime(2024, 2, 15, 9, 0, 0)
            log_entries = []
            for i in range(250):
                timestamp = base_time + timedelta(minutes=i * 2)
                time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                if i % 10 == 0:
                    log_entries.append(f"[{time_str}] ERROR: Database connection timeout after 30s")
                elif i % 7 == 0:
                    log_entries.append(f"[{time_str}] WARN: High memory usage detected: 87%")
                elif i % 15 == 0:
                    log_entries.append(f"[{time_str}] ERROR: Failed to process request ID {i}: invalid payload")
                else:
                    log_entries.append(f"[{time_str}] INFO: Request processed successfully ID={i}")

            self._upload_content("\n".join(log_entries) + "\n", f"{self.workspace_path}/application.log")
            logger.info("Uploaded application.log")

            # 10. Upload inventory.csv
            inventory_csv_content = """item_id,name,quantity,price,category,last_updated
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
"""
            self._upload_content(inventory_csv_content, f"{self.workspace_path}/inventory.csv")
            logger.info("Uploaded inventory.csv")

            # Pre-create user profile directories
            for user in sample_data["users"]:
                user_dir = f"{self.workspace_path}/users/{user['name']}"
                self._exec_command(f"mkdir -p '{user_dir}'")
                profile_content = f"Email: {user['email']}\nRole: {user['role']}\nAction Items: 0\n"
                self._upload_content(profile_content, f"{user_dir}/profile.txt")

            logger.info("Remote setup complete")

            return SetupResult(
                status=CheckStatus.PASS,
                message="Daytona sandbox workspace created successfully",
                setup_data={
                    "workspace_dir": self.workspace_path,
                    "data_json": remote_data_json,
                    "notes_txt": remote_notes_txt,
                    "reports_dir": reports_dir,
                    "expected_users": sample_data["users"],
                    "logs_dir": logs_dir,
                    "sales_csv": remote_sales_csv,
                    "config_v1": f"{self.workspace_path}/config_v1.ini",
                    "config_v2": f"{self.workspace_path}/config_v2.ini",
                    "employees_csv": f"{reports_dir}/employees.csv",
                    "departments_json": f"{reports_dir}/departments.json",
                    "projects_xml": f"{reports_dir}/projects.xml",
                    "application_log": f"{self.workspace_path}/application.log",
                    "inventory_csv": f"{self.workspace_path}/inventory.csv",
                },
            )

        except Exception as e:
            logger.error(f"Daytona setup failed: {e}")
            return SetupResult(
                status=CheckStatus.FAIL,
                message=f"Daytona setup error: {str(e)}",
                error=str(e),
            )

    def remote_validate(
        self,
        task_name: str,
        validation_fn: Callable[[str, dict[str, Any]], TaskResult],
        setup_data: dict[str, Any],
    ) -> TaskResult:
        """Download files from sandbox and validate locally."""
        temp_dir = None
        try:
            self.connect()

            temp_dir = tempfile.mkdtemp(prefix="openclaw_daytona_validate_")
            logger.info(f"Downloading files from {self.workspace_path} to {temp_dir}...")

            self._download_directory_recursive(self.workspace_path, temp_dir)

            logger.info("Files downloaded, running validation...")

            local_setup_data = setup_data.copy()
            local_setup_data["workspace_dir"] = temp_dir
            local_setup_data["data_json"] = os.path.join(temp_dir, "data.json")
            local_setup_data["notes_txt"] = os.path.join(temp_dir, "notes.txt")
            local_setup_data["reports_dir"] = os.path.join(temp_dir, "reports")

            docs_dir = os.path.join(temp_dir, "documents")
            local_setup_data["documents_dir"] = docs_dir
            local_setup_data["business_article"] = os.path.join(docs_dir, "business_report.txt")
            local_setup_data["technical_doc"] = os.path.join(docs_dir, "technical_paper.txt")
            local_setup_data["article_a"] = os.path.join(docs_dir, "ai_article_a.txt")
            local_setup_data["article_b"] = os.path.join(docs_dir, "ai_article_b.txt")
            local_setup_data["long_article"] = os.path.join(docs_dir, "quantum_computing.txt")
            local_setup_data["qa_article"] = os.path.join(docs_dir, "renewable_energy.txt")
            local_setup_data["sentiment_article"] = os.path.join(docs_dir, "social_media_impact.txt")

            validation_result = validation_fn("", local_setup_data)

            if validation_result.success:
                logger.info(
                    f"Validation complete: success={validation_result.success}, "
                    f"accuracy={validation_result.accuracy_score:.1f}%"
                )
            else:
                logger.warning(
                    f"Validation complete: success={validation_result.success}, "
                    f"accuracy={validation_result.accuracy_score:.1f}% - "
                    f"reason: {validation_result.error_message}"
                )

            return validation_result

        except Exception as e:
            logger.error(f"Daytona validation failed for {task_name}: {e}")
            return TaskResult(
                task_name=task_name,
                prompt="",
                success=False,
                latency=0.0,
                accuracy_score=0.0,
                error_message=f"Daytona validation error: {str(e)}",
            )
        finally:
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)

    def _download_directory_recursive(self, remote_dir: str, local_dir: str) -> None:
        """Recursively download directory from sandbox."""
        try:
            os.makedirs(local_dir, exist_ok=True)

            items = self._sandbox.fs.list_files(remote_dir)

            for item in items:
                name = item.name if hasattr(item, 'name') else str(item)
                remote_path = f"{remote_dir}/{name}"
                local_path = os.path.join(local_dir, name)

                is_dir = item.is_dir if hasattr(item, 'is_dir') else False
                if is_dir:
                    self._download_directory_recursive(remote_path, local_path)
                else:
                    data = self._sandbox.fs.download_file(remote_path)
                    if data is not None:
                        with open(local_path, "wb") as f:
                            f.write(data)

        except Exception as e:
            logger.warning(f"Error downloading {remote_dir}: {e}")

    def list_models(self) -> list[str]:
        """List available models via openclaw CLI in the sandbox."""
        self.connect()
        logger.info("Listing available models in Daytona sandbox")

        exit_code, stdout, stderr = self._exec_command("openclaw models list --json")
        if exit_code != 0:
            raise RuntimeError(f"Failed to list models: {(stdout + stderr).strip()}")

        try:
            data = json.loads(stdout.strip())
            models: list[str] = []
            items: list = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for val in data.values():
                    if isinstance(val, list):
                        items = val
                        break
            for item in items:
                if isinstance(item, str):
                    models.append(item)
                elif isinstance(item, dict):
                    for k in ("key", "id", "model", "name"):
                        if k in item:
                            models.append(str(item[k]))
                            break
            logger.info(f"Found {len(models)} model(s): {models}")
            return models
        except json.JSONDecodeError:
            raise RuntimeError(f"Could not parse model list output: {stdout[:200]}")

    def switch_model(self, model: str) -> str:
        """Switch the openclaw model in the sandbox."""
        self.connect()
        logger.info(f"Switching sandbox model to: {model}")

        exit_code, stdout, stderr = self._exec_command(f"openclaw models set {model}")
        output = (stdout + stderr).strip()
        if exit_code != 0:
            raise RuntimeError(f"Failed to switch model to {model!r}: {output}")
        logger.info(f"Model switched to {model}: {output}")

        exit_code2, stdout2, stderr2 = self._exec_command("openclaw models fallbacks clear")
        if exit_code2 == 0:
            logger.info("Cleared model fallbacks for benchmark isolation")
        return output

    def remote_cleanup(self) -> bool:
        """Remove workspace and delete the sandbox."""
        try:
            if self._sandbox is not None:
                logger.info(f"Cleaning up Daytona sandbox workspace: {self.workspace_path}")
                self._exec_command(f"rm -rf {self.workspace_path}")
                self.disconnect()
                logger.info("Daytona cleanup complete")
            return True
        except Exception as e:
            logger.error(f"Daytona cleanup failed: {e}")
            return False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
