#!/usr/bin/env python3
"""Setup workspace for count-unread task.
Creates /workspace/inbox.txt with 8 emails, exactly 3 unread.
"""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

inbox_content = """\
From: Alice Johnson <alice@example.com>
To: Bob Smith <bob@example.com>
Subject: Q1 Budget Review
Date: Mon, 15 Mar 2026 09:30:00 +0000
Status: read

Hi Bob,

Please find attached the Q1 budget review for your approval. Let me know if you have any questions.

Best,
Alice

---

From: David Lee <david.lee@company.com>
To: Bob Smith <bob@example.com>
Subject: Re: Project Phoenix Timeline
Date: Mon, 15 Mar 2026 10:45:00 +0000
Status: unread

Bob,

The timeline looks good to me. I will reach out to the team leads to confirm availability.

Regards,
David

---

From: notifications@github.com
To: Bob Smith <bob@example.com>
Subject: [company/api] Pull request #42 opened by jsmith
Date: Mon, 15 Mar 2026 11:00:00 +0000
Status: read

jsmith opened pull request #42 in company/api.

---

From: HR Team <hr@company.com>
To: Bob Smith <bob@example.com>
Subject: Upcoming Performance Reviews - Action Required
Date: Tue, 16 Mar 2026 08:00:00 +0000
Status: unread

Dear Bob,

Performance review season is approaching. Please complete your self-assessment by March 25, 2026.

Best regards,
HR Team

---

From: Carol White <carol.white@partner.org>
To: Bob Smith <bob@example.com>
Subject: Partnership Agreement Draft
Date: Tue, 16 Mar 2026 09:15:00 +0000
Status: read

Bob,

I have sent over the revised partnership agreement draft. Please review sections 3 and 7.

Thanks,
Carol

---

From: IT Support <itsupport@company.com>
To: Bob Smith <bob@example.com>
Subject: Scheduled Maintenance Window - March 20
Date: Tue, 16 Mar 2026 12:00:00 +0000
Status: read

Please be aware that scheduled maintenance will occur on March 20 from 2:00 AM to 4:00 AM UTC.

---

From: Marketing Team <marketing@company.com>
To: Bob Smith <bob@example.com>
Subject: New Brand Guidelines Released
Date: Wed, 17 Mar 2026 08:30:00 +0000
Status: read

Hi Team,

The updated brand guidelines are now available on the intranet. Please review before your next customer-facing presentation.

---

From: Finance <finance@company.com>
To: Bob Smith <bob@example.com>
Subject: Expense Report Reminder
Date: Wed, 17 Mar 2026 14:00:00 +0000
Status: unread

Hi Bob,

This is a reminder to submit your February expense report by end of day Friday.

Thanks,
Finance Team
"""

with open(os.path.join(workspace, "inbox.txt"), "w") as f:
    f.write(inbox_content)

print(f"Workspace ready: {workspace}")
