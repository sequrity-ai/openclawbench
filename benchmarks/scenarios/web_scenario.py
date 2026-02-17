"""Web Search benchmark scenario.

Architecture:
    This scenario tests the bot's ability to search the web for information
    using the Tavily search skill. Tasks progress from simple factual queries
    to complex comparative research.

    Task Flow:
       - Task 1 (Factual Search): Search for well-known facts and report them
       - Task 2 (Comparison): Compare two technologies/concepts with key differences
       - Task 3 (Current Events): Research current events or recent developments

    This design tests both search accuracy and information extraction capabilities.
"""

import logging
from datetime import datetime

from benchmarks.base import (
    BenchmarkTask,
    CheckStatus,
    HealthCheckResult,
    ScenarioBase,
    SetupResult,
)
from benchmarks.skill_checker import check_skills
from benchmarks.validators.web_validator import WebValidator

logger = logging.getLogger(__name__)


class WebScenario(ScenarioBase):
    """Benchmark scenario for web search capabilities."""

    def __init__(self, remote_manager=None):
        """Initialize Web Search scenario.

        Args:
            remote_manager: Optional RemoteWorkspaceManager (not used for web search)

        Note:
            - Requires the Tavily search skill to be installed
            - No API access verification (relies on bot's configuration)
        """
        super().__init__(
            name="Web Search",
            description="Tests agent's ability to search the web and extract information using Tavily",
            required_skills=["tavily-search"],
        )

        self.validator = WebValidator()
        self.remote_manager = remote_manager
        self.setup_data = {}

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 9 Web Search tasks with progressive complexity."""

        # Task 1: Factual Search - Simple fact-finding
        self.add_task(
            BenchmarkTask(
                name="Factual Web Search",
                prompt=(
                    "Search the web to find out when Python programming language was created "
                    "and who created it. Tell me the year and the creator's name."
                ),
                expected_output_description="Bot reports Python was created in 1991 by Guido van Rossum",
                validation_fn=self.validator.validate_factual_search,
                timeout=45.0,
                metadata={"difficulty": "easy", "category": "factual_search"},
            )
        )

        # Task 2: Comparison Research - Compare two technologies
        self.add_task(
            BenchmarkTask(
                name="Comparison Research",
                prompt=(
                    "Search the web and compare Python vs JavaScript programming languages. "
                    "Give me 3 key differences between them. Include information about their "
                    "typical use cases and typing systems."
                ),
                expected_output_description="Bot provides comparison with differences in use cases and typing",
                validation_fn=self.validator.validate_comparison_search,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "comparison"},
            )
        )

        # Task 3: Current Events - Research recent developments
        current_year = datetime.now().year
        self.add_task(
            BenchmarkTask(
                name="Current Events Research",
                prompt=(
                    f"Search the web for recent developments in artificial intelligence in {current_year}. "
                    "Tell me about one major breakthrough or trend. Include the name of the "
                    "technology or company involved."
                ),
                expected_output_description="Bot finds and reports recent AI developments with details",
                validation_fn=self.validator.validate_current_events,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "current_events"},
            )
        )

        # Task 4: Multi-Query Search - Search for multiple topics
        self.add_task(
            BenchmarkTask(
                name="Multi-Query Search",
                prompt=(
                    "Search for both 'Python async programming' and 'FastAPI tutorials'"
                ),
                expected_output_description="Bot searches for both topics and reports results mentioning Python, async, and FastAPI",
                validation_fn=self.validator.validate_multi_query_search,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "multi_query"},
            )
        )

        # Task 5: Domain-Specific Search - Search within a specific domain
        self.add_task(
            BenchmarkTask(
                name="Domain-Specific Search",
                prompt=(
                    "Find recent articles about AI on techcrunch.com"
                ),
                expected_output_description="Bot finds and reports AI articles from TechCrunch",
                validation_fn=self.validator.validate_domain_specific_search,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "domain_search"},
            )
        )

        # Task 6: News Search - Search for latest news
        self.add_task(
            BenchmarkTask(
                name="News Search",
                prompt=(
                    "What are the latest news about climate change?"
                ),
                expected_output_description="Bot retrieves and summarizes recent climate change news",
                validation_fn=self.validator.validate_news_search,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "news_search"},
            )
        )

        # Task 7: Time-Filtered Search - Search with recency constraint
        self.add_task(
            BenchmarkTask(
                name="Time-Filtered Search",
                prompt=(
                    "Find articles about OpenAI published in the last week"
                ),
                expected_output_description="Bot finds recent OpenAI articles and reports time-relevant results",
                validation_fn=self.validator.validate_time_filtered_search,
                timeout=75.0,
                metadata={"difficulty": "hard", "category": "time_filtered"},
            )
        )

        # Task 8: Search Comparison - Compare search result volumes
        self.add_task(
            BenchmarkTask(
                name="Search Comparison",
                prompt=(
                    "Search for 'React' vs 'Vue' and tell me which has more results"
                ),
                expected_output_description="Bot searches both frameworks, compares results, and declares one more prominent",
                validation_fn=self.validator.validate_search_comparison,
                timeout=75.0,
                metadata={"difficulty": "hard", "category": "search_comparison"},
            )
        )

        # Task 9: Topic Analysis - Summarize topics from search results
        self.add_task(
            BenchmarkTask(
                name="Topic Analysis",
                prompt=(
                    "Search for 'machine learning' and summarize the main topics from the top results"
                ),
                expected_output_description="Bot searches machine learning, analyzes top results, and provides topic summary",
                validation_fn=self.validator.validate_topic_analysis,
                timeout=75.0,
                metadata={"difficulty": "hard", "category": "topic_analysis"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        # Check for Tavily search skill
        local_mode = self.remote_manager is None
        checks = check_skills(self.required_skills, local_mode=local_mode, remote_manager=self.remote_manager)

        # Note: We don't verify Tavily API access directly since it's configured
        # in the bot, not in the benchmark client
        checks.append(
            HealthCheckResult(
                check_name="Tavily API Note",
                status=CheckStatus.PASS,
                message="Ensure bot has Tavily API key configured (TAVILY_API_KEY in bot's .env)",
                details={"required_skill": "tavily-search"},
            )
        )

        return checks

    def setup(self) -> SetupResult:
        """Set up the Web Search scenario.

        Returns:
            Setup result with expected validation data
        """
        try:
            logger.info("Setting up Web Search benchmark...")

            current_year = datetime.now().year

            # Store expected data for validation
            self.setup_data = {
                # Task 1: Factual Search
                "expected_facts": {
                    "year": "1991",
                    "creator": "Guido van Rossum",
                },
                # Task 2: Comparison Research
                "required_keywords": [
                    "use case",
                    "typing",
                ],
                "comparison_topics": [
                    "Python",
                    "JavaScript",
                ],
                # Task 3: Current Events
                "topic": "artificial intelligence",
                "required_elements": [
                    str(current_year),  # Must mention current year
                ],
            }

            logger.info("Setup complete - validation criteria configured")

            return SetupResult(
                status=CheckStatus.PASS,
                message="Web Search scenario configured successfully",
                setup_data=self.setup_data,
            )

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return SetupResult(
                status=CheckStatus.FAIL,
                message=f"Failed to set up Web Search scenario: {str(e)}",
                error=str(e),
            )

    def cleanup(self) -> bool:
        """Clean up the Web Search scenario.

        Returns:
            True (no cleanup needed for web searches)
        """
        logger.info("Web Search scenario cleanup (no action needed)")
        return True
