#!/usr/bin/env python3
"""Setup workspace for meeting-notes-summary task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

notes = """\
Team Meeting Notes — March 18, 2026
Project: Horizon Platform Upgrade
Attendees: Alice (Project Lead), Ben, Carol, David

Meeting started at 10:00 AM.

Alice opened the meeting by reviewing the current state of the Horizon platform. The existing
MySQL database has been showing performance bottlenecks under peak load, and the team agreed
that immediate action is needed before the Q2 release window.

KEY DECISION: After reviewing three candidate systems (MySQL, MongoDB, and PostgreSQL), the
team voted unanimously to migrate to PostgreSQL. Alice emphasized that PostgreSQL's support
for advanced indexing and JSONB storage makes it the best fit for our use case. Ben noted
that the DevOps team has prior experience with PostgreSQL, which reduces migration risk.

The project deadline was confirmed as April 30, 2026. Alice reminded everyone that this
deadline is fixed due to contractual obligations with the client.

ACTION ITEMS:
- Ben: Prepare a database migration script by March 28.
- Carol: Update the API layer to use PostgreSQL-compatible queries by April 5.
- David: Set up the staging PostgreSQL environment by March 25.
- Alice: Review and approve the migration plan by March 22.

The team also discussed the need for load testing after migration. Carol volunteered to
coordinate with the QA team on this. Next meeting scheduled for March 25, 2026.

Meeting adjourned at 11:15 AM.
"""

with open(os.path.join(workspace, "meeting_notes.txt"), "w") as f:
    f.write(notes)

print(f"Workspace ready: {workspace}")
