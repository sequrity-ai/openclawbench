"""Command-line interface for Telegram bot benchmarking."""

import argparse
import asyncio
import gc
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Ensure an event loop exists before importing pyrogram (Python 3.12+ compat)
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from benchmark_runner import EXAMPLE_SCENARIOS, BenchmarkRunner, BenchmarkScenario
from benchmarks.ai_agent import BenchmarkAgent
from benchmarks.base import CheckStatus
from benchmarks.scenarios import SCENARIO_MAP
from benchmarks.skill_checker import get_ready_skills
from config import TelegramConfig, load_config
from local_client import LocalClient
from telegram_client import TelegramClient

logger = logging.getLogger(__name__)


def _inject_custom_soul(config: TelegramConfig) -> str | None:
    """Inject custom prompt into the bot's SOUL.md, backing up the original.

    Returns the path to the backup file, or None if no injection was needed.
    """
    if not config.custom_bot_prompt_file:
        return None

    prompt_file = Path(config.custom_bot_prompt_file).expanduser().resolve()
    if not prompt_file.is_file():
        logger.warning(f"Custom bot prompt file not found: {prompt_file}")
        print(f"WARNING: CUSTOM_BOT_PROMPT_FILE not found: {prompt_file}")
        return None

    workspace = Path(config.bot_workspace_dir).expanduser().resolve()
    soul_path = workspace / "SOUL.md"
    backup_path = workspace / "SOUL.md.benchmark_backup"

    # Read custom prompt content
    custom_content = prompt_file.read_text(encoding="utf-8")

    # Back up existing SOUL.md if it exists
    if soul_path.exists():
        original_content = soul_path.read_text(encoding="utf-8")
        backup_path.write_text(original_content, encoding="utf-8")
        logger.info(f"Backed up existing SOUL.md to {backup_path}")
    else:
        # No existing SOUL.md — create a sentinel so restore knows to delete
        backup_path.write_text("", encoding="utf-8")
        logger.info("No existing SOUL.md — will remove after benchmark")

    # Write custom prompt as SOUL.md
    soul_path.write_text(custom_content, encoding="utf-8")
    logger.info(f"Injected custom bot prompt from {prompt_file} into {soul_path}")
    print(f"Custom bot prompt: injected {prompt_file} -> {soul_path}")

    return str(backup_path)


def _restore_soul(config: TelegramConfig, backup_path: str | None) -> None:
    """Restore the original SOUL.md from backup."""
    if backup_path is None:
        return

    workspace = Path(config.bot_workspace_dir).expanduser().resolve()
    soul_path = workspace / "SOUL.md"
    bp = Path(backup_path)

    if not bp.exists():
        logger.warning(f"Backup file missing, cannot restore SOUL.md: {bp}")
        return

    backup_content = bp.read_text(encoding="utf-8")
    if backup_content == "":
        # Sentinel: original SOUL.md didn't exist, remove injected one
        soul_path.unlink(missing_ok=True)
        logger.info("Removed injected SOUL.md (no original existed)")
    else:
        soul_path.write_text(backup_content, encoding="utf-8")
        logger.info(f"Restored original SOUL.md from {bp}")

    bp.unlink(missing_ok=True)
    print("Custom bot prompt: restored original SOUL.md")


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def test_connection_local_async(config: TelegramConfig) -> bool:
    """Test local gateway connection."""
    try:
        async with LocalClient(config) as client:
            info = await client.get_me_async()
            logger.info(f"Connected to local gateway: {info.get('status')}")
            return True
    except Exception as e:
        logger.error(f"Local connection failed: {e}")
        return False


def test_connection_local_sync(config: TelegramConfig) -> bool:
    """Test local gateway connection (sync)."""
    try:
        with LocalClient(config) as client:
            info = client.get_me_sync()
            logger.info(f"Connected to local gateway: {info.get('status')}")
            return True
    except Exception as e:
        logger.error(f"Local connection failed: {e}")
        return False


async def test_connection_async(config: TelegramConfig) -> bool:
    """Test Telegram bot connection asynchronously.

    Args:
        config: Telegram configuration

    Returns:
        True if connection successful
    """
    try:
        async with TelegramClient(config) as client:
            bot_info = await client.get_me_async()
            logger.info(f"Connected to bot: {bot_info.get('username')} (ID: {bot_info.get('id')})")
            return True
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False


def test_connection_sync(config: TelegramConfig) -> bool:
    """Test Telegram bot connection synchronously.

    Args:
        config: Telegram configuration

    Returns:
        True if connection successful
    """
    try:
        with TelegramClient(config) as client:
            bot_info = client.get_me_sync()
            logger.info(f"Connected to bot: {bot_info.get('username')} (ID: {bot_info.get('id')})")
            return True
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False


async def send_message_async(config: TelegramConfig, chat_id: int, text: str) -> None:
    """Send a message asynchronously.

    Args:
        config: Telegram configuration
        chat_id: Chat ID to send to
        text: Message text
    """
    async with TelegramClient(config) as client:
        message = await client.send_message_async(chat_id, text)
        logger.info(f"Message sent (ID: {message.message_id})")


def send_message_sync(config: TelegramConfig, chat_id: int, text: str) -> None:
    """Send a message synchronously.

    Args:
        config: Telegram configuration
        chat_id: Chat ID to send to
        text: Message text
    """
    with TelegramClient(config) as client:
        message = client.send_message_sync(chat_id, text)
        logger.info(f"Message sent (ID: {message.message_id})")


async def run_benchmark_async(
    config: TelegramConfig, scenario: BenchmarkScenario, chat_id: int, output_path: Path | None
) -> None:
    """Run a benchmark scenario asynchronously.

    Args:
        config: Telegram configuration
        scenario: Benchmark scenario to run
        chat_id: Chat ID for testing
        output_path: Optional output path for results
    """
    runner = BenchmarkRunner(config)
    metrics = await runner.run_scenario_async(scenario, chat_id)

    # Print summary
    print("\n=== Benchmark Results ===")
    print(f"Benchmark Type: {metrics.benchmark_type}")
    print(f"Duration: {metrics.total_duration:.2f}s")
    print(f"Messages Sent: {metrics.messages_sent}")
    print(f"Messages Received: {metrics.messages_received}")
    print(f"Success Rate: {metrics.success_rate:.2f}%")
    print(f"Avg Response Time: {metrics.avg_response_time:.2f}s")
    print(f"Min Response Time: {metrics.min_response_time:.2f}s")
    print(f"Max Response Time: {metrics.max_response_time:.2f}s")

    if metrics.error_messages:
        print(f"\nErrors: {len(metrics.error_messages)}")
        for error in metrics.error_messages[:5]:
            print(f"  - {error}")

    if output_path:
        runner.export_results(output_path, format="markdown")
        print(f"\nResults exported to: {output_path}")


def run_benchmark_sync(
    config: TelegramConfig, scenario: BenchmarkScenario, chat_id: int, output_path: Path | None
) -> None:
    """Run a benchmark scenario synchronously.

    Args:
        config: Telegram configuration
        scenario: Benchmark scenario to run
        chat_id: Chat ID for testing
        output_path: Optional output path for results
    """
    runner = BenchmarkRunner(config)
    metrics = runner.run_scenario_sync(scenario, chat_id)

    # Print summary
    print("\n=== Benchmark Results ===")
    print(f"Benchmark Type: {metrics.benchmark_type}")
    print(f"Duration: {metrics.total_duration:.2f}s")
    print(f"Messages Sent: {metrics.messages_sent}")
    print(f"Messages Received: {metrics.messages_received}")
    print(f"Success Rate: {metrics.success_rate:.2f}%")
    print(f"Avg Response Time: {metrics.avg_response_time:.2f}s")
    print(f"Min Response Time: {metrics.min_response_time:.2f}s")
    print(f"Max Response Time: {metrics.max_response_time:.2f}s")

    if metrics.error_messages:
        print(f"\nErrors: {len(metrics.error_messages)}")
        for error in metrics.error_messages[:5]:
            print(f"  - {error}")

    if output_path:
        runner.export_results(output_path, format="markdown")
        print(f"\nResults exported to: {output_path}")


def _build_scenarios(args, skip_missing: bool = True, local_mode: bool = True, remote_manager=None):
    """Build scenario list, optionally skipping those with missing skills.

    In Telegram mode, skill detection is unavailable so all scenarios are included
    (missing skills will surface as task failures at runtime).

    Args:
        args: CLI arguments
        skip_missing: Skip scenarios with missing skills
        local_mode: True for local mode, False for Telegram mode
        remote_manager: Optional RemoteWorkspaceManager for remote validation
    """
    from benchmarks.scenario_factory import create_scenario

    ready_skills = get_ready_skills(local_mode=local_mode)
    config = load_config()

    # Get scenario classes to instantiate
    if args.scenario == "all":
        scenario_classes = list(SCENARIO_MAP.values())
    else:
        cls = SCENARIO_MAP.get(args.scenario)
        if not cls:
            raise ValueError(f"Unknown scenario: {args.scenario}")
        scenario_classes = [cls]

    # Instantiate scenarios using factory
    candidates = [create_scenario(cls, config, remote_manager) for cls in scenario_classes]

    scenarios = []
    skipped = []

    # If ready_skills is None (Telegram mode), we can't filter — run everything
    if ready_skills is None:
        return candidates, skipped

    for scenario in candidates:
        missing = [s for s in scenario.required_skills if s not in ready_skills]
        if missing and skip_missing:
            skipped.append((scenario.name, missing))
        else:
            scenarios.append(scenario)

    return scenarios, skipped


def _print_suite_header(config, scenarios, skipped, args):
    """Print the benchmark suite header."""
    mode = "local" if config.local_mode else ("async" if config.async_mode else "sync")

    print(f"\n{'='*60}")
    print("OpenClaw Benchmark Suite")
    print(f"Mode: {mode}")
    if config.bot_model:
        print(f"Bot model: {config.bot_model}")
    print(f"Running {len(scenarios)} scenario(s): {', '.join(s.name for s in scenarios)}")

    if not config.local_mode:
        print("Note: Skill detection unavailable in Telegram mode — all scenarios will run")

    if skipped:
        print(f"\nSkipped {len(skipped)} scenario(s) due to missing skills:")
        for name, missing in skipped:
            print(f"  - {name} (missing: {', '.join(missing)})")

    print(f"{'='*60}")

    # Display scenario details with tasks
    print("\nScenarios to run:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario.name}")
        print(f"   Description: {scenario.description}")
        skills_label = ", ".join(scenario.required_skills) or "(core tools only)"
        print(f"   Required skills: {skills_label}")
        print(f"   Tasks ({len(scenario.tasks)}):")
        for j, task in enumerate(scenario.tasks, 1):
            difficulty = task.metadata.get("difficulty", "unknown").upper()
            # Truncate long prompts for display
            prompt_preview = task.prompt[:100].replace("\n", " ")
            if len(task.prompt) > 100:
                prompt_preview += "..."
            print(f"      {j}. {task.name} [{difficulty}]")
            print(f"         {prompt_preview}")

    print(f"\n{'='*60}\n")


def _print_scenario_result(result, index, total):
    """Print a single scenario result."""
    passed = sum(1 for t in result.task_results if t.success)
    print(f"\n{'-'*60}")
    print(f"Scenario: {result.scenario_name}")
    print(f"Duration: {result.total_duration:.2f}s")
    print(f"Tasks passed: {passed}/{len(result.task_results)}")
    print(f"Average accuracy: {result.average_accuracy:.1f}%")
    print(f"Average latency: {result.average_latency:.2f}s")
    print(f"Tokens: input={result.total_input_tokens:,} output={result.total_output_tokens:,} reasoning={result.total_reasoning_tokens:,} total={result.total_tokens:,}")
    print(f"{'-'*60}\n")


def _export_results(config, all_results, output_path, single_turn: bool = False):
    """Export results to JSON."""
    export_data = {
        "config": {
            "async_mode": config.async_mode,
            "local_mode": config.local_mode,
            "bot_model": config.bot_model if config.bot_model else None,
            "mode": "single_turn" if single_turn else "multi_turn",
        },
        "scenarios": [result.to_dict() for result in all_results],
        "summary": {
            "total_scenarios": len(all_results),
            "total_tasks": sum(len(r.task_results) for r in all_results),
            "tasks_passed": sum(
                sum(1 for t in r.task_results if t.success) for r in all_results
            ),
            "overall_accuracy": (
                sum(r.average_accuracy for r in all_results) / len(all_results)
                if all_results
                else 0.0
            ),
        },
    }

    # Ensure parent directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2)

    print(f"\nResults exported to: {output_path}")


async def run_benchmark_suite_async(config: TelegramConfig, args) -> None:
    """Run benchmark suite asynchronously."""
    # Create RemoteWorkspaceManager if in remote mode (Telegram) and SSH is configured
    remote_manager = None
    if not config.local_mode:
        if config.bot_ssh_key_path or config.bot_ssh_password:
            logger.info("Remote validation enabled via SSH")
            from benchmarks.remote_workspace import RemoteWorkspaceManager
            remote_manager = RemoteWorkspaceManager(
                host=config.bot_ssh_host,
                port=config.bot_ssh_port,
                user=config.bot_ssh_user,
                key_path=config.bot_ssh_key_path if config.bot_ssh_key_path else None,
                password=config.bot_ssh_password if config.bot_ssh_password else None,
                workspace_path=config.bot_workspace_path,
                key_passphrase=config.bot_ssh_key_passphrase if config.bot_ssh_key_passphrase else None,
            )
            print(f"Remote validation: SSH to {config.bot_ssh_user}@{config.bot_ssh_host}")
        else:
            logger.warning("Remote mode without SSH credentials - validation will be skipped")
            print("⚠️  Remote mode without SSH credentials - file validation will be skipped")

    # Switch bot model if requested
    if config.bot_model and config.local_mode:
        from benchmarks.remote_workspace import LocalModelManager
        local_manager = LocalModelManager()
        print(f"Switching bot model to: {config.bot_model}")
        try:
            output = local_manager.switch_model(config.bot_model)
            print(f"Bot model switched to {config.bot_model}")
            if output:
                print(f"  {output}")
        except Exception as e:
            print(f"WARNING: Failed to switch bot model: {e}")
            raise
    elif config.bot_model and not config.local_mode:
        if remote_manager:
            print(f"Switching bot model to: {config.bot_model}")
            try:
                output = remote_manager.switch_model(config.bot_model)
                print(f"Bot model switched to {config.bot_model}")
                if output:
                    print(f"  {output}")
            except Exception as e:
                print(f"WARNING: Failed to switch bot model: {e}")
                raise
        else:
            print("WARNING: --bot-model requires SSH credentials (BOT_SSH_KEY_PATH or BOT_SSH_PASSWORD)")

    scenarios, skipped = _build_scenarios(args, skip_missing=args.skip_missing, local_mode=config.local_mode, remote_manager=remote_manager)

    if not scenarios:
        print("\nNo scenarios to run (all skipped due to missing skills).")
        return

    # Filter tasks by difficulty if requested
    if args.difficulty and args.difficulty != "all":
        for scenario in scenarios:
            original_count = len(scenario.tasks)
            scenario.tasks = [
                t for t in scenario.tasks
                if t.metadata.get("difficulty") == args.difficulty
            ]
            if len(scenario.tasks) < original_count:
                logger.info(
                    f"Filtered {scenario.name}: {original_count} -> {len(scenario.tasks)} tasks "
                    f"(difficulty={args.difficulty})"
                )
        # Remove scenarios that have no tasks left after filtering
        scenarios = [s for s in scenarios if s.tasks]
        if not scenarios:
            print(f"\nNo tasks match difficulty='{args.difficulty}'. Nothing to run.")
            return

    _print_suite_header(config, scenarios, skipped, args)

    # Apply max-turns override
    max_turns = args.max_turns if args.max_turns is not None else config.max_conversation_turns

    # Create AI agent (skip in single-turn mode)
    single_turn = getattr(args, "single_turn", False)
    ai_agent = None

    if single_turn:
        print("Single-turn mode: sending prompts directly (no AI agent)")
    else:
        if not config.openai_api_key:
            print("\nERROR: OPENAI_API_KEY is required for multi-turn conversations.")
            print("Please set OPENAI_API_KEY in your .env file.")
            raise ValueError("Missing required OPENAI_API_KEY configuration")

        logger.info("Creating AI agent for multi-turn conversations")
        ai_agent = BenchmarkAgent(
            model_name=config.ai_agent_model,
            openai_api_key=config.openai_api_key,
            max_turns=max_turns,
            conversation_timeout=config.conversation_timeout,
        )
        print(f"Multi-turn mode: max {max_turns} turns, {config.conversation_timeout}s timeout, model {config.ai_agent_model}")

    # Inject custom bot prompt (SOUL.md) if configured
    soul_backup = _inject_custom_soul(config)

    try:
        client_cls = LocalClient if config.local_mode else TelegramClient
        async with client_cls(config) as client:
            all_results = []

            # Determine bot identifier based on client type
            bot_identifier = args.chat_id if config.local_mode else config.openclaw_bot_username

            for i, scenario in enumerate(scenarios, 1):
                print(f"\n[{i}/{len(scenarios)}] Running scenario: {scenario.name}")
                print(f"Description: {scenario.description}")
                skills_label = ", ".join(scenario.required_skills) or "(core tools only)"
                print(f"Required skills: {skills_label}\n")

                result = await scenario.run_async(
                    client,
                    bot_identifier,
                    skip_setup=args.no_setup,
                    timeout_multiplier=config.timeout_multiplier,
                    ai_agent=ai_agent,
                )
                all_results.append(result)
                _print_scenario_result(result, i, len(scenarios))

            if args.output:
                _export_results(config, all_results, args.output, single_turn=single_turn)
    finally:
        _restore_soul(config, soul_backup)


def run_benchmark_suite_sync(config: TelegramConfig, args) -> None:
    """Run benchmark suite synchronously."""
    # Create RemoteWorkspaceManager if in remote mode (Telegram) and SSH is configured
    remote_manager = None
    if not config.local_mode:
        if config.bot_ssh_key_path or config.bot_ssh_password:
            logger.info("Remote validation enabled via SSH")
            from benchmarks.remote_workspace import RemoteWorkspaceManager
            remote_manager = RemoteWorkspaceManager(
                host=config.bot_ssh_host,
                port=config.bot_ssh_port,
                user=config.bot_ssh_user,
                key_path=config.bot_ssh_key_path if config.bot_ssh_key_path else None,
                password=config.bot_ssh_password if config.bot_ssh_password else None,
                workspace_path=config.bot_workspace_path,
                key_passphrase=config.bot_ssh_key_passphrase if config.bot_ssh_key_passphrase else None,
            )
            print(f"Remote validation: SSH to {config.bot_ssh_user}@{config.bot_ssh_host}")
        else:
            logger.warning("Remote mode without SSH credentials - validation will be skipped")
            print("⚠️  Remote mode without SSH credentials - file validation will be skipped")

    # Switch bot model if requested
    if config.bot_model and config.local_mode:
        from benchmarks.remote_workspace import LocalModelManager
        local_manager = LocalModelManager()
        print(f"Switching bot model to: {config.bot_model}")
        try:
            output = local_manager.switch_model(config.bot_model)
            print(f"Bot model switched to {config.bot_model}")
            if output:
                print(f"  {output}")
        except Exception as e:
            print(f"WARNING: Failed to switch bot model: {e}")
            raise
    elif config.bot_model and not config.local_mode:
        if remote_manager:
            print(f"Switching bot model to: {config.bot_model}")
            try:
                output = remote_manager.switch_model(config.bot_model)
                print(f"Bot model switched to {config.bot_model}")
                if output:
                    print(f"  {output}")
            except Exception as e:
                print(f"WARNING: Failed to switch bot model: {e}")
                raise
        else:
            print("WARNING: --bot-model requires SSH credentials (BOT_SSH_KEY_PATH or BOT_SSH_PASSWORD)")

    scenarios, skipped = _build_scenarios(args, skip_missing=args.skip_missing, local_mode=config.local_mode, remote_manager=remote_manager)

    if not scenarios:
        print("\nNo scenarios to run (all skipped due to missing skills).")
        return

    # Filter tasks by difficulty if requested
    if args.difficulty and args.difficulty != "all":
        for scenario in scenarios:
            original_count = len(scenario.tasks)
            scenario.tasks = [
                t for t in scenario.tasks
                if t.metadata.get("difficulty") == args.difficulty
            ]
            if len(scenario.tasks) < original_count:
                logger.info(
                    f"Filtered {scenario.name}: {original_count} -> {len(scenario.tasks)} tasks "
                    f"(difficulty={args.difficulty})"
                )
        scenarios = [s for s in scenarios if s.tasks]
        if not scenarios:
            print(f"\nNo tasks match difficulty='{args.difficulty}'. Nothing to run.")
            return

    _print_suite_header(config, scenarios, skipped, args)

    # Apply max-turns override
    max_turns = args.max_turns if args.max_turns is not None else config.max_conversation_turns

    # Create AI agent (skip in single-turn mode)
    single_turn = getattr(args, "single_turn", False)
    ai_agent = None

    if single_turn:
        print("Single-turn mode (sync): sending prompts directly (no AI agent)")
    else:
        if not config.openai_api_key:
            print("\nERROR: OPENAI_API_KEY is required for multi-turn conversations.")
            print("Please set OPENAI_API_KEY in your .env file.")
            raise ValueError("Missing required OPENAI_API_KEY configuration")

        logger.info("Creating AI agent for multi-turn conversations (sync wrapper)")
        ai_agent = BenchmarkAgent(
            model_name=config.ai_agent_model,
            openai_api_key=config.openai_api_key,
            max_turns=max_turns,
            conversation_timeout=config.conversation_timeout,
        )
        print(f"Multi-turn mode (sync): max {max_turns} turns, {config.conversation_timeout}s timeout, model {config.ai_agent_model}")

    # Inject custom bot prompt (SOUL.md) if configured
    soul_backup = _inject_custom_soul(config)

    try:
        client_cls = LocalClient if config.local_mode else TelegramClient
        with client_cls(config) as client:
            all_results = []

            # Determine bot identifier based on client type
            bot_identifier = args.chat_id if config.local_mode else config.openclaw_bot_username

            for i, scenario in enumerate(scenarios, 1):
                print(f"\n[{i}/{len(scenarios)}] Running scenario: {scenario.name}")
                print(f"Description: {scenario.description}")
                skills_label = ", ".join(scenario.required_skills) or "(core tools only)"
                print(f"Required skills: {skills_label}\n")

                result = scenario.run_sync(
                    client,
                    bot_identifier,
                    skip_setup=args.no_setup,
                    timeout_multiplier=config.timeout_multiplier,
                    ai_agent=ai_agent,
                )
                all_results.append(result)
                _print_scenario_result(result, i, len(scenarios))

            if args.output:
                _export_results(config, all_results, args.output, single_turn=single_turn)
    finally:
        _restore_soul(config, soul_backup)


def _log_memory(label: str = "") -> None:
    """Log current memory usage."""
    try:
        import resource
        rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_mb = rss_kb / 1024  # Linux reports KB
        logger.info(f"[Memory] {label}: RSS={rss_mb:.0f}MB")
        print(f"  [Memory] {label}: RSS={rss_mb:.0f}MB")
    except Exception:
        pass


async def run_benchmark_sweep_async(config: TelegramConfig, args) -> None:
    """Run benchmark suite across all available models (sweep mode)."""
    from benchmarks.remote_workspace import LocalModelManager, RemoteWorkspaceManager

    if config.local_mode:
        manager = LocalModelManager()
        client_cls = LocalClient
        bot_identifier: str | int = 0
        print("Local sweep: using openclaw CLI directly")
    else:
        if not (config.bot_ssh_key_path or config.bot_ssh_password):
            print("ERROR: benchmark-sweep requires SSH credentials.")
            print("Set BOT_SSH_KEY_PATH or BOT_SSH_PASSWORD in your .env file.")
            raise ValueError("benchmark-sweep requires SSH credentials for model discovery")

        manager = RemoteWorkspaceManager(
            host=config.bot_ssh_host,
            port=config.bot_ssh_port,
            user=config.bot_ssh_user,
            key_path=config.bot_ssh_key_path if config.bot_ssh_key_path else None,
            password=config.bot_ssh_password if config.bot_ssh_password else None,
            workspace_path=config.bot_workspace_path,
            key_passphrase=config.bot_ssh_key_passphrase if config.bot_ssh_key_passphrase else None,
        )
        client_cls = TelegramClient
        bot_identifier = config.openclaw_bot_username
        print(f"Remote sweep: SSH to {config.bot_ssh_user}@{config.bot_ssh_host}")

    # Keep a reference for scenarios that need remote_manager (file setup/validate)
    remote_manager = manager if not config.local_mode else None

    # Discover available models
    mode_label = "local openclaw CLI" if config.local_mode else "remote bot"
    print(f"\nDiscovering available models on {mode_label}...")
    try:
        models = manager.list_models()
    except Exception as e:
        print(f"ERROR: Failed to list models: {e}")
        raise

    if not models:
        print(f"ERROR: No models found on {mode_label}.")
        raise RuntimeError("No models available for sweep")

    print(f"Found {len(models)} model(s):")
    for m in models:
        print(f"  - {m}")

    # Build scenarios once (same for all models)
    scenarios, skipped = _build_scenarios(
        args,
        skip_missing=args.skip_missing,
        local_mode=config.local_mode,
        remote_manager=remote_manager,
    )

    if not scenarios:
        print("\nNo scenarios to run (all skipped due to missing skills).")
        return

    if skipped:
        print(f"\nSkipping {len(skipped)} scenario(s) with missing skills: {', '.join(name for name, _ in skipped)}")

    # Create AI agent (required)
    if not config.openai_api_key:
        print("\nERROR: OPENAI_API_KEY is required for multi-turn conversations.")
        raise ValueError("Missing required OPENAI_API_KEY configuration")

    ai_agent = BenchmarkAgent(
        model_name=config.ai_agent_model,
        openai_api_key=config.openai_api_key,
        max_turns=config.max_conversation_turns,
        conversation_timeout=config.conversation_timeout,
    )

    # Print sweep header
    print(f"\n{'='*70}")
    print(f"BENCHMARK SWEEP")
    print(f"{'='*70}")
    print(f"Models:    {len(models)}")
    print(f"Scenarios: {len(scenarios)} ({', '.join(s.name for s in scenarios)})")
    print(f"AI Agent:  {config.ai_agent_model}")
    print(f"{'='*70}\n")

    # Inject custom bot prompt (SOUL.md) if configured
    soul_backup = _inject_custom_soul(config)

    results_by_model: dict[str, list] = {}

    try:
        for model_idx, model in enumerate(models, 1):
            print(f"\n{'#'*70}")
            print(f"MODEL [{model_idx}/{len(models)}]: {model}")
            print(f"{'#'*70}")

            # Switch bot to this model
            try:
                print(f"Switching bot to model: {model}")
                output = manager.switch_model(model)
                print(f"Model switched successfully.")
                if output:
                    print(f"  {output}")
            except Exception as e:
                print(f"WARNING: Failed to switch to model {model}: {e}")
                print("Skipping this model.")
                results_by_model[model] = []
                continue

            # Run all scenarios for this model
            model_results = []
            async with client_cls(config) as client:
                for i, scenario in enumerate(scenarios, 1):
                    # Re-set model before each scenario (gateway may auto-rotate primary)
                    try:
                        manager.switch_model(model)
                    except Exception as e:
                        print(f"    WARNING: Could not re-set model before scenario: {e}")
                    print(f"\n  [{i}/{len(scenarios)}] Scenario: {scenario.name}")
                    result = await scenario.run_async(
                        client,
                        bot_identifier,
                        skip_setup=args.no_setup,
                        timeout_multiplier=config.timeout_multiplier,
                        ai_agent=ai_agent,
                    )
                    model_results.append(result)
                    passed = sum(1 for t in result.task_results if t.success)
                    print(f"    Result: {passed}/{len(result.task_results)} tasks passed, {result.average_accuracy:.1f}% accuracy, tokens: {result.total_tokens:,}")
                    gc.collect()  # free memory between scenarios

            results_by_model[model] = model_results

            # Free memory between model runs
            _log_memory(f"after model {model_idx}/{len(models)} ({model})")
            gc.collect()
            _log_memory(f"after gc.collect()")
    finally:
        _restore_soul(config, soul_backup)

    # Print cross-model summary table
    scenario_names = [s.name for s in scenarios]
    col_w = 10  # width per scenario column
    model_col = 38  # width for model name column

    # Build a lookup: results_by_model[model] is a list aligned with scenarios[]
    # Map scenario name → index for fast lookup
    scen_idx = {s.name: i for i, s in enumerate(scenarios)}

    def _cell(model_results_list: list, scen_name: str) -> str:
        """Return 'P/T' string for a given model+scenario."""
        if not model_results_list:
            return "SKIP"
        for r in model_results_list:
            if r.scenario_name == scen_name:
                passed = sum(1 for t in r.task_results if t.success)
                total = len(r.task_results)
                return f"{passed}/{total}"
        return "-"

    tok_col = 14  # width for token column
    sep = "=" * (model_col + col_w * len(scenario_names) + col_w + tok_col + 2)
    thin = "-" * len(sep)

    print(f"\n{sep}")
    print(f"SWEEP SUMMARY")
    print(f"{sep}")

    # Header row
    header = f"{'Model':<{model_col}}"
    for sn in scenario_names:
        label = sn[:col_w - 1]
        header += f"{label:>{col_w}}"
    header += f"{'TOTAL':>{col_w}}"
    header += f"{'TOKENS':>{tok_col}}"
    print(header)
    print(thin)

    # One row per model
    for model, model_results in results_by_model.items():
        if not model_results:
            row = f"{model[:model_col - 1]:<{model_col}}"
            row += f"{'SKIPPED':>{col_w * len(scenario_names) + col_w + tok_col}}"
            print(row)
            continue
        total_tasks = sum(len(r.task_results) for r in model_results)
        total_passed = sum(sum(1 for t in r.task_results if t.success) for r in model_results)
        total_tokens = sum(r.total_tokens for r in model_results)
        pct = 100.0 * total_passed / total_tasks if total_tasks else 0.0
        row = f"{model[:model_col - 1]:<{model_col}}"
        for sn in scenario_names:
            row += f"{_cell(model_results, sn):>{col_w}}"
        row += f"{f'{total_passed}/{total_tasks} ({pct:.0f}%)':>{col_w}}"
        row += f"{total_tokens:>{tok_col},}"
        print(row)

    # Scenario totals row (across all models that completed)
    print(thin)
    totals_row = f"{'SCENARIO TOTALS':<{model_col}}"
    grand_passed = 0
    grand_tasks = 0
    for sn in scenario_names:
        sp = st = 0
        for model_results in results_by_model.values():
            for r in model_results:
                if r.scenario_name == sn:
                    sp += sum(1 for t in r.task_results if t.success)
                    st += len(r.task_results)
        grand_passed += sp
        grand_tasks += st
        totals_row += f"{f'{sp}/{st}':>{col_w}}"
    grand_pct = 100.0 * grand_passed / grand_tasks if grand_tasks else 0.0
    grand_tokens = sum(r.total_tokens for mrs in results_by_model.values() for r in mrs)
    totals_row += f"{f'{grand_passed}/{grand_tasks} ({grand_pct:.0f}%)':>{col_w}}"
    totals_row += f"{grand_tokens:>{tok_col},}"
    print(totals_row)
    print(sep)

    # Export results if requested
    if args.output:
        import json as _json
        sweep_data = {
            "sweep": {
                "models": models,
                "scenarios": [s.name for s in scenarios],
            },
            "config": {
                "async_mode": config.async_mode,
                "local_mode": config.local_mode,
            },
            "results_by_model": {
                model: [r.to_dict() for r in model_results]
                for model, model_results in results_by_model.items()
            },
            "summary": {
                "total_models": len(models),
                "models_completed": sum(1 for v in results_by_model.values() if v),
                "per_model": {
                    model: {
                        "total_tasks": sum(len(r.task_results) for r in model_results),
                        "tasks_passed": sum(sum(1 for t in r.task_results if t.success) for r in model_results),
                        "overall_accuracy": (
                            sum(r.average_accuracy for r in model_results) / len(model_results)
                            if model_results else 0.0
                        ),
                        "total_input_tokens": sum(r.total_input_tokens for r in model_results),
                        "total_output_tokens": sum(r.total_output_tokens for r in model_results),
                        "total_reasoning_tokens": sum(r.total_reasoning_tokens for r in model_results),
                        "total_cache_read_tokens": sum(r.total_cache_read_tokens for r in model_results),
                        "total_tokens": sum(r.total_tokens for r in model_results),
                        "per_scenario": {
                            r.scenario_name: {
                                "tasks_passed": sum(1 for t in r.task_results if t.success),
                                "total_tasks": len(r.task_results),
                                "accuracy": r.average_accuracy,
                                "input_tokens": r.total_input_tokens,
                                "output_tokens": r.total_output_tokens,
                                "reasoning_tokens": r.total_reasoning_tokens,
                                "cache_read_tokens": r.total_cache_read_tokens,
                                "total_tokens": r.total_tokens,
                            }
                            for r in model_results
                        },
                    }
                    for model, model_results in results_by_model.items()
                },
            },
        }
        with open(args.output, "w") as f:
            _json.dump(sweep_data, f, indent=2)
        print(f"\nSweep results exported to: {args.output}")


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Telegram Bot Benchmarking CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options
    parser.add_argument(
        "--async",
        dest="async_mode",
        action="store_true",
        help="Use async mode (performance)",
    )
    parser.add_argument(
        "--sync",
        dest="async_mode",
        action="store_false",
        help="Use sync mode (debugging)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local OpenClaw gateway (no Telegram needed)",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Test connection
    test_parser = subparsers.add_parser("test", help="Test Telegram bot connection")

    # Send message
    send_parser = subparsers.add_parser("send", help="Send a message to a chat")
    send_parser.add_argument("chat_id", type=int, help="Chat ID to send message to")
    send_parser.add_argument("text", help="Message text")

    # Run benchmark
    benchmark_parser = subparsers.add_parser("benchmark", help="Run a benchmark scenario")
    benchmark_parser.add_argument("chat_id", type=int, help="Chat ID for testing")
    benchmark_parser.add_argument(
        "--scenario",
        type=int,
        default=0,
        help=f"Scenario index (0-{len(EXAMPLE_SCENARIOS)-1})",
    )
    benchmark_parser.add_argument(
        "--output", "-o", type=Path, help="Output path for results (markdown)"
    )

    # List scenarios
    list_parser = subparsers.add_parser("list-scenarios", help="List available scenarios")

    # Benchmark suite
    suite_parser = subparsers.add_parser("benchmark-suite", help="Run benchmark suite")
    suite_parser.add_argument(
        "chat_id",
        type=int,
        nargs="?",
        default=0,
        help="Chat ID for local mode (ignored in Telegram mode)",
    )
    suite_parser.add_argument(
        "--scenario",
        type=str,
        choices=list(SCENARIO_MAP.keys()) + ["all"],
        default="all",
        help="Scenario to run",
    )
    suite_parser.add_argument("--no-setup", action="store_true", help="Skip setup phase")
    suite_parser.add_argument(
        "--skip-missing",
        action="store_true",
        default=True,
        help="Skip scenarios with missing skills (default: true)",
    )
    suite_parser.add_argument(
        "--no-skip-missing",
        dest="skip_missing",
        action="store_false",
        help="Fail instead of skipping scenarios with missing skills",
    )
    suite_parser.add_argument(
        "--output", "-o", type=Path, help="Output path for results (JSON)"
    )
    suite_parser.add_argument(
        "--bot-model",
        dest="bot_model",
        type=str,
        default=None,
        help="Switch bot to this model before running (e.g. anthropic/claude-opus-4-5). Requires SSH credentials.",
    )
    suite_parser.add_argument(
        "--single-turn",
        action="store_true",
        default=False,
        help="Single-turn mode: send task prompt directly to bot (no AI agent, no OPENAI_API_KEY needed)",
    )
    suite_parser.add_argument(
        "--difficulty",
        type=str,
        choices=["easy", "medium", "hard", "all"],
        default="all",
        help="Only run tasks with this difficulty level (default: all)",
    )
    suite_parser.add_argument(
        "--max-turns",
        dest="max_turns",
        type=int,
        default=None,
        help="Override max conversation turns per task (default: from config)",
    )

    # benchmark-sweep subcommand: discover all models via SSH and run all scenarios for each
    sweep_parser = subparsers.add_parser(
        "benchmark-sweep",
        help="Discover all models on remote bot and run full benchmark suite for each",
    )
    sweep_parser.add_argument(
        "--no-setup",
        action="store_true",
        help="Skip setup phase for all scenarios",
    )
    sweep_parser.add_argument(
        "--skip-missing",
        action="store_true",
        default=True,
        help="Skip scenarios with missing skills (default: true)",
    )
    sweep_parser.add_argument(
        "--no-skip-missing",
        dest="skip_missing",
        action="store_false",
        help="Fail instead of skipping scenarios with missing skills",
    )
    sweep_parser.add_argument(
        "--output", "-o", type=Path, help="Output path for sweep results (JSON)"
    )
    # benchmark-sweep always uses scenario="all" internally
    sweep_parser.set_defaults(scenario="all", chat_id=0)

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.verbose)

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        logger.error("Make sure you have a .env file with TELEGRAM_BOT_TOKEN set")
        return 1

    # Override async mode if specified
    if hasattr(args, "async_mode") and args.async_mode is not None:
        config.async_mode = args.async_mode

    # Override local mode if --local flag is set
    if hasattr(args, "local") and args.local:
        config.local_mode = True

    # Override bot model if --bot-model flag is set
    if hasattr(args, "bot_model") and args.bot_model:
        config.bot_model = args.bot_model

    mode_label = "local" if config.local_mode else ("async" if config.async_mode else "sync")
    logger.info(f"Running in {mode_label} mode")

    # Handle commands
    if args.command == "test":
        if config.local_mode:
            if config.async_mode:
                success = asyncio.run(test_connection_local_async(config))
            else:
                success = test_connection_local_sync(config)
        elif config.async_mode:
            success = asyncio.run(test_connection_async(config))
        else:
            success = test_connection_sync(config)
        return 0 if success else 1

    elif args.command == "send":
        try:
            if config.async_mode:
                asyncio.run(send_message_async(config, args.chat_id, args.text))
            else:
                send_message_sync(config, args.chat_id, args.text)
            return 0
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return 1

    elif args.command == "benchmark":
        if args.scenario < 0 or args.scenario >= len(EXAMPLE_SCENARIOS):
            logger.error(f"Invalid scenario index: {args.scenario}")
            return 1

        scenario = EXAMPLE_SCENARIOS[args.scenario]
        logger.info(f"Running scenario: {scenario.name}")

        try:
            if config.async_mode:
                asyncio.run(run_benchmark_async(config, scenario, args.chat_id, args.output))
            else:
                run_benchmark_sync(config, scenario, args.chat_id, args.output)
            return 0
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            return 1

    elif args.command == "list-scenarios":
        from benchmarks.scenarios import GmailScenario, GitHubScenario

        ready_skills = get_ready_skills(local_mode=config.local_mode)

        print("\nAvailable Benchmark Scenarios:")
        print(f"{'='*60}")

        for name, cls in SCENARIO_MAP.items():
            # Instantiate scenario with appropriate parameters
            if cls == GmailScenario:
                scenario = cls(
                    client_id=config.google_client_id,
                    client_secret=config.google_client_secret,
                    refresh_token=config.google_refresh_token,
                    benchmark_email=config.gmail_benchmark_email,
                    bot_email=config.gmail_bot_email,
                )
            elif cls == GitHubScenario:
                scenario = cls(
                    github_token=config.github_token,
                    test_repo_owner=config.github_test_repo_owner,
                    test_repo_name=config.github_test_repo_name,
                )
            else:
                scenario = cls()
            if ready_skills is None:
                status = "UNKNOWN (Telegram mode — skill detection unavailable)"
            else:
                missing = [s for s in scenario.required_skills if s not in ready_skills]
                status = "READY" if not missing else f"MISSING: {', '.join(missing)}"

            print(f"\n  {name}")
            print(f"    Name: {scenario.name}")
            print(f"    Description: {scenario.description}")
            skills_label = ", ".join(scenario.required_skills) or "(core tools only)"
            print(f"    Required skills: {skills_label}")
            print(f"    Tasks: {len(scenario.tasks)}")
            print(f"    Status: {status}")

        print(f"\n{'='*60}")
        if ready_skills is None:
            print("Skill detection unavailable in Telegram mode (cannot query remote bot)")
        else:
            print(f"Ready skills: {', '.join(sorted(ready_skills))}")

        # Also show legacy scenarios
        print("\n\nLegacy benchmark scenarios (for 'benchmark' command):")
        for i, scenario in enumerate(EXAMPLE_SCENARIOS):
            print(f"  {i}. {scenario.name} ({scenario.benchmark_type.value})")
        return 0

    elif args.command == "benchmark-suite":
        try:
            if config.async_mode:
                asyncio.run(run_benchmark_suite_async(config, args))
            else:
                run_benchmark_suite_sync(config, args)
            return 0
        except Exception as e:
            logger.error(f"Benchmark suite failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    elif args.command == "benchmark-sweep":
        try:
            asyncio.run(run_benchmark_sweep_async(config, args))
            return 0
        except Exception as e:
            logger.error(f"Benchmark sweep failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
