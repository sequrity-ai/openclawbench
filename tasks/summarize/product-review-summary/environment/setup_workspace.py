#!/usr/bin/env python3
"""Setup workspace for product-review-summary task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

review = """\
Product Review: BlueAir X500 Air Purifier
Rating: 4/5 stars
Reviewed by: James T.
Date: February 28, 2026

I've been using the BlueAir X500 in my home office for about three months now, and overall I'm
very impressed with its performance. Here's my detailed breakdown:

PROS:

Quiet Operation: This is genuinely one of the quietest air purifiers I've ever used. Even on
medium speed, you can barely hear it running. I work from home and I can have it running all
day during video calls without any background noise issues. Compared to my previous purifier,
the BlueAir X500 is dramatically quieter.

Excellent Filter Life: The manufacturer claims filters last 6 months, but according to the app
monitoring, mine is on track for 8+ months at my typical usage. Replacement filters cost around
$40, making the ongoing cost very manageable.

Air Quality: The built-in air quality sensor is accurate and responsive. When I cook something
strong in the kitchen (my office is adjacent), the unit ramps up automatically and clears the
air noticeably faster than I expected for its size class.

CONS:

High Initial Cost: At $349 retail, the BlueAir X500 is not cheap. Comparable purifiers from
competitors cover similar square footage for $200-$250. If you're on a budget, this is a hard
pill to swallow, even though the long-term filter savings partially offset the premium.

App Reliability: The companion mobile app occasionally loses connection to the device and
requires a restart. This has happened maybe 5-6 times over three months — not a dealbreaker,
but worth noting.

VERDICT: If quiet operation and excellent filter life are your priorities and cost is not a
primary concern, the BlueAir X500 is an outstanding air purifier. I'd recommend it to anyone
who can absorb the upfront price.
"""

with open(os.path.join(workspace, "review.txt"), "w") as f:
    f.write(review)

print(f"Workspace ready: {workspace}")
