"""Skill detection and prerequisite checking for benchmark scenarios."""

import json
import logging
import subprocess
from typing import TYPE_CHECKING

from benchmarks.base import CheckStatus, HealthCheckResult

if TYPE_CHECKING:
    from benchmarks.remote_workspace import RemoteWorkspaceManager

logger = logging.getLogger(__name__)


def get_ready_skills(local_mode: bool = True, remote_manager: "RemoteWorkspaceManager | None" = None) -> set[str] | None:
    """Get the set of installed and ready OpenClaw skills.

    In local mode, queries the local gateway via `openclaw skills list --json`.
    In Telegram mode, queries the remote bot via SSH.

    Args:
        local_mode: Whether we're running against the local gateway.
        remote_manager: RemoteWorkspaceManager for SSH access (required if not local_mode).

    Returns:
        Set of skill names that are eligible (ready), or None if detection fails.
    """
    if local_mode:
        # Local mode: run openclaw command locally
        try:
            result = subprocess.run(
                ["openclaw", "skills", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                logger.warning(f"Failed to list skills locally: {result.stderr.strip()}")
                return None

            data = json.loads(result.stdout)
            skills = data.get("skills", [])
            return {s["name"] for s in skills if s.get("eligible")}

        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Could not detect local skills: {e}")
            return None
    else:
        # Telegram mode: run openclaw command remotely via SSH
        if not remote_manager:
            logger.warning("Remote skill detection requested but no RemoteWorkspaceManager provided")
            return None

        try:
            remote_manager.connect()
            stdin, stdout, stderr = remote_manager.ssh_client.exec_command(
                "openclaw skills list --json",
                timeout=15
            )
            exit_status = stdout.channel.recv_exit_status()

            if exit_status != 0:
                error_msg = stderr.read().decode().strip()
                logger.warning(f"Failed to list skills remotely: {error_msg}")
                return None

            output = stdout.read().decode()
            data = json.loads(output)
            skills = data.get("skills", [])
            skill_set = {s["name"] for s in skills if s.get("eligible")}
            logger.info(f"Detected {len(skill_set)} ready skills on remote bot")
            return skill_set

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Could not detect remote skills: {e}")
            return None


def check_skills(required_skills: list[str], local_mode: bool = True, remote_manager: "RemoteWorkspaceManager | None" = None) -> list[HealthCheckResult]:
    """Check if all required skills are installed.

    Args:
        required_skills: List of skill names the scenario needs.
        local_mode: Whether we're running against the local gateway.
        remote_manager: RemoteWorkspaceManager for SSH access (required if not local_mode).

    Returns:
        List of health check results, one per required skill.
    """
    if not required_skills:
        return [
            HealthCheckResult(
                check_name="Skills",
                status=CheckStatus.PASS,
                message="No skills required (uses built-in tools only)",
            )
        ]

    ready = get_ready_skills(local_mode=local_mode, remote_manager=remote_manager)
    results = []

    if ready is None:
        # Skill detection failed - mark as warning, not fail
        mode_str = "local" if local_mode else "remote"
        for skill in required_skills:
            results.append(
                HealthCheckResult(
                    check_name=f"Skill: {skill}",
                    status=CheckStatus.WARNING,
                    message=f"Could not verify skill '{skill}' ({mode_str} detection failed)",
                )
            )
        return results

    for skill in required_skills:
        if skill in ready:
            results.append(
                HealthCheckResult(
                    check_name=f"Skill: {skill}",
                    status=CheckStatus.PASS,
                    message=f"Skill '{skill}' is installed and ready",
                )
            )
        else:
            results.append(
                HealthCheckResult(
                    check_name=f"Skill: {skill}",
                    status=CheckStatus.FAIL,
                    message=f"Skill '{skill}' is not installed. Install with: clawhub install {skill}",
                )
            )

    return results
