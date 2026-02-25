"""Web Search benchmark scenario.

ALL TASKS are time-relative to prevent breakage when dates pass.
Models MUST use web search - cannot rely on parametric knowledge.

Tasks (9):
    Easy:
       - Task 1: Most recent major product launch in past 60 days
       - Task 2: Yesterday's AAPL vs MSFT closing stock prices
       - Task 3: Biggest tech news story from past 7 days

    Medium:
       - Task 4: Most recent major AI model/LLM release in past 90 days
       - Task 5: Largest tech funding round in past 60 days
       - Task 6: Most recent major tech conference in past 6 months

    Hard:
       - Task 7: Top 3 trending financial news headlines TODAY
       - Task 8: Most recent IPO in last 30 days
       - Task 9: Most viral tech news story in past 7 days

Setup:
    No special setup required. Tasks use live web search.

Required Skills:
    tavily-search
"""

import logging

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

        # Task 1: Latest Major Product Launch - Time-relative
        self.add_task(
            BenchmarkTask(
                name="Latest Product Launch",
                prompt=(
                    "Search the web for the most recent major smartphone or tech product launch "
                    "in the past 60 days. What product was launched and when?"
                ),
                expected_output_description="Bot searches for recent product launches and identifies the most recent one",
                validation_fn=self.validator.validate_recent_product_release,
                timeout=45.0,
                metadata={"difficulty": "easy", "category": "recent_release"},
            )
        )

        # Task 2: Stock Price Yesterday - Time-relative
        self.add_task(
            BenchmarkTask(
                name="Stock Price Comparison",
                prompt=(
                    "Search the web for yesterday's closing stock prices of Apple (AAPL) and Microsoft (MSFT). "
                    "Which company had the higher closing price? Give me the company name and both prices."
                ),
                expected_output_description="Bot searches for yesterday's closing prices and compares AAPL vs MSFT",
                validation_fn=self.validator.validate_comparison_search,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "comparison"},
            )
        )

        # Task 3: Top Tech News Past Week - Time-relative
        self.add_task(
            BenchmarkTask(
                name="Top Tech News",
                prompt=(
                    "Search for the biggest tech news story from the past 7 days. "
                    "What is the story about? Give me a brief summary."
                ),
                expected_output_description="Bot searches for recent top tech news and provides summary",
                validation_fn=self.validator.validate_current_events,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "current_events"},
            )
        )

        # Task 4: Recent AI Model Release - Time-relative
        self.add_task(
            BenchmarkTask(
                name="Recent AI Model Release",
                prompt=(
                    "Search for the most recent major AI model or LLM release in the past 90 days. "
                    "What model was released, by which company, and when?"
                ),
                expected_output_description="Bot searches for recent AI model releases and identifies the most recent one",
                validation_fn=self.validator.validate_multi_query_search,
                timeout=75.0,
                metadata={"difficulty": "medium", "category": "ai_news"},
            )
        )

        # Task 5: Recent Tech Funding Round - Time-relative
        self.add_task(
            BenchmarkTask(
                name="Recent Tech Funding",
                prompt=(
                    "Search for the largest tech company funding round announced in the past 60 days. "
                    "What company raised funding, how much did they raise, and when was it announced?"
                ),
                expected_output_description="Bot searches for recent tech funding rounds and identifies the largest one",
                validation_fn=self.validator.validate_domain_specific_search,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "funding_news"},
            )
        )

        # Task 6: Recent Major Conference - Time-relative
        self.add_task(
            BenchmarkTask(
                name="Recent Major Conference",
                prompt=(
                    "Search for the most recent major tech or industry conference held in the past 6 months. "
                    "What was the conference name, where was it held, and what was a key announcement or outcome?"
                ),
                expected_output_description="Bot searches for recent major conferences and provides details",
                validation_fn=self.validator.validate_news_search,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "conference_news"},
            )
        )

        # Task 7: Top Trending Financial News (requires current search)
        self.add_task(
            BenchmarkTask(
                name="Top Trending Financial News",
                prompt=(
                    "Search for the top 3 trending financial news headlines today. "
                    "List all 3 headlines."
                ),
                expected_output_description="Bot searches for current trending financial news and lists 3 headlines",
                validation_fn=self.validator.validate_time_filtered_search,
                timeout=90.0,
                metadata={"difficulty": "hard", "category": "trending_news"},
            )
        )

        # Task 8: Recent IPO (requires current search)
        self.add_task(
            BenchmarkTask(
                name="Recent IPO Search",
                prompt=(
                    "Search for what company had an IPO or went public most recently in the last 30 days. "
                    "When did it happen? Give me the company name and date."
                ),
                expected_output_description="Bot searches for recent IPOs and identifies the most recent one with date",
                validation_fn=self.validator.validate_search_comparison,
                timeout=90.0,
                metadata={"difficulty": "hard", "category": "recent_events"},
            )
        )

        # Task 9: Viral Tech News (requires current search)
        self.add_task(
            BenchmarkTask(
                name="Viral Tech News",
                prompt=(
                    "Search for the most viral tech news story in the past 7 days. "
                    "What is the story about? Summarize it briefly."
                ),
                expected_output_description="Bot searches for recent viral tech news and provides summary",
                validation_fn=self.validator.validate_topic_analysis,
                timeout=90.0,
                metadata={"difficulty": "hard", "category": "trending_news"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        # Check for Tavily search skill
        local_mode = self.remote_manager is None
        checks = check_skills(self.required_skills, local_mode=local_mode, remote_manager=self.remote_manager)

        # CRITICAL: Check OpenAI API key (required for AI agent)
        checks.append(self._check_openai_api_key())

        # CRITICAL: Check Tavily API key is configured for validation
        # Validators require Tavily API to fetch ground truth
        import os
        from config import Config

        tavily_api_key = ""
        try:
            config = Config()
            tavily_api_key = config.tavily_api_key
        except Exception:
            tavily_api_key = os.getenv("TAVILY_API_KEY", "")

        if not tavily_api_key or tavily_api_key == "your_tavily_api_key_here":
            checks.append(
                HealthCheckResult(
                    check_name="Tavily API Key (Benchmark)",
                    status=CheckStatus.FAIL,
                    message="TAVILY_API_KEY not configured in benchmark .env file",
                    details={
                        "error": "Web Search validators require Tavily API to fetch ground truth",
                        "fix": "Get API key from https://tavily.com and set TAVILY_API_KEY in .env",
                    },
                )
            )
        else:
            checks.append(
                HealthCheckResult(
                    check_name="Tavily API Key (Benchmark)",
                    status=CheckStatus.PASS,
                    message=f"Tavily API key configured ({tavily_api_key[:10]}...)",
                    details={"validation_method": "tavily_api"},
                )
            )

        # Note for bot configuration
        checks.append(
            HealthCheckResult(
                check_name="Tavily API Note (Bot)",
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

            # Store expected data for validation
            self.setup_data = {
                # Task 1: Recent Product Release — Google Pixel 10 announced Oct 2025
                "pixel10_release": {
                    "product": "Google Pixel 10",
                    "month": "October",
                    "year": "2025",
                },
                # Task 2: Stock Price Comparison (Feb 17, 2026 closing prices)
                "stock_comparison": {
                    "date": "February 17, 2026",
                    "winner": "Microsoft",
                    "ticker_winner": "MSFT",
                    "apple_close": 263.88,
                    "msft_close": 396.86,
                },
                # Task 3: DeepSeek BBC article ground truth
                "deepseek_facts": {
                    "source": "BBC",
                    "url": "https://www.bbc.co.uk/news/articles/c5yv5976z9po",
                    "deepseek_cost_million": "6",
                    "gpt4_cost_million": "100",
                },
                # Task 4: Multi-query ground truth (two unrelated sources)
                "multi_query_facts": {
                    "arxiv_id": "2505.15917",
                    "arxiv_author_lastname": "Gidney",
                    "bbc_date": "January 2, 2025",
                    "bbc_city": "New Orleans",
                },
                # Task 6: News Search — COP29 ground truth
                "cop29_facts": {
                    "city": "Baku",
                    "country": "Azerbaijan",
                    "year": "2024",
                    "annual_pledge_billion": "300",
                    "url": "https://news.un.org/en/story/2024/11/1157416",
                },
                # Task 5: Domain-specific search — TechCrunch ElevenLabs Series C article
                "elevenlabs_facts": {
                    "source": "TechCrunch",
                    "url": "https://techcrunch.com/2025/01/30/elevenlabs-raises-180-million-in-series-c-funding-at-3-3-billion-valuation/",
                    "amount_million": "180",
                    "round": "Series C",
                    "valuation_billion": "3.3",
                    "date": "January 30, 2025",
                },
                # Task 7: Chained lookup — Nobel Physics + Chemistry 2024 → Chemistry winner's university
                "nobel_science_chain": {
                    "physics_winner_lastname": "Hinton",
                    "physics_winner_fullname": "Geoffrey Hinton",
                    "chemistry_winner_lastname": "Baker",
                    "chemistry_winner_fullname": "David Baker",
                    "chemistry_university": "University of Washington",
                    "year": "2024",
                },
                # Task 8: Chained lookup — 100m WR holder → year → PM of their country that year
                "sprint_politics_chain": {
                    "record_holder_lastname": "Bolt",
                    "record_holder_fullname": "Usain Bolt",
                    "record_year": "2009",
                    "country": "Jamaica",
                    "prime_minister_lastname": "Golding",
                    "prime_minister_fullname": "Bruce Golding",
                },
                # Task 9: Chained lookup — Best Picture 2024 → director → university → founding year
                "film_geography_chain": {
                    "film": "Oppenheimer",
                    "director_lastname": "Nolan",
                    "director_fullname": "Christopher Nolan",
                    "university": "Christ's College Cambridge",
                    "city": "Cambridge",
                    "university_founding_year": "1209",
                },
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
