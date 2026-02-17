"""Setup utilities for summarize benchmark scenario."""

import os
from pathlib import Path


class SummarizeSetup:
    """Handles setup and cleanup for summarize benchmarks."""

    def __init__(self, workspace_dir: str = "/tmp/openclaw_benchmark"):
        """Initialize summarize setup.

        Args:
            workspace_dir: Directory for test documents
        """
        self.workspace_dir = Path(workspace_dir)
        self.documents_dir = self.workspace_dir / "documents"

    def create_workspace(self) -> dict[str, str]:
        """Create test workspace with seed documents for summarization.

        Returns:
            Dict with paths to created documents and expected data
        """
        # Create directories
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir.mkdir(exist_ok=True)

        # Task 4: Executive Summary - Business article
        business_article = self.documents_dir / "business_report.txt"
        business_article.write_text("""Q4 Financial Performance Report

Executive Overview:
TechCorp International reported strong financial results for Q4 2025, exceeding analyst expectations across all key metrics. Revenue grew 23% year-over-year to $4.2 billion, driven by robust demand in cloud services and enterprise software divisions.

Key Highlights:
- Total revenue: $4.2B (up 23% YoY)
- Operating margin: 28% (improved from 24% in Q4 2024)
- Cloud services revenue: $1.8B (up 35% YoY)
- Enterprise software: $1.5B (up 18% YoY)
- Customer acquisition: 15,000 new enterprise clients

Market Performance:
The company's cloud infrastructure business showed exceptional growth, capturing additional market share from competitors. Strategic partnerships with major retail and healthcare organizations contributed significantly to revenue growth. The enterprise software division benefited from increased demand for AI-powered analytics tools.

Operational Efficiency:
TechCorp improved operational efficiency through automation initiatives and strategic cost optimization. Research and development investments increased by 15% to support next-generation product development, while sales and marketing expenses were optimized through data-driven strategies.

Outlook:
Management provided guidance for Q1 2026, projecting revenue between $4.3B and $4.5B, representing 20-25% year-over-year growth. The company plans to expand its cloud infrastructure capacity by 30% and launch three major product updates in the coming quarter.

Risk Factors:
Key risks include increased competition in cloud services, potential regulatory changes in data privacy laws, and ongoing cybersecurity challenges. The company continues to invest heavily in security infrastructure and compliance programs.

Conclusion:
TechCorp's Q4 performance demonstrates strong execution across business units and positions the company well for continued growth. Strategic investments in cloud infrastructure and AI capabilities are expected to drive long-term value creation.
""")

        # Task 5: Technical Abstract - Technical document
        technical_doc = self.documents_dir / "technical_paper.txt"
        technical_doc.write_text("""Advanced Machine Learning Techniques for Time Series Forecasting

Abstract:
This paper presents a comprehensive analysis of modern machine learning approaches for time series forecasting, with particular emphasis on deep learning architectures and hybrid models. We evaluate the performance of Long Short-Term Memory (LSTM) networks, Transformer-based models, and ensemble methods across multiple real-world datasets.

Introduction:
Time series forecasting remains a fundamental challenge in data science, with applications spanning finance, weather prediction, supply chain management, and energy systems. Traditional statistical methods like ARIMA have been augmented by machine learning techniques that can capture complex non-linear patterns.

Methodology:
We implemented and compared five distinct approaches:
1. LSTM Networks with attention mechanisms
2. Transformer architecture adapted for time series (Temporal Fusion Transformer)
3. Gradient Boosting Decision Trees (XGBoost for time series)
4. Prophet model with customized seasonality components
5. Hybrid ensemble combining multiple base models

Datasets:
Our experiments utilized four diverse datasets: stock market prices (S&P 500), electricity demand patterns, retail sales data, and weather measurements. Each dataset presented unique challenges including irregular sampling, missing values, and multiple seasonal patterns.

Experimental Results:
The Temporal Fusion Transformer achieved the lowest Mean Absolute Error (MAE) on 3 out of 4 datasets, with an average improvement of 15% over LSTM baselines. However, computational requirements were 3x higher. XGBoost demonstrated strong performance on datasets with clear feature interactions but struggled with long-term dependencies.

Key Findings:
1. Attention mechanisms significantly improve forecast accuracy for sequences with variable importance patterns
2. Hybrid ensembles provide robust performance across different data characteristics
3. Domain-specific feature engineering remains crucial despite advanced architectures
4. Computational efficiency trade-offs must be considered for production deployment

Model Interpretability:
We employed SHAP values and attention weight visualization to understand model decisions. Feature importance analysis revealed that recent historical values, day-of-week effects, and seasonal indicators were consistently significant across datasets.

Limitations:
Our study focused on univariate and low-dimensional multivariate scenarios. High-dimensional datasets with hundreds of correlated features require additional investigation. Computational constraints limited hyperparameter search space exploration.

Future Work:
Promising directions include incorporating causal inference frameworks, developing more efficient transformer architectures, and investigating few-shot learning approaches for scenarios with limited historical data.

Conclusion:
Modern deep learning architectures offer substantial improvements over traditional methods for time series forecasting, particularly when dealing with complex patterns and long sequences. The choice of model should be guided by dataset characteristics, computational constraints, and interpretability requirements.
""")

        # Task 6: Comparative Summary - Two articles on same topic
        article_a = self.documents_dir / "ai_article_a.txt"
        article_a.write_text("""The Promise of Artificial Intelligence in Healthcare

Artificial intelligence is revolutionizing healthcare delivery, offering unprecedented opportunities to improve patient outcomes and operational efficiency. Machine learning algorithms can now analyze medical images with accuracy matching or exceeding human radiologists, detect diseases earlier, and personalize treatment plans based on individual patient characteristics.

Diagnostic capabilities have advanced dramatically. AI systems trained on millions of medical images can identify patterns invisible to the human eye, catching early-stage cancers and subtle anomalies. In radiology, AI-assisted diagnosis has reduced reading times by 30% while maintaining high accuracy levels.

Drug discovery represents another transformative application. AI models can screen millions of potential compounds in silico, dramatically reducing the time and cost of bringing new medications to market. Several AI-discovered drugs are currently in clinical trials, representing a paradigm shift in pharmaceutical research.

Personalized medicine leverages AI to analyze genetic data, medical history, and lifestyle factors to recommend optimal treatments for individual patients. This approach moves beyond one-size-fits-all protocols toward precision interventions tailored to each patient's unique biology.

Operational efficiency gains are equally significant. Predictive analytics help hospitals optimize bed allocation, reduce wait times, and prevent equipment failures. Natural language processing automates documentation tasks, allowing clinicians to focus more time on patient care rather than paperwork.

The future of AI in healthcare is bright, with continued advances in natural language understanding, multimodal learning, and federated learning enabling new applications while protecting patient privacy. Integration of AI tools into clinical workflows will become increasingly seamless, making advanced capabilities accessible to healthcare providers worldwide.
""")

        article_b = self.documents_dir / "ai_article_b.txt"
        article_b.write_text("""Challenges and Concerns in Healthcare AI Implementation

While artificial intelligence holds significant potential for healthcare, serious challenges and ethical concerns must be addressed before widespread adoption is advisable. Issues surrounding data privacy, algorithmic bias, clinical validation, and liability create substantial barriers to safe implementation.

Data privacy remains a critical concern. AI systems require vast amounts of patient data for training, raising questions about consent, data ownership, and security. High-profile breaches and unauthorized data sharing have eroded public trust. Federated learning and differential privacy offer partial solutions but complicate model development and validation.

Algorithmic bias poses serious risks to equitable healthcare delivery. AI models trained primarily on data from certain demographic groups may perform poorly for underrepresented populations, potentially exacerbating existing health disparities. Studies have revealed racial bias in algorithms used for patient prioritization and risk assessment.

Clinical validation standards for AI systems lag behind the technology's rapid advancement. Many AI tools have been deployed without rigorous prospective clinical trials demonstrating actual improvement in patient outcomes. The FDA's regulatory framework struggles to keep pace with continuously learning algorithms that evolve after initial approval.

Liability and accountability questions remain unresolved. When an AI system contributes to a diagnostic error or treatment failure, determining responsibility becomes complex. Healthcare providers may face malpractice liability for AI-assisted decisions, yet they often cannot fully understand or verify the AI's reasoning.

Overreliance on AI tools could lead to deskilling of healthcare professionals and automation bias, where clinicians defer too readily to algorithmic recommendations without critical evaluation. Maintaining human judgment and clinical expertise is essential.

Integration challenges include incompatible electronic health record systems, resistance to workflow changes, and inadequate training for healthcare staff. Many AI tools remain siloed applications rather than seamlessly integrated components of clinical care.

Moving forward requires addressing these fundamental challenges through robust regulatory frameworks, transparent algorithm development, comprehensive clinical validation, and ongoing monitoring for bias and unintended consequences. The promise of healthcare AI can only be realized through careful, ethical implementation that prioritizes patient safety and equity.
""")

        # Task 7: Multi-Level Summary - Article for multiple summary lengths
        long_article = self.documents_dir / "quantum_computing.txt"
        long_article.write_text("""The Quantum Computing Revolution: From Theory to Practice

Introduction:
Quantum computing represents one of the most significant technological frontiers of the 21st century, promising to solve computational problems that are intractable for classical computers. After decades of theoretical development and experimental research, quantum computers are transitioning from laboratory curiosities to practical tools with the potential to transform industries ranging from cryptography to drug discovery.

Fundamental Principles:
Unlike classical computers that process information in binary bits (0 or 1), quantum computers leverage quantum mechanical phenomena—superposition, entanglement, and interference—to manipulate quantum bits or qubits. Superposition allows qubits to exist in multiple states simultaneously, while entanglement creates correlations between qubits that have no classical analogue. These properties enable quantum computers to explore vast solution spaces in parallel.

Technical Challenges:
Building practical quantum computers faces formidable obstacles. Qubits are extremely fragile, susceptible to decoherence from environmental noise that destroys quantum information. Maintaining coherence requires isolating qubits at temperatures near absolute zero and implementing sophisticated error correction schemes. Current quantum computers have limited qubit counts (50-100 qubits for most systems) and high error rates compared to classical computers.

Hardware Approaches:
Multiple physical platforms compete to realize scalable quantum computers. Superconducting circuits, used by IBM and Google, leverage engineered electrical circuits operating at millikelvin temperatures. Trapped ion systems, developed by IonQ and others, use electromagnetic fields to confine individual atoms. Other approaches include topological qubits, photonic quantum computers, and neutral atom arrays, each with distinct advantages and limitations.

Algorithms and Applications:
Quantum algorithms offer exponential speedups for specific problems. Shor's algorithm can factor large numbers exponentially faster than known classical algorithms, threatening current cryptographic systems. Grover's algorithm provides quadratic speedup for database search. Quantum simulation algorithms promise to revolutionize materials science and chemistry by modeling molecular systems beyond classical computational reach.

Near-Term Applications:
Even noisy intermediate-scale quantum (NISQ) devices without full error correction show promise for practical applications. Variational quantum algorithms, which combine quantum and classical processing, are being developed for optimization problems in finance, logistics, and machine learning. Quantum machine learning algorithms may offer advantages for specific pattern recognition and classification tasks.

Quantum Advantage:
In 2019, Google claimed "quantum supremacy" by performing a specific calculation faster than the world's best supercomputers. While this milestone demonstrated quantum computational advantage, the calculation lacked practical utility. Researchers continue pursuing demonstrations of quantum advantage for industrially relevant problems.

Industry and Investment:
Major technology companies—IBM, Google, Microsoft, Amazon—have launched quantum computing initiatives and cloud platforms. Startups like Rigetti, IonQ, and PsiQuantum have attracted billions in venture capital. Governments worldwide invest heavily in quantum research, recognizing its strategic importance for national security and economic competitiveness.

Cryptography and Security:
Quantum computers pose an existential threat to widely used public-key cryptography algorithms. Organizations must begin transitioning to post-quantum cryptographic standards that resist quantum attacks. Quantum key distribution offers theoretically unbreakable encryption based on quantum mechanics, though practical deployment faces infrastructure challenges.

Timeline and Outlook:
Experts debate when fault-tolerant quantum computers capable of running arbitrarily long computations will emerge. Optimistic projections suggest 10-15 years, while skeptics note that fundamental scientific challenges may extend timelines considerably. Incremental progress continues as quantum computers grow in qubit count, coherence time, and gate fidelity.

Societal Implications:
The quantum computing revolution raises profound questions about privacy, security, and computational power concentration. Access to quantum computers could create new technological divides. International cooperation and thoughtful governance will be essential to ensure quantum technologies benefit humanity broadly.

Conclusion:
Quantum computing stands at an inflection point between research and practical application. While significant technical challenges remain, rapid progress in hardware, algorithms, and error correction suggests that quantum computers will become increasingly capable in coming decades. The technology promises to reshape computational science and unlock new frontiers in human knowledge, though realizing its full potential requires sustained research, investment, and international collaboration.
""")

        # Task 8: Q&A Generation - Article for question generation
        qa_article = self.documents_dir / "renewable_energy.txt"
        qa_article.write_text("""The Global Transition to Renewable Energy

The world is undergoing a historic energy transformation as renewable sources increasingly replace fossil fuels. Solar and wind power now represent the cheapest forms of electricity generation in most countries, driving unprecedented growth in clean energy capacity. In 2025, renewables accounted for 38% of global electricity generation, up from just 20% in 2015.

Solar energy has experienced the most dramatic cost reductions, with photovoltaic panel prices falling by 90% over the past decade. Large-scale solar farms now generate electricity at $20-30 per megawatt-hour, undercutting coal and natural gas in many markets. Distributed rooftop solar has also proliferated, with over 200 million residential installations worldwide.

Wind power contributes significantly to renewable capacity, particularly in regions with strong wind resources. Offshore wind farms, featuring turbines with 15-megawatt capacity and 250-meter rotor diameters, generate power with exceptional efficiency and minimal land use. The United States, China, and European nations have committed to massive offshore wind expansion.

Energy storage technology has progressed rapidly to address intermittency challenges inherent in solar and wind generation. Lithium-ion battery costs have declined 85% since 2015, making grid-scale storage economically viable. Newer technologies including flow batteries, compressed air storage, and green hydrogen offer solutions for longer-duration storage needs.

Grid infrastructure must evolve to accommodate distributed renewable generation and bidirectional power flows. Smart grid technologies, advanced forecasting algorithms, and demand response programs help balance supply and demand in real-time. High-voltage direct current transmission lines enable long-distance renewable energy transport from optimal generation sites to population centers.

Policy support has been instrumental in driving renewable adoption. Feed-in tariffs, renewable energy credits, carbon pricing mechanisms, and clean energy standards create market frameworks favoring renewables over fossil fuels. Over 100 countries have established net-zero emissions targets, providing long-term policy certainty for clean energy investment.

Economic implications of the energy transition are profound. The renewable energy sector employed 13 million people globally in 2025, with job growth outpacing fossil fuel industry decline. Investment in renewable energy and grid modernization exceeded $500 billion annually, reshaping capital flows and industrial structure.

Challenges remain in achieving complete decarbonization. Heavy industry sectors like steel, cement, and chemicals require high-temperature heat and process inputs difficult to electrify. Long-haul aviation and shipping face energy density constraints with current battery technology. Green hydrogen production using renewable electricity offers potential solutions but requires significant scale-up.

Developing nations face unique transition challenges, balancing energy access priorities with climate commitments. International climate finance mechanisms provide crucial support for renewable deployment in countries with limited domestic capital. Technology transfer and capacity building initiatives help accelerate clean energy adoption globally.

The renewable energy transition represents the largest infrastructure transformation in human history, requiring trillions in investment over coming decades. Success demands coordinated action among governments, businesses, and civil society to overcome technical, economic, and political obstacles. The pathway to sustainable energy is clear, though execution challenges remain formidable.
""")

        # Task 9: Sentiment Analysis Summary - Article with mixed sentiment
        sentiment_article = self.documents_dir / "social_media_impact.txt"
        sentiment_article.write_text("""Social Media's Impact on Modern Society: A Balanced Assessment

Social media platforms have fundamentally transformed human communication, connection, and information sharing over the past two decades. With over 5 billion users worldwide, these platforms shape public discourse, influence political outcomes, and affect individual well-being in complex and often contradictory ways.

Positive Impacts:
Social media has democratized content creation and information distribution, giving voice to marginalized communities and enabling grassroots movements for social change. The Arab Spring, #MeToo movement, and climate activism have leveraged social platforms to coordinate action and amplify messages that traditional media might overlook.

Global connectivity benefits individuals, families, and businesses. People maintain relationships across vast distances, reconnect with old friends, and build communities around shared interests. Small businesses access marketing channels and customer engagement tools previously available only to large corporations with substantial advertising budgets.

Educational opportunities have expanded through social learning platforms, expert knowledge sharing, and accessible tutorials. Professionals network, collaborate, and advance careers through platforms like LinkedIn. Entrepreneurs bootstrap ventures using social media for customer acquisition and brand building at minimal cost.

Negative Consequences:
Mental health concerns associated with social media use have mounted. Research links excessive usage to increased rates of anxiety, depression, and loneliness, particularly among adolescents. The comparison culture fostered by curated feeds and highlight reels damages self-esteem and life satisfaction. Cyberbullying and online harassment create hostile environments that harm vulnerable users.

Misinformation and disinformation spread rapidly through social networks, undermining informed decision-making and eroding trust in institutions. Algorithmic amplification of sensational content prioritizes engagement over accuracy, creating filter bubbles and echo chambers that reinforce existing beliefs while limiting exposure to diverse perspectives.

Privacy erosion and data exploitation practices raise serious ethical questions. Platforms collect vast amounts of personal data to fuel targeted advertising, often without meaningful user consent or understanding. Data breaches expose sensitive information, while surveillance concerns grow as platforms cooperate with government requests.

Addiction by design features—infinite scrolling, push notifications, and variable reward schedules—exploit psychological vulnerabilities to maximize user engagement and screen time. This attention economy model extracts value from user attention at potential cost to productivity, relationships, and well-being.

Polarization and Social Division:
Social media algorithms optimize for engagement rather than constructive dialogue, amplifying divisive content and extreme viewpoints. Online discourse often devolves into hostility, making nuanced conversation difficult. Political polarization has intensified as people self-sort into ideologically homogeneous groups and consume information confirming their preexisting views.

Platform Responsibility:
Technology companies face mounting pressure to address harmful content, protect user privacy, and mitigate societal harms. Content moderation at scale presents enormous challenges, balancing free expression with safety. Regulatory proposals ranging from antitrust enforcement to algorithmic transparency requirements aim to increase accountability.

The Path Forward:
Realizing social media's benefits while mitigating harms requires multi-stakeholder efforts. Platform design changes prioritizing user well-being over engagement metrics could reduce addictive features. Digital literacy education helps users critically evaluate information and develop healthy usage habits. Regulatory frameworks may be necessary to protect privacy, limit manipulation, and ensure algorithmic accountability.

Individual agency matters too. Users can curate feeds mindfully, limit screen time, verify information before sharing, and engage constructively rather than reactively. Recognizing social media as a tool—neither inherently good nor bad—empowers more intentional usage aligned with personal values and goals.

Conclusion:
Social media represents a powerful technology with significant positive and negative impacts on individuals and society. Its ultimate effect depends on how we collectively choose to design, regulate, and use these platforms. Moving forward requires honest assessment of tradeoffs, evidence-based policy, responsible corporate stewardship, and individual mindfulness to create digital environments that enhance rather than diminish human flourishing.
""")

        return {
            "workspace_dir": str(self.workspace_dir),
            "documents_dir": str(self.documents_dir),
            "business_article": str(business_article),
            "technical_doc": str(technical_doc),
            "article_a": str(article_a),
            "article_b": str(article_b),
            "long_article": str(long_article),
            "qa_article": str(qa_article),
            "sentiment_article": str(sentiment_article),
        }

    def cleanup_workspace(self) -> bool:
        """Remove test workspace.

        Returns:
            True if cleanup succeeded
        """
        import shutil
        try:
            if self.workspace_dir.exists():
                shutil.rmtree(self.workspace_dir)
            return True
        except Exception as e:
            print(f"Cleanup error: {e}")
            return False
