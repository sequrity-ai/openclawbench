"""Compound benchmark scenario — tests multiple skills combined in single tasks.

Architecture:
    Each task requires the agent to use 2 or 3 different skills sequentially.
    Results from one skill feed into the next (e.g. get weather → file GitHub issue
    reporting the conditions). Validates both skills were exercised and outputs combined.

Tasks (9) — pinned validation facts:
    Easy:
       - Task 1 (Weather + Web Research): Check weather in Tokyo, search for travel tips
         → must mention "tokyo" + temperature + packing/travel word
       - Task 2 (Web Search + Summarize): Search for a Python async article and summarize it
         → must mention "python" + "async" + summary language
       - Task 3 (GitHub + Summarize): Read src/utils.js from the test repo, summarize its purpose
         → must mention "fetchdata" + "processitems" (seeded file functions)

    Medium:
       - Task 4 (Weather + GitHub Issue): Check weather in London, file issue '[BENCHMARK TEST] Weather Report'
         → must mention "london" + "weather report" + "#" (issue number)
       - Task 5 (Web Research + GitHub Issue): Research async best practices, file '[BENCHMARK TEST] Async Research'
         → must mention "async" + "async research" + "#" (issue number)
       - Task 6 (Multi-City Weather + Context): Compare weather in London, Tokyo, Paris
         → must mention all three cities + comparison word

    Hard:
       - Task 7 (GitHub Repo + Web Research): Get repo info then research JavaScript async online
         → must mention "benchmark test repository" + "openclaw-sandbox" (seeded README) + web word
       - Task 8 (Web + Weather + GitHub Chain): Search AI news, check SF weather, file '[BENCHMARK TEST] Daily Briefing'
         → must mention "san francisco" + "daily briefing" + "#" (issue number)
       - Task 9 (Research + Summarize + GitHub): Research ML healthcare, file '[BENCHMARK TEST] ML Healthcare Research'
         → must mention "healthcare" + "ml healthcare research" + "#" (issue number)

Setup:
    Uses the same GitHub test repository as the GitHub scenario (seeded with data).
    src/utils.js in the seeded repo defines fetchData() and processItems() — pinned in T3.
    README.md in the seeded repo contains "Benchmark Test Repository" / "openclaw-sandbox" — pinned in T7.

Required Skills:
    steipete/weather, tavily-search, steipete/github, steipete/summarize

Config:
    GITHUB_TOKEN — personal access token with repo scope
    GITHUB_TEST_REPO_OWNER — owner of the test repository
    GITHUB_TEST_REPO_NAME — name of the test repository
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
from benchmarks.validators.compound_validator import CompoundValidator

logger = logging.getLogger(__name__)


class CompoundScenario(ScenarioBase):
    """Benchmark scenario combining multiple skills in single tasks."""

    def __init__(self, github_token: str, test_repo_owner: str, test_repo_name: str, remote_manager=None):
        """Initialize Compound scenario.

        Args:
            github_token: Personal access token for benchmark GitHub account
            test_repo_owner: Owner of test repository (for Tasks 3–5, 7–9)
            test_repo_name: Name of test repository
            remote_manager: Optional RemoteWorkspaceManager (not used for compound)

        Note:
            - Requires steipete/weather, tavily-search, steipete/github, steipete/summarize
            - GitHub tasks create issues in the test repo; they are cleaned up afterward
        """
        super().__init__(
            name="Compound",
            description="Tests agent's ability to chain multiple skills (weather, web, GitHub, summarize) in single tasks",
            required_skills=["weather", "tavily-search", "github", "summarize"],
        )

        self.validator = CompoundValidator()
        self.test_repo_owner = test_repo_owner
        self.test_repo_name = test_repo_name
        self.remote_manager = remote_manager
        self.setup_data = {}

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 9 compound tasks."""

        # Task 1 (Easy): Weather + Web Research
        self.add_task(
            BenchmarkTask(
                name="Weather + Web Research",
                prompt=(
                    "Check the current weather in Tokyo, Japan. "
                    "Then search the web for travel tips and packing recommendations for that weather. "
                    "Combine both: tell me the weather conditions and what I should pack or bring."
                ),
                expected_output_description="Bot reports Tokyo weather and provides relevant travel/packing tips",
                validation_fn=self.validator.validate_weather_then_web,
                timeout=90.0,
                metadata={"difficulty": "easy", "category": "weather_web"},
            )
        )

        # Task 2 (Easy): Web Search + Summarize
        self.add_task(
            BenchmarkTask(
                name="Web Search + Summarize",
                prompt=(
                    "Search the web for an article about Python async programming. "
                    "Then summarize the article you found. "
                    "Tell me the key points and main takeaways."
                ),
                expected_output_description="Bot finds a Python async article and provides a summary of its key points",
                validation_fn=self.validator.validate_web_then_summarize,
                timeout=90.0,
                metadata={"difficulty": "easy", "category": "web_summarize"},
            )
        )

        # Task 3 (Easy): GitHub + Summarize
        self.add_task(
            BenchmarkTask(
                name="GitHub + Summarize",
                prompt=(
                    f"Read the file `src/utils.js` from the GitHub repository "
                    f"{self.test_repo_owner}/{self.test_repo_name}. "
                    f"Then summarize its purpose: what does the file do, what functions does it define, "
                    f"and what problem does it solve?"
                ),
                expected_output_description="Bot reads the repo file and provides a meaningful summary of its purpose",
                validation_fn=self.validator.validate_github_then_summarize,
                timeout=90.0,
                metadata={"difficulty": "easy", "category": "github_summarize"},
            )
        )

        # Task 4 (Medium): Weather + GitHub Issue
        self.add_task(
            BenchmarkTask(
                name="Weather + GitHub Issue",
                prompt=(
                    "Check the current weather in London, UK. "
                    f"Then create a GitHub issue in {self.test_repo_owner}/{self.test_repo_name} "
                    "titled '[BENCHMARK TEST] Weather Report' that includes the current weather conditions "
                    "you just retrieved. The issue body should mention the temperature, conditions, and location."
                ),
                expected_output_description="Bot checks London weather and creates a GitHub issue containing that weather data",
                validation_fn=self.validator.validate_weather_then_github,
                timeout=120.0,
                metadata={"difficulty": "medium", "category": "weather_github"},
            )
        )

        # Task 5 (Medium): Web Research + GitHub Issue
        self.add_task(
            BenchmarkTask(
                name="Web Research + GitHub Issue",
                prompt=(
                    "Search the web for information about 'Python async programming best practices'. "
                    f"Then create a GitHub issue in {self.test_repo_owner}/{self.test_repo_name} "
                    "titled '[BENCHMARK TEST] Async Research' summarizing the key findings from your search. "
                    "Include the main best practices you discovered in the issue body."
                ),
                expected_output_description="Bot researches async best practices and files a GitHub issue summarizing findings",
                validation_fn=self.validator.validate_web_then_github,
                timeout=120.0,
                metadata={"difficulty": "medium", "category": "web_github"},
            )
        )

        # Task 6 (Medium): Multi-City Weather + Web Context
        self.add_task(
            BenchmarkTask(
                name="Multi-City Weather + Context",
                prompt=(
                    "Check the current weather in London, Tokyo, and Paris. "
                    "Then compare the three cities: which is warmest, which is coolest, "
                    "and how do their conditions differ? "
                    "Also search the web for any relevant context about weather patterns in these cities."
                ),
                expected_output_description="Bot retrieves weather for all three cities and provides a comparison with context",
                validation_fn=self.validator.validate_weather_web_compare,
                timeout=120.0,
                metadata={"difficulty": "medium", "category": "multi_weather_web"},
            )
        )

        # Task 7 (Hard): GitHub Repo + Web Research
        self.add_task(
            BenchmarkTask(
                name="GitHub Repo + Web Research",
                prompt=(
                    f"Get information about the repository {self.test_repo_owner}/{self.test_repo_name}: "
                    "its description, stars, forks, and main language. "
                    "Then search the web to learn more about the technology stack used in that repo. "
                    "Combine both: give me the repo summary and what you learned about the technologies online."
                ),
                expected_output_description="Bot retrieves repo metadata and supplements with web research about the tech stack",
                validation_fn=self.validator.validate_github_web_research,
                timeout=120.0,
                metadata={"difficulty": "hard", "category": "github_web"},
            )
        )

        # Task 8 (Hard): Web + Weather + GitHub Chain (3-skill)
        self.add_task(
            BenchmarkTask(
                name="Web + Weather + GitHub Chain",
                prompt=(
                    "Do the following three things in order: "
                    "1) Search the web for the latest news about artificial intelligence. "
                    "2) Check the current weather in San Francisco, CA. "
                    f"3) Create a GitHub issue in {self.test_repo_owner}/{self.test_repo_name} "
                    "titled '[BENCHMARK TEST] Daily Briefing' that includes a brief summary of the AI news "
                    "you found AND the current weather in San Francisco."
                ),
                expected_output_description="Bot performs all three steps and creates a GitHub issue combining AI news and weather",
                validation_fn=self.validator.validate_three_skill_chain,
                timeout=150.0,
                metadata={"difficulty": "hard", "category": "three_skill_chain"},
            )
        )

        # Task 9 (Hard): Research + Summarize + GitHub (3-skill)
        self.add_task(
            BenchmarkTask(
                name="Research + Summarize + GitHub",
                prompt=(
                    "Do the following: "
                    "1) Search the web for articles about 'machine learning in healthcare'. "
                    "2) Summarize the key findings from the articles you found — focus on the main "
                    "applications, benefits, and challenges discussed. "
                    f"3) Create a GitHub issue in {self.test_repo_owner}/{self.test_repo_name} "
                    "titled '[BENCHMARK TEST] ML Healthcare Research' and paste your summary as the issue body."
                ),
                expected_output_description="Bot researches the topic, summarizes findings, and files a GitHub issue with the summary",
                validation_fn=self.validator.validate_summarize_then_github,
                timeout=150.0,
                metadata={"difficulty": "hard", "category": "research_summarize_github"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        local_mode = self.remote_manager is None
        checks = check_skills(self.required_skills, local_mode=local_mode, remote_manager=self.remote_manager)

        # CRITICAL: Check OpenAI API key (required for AI agent)
        checks.append(self._check_openai_api_key())

        # CRITICAL: Check Tavily API key (required for web search validation)
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
                    check_name="Tavily API Key (Compound)",
                    status=CheckStatus.FAIL,
                    message="TAVILY_API_KEY not configured - required for web search tasks in compound scenario",
                    details={
                        "error": "Compound scenario includes web search tasks requiring Tavily API",
                        "fix": "Get API key from https://tavily.com and set TAVILY_API_KEY in .env",
                    },
                )
            )
        else:
            checks.append(
                HealthCheckResult(
                    check_name="Tavily API Key (Compound)",
                    status=CheckStatus.PASS,
                    message=f"Tavily API key configured ({tavily_api_key[:10]}...)",
                    details={"validation_method": "tavily_api"},
                )
            )

        checks.append(
            HealthCheckResult(
                check_name="Compound Scenario Note",
                status=CheckStatus.PASS,
                message=(
                    f"Compound tasks will interact with repo {self.test_repo_owner}/{self.test_repo_name}. "
                    "GitHub issues created during tasks will be left open for inspection."
                ),
                details={
                    "test_repo": f"{self.test_repo_owner}/{self.test_repo_name}",
                    "required_skills": self.required_skills,
                },
            )
        )

        return checks

    def setup(self) -> SetupResult:
        """Set up the Compound scenario.

        Returns:
            Setup result with test repository information
        """
        try:
            logger.info("Setting up Compound benchmark...")

            self.setup_data = {
                "repo_owner": self.test_repo_owner,
                "repo_name": self.test_repo_name,
            }

            logger.info(f"Setup complete for compound scenario using {self.test_repo_owner}/{self.test_repo_name}")

            return SetupResult(
                status=CheckStatus.PASS,
                message="Compound scenario configured successfully",
                setup_data=self.setup_data,
            )

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return SetupResult(
                status=CheckStatus.FAIL,
                message=f"Failed to set up Compound scenario: {str(e)}",
                error=str(e),
            )

    def cleanup(self) -> bool:
        """Clean up the Compound scenario.

        Returns:
            True (GitHub issues created by tasks are left for inspection)
        """
        logger.info("Compound scenario cleanup complete (GitHub issues left open for inspection)")
        return True
