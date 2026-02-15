"""Telegram Client API client using Pyrogram for user-based interactions."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from pyrogram import Client
from pyrogram.types import Message as PyrogramMessage

from config import TelegramConfig

logger = logging.getLogger(__name__)


@dataclass
class TelegramMessage:
    """Represents a Telegram message."""

    message_id: int
    chat_id: int
    text: str | None
    from_user_id: int | None
    from_username: str | None
    date: int

    @classmethod
    def from_pyrogram(cls, msg: PyrogramMessage) -> "TelegramMessage":
        """Create a TelegramMessage from Pyrogram Message."""
        return cls(
            message_id=msg.id,
            chat_id=msg.chat.id,
            text=msg.text,
            from_user_id=msg.from_user.id if msg.from_user else None,
            from_username=msg.from_user.username if msg.from_user else None,
            date=int(msg.date.timestamp()) if msg.date else 0,
        )


class TelegramClient:
    """Telegram Client API client using Pyrogram."""

    def __init__(self, config: TelegramConfig):
        """Initialize the Telegram client.

        Args:
            config: Telegram configuration
        """
        self.config = config
        self._client: Client | None = None
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging based on configuration."""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        if self.config.debug_mode:
            logger.setLevel(logging.DEBUG)

    async def __aenter__(self) -> "TelegramClient":
        """Async context manager entry."""
        # Check if session exists
        from pathlib import Path
        import os

        # Use absolute path for session file
        session_dir = os.getcwd()
        session_name = self.config.telegram_session_name
        session_path = os.path.join(session_dir, session_name)
        session_file = Path(f"{session_path}.session")

        # Only pass phone_number if session doesn't exist (first time auth)
        client_kwargs = {
            "name": session_path,
            "api_id": self.config.telegram_api_id,
            "api_hash": self.config.telegram_api_hash,
        }
        if not session_file.exists() and self.config.telegram_phone:
            client_kwargs["phone_number"] = self.config.telegram_phone

        self._client = Client(**client_kwargs)
        await self._client.start()
        logger.info("Telegram client started")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.stop()
            logger.info("Telegram client stopped")

    def __enter__(self) -> "TelegramClient":
        """Sync context manager entry."""
        # Check if session exists
        from pathlib import Path
        import os

        # Use absolute path for session file
        session_dir = os.getcwd()
        session_name = self.config.telegram_session_name
        session_path = os.path.join(session_dir, session_name)
        session_file = Path(f"{session_path}.session")

        # Only pass phone_number if session doesn't exist (first time auth)
        client_kwargs = {
            "name": session_path,
            "api_id": self.config.telegram_api_id,
            "api_hash": self.config.telegram_api_hash,
        }
        if not session_file.exists() and self.config.telegram_phone:
            client_kwargs["phone_number"] = self.config.telegram_phone

        self._client = Client(**client_kwargs)
        self._client.start()
        logger.info("Telegram client started (sync)")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Sync context manager exit."""
        if self._client:
            self._client.stop()
            logger.info("Telegram client stopped (sync)")

    async def send_message_async(
        self, chat_id: int | str, text: str
    ) -> TelegramMessage:
        """Send a message asynchronously.

        Args:
            chat_id: Chat ID or username to send message to
            text: Message text

        Returns:
            Sent message
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use context manager.")

        msg = await self._client.send_message(chat_id, text)
        return TelegramMessage.from_pyrogram(msg)

    def send_message_sync(
        self, chat_id: int | str, text: str
    ) -> TelegramMessage:
        """Send a message synchronously.

        Args:
            chat_id: Chat ID or username to send message to
            text: Message text

        Returns:
            Sent message
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use context manager.")

        msg = self._client.send_message(chat_id, text)
        return TelegramMessage.from_pyrogram(msg)

    async def get_chat_history_async(
        self, chat_id: int | str, limit: int = 10
    ) -> list[TelegramMessage]:
        """Get chat history asynchronously.

        Args:
            chat_id: Chat ID or username
            limit: Number of messages to retrieve

        Returns:
            List of messages
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use context manager.")

        messages = []
        async for msg in self._client.get_chat_history(chat_id, limit=limit):
            messages.append(TelegramMessage.from_pyrogram(msg))
        return messages

    def get_chat_history_sync(
        self, chat_id: int | str, limit: int = 10
    ) -> list[TelegramMessage]:
        """Get chat history synchronously.

        Args:
            chat_id: Chat ID or username
            limit: Number of messages to retrieve

        Returns:
            List of messages
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use context manager.")

        messages = []
        for msg in self._client.get_chat_history(chat_id, limit=limit):
            messages.append(TelegramMessage.from_pyrogram(msg))
        return messages

    async def get_me_async(self) -> dict[str, Any]:
        """Get current user information asynchronously.

        Returns:
            User information
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use context manager.")

        me = await self._client.get_me()
        return {
            "id": me.id,
            "username": me.username,
            "first_name": me.first_name,
            "last_name": me.last_name,
            "phone_number": me.phone_number,
        }

    def get_me_sync(self) -> dict[str, Any]:
        """Get current user information synchronously.

        Returns:
            User information
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use context manager.")

        me = self._client.get_me()
        return {
            "id": me.id,
            "username": me.username,
            "first_name": me.first_name,
            "last_name": me.last_name,
            "phone_number": me.phone_number,
        }


class TelegramSession:
    """Manages a conversation session with a Telegram bot."""

    def __init__(self, client: TelegramClient, bot_username: str):
        """Initialize a Telegram session.

        Args:
            client: Telegram client
            bot_username: Bot username to chat with (e.g., '@aaron123openclawbot')
        """
        self.client = client
        self.bot_username = bot_username if bot_username.startswith("@") else f"@{bot_username}"
        self.messages: list[TelegramMessage] = []
        self.start_time = time.time()
        self._last_message_id: int = 0

    async def send_message_async(
        self, text: str, wait_for_response: bool = True, timeout: float = 30.0
    ) -> TelegramMessage | None:
        """Send a message and optionally wait for a response.

        Args:
            text: Message text
            wait_for_response: Whether to wait for a response
            timeout: Maximum time to wait for response in seconds

        Returns:
            Response message if wait_for_response is True, else None
        """
        sent_msg = await self.client.send_message_async(self.bot_username, text)
        self.messages.append(sent_msg)
        self._last_message_id = sent_msg.message_id
        logger.info(f"Sent message to {self.bot_username}: {text[:50]}...")

        if wait_for_response:
            response = await self._wait_for_response_async(timeout)
            if response:
                self.messages.append(response)
                self._last_message_id = response.message_id
            return response

        return None

    def send_message_sync(
        self, text: str, wait_for_response: bool = True, timeout: float = 30.0
    ) -> TelegramMessage | None:
        """Send a message and optionally wait for a response (sync).

        Args:
            text: Message text
            wait_for_response: Whether to wait for a response
            timeout: Maximum time to wait for response in seconds

        Returns:
            Response message if wait_for_response is True, else None
        """
        sent_msg = self.client.send_message_sync(self.bot_username, text)
        self.messages.append(sent_msg)
        self._last_message_id = sent_msg.message_id
        logger.info(f"Sent message to {self.bot_username}: {text[:50]}...")

        if wait_for_response:
            response = self._wait_for_response_sync(timeout)
            if response:
                self.messages.append(response)
                self._last_message_id = response.message_id
            return response

        return None

    async def _wait_for_response_async(self, timeout: float) -> TelegramMessage | None:
        """Wait for a response from the bot asynchronously.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Response message or None if timeout
        """
        start_time = time.time()
        polling_interval = self.client.config.polling_interval

        while time.time() - start_time < timeout:
            # Get recent chat history
            history = await self.client.get_chat_history_async(self.bot_username, limit=5)

            # Look for bot's response after our last message
            for msg in reversed(history):  # Check newest first
                if (
                    msg.message_id > self._last_message_id
                    and msg.from_username  # Message has a sender
                    and msg.text  # Has text content
                ):
                    logger.info(f"Received response from {self.bot_username}: {msg.text[:50]}...")
                    return msg

            await asyncio.sleep(polling_interval)

        logger.warning(f"Response timeout after {timeout}s")
        return None

    def _wait_for_response_sync(self, timeout: float) -> TelegramMessage | None:
        """Wait for a response from the bot synchronously.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Response message or None if timeout
        """
        start_time = time.time()
        polling_interval = self.client.config.polling_interval

        while time.time() - start_time < timeout:
            # Get recent chat history
            history = self.client.get_chat_history_sync(self.bot_username, limit=5)

            # Look for bot's response after our last message
            for msg in reversed(history):  # Check newest first
                if (
                    msg.message_id > self._last_message_id
                    and msg.from_username  # Message has a sender
                    and msg.text  # Has text content
                ):
                    logger.info(f"Received response from {self.bot_username}: {msg.text[:50]}...")
                    return msg

            time.sleep(polling_interval)

        logger.warning(f"Response timeout after {timeout}s")
        return None

    def get_duration(self) -> float:
        """Get the duration of the session in seconds."""
        return time.time() - self.start_time
