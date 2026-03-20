#!/usr/bin/env python3
"""Harbor-native benchmark runner CLI.

Usage:
    python run.py --scenario file --backend local
    python run.py --scenario file --backend daytona
    python run.py --scenario all --difficulty easy
    python run.py --task tasks/file/file-organization
    python run.py --list
    python run.py --verify-only
"""

import argparse
import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from config import TelegramConfig, load_config
from task_runner import (
    DaytonaBackend,
    LocalBackend,
    TaskRunner,
    TaskSpec,
    discover_tasks,
    export_results,
)

TASKS_DIR = Path(__file__).parent / "tasks"

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_backend(backend_name: str, config: TelegramConfig):
    """Create the appropriate workspace backend."""
    if backend_name == "local":
        return LocalBackend(config.bot_workspace_path)
    elif backend_name == "daytona":
        if not config.daytona_api_key:
            print("ERROR: Daytona backend requires DAYTONA_API_KEY in .env")
            sys.exit(1)
        return DaytonaBackend(
            api_key=config.daytona_api_key,
            api_url=config.daytona_api_url,
            image=config.daytona_image,
        )
    else:
        print(f"ERROR: Unknown backend: {backend_name}")
        sys.exit(1)


def list_tasks(tasks: list[TaskSpec]) -> None:
    """Print a formatted list of tasks."""
    if not tasks:
        print("No tasks found.")
        return

    current_scenario = ""
    for t in tasks:
        if t.scenario != current_scenario:
            current_scenario = t.scenario
            print(f"\n{current_scenario}/")
        print(f"  {t.name:<35} {t.difficulty:<8} timeout={t.timeout_sec}s")

    print(f"\nTotal: {len(tasks)} tasks")


def verify_solutions(tasks: list[TaskSpec]) -> None:
    """Run reference solutions against test harnesses to verify correctness."""
    from task_runner import LocalBackend

    backend = LocalBackend("/tmp/openclaw_verify")
    passed = 0
    failed = 0

    for task in tasks:
        solve_sh = task.path / "solution" / "solve.sh"
        if not solve_sh.exists():
            print(f"  SKIP: {task.scenario}/{task.name} (no solve.sh)")
            continue

        # Setup
        backend.cleanup_workspace()
        backend.setup_workspace(task)

        # Run reference solution with workspace path substituted
        script = solve_sh.read_text().replace("/workspace", backend.workspace_path)
        subprocess.run(
            ["bash", "-c", script],
            capture_output=True, text=True,
        )

        # Verify
        reward = backend.run_verifier(task)
        if reward >= 1.0:
            print(f"  PASS: {task.scenario}/{task.name}")
            passed += 1
        else:
            print(f"  FAIL: {task.scenario}/{task.name} (reward={reward})")
            failed += 1

    backend.cleanup_workspace()
    print(f"\n{passed}/{passed + failed} passed")
    if failed:
        sys.exit(1)


async def run_bench(args, config: TelegramConfig) -> None:
    """Run benchmark tasks."""
    # Discover tasks
    if args.task:
        # Single task by path
        task_path = Path(args.task)
        if not task_path.exists():
            print(f"ERROR: Task path not found: {task_path}")
            sys.exit(1)
        # Determine scenario from parent dir
        scenario_name = task_path.parent.name
        tasks = discover_tasks(task_path.parent.parent, scenario=scenario_name, task_name=task_path.name)
    else:
        tasks = discover_tasks(
            TASKS_DIR,
            scenario=args.scenario,
            difficulty=args.difficulty,
        )

    if not tasks:
        print("No tasks found matching filters.")
        sys.exit(1)

    scenario_label = args.scenario if not args.task else tasks[0].scenario
    print(f"Running {len(tasks)} task(s) [{scenario_label}] with backend={args.backend}")
    print("=" * 60)

    # Create backend and runner
    backend = create_backend(args.backend, config)
    runner = TaskRunner(
        backend=backend,
        agent_id=config.agent_id,
        timeout_multiplier=config.timeout_multiplier,
    )

    # Run suite
    suite = await runner.run_suite(tasks, scenario_name=scenario_label)

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    for r in suite.task_results:
        status = "PASS" if r.success else "FAIL"
        tokens = r.input_tokens + r.output_tokens + r.reasoning_tokens
        print(f"  {status}: {r.scenario}/{r.task_name} ({r.latency:.1f}s, {tokens} tokens)")

    passed = sum(1 for r in suite.task_results if r.success)
    print(f"\n{passed}/{len(suite.task_results)} passed")
    print(f"Average accuracy: {suite.average_accuracy:.1f}%")
    print(f"Average latency: {suite.average_latency:.1f}s")
    print(f"Total tokens: {suite.total_tokens}")
    print(f"Duration: {suite.total_duration:.1f}s")

    # Export if requested
    if args.output:
        output_path = Path(args.output)
        export_results(suite, output_path)
        print(f"\nResults exported to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Benchmark Runner")
    parser.add_argument(
        "--scenario", "-s",
        default="file",
        help="Scenario to run (file, weather, web, etc. or 'all')",
    )
    parser.add_argument(
        "--backend", "-b",
        choices=["local", "daytona"],
        default="local",
        help="Workspace backend (default: local)",
    )
    parser.add_argument(
        "--difficulty", "-d",
        choices=["easy", "medium", "hard", "all"],
        default="all",
        help="Filter tasks by difficulty",
    )
    parser.add_argument(
        "--task", "-t",
        help="Run a single task by path (e.g. tasks/file/file-organization)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Export results to file (JSON or Markdown)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available tasks and exit",
    )
    parser.add_argument(
        "--verify-only", action="store_true",
        help="Verify reference solutions pass all tests",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)
    config = load_config()

    if args.list:
        tasks = discover_tasks(TASKS_DIR, scenario=args.scenario, difficulty=args.difficulty)
        list_tasks(tasks)
        return

    if args.verify_only:
        tasks = discover_tasks(TASKS_DIR, scenario=args.scenario, difficulty=args.difficulty)
        print(f"Verifying {len(tasks)} task(s)...")
        verify_solutions(tasks)
        return

    asyncio.run(run_bench(args, config))


if __name__ == "__main__":
    main()
