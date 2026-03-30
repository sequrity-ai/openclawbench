#!/usr/bin/env python3
"""Setup workspace for extract-all-attachments task.
Creates /workspace/inbox.txt with 6 emails, 3 with Attachments headers.
Unique attachments: report.pdf, budget_2026.xlsx, logo.png, presentation.pptx
"""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

inbox_content = """\
From: Alice Johnson <alice@example.com>
To: Bob Smith <bob@example.com>
Subject: Q1 Financial Summary
Date: Mon, 16 Mar 2026 09:00:00 +0000
Status: read
Attachments: report.pdf, budget_2026.xlsx

Hi Bob,

Please find the Q1 financial summary documents attached. The report covers all business units and includes the updated budget projections for 2026.

Let me know if you have questions.

Alice

---

From: IT Support <itsupport@company.com>
To: Bob Smith <bob@example.com>
Subject: VPN Configuration Update
Date: Mon, 16 Mar 2026 11:00:00 +0000
Status: read

Hi Bob,

Please update your VPN configuration using the instructions in this email. No attachments needed — just follow the steps below.

Step 1: Open VPN client settings
Step 2: Update server address to vpn2.company.com
Step 3: Reconnect

IT Support

---

From: Marketing Team <marketing@company.com>
To: Bob Smith <bob@example.com>
Subject: Brand Assets for Q2 Campaign
Date: Tue, 17 Mar 2026 08:30:00 +0000
Status: unread
Attachments: logo.png, presentation.pptx

Hi Bob,

Attached are the updated brand assets for the Q2 campaign. Please use the new logo in all external communications starting April 1.

The presentation template has also been updated with the new brand guidelines.

Best,
Marketing Team

---

From: David Lee <david.lee@company.com>
To: Bob Smith <bob@example.com>
Subject: Sprint Planning Notes
Date: Tue, 17 Mar 2026 14:00:00 +0000
Status: unread

Bob,

Quick summary of today's sprint planning:

- Sprint 22 runs March 18 - April 1
- Priority: payment module refactoring (tickets PX-2215 through PX-2220)
- Capacity: 34 story points

David

---

From: Rachel Kim <rachel.kim@company.com>
To: Bob Smith <bob@example.com>
Subject: Offsite Agenda
Date: Wed, 18 Mar 2026 09:00:00 +0000
Status: read

Hi Bob,

Looking forward to the offsite next week! I will send the agenda and logistics separately.

Rachel

---

From: Finance <finance@company.com>
To: Bob Smith <bob@example.com>
Subject: Year-End Tax Documents
Date: Wed, 18 Mar 2026 10:30:00 +0000
Status: read

Hi Bob,

Your year-end tax documents are ready. Please log in to the employee portal to download them directly.

Finance Team
"""

with open(os.path.join(workspace, "inbox.txt"), "w") as f:
    f.write(inbox_content)

print(f"Workspace ready: {workspace}")
