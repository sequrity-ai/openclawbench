"""Local OpenClaw client using the 'openclaw agent' CLI command."""

import json
import logging
import subprocess
import time
from dataclasses import dataclass

from config import TelegramConfig

logger = logging.getLogger(__name__)


@dataclass
class LocalMessage:
    """Represents a response from the local OpenClaw agent."""

    text: str | None
    message_id: str
    timestamp: float
    duration_ms: float = 0.0
    model: str | None = None


class LocalClient:
    """Client that talks to the local OpenClaw agent via the CLI."""

    def __init__(self, config: TelegramConfig):
        self.config = config
        self.agent_id = config.agent_id

    async def __aenter__(self) -> "LocalClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def __enter__(self) -> "LocalClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    async def get_me_async(self) -> dict:
        """Verify the gateway is reachable."""
        return self._check_gateway()

    def get_me_sync(self) -> dict:
        """Verify the gateway is reachable (sync)."""
        return self._check_gateway()

    def _check_gateway(self) -> dict:
        result = subprocess.run(
            ["openclaw", "health"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return {"username": "openclaw_local", "id": 0, "status": "connected"}
        raise ValueError(f"Gateway not reachable: {result.stderr.strip()}")

    def _run_agent(self, message: str, timeout: float) -> LocalMessage:
        """Run openclaw agent and return the parsed response."""
        cmd = [
            "openclaw",
            "agent",
            "--agent",
            self.agent_id,
            "--message",
            message,
            "--json",
            "--timeout",
            str(int(timeout)),
        ]

        logger.debug(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 30,  # extra buffer for subprocess overhead
        )

        if result.returncode != 0:
            logger.error(f"Agent command failed: {result.stderr.strip()}")
            raise ValueError(f"Agent command failed: {result.stderr.strip()}")

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse agent response: {result.stdout[:200]}")

        # Extract response text from payloads
        payloads = data.get("result", {}).get("payloads", [])
        text_parts = [p.get("text", "") for p in payloads if p.get("text")]
        full_text = "\n".join(text_parts) if text_parts else None

        meta = data.get("result", {}).get("meta", {})
        agent_meta = meta.get("agentMeta", {})

        return LocalMessage(
            text=full_text,
            message_id=data.get("runId", ""),
            timestamp=time.time(),
            duration_ms=meta.get("durationMs", 0.0),
            model=agent_meta.get("model"),
        )

    async def send_and_receive_async(
        self, message: str, timeout: float = 120.0
    ) -> LocalMessage:
        """Send a message and get the agent's response (async wrapper)."""
        return self._run_agent(message, timeout)

    def send_and_receive_sync(
        self, message: str, timeout: float = 120.0
    ) -> LocalMessage:
        """Send a message and get the agent's response (sync)."""
        return self._run_agent(message, timeout)


class LocalSession:
    """Manages a conversation session with the local OpenClaw agent."""

    def __init__(self, client: LocalClient, chat_id: int = 0):
        self.client = client
        self.chat_id = chat_id
        self.messages: list[LocalMessage] = []
        self.start_time = time.time()

    async def send_message_async(
        self, text: str, wait_for_response: bool = True, timeout: float = 120.0
    ) -> LocalMessage | None:
        """Send a message and wait for the agent's response."""
        logger.info(f"Sending to local agent: {text[:80]}...")

        if not wait_for_response:
            return None

        response = await self.client.send_and_receive_async(text, timeout=timeout)
        self.messages.append(response)

        if response.text:
            logger.info(
                f"Received response ({len(response.text)} chars, "
                f"{response.duration_ms:.0f}ms): {response.text[:80]}..."
            )
        else:
            logger.warning("Received empty response from agent")

        return response

    def send_message_sync(
        self, text: str, wait_for_response: bool = True, timeout: float = 120.0
    ) -> LocalMessage | None:
        """Send a message and wait for the agent's response (sync)."""
        logger.info(f"Sending to local agent: {text[:80]}...")

        if not wait_for_response:
            return None

        response = self.client.send_and_receive_sync(text, timeout=timeout)
        self.messages.append(response)

        if response.text:
            logger.info(
                f"Received response ({len(response.text)} chars, "
                f"{response.duration_ms:.0f}ms): {response.text[:80]}..."
            )
        else:
            logger.warning("Received empty response from agent")

        return response

    def get_duration(self) -> float:
        """Get the duration of the session in seconds."""
        return time.time() - self.start_time
