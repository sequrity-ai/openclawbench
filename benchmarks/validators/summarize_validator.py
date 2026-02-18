"""Validation utilities for Summarize benchmark tasks.

All validators are pinned to specific facts from:
  - Tasks 1-3: Known facts from public URLs (Wikipedia, YouTube, python.org)
  - Tasks 4-9: Specific facts seeded into the local documents by SummarizeSetup
"""

import logging
from typing import Any

from benchmarks.base import TaskResult

logger = logging.getLogger(__name__)


class SummarizeValidator:
    """Validates Summarize task results against specific ground-truth facts."""

    @staticmethod
    def validate_url_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 1: Summary of Python Wikipedia article (EASY).

        Expected: Bot summarizes the Wikipedia article and mentions that Python
        was created by Guido van Rossum and first released in 1991.

        Conditions:
          1. "guido" appears (the creator's first name — unique to Python's origin story)
          2. "1991" appears (the year Python was first released)
        """
        url_facts = setup_data.get("url_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"url_facts": url_facts}
        error_message = None

        try:
            response_lower = response.lower()

            guido_found = "guido" in response_lower
            year_found = "1991" in response_lower
            validation_details["guido_found"] = guido_found
            validation_details["year_1991_found"] = year_found

            if guido_found and year_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not guido_found:
                    missing_parts.append("creator 'Guido' (van Rossum)")
                if not year_found:
                    missing_parts.append("creation year '1991'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="URL Summary",
            prompt="Can you summarize this article for me? https://en.wikipedia.org/wiki/Python_(programming_language)",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_youtube_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 2: Summary of 'Python in 100 Seconds' YouTube video (EASY).

        Expected: Bot summarizes the Fireship video covering Python's key
        properties — interpreted, dynamically typed, beginner-friendly.

        Conditions:
          1. "100 seconds" OR "fireship" appears (identifies the specific video)
          2. "interpreted" OR "dynamic" OR "beginner" appears (video's key talking points)
        """
        youtube_facts = setup_data.get("youtube_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"youtube_facts": youtube_facts}
        error_message = None

        try:
            response_lower = response.lower()

            video_identified = "100 seconds" in response_lower or "fireship" in response_lower
            content_found = any(kw in response_lower for kw in ["interpreted", "dynamic", "beginner"])
            matched_content = [kw for kw in ["interpreted", "dynamic", "beginner"] if kw in response_lower]
            validation_details["video_identified"] = video_identified
            validation_details["content_found"] = content_found
            validation_details["matched_content"] = matched_content

            if video_identified and content_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not video_identified:
                    missing_parts.append("video identified ('100 seconds' or 'Fireship')")
                if not content_found:
                    missing_parts.append("Python property ('interpreted', 'dynamic', or 'beginner')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="YouTube Summary",
            prompt="Summarize this YouTube video: https://www.youtube.com/watch?v=x7X9w_GIm1s (Python in 100 Seconds)",
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_comparison_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 3: Compare Wikipedia article vs python.org/about (EASY).

        Expected: Bot summarizes both sources and identifies differences.
        Wikipedia is encyclopedic/historical; python.org/about is promotional/community-focused.

        Conditions:
          1. "wikipedia" appears (first source referenced)
          2. "python.org" OR "official" appears (second source referenced)
          3. "open source" OR "community" OR "philosophy" appears (facts unique to python.org/about)
        """
        comparison_facts = setup_data.get("comparison_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"comparison_facts": comparison_facts}
        error_message = None

        try:
            response_lower = response.lower()

            wikipedia_found = "wikipedia" in response_lower
            python_org_found = "python.org" in response_lower or "official" in response_lower
            # python.org/about emphasizes community, open source, philosophy — Wikipedia is encyclopedic
            philosophy_found = any(kw in response_lower for kw in ["open source", "community", "philosophy"])
            matched_philosophy = [kw for kw in ["open source", "community", "philosophy"] if kw in response_lower]

            validation_details["wikipedia_found"] = wikipedia_found
            validation_details["python_org_found"] = python_org_found
            validation_details["philosophy_found"] = philosophy_found
            validation_details["matched_philosophy"] = matched_philosophy

            if wikipedia_found and python_org_found and philosophy_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not wikipedia_found:
                    missing_parts.append("'Wikipedia' source referenced")
                if not python_org_found:
                    missing_parts.append("'python.org' or 'official' source referenced")
                if not philosophy_found:
                    missing_parts.append("python.org theme ('open source', 'community', or 'philosophy')")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Comparison Summary",
            prompt=(
                "Compare and summarize these two articles about Python: "
                "1) https://en.wikipedia.org/wiki/Python_(programming_language) "
                "2) https://www.python.org/about/ "
                "What are the key differences in how they describe Python?"
            ),
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_executive_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 4: Executive summary of business_report.txt (MEDIUM).

        Seeded document: TechCorp Q4 2025 report.
        Key facts: revenue $4.2B, 23% YoY growth, cloud services $1.8B (up 35%).

        Conditions:
          1. "4.2" appears (the total Q4 revenue figure)
          2. "23" appears (the 23% YoY revenue growth)
        """
        business_facts = setup_data.get("business_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"business_facts": business_facts}
        error_message = None

        try:
            response_lower = response.lower()

            revenue_found = "4.2" in response_lower
            growth_found = "23" in response_lower
            validation_details["revenue_4_2b_found"] = revenue_found
            validation_details["growth_23pct_found"] = growth_found

            if revenue_found and growth_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not revenue_found:
                    missing_parts.append("revenue figure '$4.2B'")
                if not growth_found:
                    missing_parts.append("growth rate '23%'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Executive Summary",
            prompt=(
                "Please read the business report at /tmp/openclaw_benchmark/documents/business_report.txt "
                "and create an executive summary. The summary should highlight key financial highlights, "
                "business performance metrics, and strategic outlook. Keep it concise and professional."
            ),
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_technical_abstract(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 5: Technical abstract of technical_paper.txt (MEDIUM).

        Seeded document: ML paper on time series forecasting.
        Key facts: compares LSTM, Temporal Fusion Transformer, XGBoost, Prophet, hybrid ensembles.
        TFT achieved lowest MAE on 3 out of 4 datasets.

        Conditions:
          1. "lstm" appears (one of the named models)
          2. "temporal fusion transformer" OR "tft" appears (the best-performing model)
        """
        technical_facts = setup_data.get("technical_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"technical_facts": technical_facts}
        error_message = None

        try:
            response_lower = response.lower()

            lstm_found = "lstm" in response_lower
            tft_found = "temporal fusion transformer" in response_lower or "tft" in response_lower
            validation_details["lstm_found"] = lstm_found
            validation_details["tft_found"] = tft_found

            if lstm_found and tft_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not lstm_found:
                    missing_parts.append("model 'LSTM'")
                if not tft_found:
                    missing_parts.append("model 'Temporal Fusion Transformer' or 'TFT'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Technical Abstract",
            prompt=(
                "Please read the technical paper at /tmp/openclaw_benchmark/documents/technical_paper.txt "
                "and write a technical abstract focusing on the key concepts, methodology, and findings. "
                "Identify the main approaches discussed and summarize the experimental results."
            ),
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_comparative_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 6: Compare ai_article_a.txt vs ai_article_b.txt (MEDIUM).

        Seeded docs: two AI-in-healthcare articles.
          - ai_article_a.txt: pro-AI perspective — mentions drug discovery, 30% reading time reduction
          - ai_article_b.txt: cautionary perspective — mentions algorithmic bias, liability

        Conditions:
          1. "bias" appears (term unique to article_b's cautionary perspective)
          2. "drug discovery" appears (term unique to article_a's optimistic perspective)
        """
        comparison_ai_facts = setup_data.get("comparison_ai_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"comparison_ai_facts": comparison_ai_facts}
        error_message = None

        try:
            response_lower = response.lower()

            # article_b key term — proves cautionary article was read
            bias_found = "bias" in response_lower
            # article_a key term — proves optimistic article was read
            drug_discovery_found = "drug discovery" in response_lower
            validation_details["bias_found"] = bias_found
            validation_details["drug_discovery_found"] = drug_discovery_found

            if bias_found and drug_discovery_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not bias_found:
                    missing_parts.append("'bias' (from cautionary article_b)")
                if not drug_discovery_found:
                    missing_parts.append("'drug discovery' (from optimistic article_a)")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Comparative Summary",
            prompt=(
                "Read these two articles about AI in healthcare: "
                "1) /tmp/openclaw_benchmark/documents/ai_article_a.txt "
                "2) /tmp/openclaw_benchmark/documents/ai_article_b.txt "
                "Compare and summarize both articles. What are the key differences in their perspectives? "
                "What do they agree and disagree on?"
            ),
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_multilevel_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 7: Three-level summary of quantum_computing.txt (HARD).

        Seeded document: article on quantum computing covering qubits, superposition,
        entanglement, hardware platforms, algorithms, and Shor's algorithm.

        Conditions:
          1. "qubit" OR "qubits" appears (the fundamental quantum unit — must appear in any real summary)
          2. "superposition" appears (core principle explained in the document)
        """
        quantum_facts = setup_data.get("quantum_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"quantum_facts": quantum_facts}
        error_message = None

        try:
            response_lower = response.lower()

            qubit_found = "qubit" in response_lower
            superposition_found = "superposition" in response_lower
            validation_details["qubit_found"] = qubit_found
            validation_details["superposition_found"] = superposition_found

            if qubit_found and superposition_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not qubit_found:
                    missing_parts.append("'qubit' / 'qubits'")
                if not superposition_found:
                    missing_parts.append("'superposition'")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Multi-Level Summary",
            prompt=(
                "Read the article at /tmp/openclaw_benchmark/documents/quantum_computing.txt "
                "and provide THREE levels of summary:\n"
                "1. One-sentence summary: Capture the entire article in a single sentence\n"
                "2. One-paragraph summary: A concise paragraph with the key points\n"
                "3. Detailed summary: A comprehensive overview covering all major sections"
            ),
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_qa_generation(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 8: Q&A study guide from renewable_energy.txt (HARD).

        Seeded document: article on global renewable energy transition.
        Key facts: renewables = 38% of global electricity in 2025 (up from 20% in 2015),
        solar costs fell 90%, lithium-ion battery costs fell 85%.

        Conditions:
          1. "38" appears (38% renewable share in 2025 — the headline statistic)
          2. "lithium" appears (lithium-ion batteries — a key technology discussed)
        """
        renewable_facts = setup_data.get("renewable_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"renewable_facts": renewable_facts}
        error_message = None

        try:
            response_lower = response.lower()

            pct_found = "38" in response_lower
            lithium_found = "lithium" in response_lower
            validation_details["pct_38_found"] = pct_found
            validation_details["lithium_found"] = lithium_found

            if pct_found and lithium_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not pct_found:
                    missing_parts.append("'38' (38% renewable electricity share in 2025)")
                if not lithium_found:
                    missing_parts.append("'lithium' (lithium-ion battery storage)")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Q&A Generation",
            prompt=(
                "Read the article at /tmp/openclaw_benchmark/documents/renewable_energy.txt "
                "and generate a Q&A study guide from it. Create at least 5 questions with detailed answers "
                "that cover the main ideas, key facts, and important concepts in the article. "
                "Format each entry clearly as Question and Answer."
            ),
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )

    @staticmethod
    def validate_sentiment_summary(response: str, setup_data: dict[str, Any]) -> TaskResult:
        """Validate Task 9: Sentiment analysis of social_media_impact.txt (HARD).

        Seeded document: balanced assessment of social media's impact on society.
        Key facts: "over 5 billion users worldwide", explicit Positive/Negative sections,
        mixed overall sentiment (both celebratory and critical tones).

        Conditions:
          1. "5 billion" appears (the opening user-count statistic — proves doc was read)
          2. "positive" AND "negative" both appear (the two explicit sentiment sections)
        """
        sentiment_facts = setup_data.get("sentiment_facts", {})

        success = False
        accuracy_score = 0.0
        validation_details = {"sentiment_facts": sentiment_facts}
        error_message = None

        try:
            response_lower = response.lower()

            five_billion_found = "5 billion" in response_lower
            positive_found = "positive" in response_lower
            negative_found = "negative" in response_lower
            validation_details["five_billion_found"] = five_billion_found
            validation_details["positive_found"] = positive_found
            validation_details["negative_found"] = negative_found

            if five_billion_found and positive_found and negative_found:
                success = True
                accuracy_score = 100.0
            else:
                missing_parts = []
                if not five_billion_found:
                    missing_parts.append("'5 billion' users statistic")
                if not positive_found:
                    missing_parts.append("'positive' sentiment label")
                if not negative_found:
                    missing_parts.append("'negative' sentiment label")
                error_message = f"Missing: {'; '.join(missing_parts)}"

        except Exception as e:
            error_message = f"Validation error: {str(e)}"

        return TaskResult(
            task_name="Sentiment Analysis Summary",
            prompt=(
                "Read the article at /tmp/openclaw_benchmark/documents/social_media_impact.txt "
                "and provide a summary that includes sentiment analysis. In your response:\n"
                "1. Summarize the main points of the article\n"
                "2. Analyze the overall tone and sentiment (positive, negative, neutral, or mixed)\n"
                "3. Identify sections with notably positive or negative sentiment\n"
                "4. Describe how the author's tone shifts throughout the article"
            ),
            success=success,
            latency=0.0,
            accuracy_score=accuracy_score,
            response_text=response,
            validation_details=validation_details,
            error_message=error_message,
        )
