"""Skill detection and prerequisite checking for benchmark scenarios."""

import json
import logging
import subprocess

from benchmarks.base import CheckStatus, HealthCheckResult

logger = logging.getLogger(__name__)


def get_ready_skills(local_mode: bool = True) -> set[str]:
    """Get the set of installed and ready OpenClaw skills.

    In local mode, queries the local gateway via `openclaw skills list --json`.
    In Telegram mode, returns None since we can't detect remote bot skills.

    Args:
        local_mode: Whether we're running against the local gateway.

    Returns:
        Set of skill names that are eligible (ready), or None if detection
        is unavailable (Telegram mode).
    """
    if not local_mode:
        logger.info("Skill detection not available in Telegram mode (remote bot)")
        return None

    try:
        result = subprocess.run(
            ["openclaw", "skills", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            logger.warning(f"Failed to list skills: {result.stderr.strip()}")
            return set()

        data = json.loads(result.stdout)
        skills = data.get("skills", [])
        return {s["name"] for s in skills if s.get("eligible")}

    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning(f"Could not detect skills: {e}")
        return set()


def check_skills(required_skills: list[str]) -> list[HealthCheckResult]:
    """Check if all required skills are installed.

    Args:
        required_skills: List of skill names the scenario needs.

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

    ready = get_ready_skills()
    results = []

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
