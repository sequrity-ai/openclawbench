#!/usr/bin/env python3
"""Setup workspace for extract-meeting-details task.
Creates /workspace/meeting_invite.txt with a calendar invite email.
"""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

meeting_content = """\
From: Rachel Kim <rachel.kim@company.com>
To: Product Team <product-team@company.com>
Subject: Team Sync - Q2 Planning
Date: Mon, 23 Mar 2026 08:00:00 +0000
Status: unread

Hi everyone,

You are invited to the Team Sync - Q2 Planning session. Please see the details below:

Meeting Date & Time: Wednesday, April 8, 2026 at 2:00 PM UTC
Duration: 90 minutes
Location: Zoom: https://zoom.us/j/123456789

Attendees:
- Rachel Kim (Organizer)
- Bob Smith
- Alice Johnson
- David Lee
- Priya Patel
- Marcus Webb

Agenda:
1. Q1 retrospective highlights (15 min)
2. Q2 OKR review and alignment (30 min)
3. Roadmap prioritization exercise (30 min)
4. Open discussion and next steps (15 min)

Please come prepared with your team's Q1 accomplishments and top priorities for Q2.

A calendar invitation has been sent separately. Please accept or decline by April 2.

Best,
Rachel Kim
Senior Product Manager
"""

with open(os.path.join(workspace, "meeting_invite.txt"), "w") as f:
    f.write(meeting_content)

print(f"Workspace ready: {workspace}")
