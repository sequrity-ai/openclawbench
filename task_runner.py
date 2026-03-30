"""Harbor-native task runner for openclawbench.

Discovers tasks from the filesystem, runs them against an agent, and validates
results using test scripts. Each task is a directory containing:

  instruction.md        - prompt for the agent
  task.toml             - metadata (difficulty, timeout, category, etc.)
  environment/setup.py  - seed data creation (optional)
  tests/test.sh         - validation script (writes reward.txt)
  solution/solve.sh     - reference solution (optional)
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TaskSpec:
    """A task loaded from a directory."""

    name: str
    scenario: str
    path: Path
    instruction: str
    difficulty: str = "easy"
    category: str = ""
    tags: list[str] = field(default_factory=list)
    timeout_sec: int = 120
    verifier_timeout_sec: int = 60
    validation_type: str = "file"  # "file" or "response"
    required_skills: list[str] = field(default_factory=list)
    required_credentials: list[str] = field(default_factory=list)
    allow_internet: bool = False


@dataclass
class TaskResult:
    """Result of a single task execution."""

    task_name: str
    scenario: str
    prompt: str
    success: bool
    reward: float  # 0.0 or 1.0
    latency: float
    accuracy_score: float  # 0-100
    response_text: str | None = None
    error_message: str | None = None
    conversation_turns: int = 1
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    completion_reason: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cache_read_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_name": self.task_name,
            "scenario": self.scenario,
            "prompt": self.prompt,
            "success": self.success,
            "reward": self.reward,
            "latency": self.latency,
            "accuracy_score": self.accuracy_score,
            "response_text": self.response_text,
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
class SuiteResult:
    """Result of running a suite of tasks."""

    scenario_name: str
    start_time: float
    end_time: float
    total_duration: float
    task_results: list[TaskResult]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def all_tasks_passed(self) -> bool:
        return all(t.success for t in self.task_results)

    @property
    def average_accuracy(self) -> float:
        if not self.task_results:
            return 0.0
        return sum(t.accuracy_score for t in self.task_results) / len(self.task_results)

    @property
    def average_latency(self) -> float:
        if not self.task_results:
            return 0.0
        return sum(t.latency for t in self.task_results) / len(self.task_results)

    @property
    def total_input_tokens(self) -> int:
        return sum(t.input_tokens for t in self.task_results)

    @property
    def total_output_tokens(self) -> int:
        return sum(t.output_tokens for t in self.task_results)

    @property
    def total_reasoning_tokens(self) -> int:
        return sum(t.reasoning_tokens for t in self.task_results)

    @property
    def total_cache_read_tokens(self) -> int:
        return sum(t.cache_read_tokens for t in self.task_results)

    @property
    def total_tokens(self) -> int:
        return (
            self.total_input_tokens
            + self.total_output_tokens
            + self.total_reasoning_tokens
            + self.total_cache_read_tokens
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration": self.total_duration,
            "task_results": [t.to_dict() for t in self.task_results],
            "all_tasks_passed": self.all_tasks_passed,
            "average_accuracy": self.average_accuracy,
            "average_latency": self.average_latency,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_reasoning_tokens": self.total_reasoning_tokens,
            "total_cache_read_tokens": self.total_cache_read_tokens,
            "total_tokens": self.total_tokens,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Workspace backends
# ---------------------------------------------------------------------------

class LocalBackend:
    """Runs tasks on the local filesystem."""

    def __init__(self, workspace_path: str = "/tmp/openclaw_benchmark"):
        self.workspace_path = workspace_path

    def setup_workspace(self, task: TaskSpec) -> None:
        """Run the task's setup script to seed the workspace."""
        os.makedirs(self.workspace_path, exist_ok=True)

        setup_py = task.path / "environment" / "setup_workspace.py"
        setup_sh = task.path / "environment" / "setup.sh"

        if setup_py.exists():
            subprocess.run(
                ["python3", str(setup_py), self.workspace_path],
                check=True, capture_output=True, text=True,
            )
            logger.info(f"Setup complete: {setup_py}")
        elif setup_sh.exists():
            subprocess.run(
                ["bash", str(setup_sh), self.workspace_path],
                check=True, capture_output=True, text=True,
            )
            logger.info(f"Setup complete: {setup_sh}")
        else:
            logger.info(f"No setup script for task {task.name}")

    def cleanup_workspace(self) -> None:
        if os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)
            logger.info(f"Cleaned up workspace: {self.workspace_path}")

    def run_verifier(self, task: TaskSpec, response_text: str | None = None) -> float:
        """Run test.sh and return reward (0.0 or 1.0)."""
        reward_dir = os.path.join(self.workspace_path, ".logs", "verifier")
        os.makedirs(reward_dir, exist_ok=True)
        reward_file = os.path.join(reward_dir, "reward.txt")

        # Write agent response for response-based tasks
        if response_text is not None:
            agent_dir = os.path.join(self.workspace_path, ".logs", "agent")
            os.makedirs(agent_dir, exist_ok=True)
            with open(os.path.join(agent_dir, "response.txt"), "w") as f:
                f.write(response_text)

        test_sh = task.path / "tests" / "test.sh"
        test_py = task.path / "tests" / "test.py"

        env = os.environ.copy()
        env["WORKSPACE"] = self.workspace_path
        env["REWARD_DIR"] = reward_dir

        if test_sh.exists():
            # Rewrite /workspace and /logs/verifier paths for local execution
            script = test_sh.read_text()
            script = script.replace("/workspace", self.workspace_path)
            script = script.replace("/logs/verifier", reward_dir)
            script = script.replace("/logs/agent", os.path.join(self.workspace_path, ".logs", "agent"))

            result = subprocess.run(
                ["bash", "-c", script],
                capture_output=True, text=True, timeout=task.verifier_timeout_sec,
                env=env,
            )
            if result.returncode != 0:
                logger.warning(f"Verifier failed: {result.stderr.strip()}")
        elif test_py.exists():
            script = test_py.read_text()
            script = script.replace("/workspace", self.workspace_path)
            script = script.replace("/logs/verifier", reward_dir)
            script = script.replace("/logs/agent", os.path.join(self.workspace_path, ".logs", "agent"))

            result = subprocess.run(
                ["python3", "-c", script],
                capture_output=True, text=True, timeout=task.verifier_timeout_sec,
                env=env,
            )
            if result.returncode != 0:
                logger.warning(f"Verifier failed: {result.stderr.strip()}")
        else:
            logger.error(f"No test script found for task {task.name}")
            return 0.0

        try:
            with open(reward_file) as f:
                return float(f.read().strip())
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Could not read reward.txt: {e}")
            return 0.0


class DaytonaBackend:
    """Runs tasks in a Daytona cloud sandbox with openclaw agent installed."""

    # Built-in provider definitions: env var, base URL, and API adapter type.
    # openclaw validates that baseUrl and models are present even for well-known
    # providers, so we must supply the full config block.
    BUILTIN_PROVIDERS: dict[str, dict[str, str]] = {
        "openai": {
            "env_var": "OPENAI_API_KEY",
            "baseUrl": "https://api.openai.com/v1",
            "api": "openai-completions",
        },
        "anthropic": {
            "env_var": "ANTHROPIC_API_KEY",
            "baseUrl": "https://api.anthropic.com",
            "api": "anthropic-messages",
        },
        "google": {
            "env_var": "GEMINI_API_KEY",
            "baseUrl": "https://generativelanguage.googleapis.com/v1beta",
            "api": "google-generative-ai",
        },
        "groq": {
            "env_var": "GROQ_API_KEY",
            "baseUrl": "https://api.groq.com/openai/v1",
            "api": "openai-completions",
        },
        "mistral": {
            "env_var": "MISTRAL_API_KEY",
            "baseUrl": "https://api.mistral.ai/v1",
            "api": "openai-completions",
        },
        "xai": {
            "env_var": "XAI_API_KEY",
            "baseUrl": "https://api.x.ai/v1",
            "api": "openai-completions",
        },
        "together": {
            "env_var": "TOGETHER_API_KEY",
            "baseUrl": "https://api.together.xyz/v1",
            "api": "openai-completions",
        },
    }

    @staticmethod
    def _build_sequrity_provider_config() -> dict:
        """Build the custom sequrity provider config block.

        Requires SEQURITY_API_KEY, SEQURITY_AZURE_KEY in env or .env file.
        Uses SEQURITY_BASE_URL if set, otherwise defaults to public endpoint.
        """
        api_key = os.environ.get("SEQURITY_API_KEY", "")
        azure_key = os.environ.get("SEQURITY_AZURE_KEY", "")
        base_url = os.environ.get(
            "SEQURITY_BASE_URL",
            "https://api.sequrity.ai/control/chat/sequrity_azure/v1",
        )
        return {
            "baseUrl": base_url,
            "apiKey": api_key,
            "api": "openai-completions",
            "headers": {
                "X-Features": '{"agent_arch":"dual-llm"}',
                "X-Policy": '{"mode": "standard", "presets": {"default_allow": true, "default_allow_enforcement_level": "soft"}}',
                "X-Config": '{"fsm":{"enable_multistep_planning":true,"disable_rllm":true,"max_n_turns":50,"max_pllm_steps":50,"max_pllm_failed_steps":10,"history_mismatch_policy":"restart_turn"},"response_format":{"strip_response_content":true}}',
                "X-Api-Key": azure_key,
            },
            "authHeader": True,
            "models": [
                {
                    "id": "gpt-5.2",
                    "name": "Sequrity Azure GPT-5.2",
                    "reasoning": False,
                    "input": ["text"],
                    "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
                    "contextWindow": 200000,
                    "maxTokens": 16384,
                    "compat": {
                        "supportsDeveloperRole": False,
                        "supportsUsageInStreaming": False,
                        "supportsStrictMode": True,
                    },
                }
            ],
        }

    @classmethod
    def _build_openclaw_config(cls, provider: str, model: str) -> dict:
        """Build openclaw config for the sandbox.

        Args:
            provider: Provider name (e.g. "sequrity", "openai", "anthropic").
            model: Model ID (e.g. "gpt-5.2", "claude-sonnet-4-6", "gpt-5.4").
        """
        # --- provider-specific models block ---
        providers_block: dict[str, Any] = {}

        # Helper to build a minimal model catalog entry for the requested model.
        def _model_entry(model_id: str) -> list[dict[str, Any]]:
            return [
                {
                    "id": model_id,
                    "name": model_id,
                    "reasoning": False,
                    "input": ["text"],
                    "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
                    "contextWindow": 200000,
                    "maxTokens": 16384,
                }
            ]

        if provider == "sequrity":
            providers_block["sequrity"] = cls._build_sequrity_provider_config()
        elif provider in cls.BUILTIN_PROVIDERS:
            info = cls.BUILTIN_PROVIDERS[provider]
            env_var = info["env_var"]
            api_key = os.environ.get(env_var, "")
            if not api_key:
                logger.warning(
                    f"Environment variable {env_var} is not set — "
                    f"the {provider} provider may fail to authenticate in the sandbox."
                )
            providers_block[provider] = {
                "baseUrl": info["baseUrl"],
                "apiKey": api_key,
                "api": info["api"],
                "models": _model_entry(model),
            }
        else:
            # Unknown provider — assume OpenAI-compatible and let the user
            # supply config via env vars named <PROVIDER>_API_KEY / _BASE_URL.
            env_prefix = provider.upper().replace("-", "_")
            api_key = os.environ.get(f"{env_prefix}_API_KEY", "")
            base_url = os.environ.get(f"{env_prefix}_BASE_URL", "")
            if not api_key:
                logger.warning(
                    f"No API key found for custom provider '{provider}' — "
                    f"set {env_prefix}_API_KEY in your environment."
                )
            if not base_url:
                logger.warning(
                    f"No base URL for custom provider '{provider}' — "
                    f"set {env_prefix}_BASE_URL in your environment."
                )
            providers_block[provider] = {
                "baseUrl": base_url,
                "apiKey": api_key,
                "api": "openai-completions",
                "models": _model_entry(model),
            }

        model_ref = f"{provider}/{model}"

        return {
            "models": {"providers": providers_block},
            "agents": {
                "defaults": {
                    "model": {"primary": model_ref, "fallbacks": []},
                    "workspace": "/workspace",
                    "timeoutSeconds": 300,
                    "sandbox": {"mode": "off"},
                }
            },
            "tools": {
                "exec": {"host": "sandbox"},
            },
            "gateway": {
                "port": 18789,
                "mode": "local",
                "bind": "loopback",
                "auth": {"mode": "token", "token": "sandbox_bench_token"},
            },
        }

    def __init__(self, api_key: str, api_url: str = "https://app.daytona.io/api",
                 image: str = "node:22-bookworm", workspace_path: str = "/workspace",
                 provider: str = "sequrity", model: str = "gpt-5.2"):
        self.api_key = api_key
        self.api_url = api_url
        self.image = image
        self.workspace_path = workspace_path
        self.provider = provider
        self.model = model
        self._daytona = None
        self._sandbox = None

    def _get_client(self):
        if self._daytona is None:
            from daytona_sdk import Daytona, DaytonaConfig
            self._daytona = Daytona(DaytonaConfig(
                api_key=self.api_key,
                api_url=self.api_url,
            ))
        return self._daytona

    def _ensure_sandbox(self):
        if self._sandbox is None:
            from daytona_sdk import CreateSandboxFromImageParams
            client = self._get_client()
            logger.info("Creating Daytona sandbox...")
            self._sandbox = client.create(
                CreateSandboxFromImageParams(image=self.image),
                timeout=120,
            )
            self._sandbox.process.exec(f"mkdir -p {self.workspace_path}")
            logger.info(f"Sandbox created: {self._sandbox.id}")
            self._install_openclaw()

    def _install_openclaw(self):
        """Install openclaw and write config inside the sandbox."""
        logger.info("Installing openclaw in sandbox...")

        # Install openclaw from GitHub release tarball (pre-built from fork with sequrity FSM fix).
        # To update: rebuild locally, create a new GitHub release, and update the URL below.
        release_url = "https://github.com/Aaron-Zhao123/openclaw/releases/download/v2026.3.14/openclaw-2026.3.14.tgz"
        logger.info(f"Installing openclaw from release: {release_url}")
        r = self._sandbox.process.exec(f"npm install -g {release_url}", timeout=180)
        logger.info(f"install stdout: {r.result.strip()[-500:] if r.result else '(no output)'}")
        logger.info(f"install exit: {r.exit_code}")

        # Install python3 (node:22-bookworm has apt)
        self._sandbox.process.exec(
            "apt-get update -qq && apt-get install -y -qq python3 > /dev/null 2>&1",
            timeout=120,
        )

        # Write openclaw config
        config_json = json.dumps(self._build_openclaw_config(self.provider, self.model), indent=2)
        self._sandbox.process.exec("mkdir -p /root/.openclaw")
        self._sandbox.fs.upload_file(
            config_json.encode("utf-8"),
            "/root/.openclaw/openclaw.json",
        )
        logger.info("openclaw config written to sandbox")

        # Verify openclaw is available
        r = self._sandbox.process.exec("openclaw --version")
        logger.info(f"openclaw version: {r.result.strip()}")

        # Log the config for debugging
        logger.info("Sandbox config: workspace=/workspace, sandbox=off, exec.host=node")

    def send_to_agent(self, message: str, timeout: float, agent_id: str = "main", session_id: str | None = None) -> dict:
        """Run openclaw agent inside the sandbox and return parsed response."""
        self._ensure_sandbox()

        sid = session_id or f"bench-{int(time.time())}"
        agent_cmd = (
            f"openclaw agent --local "
            f"--session-id {json.dumps(sid)} "
            f"--message {json.dumps(message)} "
            f"--json --timeout {int(timeout) + 180}"
        )
        cmd = f"bash -c {json.dumps(agent_cmd + ' 2>&1')}"
        logger.debug(f"Running in sandbox: openclaw agent --message '{message[:80]}...'")

        r = self._sandbox.process.exec(cmd, timeout=int(timeout) + 240)
        stdout = r.result
        logger.info(f"[agent raw] exit={getattr(r, 'exit_code', '?')} len={len(stdout) if stdout else 0} first500={repr(stdout[:500] if stdout else None)}")

        if not stdout or not stdout.strip():
            raise RuntimeError("Empty response from agent in sandbox")

        # Parse JSON (may have non-JSON lines before it)
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            json_start = stdout.find("{")
            if json_start >= 0:
                try:
                    data = json.loads(stdout[json_start:])
                except json.JSONDecodeError:
                    raise RuntimeError(f"Failed to parse agent response: {stdout[:300]}")
            else:
                raise RuntimeError(f"No JSON in agent response: {stdout[:300]}")

        # Extract response text
        inner = data.get("result", data)
        payloads = inner.get("payloads", [])
        text_parts = [p.get("text", "") for p in payloads if p.get("text")]
        text = "\n".join(text_parts) if text_parts else None

        meta = inner.get("meta", {})
        agent_meta = meta.get("agentMeta", {})
        usage = agent_meta.get("usage", {})
        return {
            "text": text,
            "input_tokens": usage.get("input", 0),
            "output_tokens": usage.get("output", 0),
            "reasoning_tokens": usage.get("reasoning", 0),
            "cache_read_tokens": usage.get("totalCacheRead", 0) or usage.get("cacheRead", 0),
            "duration_ms": meta.get("durationMs", 0.0),
            "model": agent_meta.get("model"),
        }

    def setup_workspace(self, task: TaskSpec) -> None:
        self._ensure_sandbox()

        setup_py = task.path / "environment" / "setup_workspace.py"
        setup_sh = task.path / "environment" / "setup.sh"

        if setup_py.exists():
            with open(setup_py, "rb") as f:
                self._sandbox.fs.upload_file(f.read(), "/tmp/setup_workspace.py")
            r = self._sandbox.process.exec(f"python3 /tmp/setup_workspace.py {self.workspace_path}")
            logger.info(f"Setup: {r.result.strip()}")
        elif setup_sh.exists():
            with open(setup_sh, "rb") as f:
                self._sandbox.fs.upload_file(f.read(), "/tmp/setup.sh")
            self._sandbox.process.exec(f"bash /tmp/setup.sh {self.workspace_path}")

    def cleanup_workspace(self) -> None:
        """Clean workspace directory inside the sandbox (keeps sandbox alive)."""
        if self._sandbox is not None:
            self._sandbox.process.exec(f"rm -rf {self.workspace_path}/*")
            self._sandbox.process.exec("rm -rf /logs/verifier /logs/agent")
            logger.info("Cleaned workspace in sandbox")

    def destroy(self) -> None:
        """Stop and delete the sandbox."""
        if self._sandbox is not None:
            client = self._get_client()
            sid = self._sandbox.id
            # Stop first (required before delete on some plans)
            try:
                client.stop(self._sandbox)
                logger.info(f"Sandbox stopped: {sid}")
            except Exception as e:
                logger.debug(f"Sandbox stop skipped ({sid}): {e}")
            # Then delete
            try:
                client.delete(self._sandbox)
                logger.info(f"Sandbox deleted: {sid}")
            except Exception as e:
                logger.warning(f"Failed to delete sandbox {sid}: {e}")
            self._sandbox = None

    def run_verifier(self, task: TaskSpec, response_text: str | None = None) -> float:
        self._ensure_sandbox()

        reward_dir = "/logs/verifier"
        agent_dir = "/logs/agent"
        self._sandbox.process.exec(f"mkdir -p {reward_dir} {agent_dir}")

        # Write agent response for response-based tasks
        if response_text is not None:
            self._sandbox.fs.upload_file(
                response_text.encode("utf-8"),
                f"{agent_dir}/response.txt",
            )

        test_sh = task.path / "tests" / "test.sh"
        test_py = task.path / "tests" / "test.py"

        if test_sh.exists():
            with open(test_sh, "rb") as f:
                self._sandbox.fs.upload_file(f.read(), "/tmp/test.sh")
            self._sandbox.process.exec(f"REWARD_DIR={reward_dir} bash /tmp/test.sh")
        elif test_py.exists():
            with open(test_py, "rb") as f:
                self._sandbox.fs.upload_file(f.read(), "/tmp/test.py")
            self._sandbox.process.exec(f"REWARD_DIR={reward_dir} python3 /tmp/test.py")
        else:
            logger.error(f"No test script for {task.name}")
            return 0.0

        r = self._sandbox.process.exec(f"cat {reward_dir}/reward.txt")
        try:
            return float(r.result.strip())
        except (ValueError, AttributeError):
            logger.error("Could not read reward.txt from sandbox")
            return 0.0


# ---------------------------------------------------------------------------
# Task discovery
# ---------------------------------------------------------------------------

def _parse_toml_simple(text: str) -> dict:
    """Minimal TOML parser for task.toml files.

    Handles flat key=value pairs and [section] headers.
    Does not handle nested tables, arrays of tables, or multi-line values.
    """
    result: dict[str, Any] = {}
    current_section: dict[str, Any] | None = None
    current_key: str | None = None

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Section header
        if stripped.startswith("[") and stripped.endswith("]"):
            section_name = stripped[1:-1].strip()
            # Handle dotted sections like [metadata]
            parts = [p.strip() for p in section_name.split(".")]
            d = result
            for part in parts:
                if part not in d:
                    d[part] = {}
                d = d[part]
            current_section = d
            current_key = None
            continue

        if "=" in stripped:
            key, _, value = stripped.partition("=")
            key = key.strip()
            value = value.strip()

            # Parse value
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            elif value.startswith("[") and value.endswith("]"):
                # Simple array
                inner = value[1:-1].strip()
                if inner:
                    items = []
                    for item in inner.split(","):
                        item = item.strip().strip('"').strip("'")
                        if item:
                            items.append(item)
                    value = items
                else:
                    value = []
            elif value == "true":
                value = True
            elif value == "false":
                value = False
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass

            target = current_section if current_section is not None else result
            target[key] = value

    return result


def discover_tasks(
    tasks_dir: Path,
    scenario: str | None = None,
    difficulty: str | None = None,
    task_name: str | None = None,
) -> list[TaskSpec]:
    """Discover tasks from the filesystem.

    Args:
        tasks_dir: Root directory containing scenario subdirectories
        scenario: Filter by scenario name (e.g. "file", "weather")
        difficulty: Filter by difficulty ("easy", "medium", "hard")
        task_name: Filter by specific task name

    Returns:
        List of TaskSpec objects
    """
    tasks = []

    if not tasks_dir.exists():
        logger.warning(f"Tasks directory not found: {tasks_dir}")
        return tasks

    # Walk tasks/<scenario>/<task-name>/ structure
    for scenario_dir in sorted(tasks_dir.iterdir()):
        if not scenario_dir.is_dir():
            continue

        scenario_name = scenario_dir.name
        if scenario and scenario != "all" and scenario_name != scenario:
            continue

        for task_dir in sorted(scenario_dir.iterdir()):
            if not task_dir.is_dir():
                continue

            toml_file = task_dir / "task.toml"
            instruction_file = task_dir / "instruction.md"

            if not toml_file.exists() or not instruction_file.exists():
                continue

            # Parse task.toml
            toml_data = _parse_toml_simple(toml_file.read_text())
            metadata = toml_data.get("metadata", {})
            agent_cfg = toml_data.get("agent", {})
            verifier_cfg = toml_data.get("verifier", {})
            env_cfg = toml_data.get("environment", {})
            cred_cfg = toml_data.get("credentials", {})

            task_difficulty = metadata.get("difficulty", "easy")
            if difficulty and difficulty != "all" and task_difficulty != difficulty:
                continue

            name = task_dir.name
            if task_name and name != task_name:
                continue

            instruction = instruction_file.read_text().strip()

            spec = TaskSpec(
                name=name,
                scenario=scenario_name,
                path=task_dir,
                instruction=instruction,
                difficulty=task_difficulty,
                category=metadata.get("category", ""),
                tags=metadata.get("tags", []),
                timeout_sec=agent_cfg.get("timeout_sec", 120),
                verifier_timeout_sec=verifier_cfg.get("timeout_sec", 60),
                validation_type=metadata.get("validation_type", "file"),
                required_skills=metadata.get("required_skills", []),
                required_credentials=cred_cfg.get("required", []),
                allow_internet=env_cfg.get("allow_internet", False),
            )
            tasks.append(spec)

    logger.info(f"Discovered {len(tasks)} tasks from {tasks_dir}")
    return tasks


# ---------------------------------------------------------------------------
# Session lock cleanup (from base.py)
# ---------------------------------------------------------------------------

def _clear_stale_session_locks(agent_id: str = "main") -> None:
    """Remove stale .lock files for the given agent."""
    import glob as globmod

    lock_pattern = os.path.expanduser(f"~/.openclaw/agents/{agent_id}/sessions/*.lock")
    for lock_path in globmod.glob(lock_pattern):
        try:
            with open(lock_path) as f:
                content = f.read().strip()
            pid = None
            for part in content.split():
                if part.isdigit():
                    pid = int(part)
                    break
            if pid:
                try:
                    os.kill(pid, 0)
                    continue  # process alive, skip
                except OSError:
                    pass
            os.remove(lock_path)
            logger.info(f"Removed stale session lock: {lock_path}")
        except Exception as e:
            logger.warning(f"Could not check/remove lock {lock_path}: {e}")


# ---------------------------------------------------------------------------
# Task runner
# ---------------------------------------------------------------------------

class TaskRunner:
    """Runs benchmark tasks from Harbor-format directories."""

    def __init__(
        self,
        backend: LocalBackend | DaytonaBackend,
        agent_id: str = "main",
        timeout_multiplier: float = 1.0,
    ):
        self.backend = backend
        self.agent_id = agent_id
        self.timeout_multiplier = timeout_multiplier

    def _send_to_agent(self, message: str, timeout: float, session_id: str | None = None) -> dict:
        """Send a message to the openclaw agent and return parsed response.

        Returns dict with keys: text, input_tokens, output_tokens,
        reasoning_tokens, cache_read_tokens, duration_ms, model.
        """
        cmd = [
            "openclaw", "agent",
            "--local",
            "--session-id", session_id or f"bench-{int(time.time())}",
            "--message", message,
            "--json",
            "--timeout", str(int(timeout)),
        ]

        logger.debug(f"Running: openclaw agent --message '{message[:80]}...'")
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout + 30,
        )

        if result.stderr:
            logger.debug(f"[agent stderr] {result.stderr.strip()[:500]}")
        if result.returncode != 0:
            raise RuntimeError(f"Agent command failed (rc={result.returncode}): {result.stderr.strip()[:500]}")

        # openclaw may write JSON to stderr (e.g. when runtime.log goes to stderr)
        # Fall back to stderr if stdout has no JSON
        stdout = result.stdout
        if not stdout.strip() or "{" not in stdout:
            stdout = result.stderr
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            # Try to find JSON object in the output
            json_start = stdout.find("{")
            if json_start >= 0:
                try:
                    data = json.loads(stdout[json_start:])
                except json.JSONDecodeError:
                    raise RuntimeError(f"Failed to parse agent response: {stdout[:200]}")
            else:
                raise RuntimeError(f"No JSON found in agent response: {stdout[:200]}")

        # Extract response text — handle both wrapped {"result": {...}} and flat {"payloads": [...]}
        inner = data.get("result", data)
        payloads = inner.get("payloads", [])
        text_parts = [p.get("text", "") for p in payloads if p.get("text")]
        text = "\n".join(text_parts) if text_parts else None

        # Extract token usage
        meta = inner.get("meta", {})
        agent_meta = meta.get("agentMeta", {})
        usage = agent_meta.get("usage", {})
        last_call = agent_meta.get("lastCallUsage", {})
        inp = usage.get("totalInput", 0) or usage.get("input", 0)
        # Log raw usage for debugging cache reads
        if inp > 36000:  # 3+ turns
            logger.debug(f"[cache-debug] usage={usage} lastCallUsage={last_call}")
        return {
            "text": text,
            "input_tokens": inp,
            "output_tokens": usage.get("output", 0),
            "reasoning_tokens": usage.get("reasoning", 0),
            "cache_read_tokens": usage.get("totalCacheRead", 0) or usage.get("cacheRead", 0),
            "duration_ms": meta.get("durationMs", 0.0),
            "model": agent_meta.get("model"),
        }

    def _reset_session(self) -> None:
        """Send /new to reset agent session context."""
        try:
            cmd = [
                "openclaw", "agent",
                "--agent", self.agent_id,
                "--message", "/new",
                "--json",
                "--timeout", "90",
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                logger.info("Session reset: /new sent successfully")
            else:
                logger.warning(f"Session reset failed: {result.stderr.strip()}")
        except Exception as e:
            logger.warning(f"Could not reset session: {e}")

    async def run_task(self, task: TaskSpec) -> TaskResult:
        """Run a single task: setup → agent → verify → result."""
        run_id = f"{task.scenario}/{task.name}"
        logger.info(f"[{run_id}] ===== TASK START =====")
        task_start = time.time()

        try:
            # 1. Setup workspace
            logger.info(f"[{run_id}] Setting up workspace...")
            self.backend.setup_workspace(task)

            # 2. Clear stale locks (local only)
            if isinstance(self.backend, LocalBackend):
                _clear_stale_session_locks(self.agent_id)

            # 3. Build prompt — replace /workspace with actual path for local backend
            prompt = task.instruction
            if isinstance(self.backend, LocalBackend):
                prompt = prompt.replace("/workspace", self.backend.workspace_path)

            # 4. Send to agent — use a fresh session-id per task to avoid stale context
            session_id = f"bench-{task.scenario}-{task.name}-{int(time.time())}"
            logger.info(f"[{run_id}] Sending to agent (timeout={task.timeout_sec}s, session={session_id})...")
            effective_timeout = task.timeout_sec * self.timeout_multiplier
            if hasattr(self.backend, "send_to_agent"):
                agent_result = self.backend.send_to_agent(
                    prompt, effective_timeout, agent_id=self.agent_id, session_id=session_id
                )
            else:
                agent_result = self._send_to_agent(prompt, effective_timeout, session_id=session_id)
            response_text = agent_result["text"]

            task_latency = time.time() - task_start
            logger.info(
                f"[{run_id}] Agent responded in {task_latency:.1f}s "
                f"({len(response_text) if response_text else 0} chars)"
            )

            # 5. Run verifier
            logger.info(f"[{run_id}] Running verifier...")
            reward = self.backend.run_verifier(task, response_text)
            success = reward >= 1.0

            logger.info(
                f"[{run_id}] Result: {'PASS' if success else 'FAIL'} "
                f"(reward={reward}, latency={task_latency:.1f}s, "
                f"tokens: in={agent_result['input_tokens']} "
                f"out={agent_result['output_tokens']} "
                f"cache_read={agent_result['cache_read_tokens']})"
            )

            return TaskResult(
                task_name=task.name,
                scenario=task.scenario,
                prompt=prompt,
                success=success,
                reward=reward,
                latency=task_latency,
                accuracy_score=100.0 if success else 0.0,
                response_text=response_text,
                conversation_turns=1,
                completion_reason="single_turn",
                input_tokens=agent_result["input_tokens"],
                output_tokens=agent_result["output_tokens"],
                reasoning_tokens=agent_result["reasoning_tokens"],
                cache_read_tokens=agent_result["cache_read_tokens"],
            )

        except Exception as e:
            task_latency = time.time() - task_start
            logger.error(f"[{run_id}] Task error: {e}")
            logger.info(f"[{run_id}] Result: FAIL (reward=0.0, latency={task_latency:.1f}s, tokens: in=0 out=0 cache_read=0)")
            return TaskResult(
                task_name=task.name,
                scenario=task.scenario,
                prompt=task.instruction,
                success=False,
                reward=0.0,
                latency=task_latency,
                accuracy_score=0.0,
                error_message=str(e),
            )

    async def run_suite(
        self,
        tasks: list[TaskSpec],
        scenario_name: str = "all",
    ) -> SuiteResult:
        """Run a suite of tasks sequentially."""
        start_time = time.time()
        results = []

        for i, task in enumerate(tasks, 1):
            logger.info(f"===== Task {i}/{len(tasks)}: {task.scenario}/{task.name} =====")

            # Wait between tasks for session lock release
            if i > 1:
                logger.info("Waiting 3s for session lock release...")
                await asyncio.sleep(3)

            result = await self.run_task(task)
            results.append(result)

            # Cleanup workspace between tasks
            self.backend.cleanup_workspace()

        # Destroy sandbox if using Daytona
        if hasattr(self.backend, "destroy"):
            self.backend.destroy()

        end_time = time.time()

        suite = SuiteResult(
            scenario_name=scenario_name,
            start_time=start_time,
            end_time=end_time,
            total_duration=end_time - start_time,
            task_results=results,
        )

        passed = sum(1 for r in results if r.success)
        logger.info(f"Suite complete: {passed}/{len(results)} passed")
        logger.info(f"Average accuracy: {suite.average_accuracy:.1f}%")
        logger.info(f"Average latency: {suite.average_latency:.1f}s")
        logger.info(
            f"Tokens: in={suite.total_input_tokens} out={suite.total_output_tokens} "
            f"reasoning={suite.total_reasoning_tokens} "
            f"cache_read={suite.total_cache_read_tokens} total={suite.total_tokens}"
        )

        return suite


# ---------------------------------------------------------------------------
# Result export
# ---------------------------------------------------------------------------

def export_results(suite: SuiteResult, output_path: Path) -> None:
    """Export results to JSON or Markdown."""
    data = suite.to_dict()

    # Add summary
    data["summary"] = {
        "total_tasks": len(suite.task_results),
        "tasks_passed": sum(1 for t in suite.task_results if t.success),
        "tasks_failed": sum(1 for t in suite.task_results if not t.success),
        "overall_accuracy": suite.average_accuracy,
        "average_latency": suite.average_latency,
        "total_tokens": suite.total_tokens,
    }

    if output_path.suffix == ".json":
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Results exported to {output_path}")
    elif output_path.suffix == ".md":
        _export_markdown(data, output_path)
        logger.info(f"Results exported to {output_path}")
    else:
        # Default to JSON
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Results exported to {output_path}")


def _export_markdown(data: dict, output_path: Path) -> None:
    """Export results as a Markdown report."""
    lines = [
        f"# Benchmark Results: {data['scenario_name']}",
        "",
        f"**Duration**: {data['total_duration']:.1f}s",
        f"**Tasks**: {data['summary']['tasks_passed']}/{data['summary']['total_tasks']} passed",
        f"**Accuracy**: {data['summary']['overall_accuracy']:.1f}%",
        f"**Total Tokens**: {data['summary']['total_tokens']}",
        "",
        "## Results",
        "",
        "| Task | Scenario | Result | Latency | Tokens |",
        "|------|----------|--------|---------|--------|",
    ]

    for t in data["task_results"]:
        status = "PASS" if t["success"] else "FAIL"
        total_t = t["input_tokens"] + t["output_tokens"] + t["reasoning_tokens"]
        lines.append(
            f"| {t['task_name']} | {t['scenario']} | {status} | {t['latency']:.1f}s | {total_t} |"
        )

    lines.append("")
    output_path.write_text("\n".join(lines))
