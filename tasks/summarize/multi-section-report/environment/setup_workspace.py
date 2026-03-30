#!/usr/bin/env python3
"""Setup workspace for multi-section-report task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

report = """\
NovaTech Ltd — Q1 2026 Quarterly Business Report
Period: January 1, 2026 – March 31, 2026
Prepared by: Finance & Operations Division
Approved by: CEO, Rachel Ng

EXECUTIVE SUMMARY
-----------------
NovaTech Ltd concluded Q1 2026 with strong financial and operational results, surpassing
internal targets across most key performance indicators. Revenue growth continued to
accelerate, and strategic expansion into the Asia-Pacific region is progressing ahead
of schedule.

FINANCIAL PERFORMANCE
---------------------
Total revenue for Q1 2026 reached $4.2 million, representing an 18% increase year-over-year
compared to Q1 2025 ($3.56 million). This growth was driven primarily by a 24% increase in
SaaS subscription renewals and a 12% uplift in professional services engagements.

Gross margin improved to 67%, up from 63% in Q1 2025, as a result of ongoing infrastructure
cost optimization and the full-year effect of the 2025 data center migration.

Operating expenses totalled $2.1 million, a 9% increase year-over-year, reflecting planned
investments in sales headcount and product development. EBITDA for the quarter was $1.3
million, a 31% improvement over Q1 2025.

OPERATIONAL HIGHLIGHTS
----------------------
NovaTech Ltd hired 23 new employees during Q1 2026, bringing total headcount to 187. The
majority of new hires joined the Engineering and Customer Success teams. Staff retention
rate remained high at 94%, above the industry average of 88%.

The company achieved SOC 2 Type II certification in February 2026, a milestone that
has already contributed to three new enterprise contract wins.

EXPANSION: SINGAPORE OFFICE
----------------------------
Construction of the Singapore office is proceeding on schedule, with an expected opening
date of June 1, 2026. The Singapore office will serve as NovaTech's regional headquarters
for Asia-Pacific operations, covering clients in Singapore, Malaysia, Indonesia, and
Australia. Initial headcount at the Singapore location is expected to be 15 employees,
growing to 40 by end of 2026.

This expansion is supported by a strategic partnership with local firm Meridian Advisors,
who will provide regulatory compliance support across the target markets.

OUTLOOK
-------
Q2 2026 guidance: Revenue in the range of $4.5–4.8 million. NovaTech expects continued
margin expansion as Singapore operations ramp up and the new enterprise contracts begin
contributing. The company remains on track to achieve its full-year 2026 target of $18
million in revenue.
"""

with open(os.path.join(workspace, "report.txt"), "w") as f:
    f.write(report)

print(f"Workspace ready: {workspace}")
