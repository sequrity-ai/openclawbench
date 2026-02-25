"""Base classes for OpenClaw benchmark scenarios."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from benchmarks.ai_agent import BenchmarkAgent, ConversationResult

logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    """Status of a health check or setup operation."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    WARNING = "warning"


@dataclass
class HealthCheckResult:
    """Result of a pre-flight health check."""

    check_name: str
    status: CheckStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Check if the health check passed."""
        return self.status == CheckStatus.PASS


@dataclass
class SetupResult:
    """Result of scenario setup operations."""

    status: CheckStatus
    message: str
    setup_data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        """Check if setup succeeded."""
        return self.status == CheckStatus.PASS


@dataclass
class TaskResult:
    """Result of a single benchmark task execution."""

    task_name: str
    prompt: str
    success: bool
    latency: float
    accuracy_score: float  # 0-100
    response_text: str | None = None
    validation_details: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    # Multi-turn conversation tracking
    conversation_turns: int = 1  # Number of turns in conversation (default 1 for single-turn)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    completion_reason: str = ""  # "goal_achieved", "max_turns", "timeout", "error", "validation"
    # Token usage tracking
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cache_read_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_name": self.task_name,
            "prompt": self.prompt,
            "success": self.success,
            "latency": self.latency,
            "accuracy_score": self.accuracy_score,
            "response_text": self.response_text,
            "validation_details": self.validation_details,
            "error_message": self.error_message,
            "conversation_turns": self.conversation_turns,
            "conversation_history": self.conversation_history,
            "completion_reason": self.completion_reason,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "cache_read_tokens": self.cache_read_tokens,
        }


@dataclass
class ScenarioResult:
    """Result of running an entire scenario."""

    scenario_name: str
    start_time: float
    end_time: float
    total_duration: float
    health_checks: list[HealthCheckResult]
    setup_result: SetupResult | None
    task_results: list[TaskResult]
    cleanup_success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def all_tasks_passed(self) -> bool:
        """Check if all tasks passed."""
        return all(task.success for task in self.task_results)

    @property
    def average_accuracy(self) -> float:
        """Calculate average accuracy across all tasks."""
        if not self.task_results:
            return 0.0
        return sum(task.accuracy_score for task in self.task_results) / len(self.task_results)

    @property
    def average_latency(self) -> float:
        """Calculate average latency across all tasks."""
        if not self.task_results:
            return 0.0
        return sum(task.latency for task in self.task_results) / len(self.task_results)

    @property
    def total_input_tokens(self) -> int:
        return sum(task.input_tokens for task in self.task_results)

    @property
    def total_output_tokens(self) -> int:
        return sum(task.output_tokens for task in self.task_results)

    @property
    def total_reasoning_tokens(self) -> int:
        return sum(task.reasoning_tokens for task in self.task_results)

    @property
    def total_cache_read_tokens(self) -> int:
        return sum(task.cache_read_tokens for task in self.task_results)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens + self.total_reasoning_tokens + self.total_cache_read_tokens

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "scenario_name": self.scenario_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration": self.total_duration,
            "health_checks": [
                {
                    "check_name": check.check_name,
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details,
                }
                for check in self.health_checks
            ],
            "setup_result": {
                "status": self.setup_result.status.value if self.setup_result else None,
                "message": self.setup_result.message if self.setup_result else None,
                "error": self.setup_result.error if self.setup_result else None,
            }
            if self.setup_result
            else None,
            "task_results": [task.to_dict() for task in self.task_results],
            "all_tasks_passed": self.all_tasks_passed,
            "average_accuracy": self.average_accuracy,
            "average_latency": self.average_latency,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_reasoning_tokens": self.total_reasoning_tokens,
            "total_cache_read_tokens": self.total_cache_read_tokens,
            "total_tokens": self.total_tokens,
            "cleanup_success": self.cleanup_success,
            "metadata": self.metadata,
        }


@dataclass
class BenchmarkTask:
    """Definition of a single benchmark task."""

    name: str
    prompt: str
    expected_output_description: str
    validation_fn: Callable[[str, dict[str, Any]], TaskResult]
    timeout: float = 60.0
    metadata: dict[str, Any] = field(default_factory=dict)
    # Set True for tasks where validation reads files produced by the bot (File scenario).
    # False (default) means validation checks the bot's response text.
    validates_files: bool = False


def _create_session(client: Any, bot_identifier: int | str) -> Any:
    """Create the appropriate session type based on the client.

    Args:
        client: Either LocalClient or TelegramClient
        bot_identifier: For LocalClient: chat_id (int)
                       For TelegramClient: bot_username (str)
    """
    from local_client import LocalClient, LocalSession

    if isinstance(client, LocalClient):
        # LocalClient expects chat_id (int)
        return LocalSession(client, bot_identifier)

    from telegram_client import TelegramSession

    # TelegramClient expects bot_username (str)
    return TelegramSession(client, bot_identifier)


class ScenarioBase(ABC):
    """Base class for benchmark scenarios."""

    def __init__(self, name: str, description: str, required_skills: list[str]):
        """Initialize scenario.

        Args:
            name: Scenario name
            description: Human-readable description
            required_skills: List of required OpenClaw skills/capabilities
        """
        self.name = name
        self.description = description
        self.required_skills = required_skills
        self.tasks: list[BenchmarkTask] = []

    @staticmethod
    def _check_openai_api_key() -> HealthCheckResult:
        """Check if OpenAI API key is configured (required for ALL scenarios).

        Returns:
            Health check result for OpenAI API key
        """
        import os
        from config import Config

        try:
            config = Config()
            api_key = config.openai_api_key
        except Exception:
            api_key = os.getenv("OPENAI_API_KEY", "")

        if not api_key or api_key == "your_openai_api_key_here":
            return HealthCheckResult(
                check_name="OpenAI API Key (REQUIRED)",
                status=CheckStatus.FAIL,
                message="OPENAI_API_KEY not configured - required for AI agent in ALL scenarios",
                details={
                    "error": "AI agent needs OpenAI API to conduct multi-turn conversations",
                    "fix": "Set OPENAI_API_KEY in .env file",
                },
            )
        else:
            return HealthCheckResult(
                check_name="OpenAI API Key",
                status=CheckStatus.PASS,
                message=f"OpenAI API key configured ({api_key[:10]}...)",
                details={"model": "AI agent uses this for conversations"},
            )

    @abstractmethod
    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks.

        Returns:
            List of health check results
        """
        pass

    @abstractmethod
    def setup(self) -> SetupResult:
        """Set up the scenario (e.g., create test data).

        Returns:
            Setup result
        """
        pass

    @abstractmethod
    def cleanup(self) -> bool:
        """Clean up after scenario (e.g., delete test data).

        Returns:
            True if cleanup succeeded
        """
        pass

    def add_task(self, task: BenchmarkTask) -> None:
        """Add a task to this scenario.

        Args:
            task: Benchmark task to add
        """
        self.tasks.append(task)

    def _pre_cleanup(self, run_id: str) -> None:
        """Clean artifacts from previous runs before setup.

        Subclasses should override this to remove scenario-specific artifacts.
        Default implementation removes the standard workspace directory.

        Args:
            run_id: Unique identifier for this run (for logging)
        """
        import shutil
        from pathlib import Path

        workspace_dir = Path("/tmp/openclaw_benchmark")
        if workspace_dir.exists():
            logger.info(f"[{run_id}] Removing stale workspace: {workspace_dir}")
            shutil.rmtree(workspace_dir)
            logger.info(f"[{run_id}] Pre-cleanup complete")
        else:
            logger.info(f"[{run_id}] No previous workspace found, skipping pre-cleanup")

    async def run_async(
        self,
        client: Any,
        bot_identifier: int | str,
        ai_agent: BenchmarkAgent,
        skip_setup: bool = False,
        timeout_multiplier: float = 1.0,
    ) -> ScenarioResult:
        """Run the scenario asynchronously.

        Args:
            client: Client (LocalClient or TelegramClient)
            bot_identifier: For LocalClient: chat_id (int), For TelegramClient: bot_username (str)
            ai_agent: BenchmarkAgent for multi-turn conversations (required)
            skip_setup: Skip setup phase
            timeout_multiplier: Multiply all task timeouts by this factor

        Returns:
            Scenario result
        """
        start_time = time.time()
        run_id = f"{self.name.replace(' ', '_')}_{int(start_time)}"
        logger.info(f"[{run_id}] ===== SCENARIO START: {self.name} =====")

        # Pre-cleanup: Remove artifacts from previous runs
        if not skip_setup:
            logger.info(f"[{run_id}] Running pre-cleanup...")
            self._pre_cleanup(run_id)

        # Health checks
        logger.info(f"[{run_id}] Running health checks...")
        health_checks = self.pre_check()
        failed_checks = [check for check in health_checks if not check.passed]

        if failed_checks:
            logger.warning(f"[{run_id}] {len(failed_checks)} health check(s) failed")
            for check in failed_checks:
                logger.warning(f"[{run_id}]   - {check.check_name}: {check.message}")

        # Setup
        setup_result = None
        if not skip_setup:
            logger.info(f"[{run_id}] ===== SETUP START =====")
            setup_result = self.setup()
            if not setup_result.succeeded:
                logger.error(f"[{run_id}] Setup failed: {setup_result.message}")
                # Continue anyway to see what happens
            logger.info(f"[{run_id}] ===== SETUP COMPLETE =====")

        # Run tasks
        task_results = []

        for i, task in enumerate(self.tasks, 1):
            logger.info(f"[{run_id}] ===== TASK {i}/{len(self.tasks)}: {task.name} =====")
            task_start = time.time()

            # Fresh session per task — prevents context from previous tasks leaking in
            session = _create_session(client, bot_identifier)

            # Send /new to reset bot conversation context (resets Sequrity session ID too)
            session_reset_ok = False
            try:
                logger.info(f"[{run_id}] Sending /new to reset session context")
                response = await session.send_message_async("/new", wait_for_response=True, timeout=90.0)
                if response:
                    logger.info(f"[{run_id}] Session reset confirmed: {response.text[:80] if response.text else '(empty)'}")
                    session_reset_ok = True
                else:
                    logger.warning(f"[{run_id}] No response to /new within 30s, retrying")
                    response = await session.send_message_async("/new", wait_for_response=True, timeout=90.0)
                    if response:
                        logger.info(f"[{run_id}] Session reset confirmed on retry: {response.text[:80] if response.text else '(empty)'}")
                        session_reset_ok = True
                    else:
                        logger.error(
                            f"[{run_id}] /new got no response after retry — "
                            f"session context may NOT be clean for task: {task.name}"
                        )
            except Exception as e:
                logger.error(f"[{run_id}] Could not send /new (session context may be dirty): {e}")

            try:
                # Multi-turn conversation mode with AI agent
                logger.info(f"[{run_id}] Starting multi-turn conversation for task: {task.name}")
                logger.info(f"[{run_id}] Task description: {task.expected_output_description}")

                # Run the conversation (pass full prompt, not just expected output description)
                effective_timeout = task.timeout * timeout_multiplier
                conversation_result: ConversationResult = await ai_agent.run_conversation_async(
                    task_name=task.name,
                    task_description=task.prompt,  # Use full prompt with all details
                    session=session,
                    task_timeout=effective_timeout,
                )

                task_latency = conversation_result.total_latency

                # Get all bot responses for validation (concatenated)
                # Use all responses for local validation so validators can check entire conversation
                all_bot_responses = "\n\n".join(
                    turn.bot_response for turn in conversation_result.conversation_turns if turn.bot_response
                )
                final_response = all_bot_responses if all_bot_responses else None

                # Validate the conversation outcome
                if conversation_result.success:
                    # File-based tasks: download bot-produced files from remote and validate them.
                    # Response-based tasks: validate the bot's reply text directly even in remote mode.
                    if hasattr(self, 'remote_manager') and self.remote_manager and task.validates_files:
                        # Remote file validation: download files and validate
                        logger.info(f"[{run_id}] Running remote file validation for task: {task.name}")
                        validation_result = self.remote_manager.remote_validate(
                            task_name=task.name,
                            validation_fn=task.validation_fn,
                            setup_data=setup_result.setup_data if setup_result else {},
                        )
                    else:
                        # Response-based validation: use all bot responses concatenated
                        validation_result = task.validation_fn(
                            final_response, setup_result.setup_data if setup_result else {}
                        )
                    validation_result.latency = task_latency
                    validation_result.conversation_turns = conversation_result.total_turns
                    validation_result.conversation_history = [
                        {
                            "turn": turn.turn_number,
                            "user": turn.user_message,
                            "bot": turn.bot_response,
                            "timestamp": turn.timestamp,
                        }
                        for turn in conversation_result.conversation_turns
                    ]
                    validation_result.completion_reason = conversation_result.completion_reason
                    validation_result.input_tokens = conversation_result.total_input_tokens
                    validation_result.output_tokens = conversation_result.total_output_tokens
                    validation_result.reasoning_tokens = conversation_result.total_reasoning_tokens
                    validation_result.cache_read_tokens = conversation_result.total_cache_read_tokens
                    task_results.append(validation_result)

                    logger.info(
                        f"[{run_id}] Multi-turn task completed: turns={conversation_result.total_turns}, "
                        f"success={validation_result.success}, "
                        f"accuracy={validation_result.accuracy_score:.1f}, "
                        f"latency={task_latency:.2f}s, "
                        f"reason={conversation_result.completion_reason}, "
                        f"tokens: in={conversation_result.total_input_tokens} "
                        f"out={conversation_result.total_output_tokens} "
                        f"reasoning={conversation_result.total_reasoning_tokens} "
                        f"cache_read={conversation_result.total_cache_read_tokens}"
                    )
                else:
                    # Conversation failed
                    task_results.append(
                        TaskResult(
                            task_name=task.name,
                            prompt=task.prompt,
                            success=False,
                            latency=task_latency,
                            accuracy_score=0.0,
                            error_message=conversation_result.error_message or f"Conversation failed: {conversation_result.completion_reason}",
                            conversation_turns=conversation_result.total_turns,
                            conversation_history=[
                                {
                                    "turn": turn.turn_number,
                                    "user": turn.user_message,
                                    "bot": turn.bot_response,
                                    "timestamp": turn.timestamp,
                                }
                                for turn in conversation_result.conversation_turns
                            ],
                            completion_reason=conversation_result.completion_reason,
                            input_tokens=conversation_result.total_input_tokens,
                            output_tokens=conversation_result.total_output_tokens,
                            reasoning_tokens=conversation_result.total_reasoning_tokens,
                            cache_read_tokens=conversation_result.total_cache_read_tokens,
                        )
                    )
                    logger.error(
                        f"[{run_id}] Multi-turn task failed: {conversation_result.error_message or conversation_result.completion_reason}"
                    )

            except Exception as e:
                task_latency = time.time() - task_start
                logger.error(f"[{run_id}] Task error: {e}")
                task_results.append(
                    TaskResult(
                        task_name=task.name,
                        prompt=task.prompt,
                        success=False,
                        latency=task_latency,
                        accuracy_score=0.0,
                        error_message=str(e),
                    )
                )

        # Cleanup
        logger.info(f"[{run_id}] Running cleanup...")
        cleanup_success = self.cleanup()

        end_time = time.time()
        total_duration = end_time - start_time

        result = ScenarioResult(
            scenario_name=self.name,
            start_time=start_time,
            end_time=end_time,
            total_duration=total_duration,
            health_checks=health_checks,
            setup_result=setup_result,
            task_results=task_results,
            cleanup_success=cleanup_success,
            metadata={"description": self.description, "required_skills": self.required_skills},
        )

        logger.info(f"[{run_id}] Scenario completed: {self.name}")
        logger.info(f"[{run_id}]   Tasks passed: {sum(1 for t in task_results if t.success)}/{len(task_results)}")
        logger.info(f"[{run_id}]   Average accuracy: {result.average_accuracy:.1f}%")
        logger.info(f"[{run_id}]   Average latency: {result.average_latency:.2f}s")
        logger.info(
            f"[{run_id}]   Tokens: input={result.total_input_tokens} "
            f"output={result.total_output_tokens} "
            f"reasoning={result.total_reasoning_tokens} "
            f"cache_read={result.total_cache_read_tokens} "
            f"total={result.total_tokens}"
        )

        return result

    def run_sync(
        self,
        client: Any,
        bot_identifier: int | str,
        ai_agent: BenchmarkAgent,
        skip_setup: bool = False,
        timeout_multiplier: float = 1.0,
    ) -> ScenarioResult:
        """Run the scenario synchronously.

        Args:
            client: Client (LocalClient or TelegramClient)
            bot_identifier: For LocalClient: chat_id (int), For TelegramClient: bot_username (str)
            ai_agent: BenchmarkAgent for multi-turn conversations (required)
            skip_setup: Skip setup phase
            timeout_multiplier: Multiply all task timeouts by this factor

        Returns:
            Scenario result
        """
        start_time = time.time()
        run_id = f"{self.name.replace(' ', '_')}_{int(start_time)}"
        logger.info(f"[{run_id}] ===== SCENARIO START: {self.name} =====")

        # Pre-cleanup: Remove artifacts from previous runs
        if not skip_setup:
            logger.info(f"[{run_id}] Running pre-cleanup...")
            self._pre_cleanup(run_id)

        # Health checks
        logger.info(f"[{run_id}] Running health checks...")
        health_checks = self.pre_check()
        failed_checks = [check for check in health_checks if not check.passed]

        if failed_checks:
            logger.warning(f"[{run_id}] {len(failed_checks)} health check(s) failed")
            for check in failed_checks:
                logger.warning(f"[{run_id}]   - {check.check_name}: {check.message}")

        # Setup
        setup_result = None
        if not skip_setup:
            logger.info(f"[{run_id}] ===== SETUP START =====")
            setup_result = self.setup()
            if not setup_result.succeeded:
                logger.error(f"[{run_id}] Setup failed: {setup_result.message}")
            logger.info(f"[{run_id}] ===== SETUP COMPLETE =====")

        # Run tasks
        task_results = []

        for i, task in enumerate(self.tasks, 1):
            logger.info(f"[{run_id}] ===== TASK {i}/{len(self.tasks)}: {task.name} =====")
            task_start = time.time()

            # Fresh session per task — prevents context from previous tasks leaking in
            session = _create_session(client, bot_identifier)

            # Send /new to reset bot conversation context (resets Sequrity session ID too)
            session_reset_ok = False
            try:
                logger.info(f"[{run_id}] Sending /new to reset session context")
                response = session.send_message_sync("/new", wait_for_response=True, timeout=90.0)
                if response:
                    logger.info(f"[{run_id}] Session reset confirmed: {response.text[:80] if response.text else '(empty)'}")
                    session_reset_ok = True
                else:
                    logger.warning(f"[{run_id}] No response to /new within 30s, retrying")
                    response = session.send_message_sync("/new", wait_for_response=True, timeout=90.0)
                    if response:
                        logger.info(f"[{run_id}] Session reset confirmed on retry: {response.text[:80] if response.text else '(empty)'}")
                        session_reset_ok = True
                    else:
                        logger.error(
                            f"[{run_id}] /new got no response after retry — "
                            f"session context may NOT be clean for task: {task.name}"
                        )
            except Exception as e:
                logger.error(f"[{run_id}] Could not send /new (session context may be dirty): {e}")

            try:
                # Multi-turn conversation mode with AI agent (sync wrapper)
                logger.info(f"[{run_id}] Starting multi-turn conversation for task: {task.name}")

                # Run the conversation using sync wrapper (pass full prompt, not just expected output description)
                effective_timeout = task.timeout * timeout_multiplier
                conversation_result: ConversationResult = ai_agent.run_conversation_sync(
                    task_name=task.name,
                    task_description=task.prompt,
                    session=session,
                    task_timeout=effective_timeout,
                )

                task_latency = conversation_result.total_latency

                # Get all bot responses for validation (concatenated)
                # Use all responses for local validation so validators can check entire conversation
                all_bot_responses = "\n\n".join(
                    turn.bot_response for turn in conversation_result.conversation_turns if turn.bot_response
                )
                final_response = all_bot_responses if all_bot_responses else None

                # Validate the conversation outcome
                if conversation_result.success:
                    # File-based tasks: download bot-produced files from remote and validate them.
                    # Response-based tasks: validate the bot's reply text directly even in remote mode.
                    if hasattr(self, 'remote_manager') and self.remote_manager and task.validates_files:
                        # Remote file validation: download files and validate
                        logger.info(f"[{run_id}] Running remote file validation for task: {task.name}")
                        validation_result = self.remote_manager.remote_validate(
                            task_name=task.name,
                            validation_fn=task.validation_fn,
                            setup_data=setup_result.setup_data if setup_result else {},
                        )
                    else:
                        # Response-based validation: use all bot responses concatenated
                        validation_result = task.validation_fn(
                            final_response, setup_result.setup_data if setup_result else {}
                        )
                    validation_result.latency = task_latency
                    validation_result.conversation_turns = conversation_result.total_turns
                    validation_result.conversation_history = [
                        {
                            "turn": turn.turn_number,
                            "user": turn.user_message,
                            "bot": turn.bot_response,
                            "timestamp": turn.timestamp,
                        }
                        for turn in conversation_result.conversation_turns
                    ]
                    validation_result.completion_reason = conversation_result.completion_reason
                    validation_result.input_tokens = conversation_result.total_input_tokens
                    validation_result.output_tokens = conversation_result.total_output_tokens
                    validation_result.reasoning_tokens = conversation_result.total_reasoning_tokens
                    validation_result.cache_read_tokens = conversation_result.total_cache_read_tokens
                    task_results.append(validation_result)

                    logger.info(
                        f"[{run_id}] Task completed: {conversation_result.total_turns} turns, "
                        f"success={validation_result.success}, "
                        f"accuracy={validation_result.accuracy_score:.1f}%, "
                        f"completion={conversation_result.completion_reason}, "
                        f"latency={task_latency:.2f}s, "
                        f"tokens: in={conversation_result.total_input_tokens} "
                        f"out={conversation_result.total_output_tokens} "
                        f"reasoning={conversation_result.total_reasoning_tokens} "
                        f"cache_read={conversation_result.total_cache_read_tokens}"
                    )
                    if validation_result.validation_details:
                        logger.info(f"[{run_id}] Validation details: {validation_result.validation_details}")
                else:
                    # Conversation failed or no final response
                    error_msg = (
                        conversation_result.error_message
                        if conversation_result.error_message
                        else f"Conversation ended: {conversation_result.completion_reason}"
                    )
                    task_results.append(
                        TaskResult(
                            task_name=task.name,
                            prompt=task.prompt,
                            success=False,
                            latency=task_latency,
                            accuracy_score=0.0,
                            error_message=error_msg,
                            conversation_turns=conversation_result.total_turns,
                            conversation_history=[
                                {
                                    "turn": turn.turn_number,
                                    "user": turn.user_message,
                                    "bot": turn.bot_response,
                                    "timestamp": turn.timestamp,
                                }
                                for turn in conversation_result.conversation_turns
                            ],
                            completion_reason=conversation_result.completion_reason,
                            input_tokens=conversation_result.total_input_tokens,
                            output_tokens=conversation_result.total_output_tokens,
                            reasoning_tokens=conversation_result.total_reasoning_tokens,
                            cache_read_tokens=conversation_result.total_cache_read_tokens,
                        )
                    )
                    logger.error(
                        f"[{run_id}] Task failed: {conversation_result.total_turns} turns, "
                        f"completion={conversation_result.completion_reason}, error={error_msg}"
                    )

            except Exception as e:
                task_latency = time.time() - task_start
                logger.error(f"[{run_id}] Task error: {e}")
                task_results.append(
                    TaskResult(
                        task_name=task.name,
                        prompt=task.prompt,
                        success=False,
                        latency=task_latency,
                        accuracy_score=0.0,
                        error_message=str(e),
                    )
                )

        # Cleanup
        logger.info(f"[{run_id}] Running cleanup...")
        cleanup_success = self.cleanup()

        end_time = time.time()
        total_duration = end_time - start_time

        result = ScenarioResult(
            scenario_name=self.name,
            start_time=start_time,
            end_time=end_time,
            total_duration=total_duration,
            health_checks=health_checks,
            setup_result=setup_result,
            task_results=task_results,
            cleanup_success=cleanup_success,
            metadata={"description": self.description, "required_skills": self.required_skills},
        )

        logger.info(f"[{run_id}] Scenario completed: {self.name}")
        logger.info(f"[{run_id}]   Tasks passed: {sum(1 for t in task_results if t.success)}/{len(task_results)}")
        logger.info(f"[{run_id}]   Average accuracy: {result.average_accuracy:.1f}%")
        logger.info(f"[{run_id}]   Average latency: {result.average_latency:.2f}s")
        logger.info(
            f"[{run_id}]   Tokens: input={result.total_input_tokens} "
            f"output={result.total_output_tokens} "
            f"reasoning={result.total_reasoning_tokens} "
            f"cache_read={result.total_cache_read_tokens} "
            f"total={result.total_tokens}"
        )

        return result
