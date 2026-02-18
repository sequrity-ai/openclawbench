"""Validation utilities for Web Search benchmark tasks."""

import logging
from typing import Any

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)


class WebValidator:
    """Validates Web Search task results."""

    @staticmethod
    def validate_factual_search(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Factual web search.

        Expected: Bot found and reported correct factual information

        Args:
            response: Full conversation history (all bot responses concatenated)
            setup_data: Setup data including expected facts
        """
        expected_facts = setup_data.get("expected_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"expected_facts": expected_facts}
        error_message = None

        try:
            # Check if bot mentioned all expected facts (case-insensitive)
            facts_found = []
            facts_missing = []

            for fact_name, fact_value in expected_facts.items():
                # Convert to lowercase for comparison
                if str(fact_value).lower() in response.lower():
                    facts_found.append(fact_name)
                else:
                    facts_missing.append(fact_name)

            validation_details["facts_found"] = facts_found
            validation_details["facts_missing"] = facts_missing

            # Binary scoring: ALL facts must be present
            if len(facts_found) == len(expected_facts):
                success = True
                accuracy_score = 100.0
            else:
                accuracy_score = 0.0
                error_message = f"Missing expected facts: {', '.join(facts_missing)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Factual Web Search",
            prompt="Search for factual information on the web",
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
