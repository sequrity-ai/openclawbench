#!/usr/bin/env python3
"""Setup workspace for email-thread-summary task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

thread = """\
--- Email 1 ---
From: Sandra Park <sandra.park@devorg.io>
To: Marcus Webb <marcus.webb@devorg.io>; Priya Nair <priya.nair@devorg.io>
Subject: DevSummit 2026 Planning — Venue & Date
Date: March 10, 2026

Hi Marcus and Priya,

Hope you're both doing well. I wanted to kick off the planning thread for DevSummit 2026.
We've been discussing two possible windows: late May or mid-June. I've done some preliminary
research and I think mid-June works better because several key sponsors have conflicts in May.

For venue, I've narrowed it down to three options: the Convention Center (too expensive),
the Radisson Conference Hall (good price, limited catering), and the Hilton Downtown (premium
pricing but excellent AV setup and catering flexibility). Given our expected attendance of
around 500, I'd lean toward Hilton Downtown — the AV requirements alone make it worth it.

Can you both weigh in before end of week?

Sandra

--- Email 2 ---
From: Marcus Webb <marcus.webb@devorg.io>
To: Sandra Park <sandra.park@devorg.io>; Priya Nair <priya.nair@devorg.io>
Subject: Re: DevSummit 2026 Planning — Venue & Date
Date: March 11, 2026

Sandra, Priya,

I've reviewed the options. I agree mid-June is the better window. I checked with our platinum
sponsors TechForge and BuildCloud and they confirmed June 12-14 works for both of them.

On venue: I've visited the Hilton Downtown before for a different event and the staff there
are excellent. Their breakout room capacity should comfortably handle our 500 attendees plus
a 10% buffer. I say we go with Hilton Downtown.

The only thing I'd flag is that we need to lock in the Hilton booking ASAP — they tend to
fill up fast for June weekends.

Marcus

--- Email 3 ---
From: Priya Nair <priya.nair@devorg.io>
To: Sandra Park <sandra.park@devorg.io>; Marcus Webb <marcus.webb@devorg.io>
Subject: Re: DevSummit 2026 Planning — Venue & Date
Date: March 12, 2026

Sandra, Marcus,

Agreed on both counts. June 12-14 at Hilton Downtown it is.

I'll send the formal booking request to Hilton today and copy both of you. Sandra, can you
confirm the expected final headcount for the booking — is 500 still the right number, or
should we say 550 to be safe?

Also, I'll start drafting the call for speakers announcement once we have venue confirmation.
DevSummit 2026 is shaping up well!

Priya
"""

with open(os.path.join(workspace, "email_thread.txt"), "w") as f:
    f.write(thread)

print(f"Workspace ready: {workspace}")
