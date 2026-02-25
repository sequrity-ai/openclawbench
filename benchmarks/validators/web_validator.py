"""Validation utilities for Web Search benchmark tasks.

Validators use Tavily API (same as bot) to fetch ground truth from web search.
Uses LLM to judge if bot's answer matches any of top 3 Tavily results.
REQUIRES Tavily API key to be configured - validators will fail without it.
"""

import logging
import os
from typing import Any

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)

# Try to import Tavily client
try:
    from tavily import TavilyClient

    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    logger.warning("Tavily not installed. Web validators will use hardcoded validation.")


class WebValidator:
    """Validates Web Search task results using Tavily API + LLM judge."""

    @staticmethod
    def _search_tavily(query: str, max_results: int = 3) -> list[dict]:
        """Search using Tavily API (same as bot uses).

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with 'title' and 'content'

        Raises:
            Exception: If Tavily is not available or API key not configured
        """
        if not TAVILY_AVAILABLE:
            raise Exception("Tavily not installed. Run: uv add tavily-python")

        # Get Tavily API key from environment
        from config import Config

        try:
            config = Config()
            api_key = config.tavily_api_key
        except Exception:
            api_key = os.getenv("TAVILY_API_KEY", "")

        if not api_key or api_key == "your_tavily_api_key_here":
            raise Exception("TAVILY_API_KEY not configured in .env file. Get API key from https://tavily.com")

        try:
            client = TavilyClient(api_key=api_key)
            result = client.search(query, max_results=max_results)
            return result.get("results", [])
        except Exception as e:
            raise Exception(f"Tavily search failed: {e}")

    @staticmethod
    def _llm_judge(bot_response: str, tavily_results: list[dict], question: str) -> tuple[bool, str]:
        """Use LLM to judge if bot's answer matches any of the Tavily results.

        Args:
            bot_response: Bot's answer to the question
            tavily_results: Top 3 Tavily search results (ground truth)
            question: Original question asked

        Returns:
            Tuple of (success: bool, explanation: str)
        """
        from pydantic_ai import Agent

        # Format Tavily results for LLM
        tavily_summary = "\n\n".join([
            f"Result {i+1}:\nTitle: {r.get('title', 'N/A')}\nContent: {r.get('content', 'N/A')}"
            for i, r in enumerate(tavily_results[:3])
        ])

        judge_prompt = f"""You are a factual accuracy judge. Your task is to determine if the bot's answer is factually correct based on web search results.

Question asked to bot: {question}

Bot's answer:
{bot_response}

Ground truth (Top 3 Tavily search results):
{tavily_summary}

Instructions:
1. Check if the bot's answer is factually consistent with ANY of the top 3 search results
2. The bot doesn't need to match all results - just needs to be correct based on at least one
3. Minor wording differences are OK - focus on factual accuracy
4. Respond with EXACTLY "PASS" or "FAIL" on the first line, then explanation

Your judgment:"""

        try:
            # Use gpt-5-mini for judging (same as benchmark agent)
            from config import Config
            config = Config()

            agent = Agent(model=f"openai:{config.ai_agent_model}")
            result = agent.run_sync(judge_prompt)

            judgment_text = result.data.strip()
            first_line = judgment_text.split("\n")[0].strip().upper()

            success = first_line == "PASS"
            explanation = "\n".join(judgment_text.split("\n")[1:]).strip()

            return success, explanation
        except Exception as e:
            logger.error(f"LLM judge failed: {e}")
            return False, f"LLM judge error: {str(e)}"

    @staticmethod
    def validate_recent_product_release(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Recent product release search.

        Strategy:
          1. Search Tavily for "Google Pixel 10 announcement date"
          2. Extract month/year from Tavily results (ground truth)
          3. Check bot's response mentions same month/year
          4. REQUIRES Tavily API - fails if not configured

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data (not used, Tavily provides ground truth)
        """
        success = False
        accuracy_score = 0.0
        validation_details = {"validation_method": "tavily"}
        error_message = None

        try:
            response_lower = response.lower()

            # Fetch ground truth from Tavily
            search_results = WebValidator._search_tavily("Google Pixel 10 announcement date", max_results=5)
            validation_details["tavily_results_count"] = len(search_results)

            # Combine all search result content
            search_content = " ".join(
                r.get("content", "") + " " + r.get("title", "") for r in search_results
            ).lower()
            validation_details["search_content_sample"] = search_content[:300]

            # Extract month and year from Tavily search results (ground truth)
            month_in_search = "october" in search_content or "oct" in search_content
            year_in_search = "2025" in search_content

            # Check if bot's response matches Tavily findings
            month_in_response = "october" in response_lower or "oct" in response_lower
            year_in_response = "2025" in response_lower

            validation_details["tavily_found_month"] = month_in_search
            validation_details["tavily_found_year"] = year_in_search
            validation_details["bot_mentioned_month"] = month_in_response
            validation_details["bot_mentioned_year"] = year_in_response

            # Success if both month and year match Tavily results
            if month_in_search and year_in_search:
                if month_in_response and year_in_response:
                    success = True
                    accuracy_score = 100.0
                else:
                    missing = []
                    if not month_in_response:
                        missing.append("October")
                    if not year_in_response:
                        missing.append("2025")
                    error_message = f"Bot didn't mention: {', '.join(missing)} (Tavily found both)"
            else:
                error_message = f"Tavily search couldn't find announcement date (month={month_in_search}, year={year_in_search})"

        except Exception as e:
            error_message = f"Tavily validation error: {str(e)}"

        return TaskResult(
            task_name="Recent Product Release",
            prompt="Search for when Google Pixel 10 smartphone was announced",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_comparison_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: Stock price comparison (ground-truth).

        Expected: Bot named Microsoft as the company with the higher closing price on Feb 17, 2026.
        Validator only checks that Microsoft (or MSFT) is identified as the winner — not exact prices.

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including stock_comparison ground truth
        """
        stock_comparison = setup_data.get("stock_comparison", {})

        success = False
        accuracy_score = 0.0
        validation_details = {
            "stock_comparison": stock_comparison,
            "expected_winner": stock_comparison.get("winner", "Microsoft"),
        }
        error_message = None

        try:
            response_lower = response.lower()

            # Check that the winning company (Microsoft / MSFT) is named in the response
            winner_found = "microsoft" in response_lower or "msft" in response_lower
            validation_details["winner_found"] = winner_found

            if winner_found:
                success = True
                accuracy_score = 100.0
            else:
                error_message = "Response did not name Microsoft (or MSFT) as the company with the higher stock price"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Comparison Research",
            prompt="Which company had the higher closing stock price on Feb 17, 2026: Apple or Microsoft?",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_current_events(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: DeepSeek BBC article ground-truth facts.

        Expected: Bot found the BBC article and reported DeepSeek cost ~$6 million vs GPT-4 ~$100 million.
        Four conditions must all pass:
          1. "deepseek" mentioned
          2. "6" + ("million" or "m") OR "$6" mentioned (DeepSeek cost)
          3. "100" + ("million" or "m") OR "$100" mentioned (GPT-4 cost)
          4. At least one of: "bbc", "openai", "gpt-4", "gpt4"

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including deepseek_facts ground truth
        """
        deepseek_facts = setup_data.get("deepseek_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {
            "deepseek_facts": deepseek_facts,
        }
        error_message = None

        try:
            response_lower = response.lower()

            # Condition 1: "deepseek" mentioned
            deepseek_found = "deepseek" in response_lower
            validation_details["deepseek_found"] = deepseek_found

            # Condition 2: DeepSeek cost ~$6 million
            # Accept: "$6", "6 million", "6m", "six million"
            deepseek_cost_found = (
                "$6" in response_lower
                or "6 million" in response_lower
                or "6m" in response_lower
                or "six million" in response_lower
            )
            validation_details["deepseek_cost_found"] = deepseek_cost_found

            # Condition 3: GPT-4 cost ~$100 million
            # Accept: "$100", "100 million", "100m"
            gpt4_cost_found = (
                "$100" in response_lower
                or "100 million" in response_lower
                or "100m" in response_lower
            )
            validation_details["gpt4_cost_found"] = gpt4_cost_found

            # Condition 4: Source attribution — at least one of BBC, OpenAI, GPT-4
            source_keywords = ["bbc", "openai", "gpt-4", "gpt4"]
            source_found = any(kw in response_lower for kw in source_keywords)
            matched_sources = [kw for kw in source_keywords if kw in response_lower]
            validation_details["source_found"] = source_found
            validation_details["sources_matched"] = matched_sources

            if deepseek_found and deepseek_cost_found and gpt4_cost_found and source_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not deepseek_found:
                    missing_parts.append("'deepseek'")
                if not deepseek_cost_found:
                    missing_parts.append("DeepSeek cost (~$6 million / $6m)")
                if not gpt4_cost_found:
                    missing_parts.append("GPT-4 cost (~$100 million / $100m)")
                if not source_found:
                    missing_parts.append(f"source attribution (one of: {', '.join(source_keywords)})")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Current Events Research",
            prompt="Search for the BBC article about DeepSeek training cost vs GPT-4",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_multi_query_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 4: Multi-Query Search with ground-truth facts (MEDIUM).

        Expected: Bot did two separate searches and returned both:
          1. arXiv 2505.15917 → author last name "Gidney"
          2. BBC top story Jan 2, 2025 → city "New Orleans"

        Both facts must be present — they share zero keywords, so both searches are required.

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including multi_query_facts ground truth
        """
        multi_query_facts = setup_data.get("multi_query_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {
            "multi_query_facts": multi_query_facts,
        }
        error_message = None

        try:
            response_lower = response.lower()

            # Fact 1: arXiv paper author — "Gidney"
            arxiv_found = "gidney" in response_lower
            validation_details["arxiv_author_found"] = arxiv_found

            # Fact 2: BBC top story city — "New Orleans" (also accept "bourbon" as strong signal)
            bbc_found = "new orleans" in response_lower or "bourbon" in response_lower
            validation_details["bbc_city_found"] = bbc_found

            if arxiv_found and bbc_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not arxiv_found:
                    missing_parts.append("arXiv author 'Gidney' (paper 2505.15917)")
                if not bbc_found:
                    missing_parts.append("BBC city 'New Orleans' (top story Jan 2, 2025)")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Multi-Query Search",
            prompt="Search arXiv for paper 2505.15917 (author) and BBC for top story Jan 2 2025 (city)",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_domain_specific_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 5: Domain-Specific Search (MEDIUM) — ground-truth.

        Expected: Bot searched techcrunch.com and found the ElevenLabs Series C article,
        reporting the $180 million raise.

        Three conditions must all pass:
          1. "elevenlabs" mentioned
          2. "180" appears in the response (the $180M amount)
          3. "techcrunch" mentioned (proves domain-specific search was used)

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including elevenlabs_facts ground truth
        """
        elevenlabs_facts = setup_data.get("elevenlabs_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {
            "elevenlabs_facts": elevenlabs_facts,
        }
        error_message = None

        try:
            response_lower = response.lower()

            # Condition 1: Company name mentioned
            elevenlabs_found = "elevenlabs" in response_lower
            validation_details["elevenlabs_found"] = elevenlabs_found

            # Condition 2: The $180M amount (accept "180 million", "$180", "180m")
            amount_found = (
                "180 million" in response_lower
                or "$180" in response_lower
                or "180m" in response_lower
                or "180" in response_lower  # bare number — prompt asks for dollar amount
            )
            validation_details["amount_found"] = amount_found

            # Condition 3: TechCrunch as domain source
            techcrunch_found = "techcrunch" in response_lower
            validation_details["techcrunch_found"] = techcrunch_found

            if elevenlabs_found and amount_found and techcrunch_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not elevenlabs_found:
                    missing_parts.append("'ElevenLabs'")
                if not amount_found:
                    missing_parts.append("funding amount ($180 million)")
                if not techcrunch_found:
                    missing_parts.append("'TechCrunch' source")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Domain-Specific Search",
            prompt="Search techcrunch.com for ElevenLabs Series C funding article (Jan 2025)",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_news_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 6: News Search — COP29 ground-truth (MEDIUM).

        Expected: Bot searched for COP29 and reported:
          1. City: Baku (Azerbaijan)
          2. Annual climate finance pledge: $300 billion

        Both facts must appear — neither appears in the prompt, so both require actual search.

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including cop29_facts ground truth
        """
        cop29_facts = setup_data.get("cop29_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"cop29_facts": cop29_facts}
        error_message = None

        try:
            response_lower = response.lower()

            # Condition 1: City — "baku" (not in the prompt)
            baku_found = "baku" in response_lower
            validation_details["baku_found"] = baku_found

            # Condition 2: Annual pledge — "300" (accept "300 billion", "$300", "300b")
            amount_found = "300" in response_lower
            validation_details["amount_found"] = amount_found

            if baku_found and amount_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not baku_found:
                    missing_parts.append("COP29 city 'Baku'")
                if not amount_found:
                    missing_parts.append("annual pledge '$300 billion'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="News Search",
            prompt="COP29 November 2024 — city and annual climate finance pledge",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_time_filtered_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 7: Chained Lookup — Nobel Physics + Chemistry 2024 → Chemistry winner's university (HARD).

        3-hop chain:
          Hop 1: 2024 Nobel Physics winner → Hinton
          Hop 2: 2024 Nobel Chemistry winner → Baker
          Hop 3: Baker's university → University of Washington

        All three must appear: "hinton" AND "baker" AND "washington".

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including nobel_science_chain ground truth
        """
        chain = setup_data.get("nobel_science_chain", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"nobel_science_chain": chain}
        error_message = None

        try:
            response_lower = response.lower()

            # Hop 1: Nobel Physics winner
            hinton_found = "hinton" in response_lower
            validation_details["hinton_found"] = hinton_found

            # Hop 2: Nobel Chemistry winner
            baker_found = "baker" in response_lower
            validation_details["baker_found"] = baker_found

            # Hop 3: Chemistry winner's university
            washington_found = "washington" in response_lower
            validation_details["washington_found"] = washington_found

            if hinton_found and baker_found and washington_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not hinton_found:
                    missing_parts.append("Nobel Physics winner 'Hinton'")
                if not baker_found:
                    missing_parts.append("Nobel Chemistry winner 'Baker'")
                if not washington_found:
                    missing_parts.append("Chemistry winner's university 'Washington'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Time-Filtered Search",
            prompt="Nobel Physics 2024 → Nobel Chemistry 2024 → Chemistry winner's university",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_search_comparison(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 8: Chained Lookup — 100m WR holder → year → PM of their country that year (HARD).

        3-hop chain:
          Hop 1: Men's 100m world record holder → Usain Bolt
          Hop 2: Year the record was set → 2009
          Hop 3: PM of Jamaica in 2009 → Bruce Golding

        All three must appear: "bolt" AND "2009" AND "golding".

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including sprint_politics_chain ground truth
        """
        chain = setup_data.get("sprint_politics_chain", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"sprint_politics_chain": chain}
        error_message = None

        try:
            response_lower = response.lower()

            # Hop 1: Record holder
            bolt_found = "bolt" in response_lower
            validation_details["bolt_found"] = bolt_found

            # Hop 2: Year the record was set
            year_found = "2009" in response_lower
            validation_details["year_found"] = year_found

            # Hop 3: PM of Jamaica in 2009
            golding_found = "golding" in response_lower
            validation_details["golding_found"] = golding_found

            if bolt_found and year_found and golding_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not bolt_found:
                    missing_parts.append("record holder 'Bolt'")
                if not year_found:
                    missing_parts.append("record year '2009'")
                if not golding_found:
                    missing_parts.append("PM of Jamaica in 2009 'Golding'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Search Comparison",
            prompt="100m WR holder → year record set → PM of their country that year",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_topic_analysis(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 9: Chained Lookup — Best Picture 2024 director → university → city → founding year (HARD).

        4-hop chain:
          Hop 1: Best Picture 2024 (Oppenheimer) → director Christopher Nolan
          Hop 2: Nolan's university → Christ's College Cambridge
          Hop 3: City → Cambridge, UK
          Hop 4: Year Cambridge University founded → 1209

        Required: "nolan" AND "cambridge" AND "1209".

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including film_geography_chain ground truth
        """
        chain = setup_data.get("film_geography_chain", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"film_geography_chain": chain}
        error_message = None

        try:
            response_lower = response.lower()

            # Hops 1+2: Director and university both contain "nolan" and "cambridge"
            nolan_found = "nolan" in response_lower
            validation_details["nolan_found"] = nolan_found

            cambridge_found = "cambridge" in response_lower
            validation_details["cambridge_found"] = cambridge_found

            # Hop 4: Founding year — very specific, unambiguous
            founding_year_found = "1209" in response_lower
            validation_details["founding_year_found"] = founding_year_found

            if nolan_found and cambridge_found and founding_year_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not nolan_found:
                    missing_parts.append("director 'Nolan'")
                if not cambridge_found:
                    missing_parts.append("university/city 'Cambridge'")
                if not founding_year_found:
                    missing_parts.append("university founding year '1209'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Topic Analysis",
            prompt="Best Picture 2024 director → university → city → university founding year",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
