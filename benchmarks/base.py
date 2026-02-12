"""Base classes for OpenClaw benchmark scenarios."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

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


def _create_session(client: Any, chat_id: int) -> Any:
    """Create the appropriate session type based on the client."""
    from local_client import LocalClient, LocalSession

    if isinstance(client, LocalClient):
        return LocalSession(client, chat_id)

    from telegram_client import TelegramSession

    return TelegramSession(client, chat_id)


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

    async def run_async(
        self, client: Any, chat_id: int, skip_setup: bool = False, timeout_multiplier: float = 1.0
    ) -> ScenarioResult:
        """Run the scenario asynchronously.

        Args:
            client: Telegram client
            chat_id: Chat ID to use
            skip_setup: Skip setup phase
            timeout_multiplier: Multiply all task timeouts by this factor

        Returns:
            Scenario result
        """
        start_time = time.time()
        logger.info(f"Starting scenario: {self.name}")

        # Health checks
        logger.info("Running health checks...")
        health_checks = self.pre_check()
        failed_checks = [check for check in health_checks if not check.passed]

        if failed_checks:
            logger.warning(f"{len(failed_checks)} health check(s) failed")
            for check in failed_checks:
                logger.warning(f"  - {check.check_name}: {check.message}")

        # Setup
        setup_result = None
        if not skip_setup:
            logger.info("Running setup...")
            setup_result = self.setup()
            if not setup_result.succeeded:
                logger.error(f"Setup failed: {setup_result.message}")
                # Continue anyway to see what happens

        # Run tasks
        task_results = []
        for i, task in enumerate(self.tasks, 1):
            logger.info(f"Running task {i}/{len(self.tasks)}: {task.name}")
            task_start = time.time()

            try:
                session = _create_session(client, chat_id)

                # Send prompt and wait for response
                effective_timeout = task.timeout * timeout_multiplier
                response = await session.send_message_async(
                    task.prompt, wait_for_response=True, timeout=effective_timeout
                )

                task_latency = time.time() - task_start

                if response and response.text:
                    # Validate response
                    validation_result = task.validation_fn(
                        response.text, setup_result.setup_data if setup_result else {}
                    )
                    validation_result.latency = task_latency
                    task_results.append(validation_result)
                    logger.info(
                        f"Task completed: success={validation_result.success}, "
                        f"accuracy={validation_result.accuracy_score:.1f}, "
                        f"latency={task_latency:.2f}s"
                    )
                else:
                    # No response or timeout
                    task_results.append(
                        TaskResult(
                            task_name=task.name,
                            prompt=task.prompt,
                            success=False,
                            latency=task_latency,
                            accuracy_score=0.0,
                            error_message="No response from bot or timeout",
                        )
                    )
                    logger.error(f"Task failed: No response from bot")

            except Exception as e:
                task_latency = time.time() - task_start
                logger.error(f"Task error: {e}")
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
        logger.info("Running cleanup...")
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

        logger.info(f"Scenario completed: {self.name}")
        logger.info(f"  Tasks passed: {sum(1 for t in task_results if t.success)}/{len(task_results)}")
        logger.info(f"  Average accuracy: {result.average_accuracy:.1f}%")
        logger.info(f"  Average latency: {result.average_latency:.2f}s")

        return result

    def run_sync(self, client: Any, chat_id: int, skip_setup: bool = False, timeout_multiplier: float = 1.0) -> ScenarioResult:
        """Run the scenario synchronously.

        Args:
            client: Telegram client
            chat_id: Chat ID to use
            skip_setup: Skip setup phase
            timeout_multiplier: Multiply all task timeouts by this factor

        Returns:
            Scenario result
        """
        start_time = time.time()
        logger.info(f"Starting scenario: {self.name}")

        # Health checks
        logger.info("Running health checks...")
        health_checks = self.pre_check()
        failed_checks = [check for check in health_checks if not check.passed]

        if failed_checks:
            logger.warning(f"{len(failed_checks)} health check(s) failed")
            for check in failed_checks:
                logger.warning(f"  - {check.check_name}: {check.message}")

        # Setup
        setup_result = None
        if not skip_setup:
            logger.info("Running setup...")
            setup_result = self.setup()
            if not setup_result.succeeded:
                logger.error(f"Setup failed: {setup_result.message}")

        # Run tasks
        task_results = []
        for i, task in enumerate(self.tasks, 1):
            logger.info(f"Running task {i}/{len(self.tasks)}: {task.name}")
            task_start = time.time()

            try:
                session = _create_session(client, chat_id)

                effective_timeout = task.timeout * timeout_multiplier
                response = session.send_message_sync(
                    task.prompt, wait_for_response=True, timeout=effective_timeout
                )

                task_latency = time.time() - task_start

                if response and response.text:
                    validation_result = task.validation_fn(
                        response.text, setup_result.setup_data if setup_result else {}
                    )
                    validation_result.latency = task_latency
                    task_results.append(validation_result)
                    logger.info(
                        f"Task completed: success={validation_result.success}, "
                        f"accuracy={validation_result.accuracy_score:.1f}, "
                        f"latency={task_latency:.2f}s"
                    )
                else:
                    task_results.append(
                        TaskResult(
                            task_name=task.name,
                            prompt=task.prompt,
                            success=False,
                            latency=task_latency,
                            accuracy_score=0.0,
                            error_message="No response from bot or timeout",
                        )
                    )
                    logger.error(f"Task failed: No response from bot")

            except Exception as e:
                task_latency = time.time() - task_start
                logger.error(f"Task error: {e}")
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
        logger.info("Running cleanup...")
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

        logger.info(f"Scenario completed: {self.name}")
        logger.info(f"  Tasks passed: {sum(1 for t in task_results if t.success)}/{len(task_results)}")
        logger.info(f"  Average accuracy: {result.average_accuracy:.1f}%")
        logger.info(f"  Average latency: {result.average_latency:.2f}s")

        return result
