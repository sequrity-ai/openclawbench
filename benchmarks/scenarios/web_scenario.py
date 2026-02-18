"""Web Search benchmark scenario.

Tasks (9):
    Easy:
       - Task 1 (Factual Web Search): When was Python created and who created it? (1991, Guido van Rossum)
       - Task 2 (Comparison Research): Which had higher closing price on Feb 17, 2026 — AAPL or MSFT? (MSFT at $396.86)
       - Task 3 (Current Events Research): BBC article on DeepSeek cost vs GPT-4 cost (~$6M vs $100M+)

    Medium:
       - Task 4 (Multi-Query Search): arXiv paper 2505.15917 author (Gidney) + BBC top story Jan 2, 2025 city (New Orleans)
       - Task 5 (Domain-Specific Search): TechCrunch article — ElevenLabs Series C amount ($180M, Jan 2025)
       - Task 6 (News Search): COP29 November 2024 — city held (Baku) + annual pledge ($300B)

    Hard:
       - Task 7 (Chained Lookup, 3-hop, Science): 2024 Nobel Physics winner (Hinton) → 2024 Nobel Chemistry winner (Baker) → Baker's university (University of Washington)
       - Task 8 (Chained Lookup, 3-hop, Sports+Politics): Men's 100m WR holder (Bolt, 2009) → PM of Jamaica in 2009 (Golding)
       - Task 9 (Chained Lookup, 4-hop, Film+Geography): Best Picture 2024 director (Nolan/Oppenheimer) → university (Christ's College Cambridge) → city (Cambridge) → founding year (1209)

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

        # Task 2: Stock Price Comparison - Verify ground-truth fact via web search
        self.add_task(
            BenchmarkTask(
                name="Comparison Research",
                prompt=(
                    "Search the web for the closing stock prices of Apple (AAPL) and Microsoft (MSFT) "
                    "on February 17, 2026. Which company had the higher closing price? "
                    "Reply with just the company name."
                ),
                expected_output_description="Bot names Microsoft as the company with the higher closing price on Feb 17, 2026",
                validation_fn=self.validator.validate_comparison_search,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "comparison"},
            )
        )

        # Task 3: Current Events - Ground-truth BBC/DeepSeek article facts
        self.add_task(
            BenchmarkTask(
                name="Current Events Research",
                prompt=(
                    "Search for the BBC news article about DeepSeek from January 2025. "
                    "According to BBC, how much did it cost to train DeepSeek, and how does "
                    "that compare to what OpenAI spent on GPT-4?"
                ),
                expected_output_description="Bot finds BBC article and reports DeepSeek cost ~$6 million vs GPT-4 cost over $100 million",
                validation_fn=self.validator.validate_current_events,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "current_events"},
            )
        )

        # Task 4: Multi-Query Search - Two unrelated ground-truth searches
        self.add_task(
            BenchmarkTask(
                name="Multi-Query Search",
                prompt=(
                    "Do two separate web searches and answer both questions: "
                    "(1) Search arXiv for the paper with ID '2505.15917' — what is the author's last name? "
                    "(2) Search BBC News for the top story on January 2, 2025 — what city was it about? "
                    "Give me both answers."
                ),
                expected_output_description="Bot searches arXiv (finds 'Gidney') and BBC (finds 'New Orleans'), reports both answers",
                validation_fn=self.validator.validate_multi_query_search,
                timeout=75.0,
                metadata={"difficulty": "medium", "category": "multi_query"},
            )
        )

        # Task 5: Domain-Specific Search - Search TechCrunch for ElevenLabs funding article
        self.add_task(
            BenchmarkTask(
                name="Domain-Specific Search",
                prompt=(
                    "Search techcrunch.com for the article about ElevenLabs raising a Series C "
                    "funding round in January 2025. How much did they raise? Give me just the dollar amount."
                ),
                expected_output_description="Bot finds TechCrunch article reporting ElevenLabs raised $180 million in Series C",
                validation_fn=self.validator.validate_domain_specific_search,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "domain_search"},
            )
        )

        # Task 6: News Search - COP29 ground-truth (city + annual pledge amount)
        self.add_task(
            BenchmarkTask(
                name="News Search",
                prompt=(
                    "Search the web for COP29, the UN climate conference held in November 2024. "
                    "What city was it held in, and what annual climate finance amount did rich nations pledge? "
                    "Give me the city and the dollar amount."
                ),
                expected_output_description="Bot finds COP29 was held in Baku and rich nations pledged $300 billion per year",
                validation_fn=self.validator.validate_news_search,
                timeout=60.0,
                metadata={"difficulty": "medium", "category": "news_search"},
            )
        )

        # Task 7: Chained Lookup (3-hop, Science) - Nobel Physics winner → Nobel Chemistry winner → Chemistry winner's university
        self.add_task(
            BenchmarkTask(
                name="Time-Filtered Search",
                prompt=(
                    "Search for who won the 2024 Nobel Prize in Physics. "
                    "Then search for who won the 2024 Nobel Prize in Chemistry. "
                    "Finally, find what university the Chemistry winner is affiliated with. "
                    "Give me both winners' last names and the university."
                ),
                expected_output_description="Bot finds Hinton (Physics) and Baker (Chemistry), then finds Baker is at University of Washington",
                validation_fn=self.validator.validate_time_filtered_search,
                timeout=90.0,
                metadata={"difficulty": "hard", "category": "chained_lookup"},
            )
        )

        # Task 8: Chained Lookup (3-hop, Sports+Politics) - 100m WR holder → year set → PM of their country that year
        self.add_task(
            BenchmarkTask(
                name="Search Comparison",
                prompt=(
                    "Search for who holds the men's 100m sprint world record and what year they set it. "
                    "Then search for who was the Prime Minister of that athlete's country in the year the record was set. "
                    "Give me the record holder's last name, the year, and the Prime Minister's last name."
                ),
                expected_output_description="Bot finds Usain Bolt set the record in 2009, then finds Bruce Golding was PM of Jamaica in 2009",
                validation_fn=self.validator.validate_search_comparison,
                timeout=90.0,
                metadata={"difficulty": "hard", "category": "chained_lookup"},
            )
        )

        # Task 9: Chained Lookup (4-hop, Film+Geography) - Best Picture 2024 → director → university → founding year
        self.add_task(
            BenchmarkTask(
                name="Topic Analysis",
                prompt=(
                    "Search for which film won Best Picture at the 2024 Academy Awards and who directed it. "
                    "Then search for what university that director attended. "
                    "Then find what city that university is in. "
                    "Finally, search for what year that university was founded. "
                    "Give me the director's last name, the university, the city, and the founding year."
                ),
                expected_output_description="Bot finds Nolan (Oppenheimer) → Christ's College Cambridge → Cambridge UK → founded 1209",
                validation_fn=self.validator.validate_topic_analysis,
                timeout=90.0,
                metadata={"difficulty": "hard", "category": "chained_lookup"},
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

            # Store expected data for validation
            self.setup_data = {
                # Task 1: Factual Search
                "expected_facts": {
                    "year": "1991",
                    "creator": "Guido van Rossum",
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
