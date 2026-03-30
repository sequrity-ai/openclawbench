#!/usr/bin/env python3
"""Setup workspace for extract-sender task.
Creates /workspace/email.txt with a single email from Dr. Sarah Chen.
"""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

email_content = """\
From: Dr. Sarah Chen <sarah.chen@techcorp.io>
To: Engineering Team <engineering@techcorp.io>
Subject: Project Phoenix Update
Date: Thu, 19 Mar 2026 14:22:00 +0000
Status: unread

Hi Team,

I wanted to share a quick update on Project Phoenix. We have completed the initial architecture review and the results are very promising. The new microservices design should reduce our API response times by approximately 40%.

Key milestones this week:
- Completed load testing on the staging environment
- Resolved the authentication token expiry bug (ticket #PX-2214)
- Onboarded two new contractors to the backend team

Next steps:
1. Final code review for the payment module (due March 22)
2. Security audit scheduled for March 25
3. Production deployment window: March 28-29

Please let me know if you have any blockers. I will hold office hours on Friday from 3-5 PM UTC for anyone who wants to discuss.

Best regards,
Dr. Sarah Chen
Principal Engineer, Platform Services
TechCorp Inc.
"""

with open(os.path.join(workspace, "email.txt"), "w") as f:
    f.write(email_content)

print(f"Workspace ready: {workspace}")
