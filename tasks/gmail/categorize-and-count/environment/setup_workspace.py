#!/usr/bin/env python3
"""Setup workspace for categorize-and-count task.
Creates /workspace/inbox.txt with 12 emails:
  4 billing/invoices, 3 meeting invites, 5 project updates.
No Category header - inferred from content.
"""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

inbox_content = """\
From: Accounts Payable <ap@vendor.com>
To: Bob Smith <bob@example.com>
Subject: Invoice #1101 - February Services
Date: Mon, 2 Mar 2026 09:00:00 +0000
Status: read

Dear Bob,

Please find enclosed Invoice #1101 for services rendered in February 2026. Amount due: $2,100.00. Payment terms: net 30.

Best regards,
Accounts Payable

---

From: Rachel Kim <rachel.kim@company.com>
To: Product Team <product-team@company.com>
Subject: Q2 Planning Meeting - Tuesday 10 AM UTC
Date: Mon, 2 Mar 2026 10:00:00 +0000
Status: read

Hi everyone,

Please join our Q2 planning meeting on Tuesday at 10 AM UTC via Zoom. Agenda: roadmap review and sprint assignments.

Rachel

---

From: Jake Torres <jake.torres@company.com>
To: Engineering <engineering@company.com>
Subject: Project Phoenix - Backend API Progress Update
Date: Mon, 2 Mar 2026 14:00:00 +0000
Status: read

Team,

Week 3 update for Project Phoenix: The backend API is 80% complete. Authentication module is done. Payment integration is in progress.

Jake

---

From: Finance <finance@company.com>
To: Bob Smith <bob@example.com>
Subject: Your Invoice #1187 is overdue - Please remit payment
Date: Tue, 3 Mar 2026 08:30:00 +0000
Status: unread

Dear Bob,

Invoice #1187 for $875.00 is now 15 days overdue. Please arrange payment at your earliest convenience to avoid a late fee.

Finance Department

---

From: Alice Johnson <alice@example.com>
To: Design Team <design@company.com>
Subject: Homepage Redesign Project - Kickoff Notes
Date: Tue, 3 Mar 2026 09:30:00 +0000
Status: read

Hi team,

Attaching the kickoff notes from our homepage redesign project. Key decisions: we will use Option B layout and target a May 1 launch.

Alice

---

From: HR Team <hr@company.com>
To: All Staff <all@company.com>
Subject: Town Hall Meeting Invite - March 20 at 3 PM UTC
Date: Tue, 3 Mar 2026 11:00:00 +0000
Status: read

You are invited to the All-Hands Town Hall on March 20 at 3 PM UTC. The agenda includes Q1 results, org updates, and open Q&A. Zoom link will follow.

HR Team

---

From: Priya Patel <priya.patel@company.com>
To: Launch Team <launch-team@company.com>
Subject: Product Launch Campaign - Status Update Week 1
Date: Wed, 4 Mar 2026 08:00:00 +0000
Status: read

Hi everyone,

Week 1 status for the product launch campaign: Landing page draft complete. PR briefing deck in review. Analytics setup begins next week.

Priya

---

From: Billing System <billing@saas-tool.com>
To: Bob Smith <bob@example.com>
Subject: Your subscription invoice for March - $149.00
Date: Wed, 4 Mar 2026 09:00:00 +0000
Status: read

Hi Bob,

Your monthly subscription invoice for March has been generated. Amount: $149.00. This will be charged to the card on file on March 10.

SaaS Tool Billing

---

From: David Lee <david.lee@company.com>
To: Engineering <engineering@company.com>
Subject: Mobile App Refactor - Sprint 5 Progress
Date: Thu, 5 Mar 2026 10:00:00 +0000
Status: unread

Team,

Sprint 5 update for the mobile app refactor: navigation redesign merged, 3 bugs fixed, 2 remaining. On track for April release.

David

---

From: Tom Nakamura <tom.nakamura@company.com>
To: Analytics Team <analytics@company.com>
Subject: Dashboard Migration Project - Milestone 2 Complete
Date: Thu, 5 Mar 2026 13:00:00 +0000
Status: read

Hi team,

Milestone 2 of the dashboard migration project is complete. All historical data has been successfully migrated to the new platform.

Tom

---

From: Marcus Webb <marcus.webb@company.com>
To: Design Team <design@company.com>
Subject: 1:1 Meeting Reschedule - New Time: Friday 2 PM UTC
Date: Fri, 6 Mar 2026 09:00:00 +0000
Status: unread

Hi,

Our 1:1 meeting has been rescheduled to Friday at 2 PM UTC. Same Zoom link as before. Looking forward to our discussion.

Marcus

---

From: Accounts Payable <ap@contractor.com>
To: Bob Smith <bob@example.com>
Subject: Contractor Invoice #2034 - March Retainer Fee
Date: Fri, 6 Mar 2026 10:30:00 +0000
Status: unread

Dear Bob,

Please find Invoice #2034 for the March retainer fee of $4,500.00. Kindly process payment by March 15.

Best regards,
Contractor Services
"""

with open(os.path.join(workspace, "inbox.txt"), "w") as f:
    f.write(inbox_content)

print(f"Workspace ready: {workspace}")
