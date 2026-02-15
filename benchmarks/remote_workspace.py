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
