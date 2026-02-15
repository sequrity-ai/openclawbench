"""Pydantic AI agent for simulating user interactions in benchmark scenarios."""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import Agent

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""

    turn_number: int
    user_message: str
    bot_response: str | None
    timestamp: float
    success: bool
    error: str | None = None


@dataclass
class ConversationResult:
    """Result of a multi-turn conversation."""

    task_name: str
    task_description: str
    conversation_turns: list[ConversationTurn] = field(default_factory=list)
    total_turns: int = 0
    success: bool = False
    completion_reason: str = ""  # "goal_achieved", "max_turns", "timeout", "error"
    total_latency: float = 0.0
    error_message: str | None = None

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a conversation turn to the result."""
        self.conversation_turns.append(turn)
        self.total_turns += 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_name": self.task_name,
            "task_description": self.task_description,
            "conversation_turns": [
                {
                    "turn_number": turn.turn_number,
                    "user_message": turn.user_message,
                    "bot_response": turn.bot_response,
                    "timestamp": turn.timestamp,
                    "success": turn.success,
                    "error": turn.error,
                }
                for turn in self.conversation_turns
            ],
            "total_turns": self.total_turns,
            "success": self.success,
            "completion_reason": self.completion_reason,
            "total_latency": self.total_latency,
            "error_message": self.error_message,
        }


class BenchmarkAgent:
    """AI agent that simulates a user interacting with the bot."""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        openai_api_key: str = "",
        max_turns: int = 10,
        conversation_timeout: float = 300.0,
    ):
        """Initialize the benchmark agent.

        Args:
            model_name: OpenAI model to use for the agent
            openai_api_key: OpenAI API key
            max_turns: Maximum number of conversation turns
            conversation_timeout: Maximum time for conversation in seconds
        """
        self.model_name = model_name
        self.max_turns = max_turns
        self.conversation_timeout = conversation_timeout
        self.openai_api_key = openai_api_key

        # Initialize Pydantic AI agent
        # Pass API key via model string format: "openai:model-name"
        self.agent = Agent(
            model=f"openai:{model_name}",
            system_prompt=(
                "You are a user testing a Telegram bot's capabilities. "
                "Your goal is to interact naturally with the bot to accomplish a given task.\n\n"
                "CRITICAL INSTRUCTIONS FOR FIRST MESSAGE:\n"
                "- In your FIRST message, you MUST convey the COMPLETE task requirements EXACTLY as given\n"
                "- Include ALL specific details: file paths, exact filenames, data sources, formatting requirements\n"
                "- Do NOT simplify, paraphrase, or omit any details from the task description\n"
                "- Do NOT replace specific paths/names with placeholders or examples\n"
                "- Copy any technical specifications verbatim (paths, formats, etc.)\n\n"
                "After the first message:\n"
                "1. Follow the bot's instructions and respond appropriately\n"
                "2. Ask clarifying questions if needed\n"
                "3. Provide additional information when the bot asks\n"
                "4. Acknowledge when the task is complete\n"
                "5. Be patient and helpful\n\n"
                "Format your responses as plain text messages to send to the bot. "
                "Do not include any meta-commentary or explanations."
            ),
        )

    async def run_conversation_async(
        self, task_name: str, task_description: str, session: Any
    ) -> ConversationResult:
        """Run a multi-turn conversation to accomplish a task.

        Args:
            task_name: Name of the task
            task_description: Description of what the user should accomplish
            session: TelegramSession or LocalSession for sending messages

        Returns:
            Conversation result with all turns and outcome
        """
        result = ConversationResult(
            task_name=task_name, task_description=task_description
        )

        start_time = time.time()
        conversation_history = []

        try:
            # Initial prompt to the agent
            initial_context = (
                f"Task: {task_description}\n\n"
                "Send your first message to the bot. Remember: you MUST include ALL details from the task description above. "
                "Do not simplify or paraphrase - include exact file paths, filenames, and all technical requirements."
            )

            for turn_num in range(1, self.max_turns + 1):
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > self.conversation_timeout:
                    result.completion_reason = "timeout"
                    result.error_message = f"Conversation timeout after {elapsed:.1f}s"
                    logger.warning(
                        f"[{task_name}] Conversation timeout after {turn_num - 1} turns"
                    )
                    break

                turn_start = time.time()
                logger.info(f"[{task_name}] Starting turn {turn_num}/{self.max_turns}")

                try:
                    # Get agent's message using Pydantic AI
                    if turn_num == 1:
                        # First turn: use initial context
                        agent_response = await self.agent.run(initial_context)
                    else:
                        # Subsequent turns: provide conversation history
                        context = self._build_context(
                            task_description, conversation_history
                        )
                        agent_response = await self.agent.run(context)

                    # Extract the response text from Pydantic AI result
                    # The result has an 'output' attribute in the new API
                    if hasattr(agent_response, 'output'):
                        user_message = str(agent_response.output).strip()
                    elif hasattr(agent_response, 'data'):
                        user_message = str(agent_response.data).strip()
                    else:
                        user_message = str(agent_response).strip()
                    logger.info(
                        f"[{task_name}] Agent message (turn {turn_num}): {user_message[:100]}..."
                    )

                    # Send message to bot and wait for response
                    bot_response = await session.send_message_async(
                        user_message, wait_for_response=True, timeout=30.0
                    )

                    turn_success = bot_response is not None and bot_response.text
                    bot_text = bot_response.text if bot_response else None

                    if bot_text:
                        logger.info(
                            f"[{task_name}] Bot response (turn {turn_num}): {bot_text[:100]}..."
                        )
                    else:
                        logger.warning(
                            f"[{task_name}] No bot response on turn {turn_num}"
                        )

                    # Record turn
                    turn = ConversationTurn(
                        turn_number=turn_num,
                        user_message=user_message,
                        bot_response=bot_text,
                        timestamp=time.time(),
                        success=turn_success,
                        error=None if turn_success else "No response from bot",
                    )
                    result.add_turn(turn)

                    # Update conversation history for next turn
                    conversation_history.append(
                        {"user": user_message, "bot": bot_text or "[no response]"}
                    )

                    # Check if agent indicates task completion
                    if self._is_task_complete(user_message, bot_text):
                        result.success = True
                        result.completion_reason = "goal_achieved"
                        logger.info(
                            f"[{task_name}] Task completed successfully after {turn_num} turns"
                        )
                        break

                except Exception as e:
                    logger.error(f"[{task_name}] Error on turn {turn_num}: {e}")
                    turn = ConversationTurn(
                        turn_number=turn_num,
                        user_message="",
                        bot_response=None,
                        timestamp=time.time(),
                        success=False,
                        error=str(e),
                    )
                    result.add_turn(turn)
                    result.completion_reason = "error"
                    result.error_message = str(e)
                    break

            # If loop completed without breaking
            if result.completion_reason == "":
                result.completion_reason = "max_turns"
                logger.info(f"[{task_name}] Reached max turns ({self.max_turns})")

        except Exception as e:
            logger.error(f"[{task_name}] Conversation error: {e}")
            result.completion_reason = "error"
            result.error_message = str(e)

        result.total_latency = time.time() - start_time
        return result

    def run_conversation_sync(
        self, task_name: str, task_description: str, session: Any
    ) -> ConversationResult:
        """Run a multi-turn conversation synchronously.

        This is a wrapper around run_conversation_async using asyncio.run().

        Args:
            task_name: Name of the task
            task_description: Description of what the user should accomplish
            session: TelegramSession or LocalSession for sending messages

        Returns:
            Conversation result
        """
        import asyncio

        # Run the async method synchronously using asyncio.run()
        return asyncio.run(
            self.run_conversation_async(task_name, task_description, session)
        )

    def _build_context(
        self, task_description: str, conversation_history: list[dict[str, str]]
    ) -> str:
        """Build context prompt for the agent based on conversation history.

        Args:
            task_description: Original task description
            conversation_history: List of previous turns

        Returns:
            Context prompt for the agent
        """
        context = f"Task: {task_description}\n\nConversation so far:\n"

        for i, turn in enumerate(conversation_history, 1):
            context += f"\nTurn {i}:\n"
            context += f"You: {turn['user']}\n"
            context += f"Bot: {turn['bot']}\n"

        context += (
            "\nBased on the conversation so far, what is your next message to the bot? "
            "If the task is complete, send a message acknowledging completion."
        )

        return context

    def _is_task_complete(
        self, user_message: str, bot_response: str | None
    ) -> bool:
        """Check if the task appears to be complete based on messages.

        Args:
            user_message: Latest user message
            bot_response: Latest bot response

        Returns:
            True if task seems complete
        """
        # Simple heuristic: look for completion indicators
        completion_phrases = [
            "thank you",
            "thanks",
            "done",
            "complete",
            "finished",
            "perfect",
            "great",
            "excellent",
        ]

        user_lower = user_message.lower()
        bot_lower = (bot_response or "").lower()

        # Check if user is expressing satisfaction/completion
        if any(phrase in user_lower for phrase in completion_phrases):
            return True

        # Check if bot indicates completion
        if bot_response and any(
            phrase in bot_lower
            for phrase in ["task complete", "all done", "successfully completed"]
        ):
            return True

        return False
