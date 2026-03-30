#!/usr/bin/env python3
"""Setup workspace for summarize-thread-action-items task.
Creates /workspace/thread.txt with a 5-message product launch thread.
Action items: Jake (April 15), Priya (April 12), Tom (April 18).
"""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

thread_content = """\
From: Rachel Kim <rachel.kim@company.com>
To: Launch Team <launch-team@company.com>
Subject: Product Launch - Coordination Kickoff
Date: Mon, 16 Mar 2026 09:00:00 +0000
Status: read

Hi everyone,

We are T-minus 4 weeks from the product launch. I am kicking off the coordination thread to assign tasks and track progress.

Here is what we need to get done before the April 28 launch:
1. Landing page finalized
2. PR and media outreach coordinated
3. Analytics and tracking verified
4. Support team briefed
5. Final QA sign-off

I will assign owners in this thread. Please confirm your availability and deadlines.

Rachel

---

From: Jake Torres <jake.torres@company.com>
To: Launch Team <launch-team@company.com>
Subject: Re: Product Launch - Coordination Kickoff
Date: Mon, 16 Mar 2026 11:00:00 +0000
Status: read

Hi Rachel,

I will take ownership of the landing page. I have already started the initial draft and need to incorporate the final copy from marketing.

Action item: Jake will finalize the landing page by April 15.

I will share the staging link for review once the copy is in.

Jake

---

From: Priya Patel <priya.patel@company.com>
To: Launch Team <launch-team@company.com>
Subject: Re: Product Launch - Coordination Kickoff
Date: Tue, 17 Mar 2026 08:30:00 +0000
Status: read

Team,

I can handle the PR and media coordination. I have existing relationships with the key tech journalists and will prepare an embargo briefing package.

Action item: Priya will coordinate with the PR team by April 12.

This gives us two weeks before launch for any press follow-ups.

Priya

---

From: Tom Nakamura <tom.nakamura@company.com>
To: Launch Team <launch-team@company.com>
Subject: Re: Product Launch - Coordination Kickoff
Date: Tue, 17 Mar 2026 14:00:00 +0000
Status: read

Hi Rachel and team,

I will own the analytics setup. We need to configure conversion tracking, funnel events, and the launch dashboard.

Action item: Tom will set up the analytics dashboard by April 18.

I will send a tracking spec for review by end of this week so Jake can make sure the landing page tags are in place.

Tom

---

From: Rachel Kim <rachel.kim@company.com>
To: Launch Team <launch-team@company.com>
Subject: Re: Product Launch - Coordination Kickoff
Date: Wed, 18 Mar 2026 09:00:00 +0000
Status: unread

Great — thank you all for the quick responses.

Summary of action items:
- Jake: landing page finalized by April 15
- Priya: PR team coordinated by April 12
- Tom: analytics dashboard live by April 18

I will follow up with support team briefing and QA sign-off separately. Next sync is Friday at 10 AM UTC.

Rachel
"""

with open(os.path.join(workspace, "thread.txt"), "w") as f:
    f.write(thread_content)

print(f"Workspace ready: {workspace}")
