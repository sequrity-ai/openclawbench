#!/usr/bin/env python3
"""Setup workspace for filter-by-sender task.
Creates /workspace/inbox.txt with 10 emails, exactly 3 from notifications@github.com.
"""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

inbox_content = """\
From: Alice Johnson <alice@example.com>
To: Bob Smith <bob@example.com>
Subject: Lunch Plans Friday
Date: Mon, 16 Mar 2026 09:00:00 +0000
Status: read

Hi Bob, are you free for lunch on Friday?

---

From: notifications@github.com
To: Bob Smith <bob@example.com>
Subject: [company/backend] Pull request #87 merged by alee
Date: Mon, 16 Mar 2026 10:30:00 +0000
Status: read

alee merged pull request #87: Fix database connection pooling in company/backend.

---

From: HR Team <hr@company.com>
To: Bob Smith <bob@example.com>
Subject: Benefits Enrollment Deadline - March 28
Date: Mon, 16 Mar 2026 11:00:00 +0000
Status: unread

Please complete your benefits enrollment by March 28, 2026.

---

From: notifications@github.com
To: Bob Smith <bob@example.com>
Subject: [company/frontend] Issue #203 assigned to you
Date: Tue, 17 Mar 2026 08:45:00 +0000
Status: unread

Issue #203 "Responsive layout breaks on mobile" has been assigned to you in company/frontend.

---

From: David Lee <david.lee@company.com>
To: Bob Smith <bob@example.com>
Subject: Architecture Review Notes
Date: Tue, 17 Mar 2026 13:00:00 +0000
Status: read

Bob, attached are the notes from today's architecture review session.

---

From: Marketing <marketing@company.com>
To: Bob Smith <bob@example.com>
Subject: Q1 Campaign Results - Record Numbers!
Date: Tue, 17 Mar 2026 15:30:00 +0000
Status: read

The Q1 marketing campaign exceeded all targets. Full report attached.

---

From: notifications@github.com
To: Bob Smith <bob@example.com>
Subject: [company/backend] New comment on your pull request #91
Date: Wed, 18 Mar 2026 09:15:00 +0000
Status: unread

carol.white commented on your pull request #91: "LGTM but please add unit tests for edge cases."

---

From: Finance <finance@company.com>
To: Bob Smith <bob@example.com>
Subject: Q1 Expense Summary Available
Date: Wed, 18 Mar 2026 10:00:00 +0000
Status: read

Your Q1 expense summary is now available in the finance portal.

---

From: IT Support <itsupport@company.com>
To: Bob Smith <bob@example.com>
Subject: VPN Client Update Required
Date: Thu, 19 Mar 2026 08:00:00 +0000
Status: unread

Please update your VPN client to version 4.2.1 by March 25.

---

From: Rachel Kim <rachel.kim@company.com>
To: Bob Smith <bob@example.com>
Subject: Re: Q2 Roadmap Discussion
Date: Thu, 19 Mar 2026 16:00:00 +0000
Status: read

Thanks for the input, Bob. I will incorporate your suggestions into the roadmap draft.
"""

with open(os.path.join(workspace, "inbox.txt"), "w") as f:
    f.write(inbox_content)

print(f"Workspace ready: {workspace}")
