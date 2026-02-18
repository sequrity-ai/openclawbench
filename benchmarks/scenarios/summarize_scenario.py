"""Summarize benchmark scenario.

Tasks (9) — all validators pinned to specific facts in the source material:
    Easy:
       - Task 1 (URL Summary): Summarize Python Wikipedia article
         → must mention Guido van Rossum + 1991
       - Task 2 (YouTube Summary): Summarize 'Python in 100 Seconds' by Fireship
         → must identify the video + mention interpreted/dynamic/beginner
       - Task 3 (Comparison Summary): Compare Wikipedia vs python.org/about
         → must reference both sources + mention open source/community/philosophy

    Medium:
       - Task 4 (Executive Summary): Summarize business_report.txt (TechCorp Q4 2025)
         → must mention $4.2B revenue + 23% YoY growth
       - Task 5 (Technical Abstract): Summarize technical_paper.txt (ML time series)
         → must mention LSTM + Temporal Fusion Transformer
       - Task 6 (Comparative Summary): Compare ai_article_a.txt vs ai_article_b.txt
         → must mention 'drug discovery' (article_a) + 'bias' (article_b)

    Hard:
       - Task 7 (Multi-Level Summary): Summarize quantum_computing.txt at 3 levels
         → must mention qubit + superposition
       - Task 8 (Q&A Generation): Generate Q&A from renewable_energy.txt
         → must mention 38% (global renewable share in 2025) + lithium
       - Task 9 (Sentiment Analysis): Summarize social_media_impact.txt with sentiment
         → must mention '5 billion' users + both 'positive' and 'negative'

Setup:
    Creates local documents at /tmp/openclaw_benchmark/documents/ including business
    reports, technical papers, and articles. Documents are uploaded to the bot workspace
    for tasks 4-9.

Required Skills:
    steipete/summarize
"""

import logging

from benchmarks.base import (
    BenchmarkTask,
    CheckStatus,
    HealthCheckResult,
    ScenarioBase,
    SetupResult,
)
from benchmarks.setup.summarize_setup import SummarizeSetup
from benchmarks.skill_checker import check_skills
from benchmarks.validators.summarize_validator import SummarizeValidator

logger = logging.getLogger(__name__)


class SummarizeScenario(ScenarioBase):
    """Benchmark scenario for content summarization."""

    def __init__(self, remote_manager=None):
        """Initialize Summarize scenario.

        Args:
            remote_manager: Optional RemoteWorkspaceManager (not used for summarize)

        Note:
            - Requires the steipete/summarize skill to be installed
            - No API keys required
        """
        super().__init__(
            name="Summarize",
            description="Tests agent's ability to summarize content from web, PDFs, videos",
            required_skills=["steipete/summarize"],
        )

        self.validator = SummarizeValidator()
        self.remote_manager = remote_manager
        self.setup_data = {}
        self.summarize_setup = SummarizeSetup()

        # Define tasks
        self._define_tasks()

    def _define_tasks(self) -> None:
        """Define the 9 Summarize tasks."""

        # Task 1: Web Article Summary
        self.add_task(
            BenchmarkTask(
                name="URL Summary",
                prompt="Can you summarize this article for me? https://en.wikipedia.org/wiki/Python_(programming_language)",
                expected_output_description="Bot provides a concise summary of the Python Wikipedia article",
                validation_fn=self.validator.validate_url_summary,
                timeout=60.0,
                metadata={"difficulty": "easy", "category": "url_summary"},
            )
        )

        # Task 2: YouTube Video Summary
        self.add_task(
            BenchmarkTask(
                name="YouTube Summary",
                prompt="Summarize this YouTube video: https://www.youtube.com/watch?v=x7X9w_GIm1s (Python in 100 Seconds)",
                expected_output_description="Bot summarizes the YouTube video content",
                validation_fn=self.validator.validate_youtube_summary,
                timeout=90.0,
                metadata={"difficulty": "easy", "category": "video_summary"},
            )
        )

        # Task 3: Multiple Source Comparison
        self.add_task(
            BenchmarkTask(
                name="Comparison Summary",
                prompt=(
                    "Compare and summarize these two articles about Python: "
                    "1) https://en.wikipedia.org/wiki/Python_(programming_language) "
                    "2) https://www.python.org/about/ "
                    "What are the key differences in how they describe Python?"
                ),
                expected_output_description="Bot compares and contrasts summaries from both sources",
                validation_fn=self.validator.validate_comparison_summary,
                timeout=120.0,
                metadata={"difficulty": "easy", "category": "comparison_summary"},
            )
        )

        # Task 4 (Medium): Executive Summary
        self.add_task(
            BenchmarkTask(
                name="Executive Summary",
                prompt=(
                    "Please read the business report at /tmp/openclaw_benchmark/documents/business_report.txt "
                    "and create an executive summary. The summary should highlight key financial highlights, "
                    "business performance metrics, and strategic outlook. Keep it concise and professional."
                ),
                expected_output_description="Bot creates a professional executive summary covering key highlights, performance metrics, and outlook",
                validation_fn=self.validator.validate_executive_summary,
                timeout=90.0,
                metadata={"difficulty": "medium", "category": "executive_summary"},
            )
        )

        # Task 5 (Medium): Technical Abstract
        self.add_task(
            BenchmarkTask(
                name="Technical Abstract",
                prompt=(
                    "Please read the technical paper at /tmp/openclaw_benchmark/documents/technical_paper.txt "
                    "and write a technical abstract focusing on the key concepts, methodology, and findings. "
                    "Identify the main approaches discussed and summarize the experimental results."
                ),
                expected_output_description="Bot provides a technical abstract covering methodology, key concepts, and findings",
                validation_fn=self.validator.validate_technical_abstract,
                timeout=90.0,
                metadata={"difficulty": "medium", "category": "technical_abstract"},
            )
        )

        # Task 6 (Medium): Comparative Summary
        self.add_task(
            BenchmarkTask(
                name="Comparative Summary",
                prompt=(
                    "Read these two articles about AI in healthcare: "
                    "1) /tmp/openclaw_benchmark/documents/ai_article_a.txt "
                    "2) /tmp/openclaw_benchmark/documents/ai_article_b.txt "
                    "Compare and summarize both articles. What are the key differences in their perspectives? "
                    "What do they agree and disagree on?"
                ),
                expected_output_description="Bot compares both AI articles, highlighting agreement and divergence between pro-AI and cautionary perspectives",
                validation_fn=self.validator.validate_comparative_summary,
                timeout=120.0,
                metadata={"difficulty": "medium", "category": "comparative_summary"},
            )
        )

        # Task 7 (Hard): Multi-Level Summary
        self.add_task(
            BenchmarkTask(
                name="Multi-Level Summary",
                prompt=(
                    "Read the article at /tmp/openclaw_benchmark/documents/quantum_computing.txt "
                    "and provide THREE levels of summary:\n"
                    "1. One-sentence summary: Capture the entire article in a single sentence\n"
                    "2. One-paragraph summary: A concise paragraph with the key points\n"
                    "3. Detailed summary: A comprehensive overview covering all major sections"
                ),
                expected_output_description="Bot provides all three summary levels with appropriate depth and structure for each",
                validation_fn=self.validator.validate_multilevel_summary,
                timeout=120.0,
                metadata={"difficulty": "hard", "category": "multilevel_summary"},
            )
        )

        # Task 8 (Hard): Q&A Generation
        self.add_task(
            BenchmarkTask(
                name="Q&A Generation",
                prompt=(
                    "Read the article at /tmp/openclaw_benchmark/documents/renewable_energy.txt "
                    "and generate a Q&A study guide from it. Create at least 5 questions with detailed answers "
                    "that cover the main ideas, key facts, and important concepts in the article. "
                    "Format each entry clearly as Question and Answer."
                ),
                expected_output_description="Bot generates at least 5 well-formed questions with comprehensive answers from the article",
                validation_fn=self.validator.validate_qa_generation,
                timeout=120.0,
                metadata={"difficulty": "hard", "category": "qa_generation"},
            )
        )

        # Task 9 (Hard): Sentiment Analysis Summary
        self.add_task(
            BenchmarkTask(
                name="Sentiment Analysis Summary",
                prompt=(
                    "Read the article at /tmp/openclaw_benchmark/documents/social_media_impact.txt "
                    "and provide a summary that includes sentiment analysis. In your response:\n"
                    "1. Summarize the main points of the article\n"
                    "2. Analyze the overall tone and sentiment (positive, negative, neutral, or mixed)\n"
                    "3. Identify sections with notably positive or negative sentiment\n"
                    "4. Describe how the author's tone shifts throughout the article"
                ),
                expected_output_description="Bot summarizes the article and provides a thorough sentiment analysis including tone, polarity, and sentiment shifts",
                validation_fn=self.validator.validate_sentiment_summary,
                timeout=120.0,
                metadata={"difficulty": "hard", "category": "sentiment_summary"},
            )
        )

    def pre_check(self) -> list[HealthCheckResult]:
        """Run pre-flight health checks."""
        # Check for summarize skill
        local_mode = self.remote_manager is None
        checks = check_skills(self.required_skills, local_mode=local_mode, remote_manager=self.remote_manager)

        checks.append(
            HealthCheckResult(
                check_name="Summarize API Note",
                status=CheckStatus.PASS,
                message="Summarize skill requires no API key configuration",
                details={"required_skill": "steipete/summarize"},
            )
        )

        return checks

    def setup(self) -> SetupResult:
        """Set up the Summarize scenario.

        Returns:
            Setup result with expected validation data
        """
        try:
            logger.info("Setting up Summarize benchmark...")

            # Ground-truth facts for validators (pinned to seeded document content)
            self.setup_data = {
                # Task 1: Python Wikipedia article
                "url_facts": {
                    "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                    "creator": "Guido van Rossum",
                    "year": "1991",
                },
                # Task 2: Python in 100 Seconds YouTube video
                "youtube_facts": {
                    "url": "https://www.youtube.com/watch?v=x7X9w_GIm1s",
                    "channel": "Fireship",
                    "key_properties": ["interpreted", "dynamic", "beginner"],
                },
                # Task 3: Wikipedia vs python.org comparison
                "comparison_facts": {
                    "source_1": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                    "source_2": "https://www.python.org/about/",
                    "python_org_themes": ["open source", "community", "philosophy"],
                },
                # Task 4: business_report.txt — TechCorp Q4 2025
                "business_facts": {
                    "company": "TechCorp International",
                    "quarter": "Q4 2025",
                    "revenue_billion": "4.2",
                    "yoy_growth_pct": "23",
                    "cloud_revenue_billion": "1.8",
                },
                # Task 5: technical_paper.txt — ML time series forecasting
                "technical_facts": {
                    "topic": "time series forecasting",
                    "models": ["LSTM", "Temporal Fusion Transformer", "XGBoost", "Prophet"],
                    "best_model": "Temporal Fusion Transformer",
                },
                # Task 6: ai_article_a.txt (pro-AI) vs ai_article_b.txt (cautionary)
                "comparison_ai_facts": {
                    "article_a_perspective": "optimistic",
                    "article_a_unique_term": "drug discovery",
                    "article_b_perspective": "cautionary",
                    "article_b_unique_term": "bias",
                },
                # Task 7: quantum_computing.txt
                "quantum_facts": {
                    "topic": "quantum computing",
                    "key_terms": ["qubit", "superposition", "entanglement"],
                },
                # Task 8: renewable_energy.txt
                "renewable_facts": {
                    "topic": "global renewable energy transition",
                    "renewable_pct_2025": "38",
                    "storage_tech": "lithium-ion",
                },
                # Task 9: social_media_impact.txt
                "sentiment_facts": {
                    "topic": "social media impact on society",
                    "user_count": "5 billion",
                    "sentiment_sections": ["positive", "negative"],
                    "overall_sentiment": "mixed",
                },
            }

            if self.remote_manager:
                # Create docs locally, then upload to remote server via SFTP
                logger.info("Creating seed documents locally...")
                workspace_data = self.summarize_setup.create_workspace()

                logger.info("Uploading seed documents to remote server...")
                self.remote_manager.connect()

                # Create remote documents directory
                remote_docs_dir = f"{self.remote_manager.workspace_path}/documents"
                self.remote_manager._exec_command(f"mkdir -p {remote_docs_dir}")

                # Upload each document
                import os
                local_docs_dir = workspace_data["documents_dir"]
                for filename in os.listdir(local_docs_dir):
                    local_path = os.path.join(local_docs_dir, filename)
                    remote_path = f"{remote_docs_dir}/{filename}"
                    self.remote_manager.sftp_client.put(local_path, remote_path)
                    logger.info(f"✓ Uploaded {filename} to {remote_path}")

                # Update paths in workspace_data to remote paths; merge with ground-truth facts
                remote_workspace_data = {
                    "workspace_dir": self.remote_manager.workspace_path,
                    "documents_dir": remote_docs_dir,
                    "business_article": f"{remote_docs_dir}/business_report.txt",
                    "technical_doc": f"{remote_docs_dir}/technical_paper.txt",
                    "article_a": f"{remote_docs_dir}/ai_article_a.txt",
                    "article_b": f"{remote_docs_dir}/ai_article_b.txt",
                    "long_article": f"{remote_docs_dir}/quantum_computing.txt",
                    "qa_article": f"{remote_docs_dir}/renewable_energy.txt",
                    "sentiment_article": f"{remote_docs_dir}/social_media_impact.txt",
                }
                self.setup_data.update(remote_workspace_data)
            else:
                # Create seed documents for Tasks 4-9 locally (fallback for local mode)
                workspace_data = self.summarize_setup.create_workspace()
                self.setup_data.update(workspace_data)

            logger.info("Setup complete - seed documents created and validation criteria configured")

            return SetupResult(
                status=CheckStatus.PASS,
                message="Summarize scenario configured successfully",
                setup_data=self.setup_data,
            )

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return SetupResult(
                status=CheckStatus.FAIL,
                message=f"Failed to set up Summarize scenario: {str(e)}",
                error=str(e),
            )

    def cleanup(self) -> bool:
        """Clean up the Summarize scenario.

        Returns:
            True if cleanup succeeded
        """
        logger.info("Summarize scenario cleanup - removing seed documents")
        local_ok = self.summarize_setup.cleanup_workspace()

        if self.remote_manager:
            try:
                remote_docs_dir = f"{self.remote_manager.workspace_path}/documents"
                self.remote_manager._exec_command(f"rm -rf {remote_docs_dir}")
                logger.info(f"Removed remote documents at {remote_docs_dir}")
            except Exception as e:
                logger.warning(f"Failed to remove remote documents: {e}")

        return local_ok
