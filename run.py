#!/usr/bin/env python3
"""OpenClawBench — benchmark runner CLI.

Usage:
    python run.py --scenario file --backend local
    python run.py --scenario file --backend daytona --provider openrouter --model anthropic/claude-sonnet-4
    python run.py --scenario all --difficulty easy
    python run.py --task tasks/file/file-organization
    python run.py --list
    python run.py --verify-only
"""

import argparse
import asyncio
import contextlib
import logging
import signal
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Load .env into os.environ for variables not modeled in BenchmarkConfig
# (e.g. GOG_TEST_EMAIL, GOG_TOKEN_FILE, provider API keys).
# override=False ensures real env vars (from CI) take precedence over .env.
load_dotenv(override=False)

from config import BenchmarkConfig, load_config
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

# Module-level reference for signal handler cleanup
_active_backend = None


def _cleanup_handler(signum, frame):
    """Best-effort sandbox cleanup on SIGTERM/SIGINT."""
    sig_name = signal.Signals(signum).name
    logger.warning(f"Received {sig_name}, cleaning up...")
    if _active_backend is not None and hasattr(_active_backend, "destroy"):
        try:
            _active_backend.destroy()
        except Exception as e:
            logger.error(f"Cleanup on {sig_name} failed: {e}")
    sys.exit(128 + signum)


def _gateway_running() -> bool:
    """Check if the openclaw gateway is reachable."""
    try:
        result = subprocess.run(
            ["openclaw", "health"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False


@contextlib.contextmanager
def ensure_gateway():
    """Start the openclaw gateway if not already running, stop it on exit."""
    if _gateway_running():
        logger.info("Gateway already running, skipping start.")
        yield
        return

    logger.info("Starting openclaw gateway...")
    proc = subprocess.Popen(
        ["openclaw", "gateway", "run", "--force"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait up to 30s for the gateway to come up
    for _ in range(6):
        time.sleep(5)
        if _gateway_running():
            logger.info("Gateway is up.")
            break
    else:
        proc.terminate()
        raise RuntimeError("openclaw gateway failed to start within 30s")

    try:
        yield
    finally:
        logger.info("Stopping openclaw gateway...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_backend(
    backend_name: str, config: BenchmarkConfig, provider: str = "sequrity", model: str = "gpt-5.2"
):
    """Create the appropriate workspace backend."""
    if backend_name == "local":
        if provider != "sequrity" or model != "gpt-5.2":
            raise NotImplementedError(
                "--provider/--model are not supported with --backend=local; "
                "configure the provider in ~/.openclaw/openclaw.json instead"
            )
        return LocalBackend(config.bot_workspace_path)
    elif backend_name == "daytona":
        if not config.daytona_api_key:
            logger.error("Daytona backend requires DAYTONA_API_KEY")
            sys.exit(1)
        return DaytonaBackend(
            api_key=config.daytona_api_key,
            api_url=config.daytona_api_url,
            image=config.daytona_image,
            provider=provider,
            model=model,
            gateway_port=config.gateway_port,
        )
    else:
        logger.error(f"Unknown backend: {backend_name}")
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


def verify_solutions(tasks: list[TaskSpec], config: BenchmarkConfig) -> None:
    """Run reference solutions against test harnesses to verify correctness."""
    verify_path = config.bot_workspace_path + "_verify"
    backend = LocalBackend(verify_path)
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
            capture_output=True,
            text=True,
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


async def run_bench(args, config: BenchmarkConfig) -> "SuiteResult":
    """Run benchmark tasks. Returns SuiteResult for exit code handling."""
    global _active_backend

    from task_runner import SuiteResult

    # Discover tasks
    if args.task:
        task_path = Path(args.task)
        if not task_path.exists():
            logger.error(f"Task path not found: {task_path}")
            sys.exit(1)
        scenario_name = task_path.parent.name
        tasks = discover_tasks(
            task_path.parent.parent, scenario=scenario_name, task_name=task_path.name
        )
    else:
        tasks = discover_tasks(
            TASKS_DIR,
            scenario=args.scenario,
            difficulty=args.difficulty,
        )

    if not tasks:
        logger.error("No tasks found matching filters.")
        sys.exit(1)

    provider = args.provider or "sequrity"
    model = args.model or "gpt-5.2"
    scenario_label = args.scenario if not args.task else tasks[0].scenario
    model_label = f" ({provider}/{model})" if args.backend == "daytona" else ""
    print(
        f"Running {len(tasks)} task(s) [{scenario_label}] with backend={args.backend}{model_label}"
    )
    print("=" * 60)

    # Create backend and runner
    backend = create_backend(args.backend, config, provider=provider, model=model)
    _active_backend = backend  # for signal handler

    try:
        runner = TaskRunner(
            backend=backend,
            agent_id=config.agent_id,
            timeout_multiplier=config.timeout_multiplier,
        )

        # Run suite (gateway must be up for local backend exec tool calls;
        # daytona runs openclaw inside the workspace, so no local gateway needed)
        if args.backend == "daytona":
            suite = await runner.run_suite(tasks, scenario_name=scenario_label)
        else:
            with ensure_gateway():
                suite = await runner.run_suite(tasks, scenario_name=scenario_label)
    finally:
        _active_backend = None

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

    return suite


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Benchmark Runner")
    parser.add_argument(
        "--scenario",
        "-s",
        default="all",
        help="Scenario to run (file, weather, web, etc. or 'all')",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all scenarios (equivalent to --scenario all)",
    )
    parser.add_argument(
        "--backend",
        "-b",
        choices=["local", "daytona"],
        default="local",
        help="Workspace backend (default: local)",
    )
    parser.add_argument(
        "--difficulty",
        "-d",
        choices=["easy", "medium", "hard", "all"],
        default="all",
        help="Filter tasks by difficulty",
    )
    parser.add_argument(
        "--provider",
        "-p",
        default=None,
        help="LLM provider for Daytona backend (e.g. sequrity, openai, anthropic, openrouter). Default: sequrity",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="Model ID for Daytona backend (e.g. gpt-5.2, claude-sonnet-4-6). Default: gpt-5.2",
    )
    parser.add_argument(
        "--task",
        "-t",
        help="Run a single task by path (e.g. tasks/file/file-organization)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Export results to file (JSON or Markdown)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available tasks and exit",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify reference solutions pass all tests",
    )
    parser.add_argument(
        "--timeout-multiplier",
        type=float,
        default=None,
        help="Multiply all task timeouts by this factor (env: TIMEOUT_MULTIPLIER)",
    )
    parser.add_argument(
        "--agent-id",
        default=None,
        help="OpenClaw agent ID (env: AGENT_ID, default: main)",
    )
    parser.add_argument(
        "--gateway-port",
        type=int,
        default=None,
        help="openclaw gateway port (env: GATEWAY_PORT, default: 18789)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()
    if args.all:
        args.scenario = "all"
    setup_logging(args.verbose)

    # Load config: env/.env first, then CLI overrides win
    config = load_config(
        timeout_multiplier=args.timeout_multiplier,
        agent_id=args.agent_id,
        gateway_port=args.gateway_port,
    )

    # Install signal handlers for clean shutdown
    signal.signal(signal.SIGTERM, _cleanup_handler)
    signal.signal(signal.SIGINT, _cleanup_handler)

    if args.list:
        tasks = discover_tasks(TASKS_DIR, scenario=args.scenario, difficulty=args.difficulty)
        list_tasks(tasks)
        return

    if args.verify_only:
        tasks = discover_tasks(TASKS_DIR, scenario=args.scenario, difficulty=args.difficulty)
        print(f"Verifying {len(tasks)} task(s)...")
        verify_solutions(tasks, config)
        return

    suite = asyncio.run(run_bench(args, config))

    # Exit non-zero if any task failed
    if not suite.all_tasks_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
