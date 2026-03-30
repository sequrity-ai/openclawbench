#!/usr/bin/env python3
"""Setup workspace for short-article-summary task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

article = """\
Tech Giant Acme Corp Launches CloudSync Pro at Competitive Price Point

SAN FRANCISCO, March 15, 2026 — Acme Corp, the enterprise software leader based in San Francisco,
officially unveiled CloudSync Pro today, its next-generation cloud storage and synchronization
platform designed for small and medium-sized businesses. The product launches at a subscription
price of $29/month per user, positioning it well below many comparable enterprise solutions.

CloudSync Pro promises seamless integration with existing productivity suites, including popular
office applications and communication tools. According to Acme Corp's Chief Product Officer,
Maria Chen, the platform was built from the ground up with security and reliability in mind.
"We spent three years listening to our customers and building exactly what they needed," Chen
said during the product launch event held at Acme Corp's downtown headquarters.

The platform supports real-time collaboration across teams in up to 50 countries, with automatic
version control and conflict resolution built in. Early beta testers praised the intuitive
interface and the speed of file syncing, with latency reportedly under 200 milliseconds for
most operations.

Acme Corp plans to offer a 30-day free trial starting March 22, 2026. The company expects to
onboard over 10,000 business customers within the first quarter of launch. Analysts from
TechWatch Research called the pricing strategy "aggressive but sustainable," noting that
Acme Corp's infrastructure costs have dropped significantly following its data center
consolidation in late 2025.

The CloudSync Pro launch marks a significant milestone for Acme Corp, which previously focused
almost exclusively on enterprise clients. This move into the SMB market represents a strategic
pivot that shareholders have anticipated since the company's annual report last October.
"""

with open(os.path.join(workspace, "article.txt"), "w") as f:
    f.write(article)

print(f"Workspace ready: {workspace}")
