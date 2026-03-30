#!/usr/bin/env python3
"""Setup workspace for find-subject task.
Creates /workspace/emails/ with 5 email files, one containing Invoice #4472.
"""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
emails_dir = os.path.join(workspace, "emails")
os.makedirs(emails_dir, exist_ok=True)

emails = [
    (
        "email_001.txt",
        """\
From: HR Team <hr@company.com>
To: All Staff <all@company.com>
Subject: Updated Remote Work Policy - Effective April 1
Date: Mon, 9 Mar 2026 08:00:00 +0000
Status: read

Dear Team,

Please review the updated remote work policy attached to this email. The new guidelines take effect on April 1, 2026.

Regards,
HR Team
""",
    ),
    (
        "email_002.txt",
        """\
From: Accounts Payable <ap@vendor.com>
To: Bob Smith <bob@example.com>
Subject: Invoice #4472 - March Services
Date: Mon, 9 Mar 2026 10:15:00 +0000
Status: unread

Dear Bob,

Please find enclosed Invoice #4472 for services rendered in March 2026. The total amount due is $3,450.00. Payment is due within 30 days.

Best regards,
Accounts Payable
Vendor Solutions Ltd.
""",
    ),
    (
        "email_003.txt",
        """\
From: IT Security <security@company.com>
To: Bob Smith <bob@example.com>
Subject: Security Training Completion Required by March 31
Date: Tue, 10 Mar 2026 09:00:00 +0000
Status: read

Hi Bob,

Your annual security awareness training must be completed by March 31, 2026. Please log in to the training portal at your earliest convenience.

Thanks,
IT Security
""",
    ),
    (
        "email_004.txt",
        """\
From: Alice Johnson <alice@example.com>
To: Bob Smith <bob@example.com>
Subject: Lunch Meeting Tomorrow at Noon
Date: Tue, 10 Mar 2026 14:30:00 +0000
Status: read

Hi Bob,

Just confirming our lunch meeting tomorrow at noon at the usual place. Looking forward to catching up!

Best,
Alice
""",
    ),
    (
        "email_005.txt",
        """\
From: Newsletter <newsletter@techdigest.io>
To: Bob Smith <bob@example.com>
Subject: Tech Digest Weekly - Top Stories in Cloud Computing
Date: Wed, 11 Mar 2026 07:00:00 +0000
Status: read

This week's top stories in cloud computing:
- Kubernetes 2.0 release candidate announced
- AWS launches new region in Southeast Asia
- Security vulnerabilities patched in popular container runtime

Read more at techdigest.io
""",
    ),
]

for filename, content in emails:
    with open(os.path.join(emails_dir, filename), "w") as f:
        f.write(content)

print(f"Workspace ready: {workspace}")
