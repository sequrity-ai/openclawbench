"""Remote workspace manager for SSH-based setup and validation."""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

import paramiko
from paramiko import SSHClient, SFTPClient

from benchmarks.base import TaskResult, SetupResult, CheckStatus

logger = logging.getLogger(__name__)


class RemoteWorkspaceManager:
    """Manages remote workspace via SSH for benchmark setup and validation."""

    def __init__(
        self,
        host: str,
        port: int = 22,
        user: str = "ubuntu",
        key_path: str | None = None,
        password: str | None = None,
        workspace_path: str = "/tmp/openclaw_benchmark",
        key_passphrase: str | None = None,
    ):
        """Initialize remote workspace manager.

        Args:
            host: SSH host (bot server hostname/IP)
            port: SSH port
            user: SSH username
            key_path: Path to SSH private key file (optional)
            password: SSH password (optional, use key_path if possible)
            workspace_path: Remote workspace directory path
            key_passphrase: Passphrase for encrypted SSH key (optional)
        """
        self.host = host
        self.port = port
        self.user = user
        self.key_path = key_path
        self.password = password
        self.workspace_path = workspace_path
        self.key_passphrase = key_passphrase

        self.ssh_client: SSHClient | None = None
        self.sftp_client: SFTPClient | None = None

    def connect(self) -> None:
        """Establish SSH connection to remote server."""
        if self.ssh_client and self.ssh_client.get_transport() and self.ssh_client.get_transport().is_active():
            return  # Already connected

        logger.info(f"Connecting to {self.user}@{self.host}:{self.port}...")

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if self.key_path:
                # Use key-based authentication
                key_path_expanded = os.path.expanduser(self.key_path)
                try:
                    self.ssh_client.connect(
                        hostname=self.host,
                        port=self.port,
                        username=self.user,
                        key_filename=key_path_expanded,
                        passphrase=self.key_passphrase,  # Support encrypted keys
                        timeout=10,
                        allow_agent=True,  # Allow ssh-agent
                    )
                except paramiko.ssh_exception.SSHException as key_error:
                    # If key file fails, try ssh-agent as fallback
                    logger.warning(f"Key file authentication failed: {key_error}. Trying ssh-agent...")
                    self.ssh_client.connect(
                        hostname=self.host,
                        port=self.port,
                        username=self.user,
                        timeout=10,
                        allow_agent=True,
                        look_for_keys=False,  # Don't auto-discover keys
                    )
            elif self.password:
                # Use password authentication
                self.ssh_client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.user,
                    password=self.password,
                    timeout=10,
                )
            else:
                # Try ssh-agent without key file
                logger.info("No key_path or password provided, trying ssh-agent...")
                self.ssh_client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.user,
                    timeout=10,
                    allow_agent=True,
                )

            self.sftp_client = self.ssh_client.open_sftp()
            logger.info(f"✓ Connected to {self.host}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}: {e}")
            # Clean up on connection failure
            if self.ssh_client:
                try:
                    self.ssh_client.close()
                except:
                    pass
                self.ssh_client = None
            self.sftp_client = None
            raise

    def disconnect(self) -> None:
        """Close SSH connection."""
        if self.sftp_client:
            self.sftp_client.close()
            self.sftp_client = None
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
        logger.info(f"Disconnected from {self.host}")

    def _exec_command(self, command: str) -> tuple[int, str, str]:
        """Execute command on remote server.

        Args:
            command: Shell command to execute

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if not self.ssh_client:
            raise RuntimeError("Not connected. Call connect() first.")

        logger.debug(f"Executing remote command: {command}")
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        stdout_str = stdout.read().decode("utf-8")
        stderr_str = stderr.read().decode("utf-8")

        if exit_code != 0:
            logger.warning(f"Command failed (exit {exit_code}): {stderr_str}")

        return exit_code, stdout_str, stderr_str

    def remote_setup(self) -> SetupResult:
        """Setup workspace on remote bot server.

        Creates workspace directory structure and uploads seed files.

        Returns:
            SetupResult with setup data
        """
        try:
            self.connect()

            # 1. Purge old workspace
            logger.info(f"Purging old workspace: {self.workspace_path}")
            exit_code, stdout, stderr = self._exec_command(f"rm -rf {self.workspace_path}")
            if exit_code != 0:
                logger.warning(f"Workspace purge warning: {stderr}")

            # 2. Create workspace structure
            logger.info(f"Creating workspace structure: {self.workspace_path}")
            reports_dir = f"{self.workspace_path}/reports"
            exit_code, stdout, stderr = self._exec_command(f"mkdir -p {reports_dir}")
            if exit_code != 0:
                return SetupResult(
                    status=CheckStatus.FAIL,
                    message=f"Failed to create workspace: {stderr}",
                    error=stderr,
                )

            # 3. Upload data.json
            logger.info("Uploading data.json...")
            sample_data = {
                "users": [
                    {"name": "Alice Johnson", "email": "alice@example.com", "role": "Engineer"},
                    {"name": "Bob Smith", "email": "bob@example.com", "role": "Designer"},
                    {"name": "Carol White", "email": "carol@example.com", "role": "Manager"},
                ]
            }

            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(sample_data, temp_file, indent=2)
                temp_path = temp_file.name

            try:
                remote_data_json = f"{self.workspace_path}/data.json"
                self.sftp_client.put(temp_path, remote_data_json)
                logger.info(f"✓ Uploaded data.json to {remote_data_json}")
            finally:
                os.unlink(temp_path)

            # 4. Upload notes.txt
            logger.info("Uploading notes.txt...")
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

            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(notes_content)
                temp_path = temp_file.name

            try:
                remote_notes_txt = f"{self.workspace_path}/notes.txt"
                self.sftp_client.put(temp_path, remote_notes_txt)
                logger.info(f"✓ Uploaded notes.txt to {remote_notes_txt}")
            finally:
                os.unlink(temp_path)

            # 5. Create logs directory structure for MEDIUM Task 1
            logger.info("Creating logs directory structure...")
            logs_dir = f"{self.workspace_path}/logs"
            api_logs_dir = f"{logs_dir}/api"
            exit_code, stdout, stderr = self._exec_command(f"mkdir -p {api_logs_dir}")
            if exit_code != 0:
                logger.warning(f"Failed to create logs directory: {stderr}")

            # Upload log files
            log_files = {
                f"{logs_dir}/app.log": "INFO: Application started\\nERROR: Connection failed\\nWARN: Retry attempt 1\\n" * 50,
                f"{logs_dir}/error.log": "ERROR: Database timeout\\nERROR: Invalid query\\n" * 100,
                f"{api_logs_dir}/requests.log": "GET /api/users 200\\nPOST /api/data 201\\n" * 75,
                f"{api_logs_dir}/access.log": "192.168.1.1 - [GET /api/status]\\n" * 60,
            }

            for remote_path, content in log_files.items():
                with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name
                try:
                    self.sftp_client.put(temp_path, remote_path)
                    logger.info(f"✓ Uploaded {remote_path}")
                finally:
                    os.unlink(temp_path)

            # 6. Upload sales_data.csv for MEDIUM Task 2
            logger.info("Uploading sales_data.csv...")
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
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
                temp_file.write(sales_csv_content)
                temp_path = temp_file.name
            try:
                remote_sales_csv = f"{self.workspace_path}/sales_data.csv"
                self.sftp_client.put(temp_path, remote_sales_csv)
                logger.info(f"✓ Uploaded sales_data.csv to {remote_sales_csv}")
            finally:
                os.unlink(temp_path)

            # 7. Upload config files for MEDIUM Task 3
            logger.info("Uploading config files...")
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
                with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name
                try:
                    remote_config = f"{self.workspace_path}/{filename}"
                    self.sftp_client.put(temp_path, remote_config)
                    logger.info(f"✓ Uploaded {filename} to {remote_config}")
                finally:
                    os.unlink(temp_path)

            # 8. Upload data files for HARD Task 2
            logger.info("Uploading data pipeline files...")
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
            pipeline_files = [
                (f"{reports_dir}/employees.csv", employees_csv_content, '.csv'),
                (f"{reports_dir}/departments.json", departments_json_content, '.json'),
                (f"{reports_dir}/projects.xml", projects_xml_content, '.xml'),
            ]

            for remote_path, content, suffix in pipeline_files:
                with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name
                try:
                    self.sftp_client.put(temp_path, remote_path)
                    logger.info(f"✓ Uploaded {os.path.basename(remote_path)} to {remote_path}")
                finally:
                    os.unlink(temp_path)

            # 8. Upload application.log for HARD Task 8
            logger.info("Creating application.log for advanced analysis...")
            from datetime import datetime, timedelta
            base_time = datetime(2024, 2, 15, 9, 0, 0)
            log_entries = []
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

            application_log_content = "\n".join(log_entries) + "\n"
            application_log_path = f"{self.workspace_path}/application.log"

            with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_file:
                temp_file.write(application_log_content)
                temp_path = temp_file.name
            try:
                self.sftp_client.put(temp_path, application_log_path)
                logger.info(f"✓ Uploaded application.log to {application_log_path}")
            finally:
                os.unlink(temp_path)

            # 9. Upload inventory.csv for HARD Task 9
            logger.info("Creating inventory.csv for data validation...")
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
            inventory_csv_path = f"{self.workspace_path}/inventory.csv"

            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
                temp_file.write(inventory_csv_content)
                temp_path = temp_file.name
            try:
                self.sftp_client.put(temp_path, inventory_csv_path)
                logger.info(f"✓ Uploaded inventory.csv to {inventory_csv_path}")
            finally:
                os.unlink(temp_path)

            logger.info("✓ Remote setup complete")

            return SetupResult(
                status=CheckStatus.PASS,
                message="Remote workspace created successfully",
                setup_data={
                    "workspace_dir": self.workspace_path,
                    "data_json": f"{self.workspace_path}/data.json",
                    "notes_txt": f"{self.workspace_path}/notes.txt",
                    "reports_dir": reports_dir,
                    "expected_users": sample_data["users"],
                    "logs_dir": logs_dir,
                    "sales_csv": f"{self.workspace_path}/sales_data.csv",
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
            logger.error(f"Remote setup failed: {e}")
            return SetupResult(
                status=CheckStatus.FAIL,
                message=f"Remote setup error: {str(e)}",
                error=str(e),
            )

    def remote_validate(
        self,
        task_name: str,
        validation_fn: Callable[[str, dict[str, Any]], TaskResult],
        setup_data: dict[str, Any],
    ) -> TaskResult:
        """Download files from remote server and validate locally.

        Args:
            task_name: Name of the task being validated
            validation_fn: Validation function to run on downloaded files
            setup_data: Setup data from remote_setup()

        Returns:
            TaskResult with validation outcome
        """
        temp_dir = None
        try:
            self.connect()

            # Create local temp directory to download files
            temp_dir = tempfile.mkdtemp(prefix="openclaw_remote_validate_")
            logger.info(f"Downloading files from {self.workspace_path} to {temp_dir}...")

            # Download entire workspace directory
            self._download_directory_recursive(self.workspace_path, temp_dir)

            logger.info("✓ Files downloaded, running validation...")

            # Update setup_data to point to local temp directory
            local_setup_data = setup_data.copy()
            local_setup_data["workspace_dir"] = temp_dir
            local_setup_data["data_json"] = os.path.join(temp_dir, "data.json")
            local_setup_data["notes_txt"] = os.path.join(temp_dir, "notes.txt")
            local_setup_data["reports_dir"] = os.path.join(temp_dir, "reports")

            # Run validation on downloaded files (pass empty string as bot_response since we validate files)
            validation_result = validation_fn("", local_setup_data)

            logger.info(
                f"Validation complete: success={validation_result.success}, "
                f"accuracy={validation_result.accuracy_score:.1f}%"
            )

            return validation_result

        except Exception as e:
            logger.error(f"Remote validation failed for {task_name}: {e}")
            return TaskResult(
                task_name=task_name,
                prompt="",
                success=False,
                latency=0.0,
                accuracy_score=0.0,
                error_message=f"Remote validation error: {str(e)}",
            )
        finally:
            # Cleanup temp directory
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temp directory: {temp_dir}")

    def _download_directory_recursive(self, remote_dir: str, local_dir: str) -> None:
        """Recursively download directory from remote server.

        Args:
            remote_dir: Remote directory path
            local_dir: Local directory path
        """
        try:
            # Create local directory
            os.makedirs(local_dir, exist_ok=True)

            # List remote directory contents
            for item in self.sftp_client.listdir_attr(remote_dir):
                remote_path = f"{remote_dir}/{item.filename}"
                local_path = os.path.join(local_dir, item.filename)

                if self._is_directory(item):
                    # Recursively download subdirectory
                    self._download_directory_recursive(remote_path, local_path)
                else:
                    # Download file
                    logger.debug(f"Downloading {remote_path} -> {local_path}")
                    self.sftp_client.get(remote_path, local_path)

        except Exception as e:
            logger.warning(f"Error downloading {remote_dir}: {e}")
            # Don't raise - some files might not exist yet (e.g., result files)

    def _is_directory(self, item) -> bool:
        """Check if SFTP item is a directory.

        Args:
            item: paramiko.SFTPAttributes object

        Returns:
            True if item is a directory
        """
        import stat
        return stat.S_ISDIR(item.st_mode)

    def list_models(self) -> list[str]:
        """List all available models on the remote bot via SSH.

        Runs `openclaw models list --json` on the remote server and parses
        the output into a list of model identifiers (provider/model format).

        Returns:
            List of model identifiers, e.g. ["openai/gpt-4o", "anthropic/claude-opus-4-5"]

        Raises:
            RuntimeError: If the command fails or output cannot be parsed
        """
        self.connect()
        logger.info("Listing available models on remote bot")
        _OPENCLAW_ENV = (
            "PATH=/home/openclaw/.nvm/versions/node/v24.13.1/bin"
            ":/home/openclaw/.local/bin:$PATH"
        )
        exit_code, stdout, stderr = self._exec_command(
            f'env {_OPENCLAW_ENV} openclaw models list --json'
        )
        if exit_code != 0:
            raise RuntimeError(f"Failed to list models: {(stdout + stderr).strip()}")

        def _parse_item(item: object) -> str | None:
            """Extract model key from a model list item."""
            if isinstance(item, str):
                return item
            if isinstance(item, dict):
                # openclaw JSON uses "key" field; fall back to id/model/name
                for k in ("key", "id", "model", "name"):
                    if k in item:
                        return str(item[k])
            return None

        try:
            data = json.loads(stdout.strip())
            models: list[str] = []
            items: list[object] = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                # Wrapped: {"models": [...], "count": N}
                for val in data.values():
                    if isinstance(val, list):
                        items = val
                        break
            for item in items:
                key = _parse_item(item)
                if key:
                    models.append(key)
            logger.info(f"Found {len(models)} model(s): {models}")
            return models
        except json.JSONDecodeError:
            # Fallback: try --plain output, one model per line
            logger.warning("JSON parse failed, trying plain text fallback")
            exit_code2, stdout2, _ = self._exec_command(
                f'env {_OPENCLAW_ENV} openclaw models list --plain'
            )
            if exit_code2 == 0:
                lines = [l.strip() for l in stdout2.splitlines() if l.strip() and "/" in l]
                logger.info(f"Found {len(lines)} model(s) (plain): {lines}")
                return lines
            raise RuntimeError(f"Could not parse model list output: {stdout[:200]}")

    def switch_model(self, model: str) -> str:
        """Switch the OpenClaw bot's primary model via SSH.

        Runs `openclaw models set <model>` on the remote server.

        Args:
            model: Model identifier in provider/model format (e.g. anthropic/claude-opus-4-5)

        Returns:
            Output from the command (for confirmation logging)

        Raises:
            RuntimeError: If the command fails
        """
        self.connect()
        logger.info(f"Switching bot model to: {model}")
        # Use bash login shell to ensure NVM/PATH is set up (openclaw requires node)
        _OPENCLAW_ENV = (
            "PATH=/home/openclaw/.nvm/versions/node/v24.13.1/bin"
            ":/home/openclaw/.local/bin:$PATH"
        )
        cmd = f'env {_OPENCLAW_ENV} openclaw models set {model}'
        exit_code, stdout, stderr = self._exec_command(cmd)
        output = (stdout + stderr).strip()
        if exit_code != 0:
            raise RuntimeError(f"Failed to switch model to {model!r}: {output}")
        logger.info(f"Model switched to {model}: {output}")
        return output

    def remote_cleanup(self) -> bool:
        """Remove workspace on remote bot server.

        Returns:
            True if cleanup succeeded
        """
        try:
            self.connect()

            logger.info(f"Cleaning up remote workspace: {self.workspace_path}")
            exit_code, stdout, stderr = self._exec_command(f"rm -rf {self.workspace_path}")

            if exit_code == 0:
                logger.info("✓ Remote cleanup complete")
                return True
            else:
                logger.warning(f"Remote cleanup warning: {stderr}")
                return False

        except Exception as e:
            logger.error(f"Remote cleanup failed: {e}")
            return False
        finally:
            self.disconnect()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class LocalModelManager:
    """Model manager for local mode - uses the openclaw CLI directly (no SSH)."""

    def list_models(self) -> list[str]:
        """List available models via local openclaw CLI.

        Runs ``openclaw models list --json`` as a subprocess and parses the
        output into a list of model identifiers (provider/model format).

        Returns:
            List of model identifiers, e.g. ["openai/gpt-4o", "anthropic/claude-opus-4-5"]

        Raises:
            RuntimeError: If the command fails or output cannot be parsed
        """
        import subprocess

        logger.info("Listing available models via local openclaw CLI")
        try:
            result = subprocess.run(
                ["openclaw", "models", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "openclaw CLI not found. Ensure 'openclaw' is installed and on PATH."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timed out waiting for 'openclaw models list --json'")

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to list models (exit {result.returncode}): {(stdout + stderr).strip()}"
            )

        def _parse_item(item: object) -> str | None:
            """Extract model key from a model list item."""
            if isinstance(item, str):
                return item
            if isinstance(item, dict):
                for k in ("key", "id", "model", "name"):
                    if k in item:
                        return str(item[k])
            return None

        try:
            data = json.loads(stdout)
            models: list[str] = []
            items: list[object] = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for val in data.values():
                    if isinstance(val, list):
                        items = val
                        break
            for item in items:
                key = _parse_item(item)
                if key:
                    models.append(key)
            logger.info(f"Found {len(models)} model(s): {models}")
            return models
        except json.JSONDecodeError:
            # Fallback: try --plain output, one model per line
            logger.warning("JSON parse failed, trying plain text fallback")
            try:
                result2 = subprocess.run(
                    ["openclaw", "models", "list", "--plain"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result2.returncode == 0:
                    lines = [
                        ln.strip()
                        for ln in result2.stdout.splitlines()
                        if ln.strip() and "/" in ln
                    ]
                    logger.info(f"Found {len(lines)} model(s) (plain): {lines}")
                    return lines
            except Exception:
                pass
            raise RuntimeError(f"Could not parse model list output: {stdout[:200]}")

    def switch_model(self, model: str) -> str:
        """Switch the local openclaw agent's primary model.

        Runs ``openclaw models set <model>`` as a subprocess.

        Args:
            model: Model identifier in provider/model format

        Returns:
            Output from the command (for confirmation logging)

        Raises:
            RuntimeError: If the command fails
        """
        import subprocess

        logger.info(f"Switching local openclaw model to: {model}")
        try:
            result = subprocess.run(
                ["openclaw", "models", "set", model],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "openclaw CLI not found. Ensure 'openclaw' is installed and on PATH."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Timed out waiting for 'openclaw models set {model}'")

        output = (result.stdout + result.stderr).strip()
        if result.returncode != 0:
            raise RuntimeError(f"Failed to switch model to {model!r}: {output}")
        logger.info(f"Model switched to {model}: {output}")
        return output
