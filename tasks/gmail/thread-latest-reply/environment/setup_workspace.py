#!/usr/bin/env python3
"""Setup workspace for thread-latest-reply task.
Creates /workspace/thread.txt with a 4-message email thread.
The last message is from Marcus Webb with decision: "Let's go with Option B".
"""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

thread_content = """\
From: Alice Johnson <alice@example.com>
To: Design Team <design@company.com>
Subject: Homepage Redesign - Decision Needed
Date: Mon, 16 Mar 2026 09:00:00 +0000
Status: read

Hi team,

We need to decide on the homepage redesign direction by end of week. I have prepared two options:

Option A: Minimalist design with a large hero image and single call-to-action button.
Option B: Dynamic layout with featured content grid and multiple entry points.

Please review the mockups in the shared drive and share your thoughts.

Alice

---

From: Priya Patel <priya.patel@company.com>
To: Design Team <design@company.com>
Subject: Re: Homepage Redesign - Decision Needed
Date: Mon, 16 Mar 2026 11:30:00 +0000
Status: read

Hi Alice,

I reviewed both mockups. I prefer Option B because it gives us more flexibility to highlight different content. Our analytics show users engage more when there are multiple content pathways.

That said, Option A is cleaner and may convert better for first-time visitors.

Happy to go with whatever the team decides.

Priya

---

From: David Lee <david.lee@company.com>
To: Design Team <design@company.com>
Subject: Re: Homepage Redesign - Decision Needed
Date: Tue, 17 Mar 2026 08:45:00 +0000
Status: read

Team,

From an engineering perspective, both are feasible within the current sprint. Option A would take about 3 days, Option B closer to 5. If timeline is a factor, Option A is safer.

I am slightly leaning toward Option B for the long-term content strategy benefits.

David

---

From: Marcus Webb <marcus.webb@company.com>
To: Design Team <design@company.com>
Subject: Re: Homepage Redesign - Decision Needed
Date: Tue, 17 Mar 2026 15:00:00 +0000
Status: unread

Hi everyone,

Thanks for the thoughtful input. After reviewing the mockups and considering the team's feedback, I have made a decision.

Let's go with Option B. The dynamic layout aligns better with our Q2 content strategy, and David's estimate of 5 days is acceptable given the added flexibility. Alice, please proceed with the detailed design specs.

I will update the project board and notify stakeholders today.

Marcus Webb
Head of Product Design
"""

with open(os.path.join(workspace, "thread.txt"), "w") as f:
    f.write(thread_content)

print(f"Workspace ready: {workspace}")
