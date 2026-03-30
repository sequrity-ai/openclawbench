#!/usr/bin/env python3
"""Setup workspace for extract-action-items task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

brief = """\
Project Brief: Nexus Platform v2 Launch
Project Code: NPL-2026
Document Version: 1.4
Date: March 17, 2026
Project Sponsor: VP of Engineering, Helen Marsh

1. PROJECT OVERVIEW
-------------------
The Nexus Platform v2 is a major architectural upgrade to our internal developer tooling
platform. The goal is to replace the current monolithic deployment system with a
microservices-based architecture that supports independent service deployments, improved
observability, and a significantly reduced mean time to recovery (MTTR) for production
incidents.

The project will be delivered in three phases:
  Phase 1: Infrastructure and tooling (April 3 - April 15)
  Phase 2: Service migration (April 15 - May 10)
  Phase 3: Rollout and monitoring (May 10 - May 31)

2. BACKGROUND AND MOTIVATION
-----------------------------
The current Nexus Platform v1 was built in 2021 and was not designed for the scale we now
operate at. Deployments currently take an average of 45 minutes end-to-end, and a single
failed service can block the entire release pipeline. The engineering team has flagged this
as the top bottleneck to shipping velocity for two consecutive quarters.

This project directly addresses the Board-level OKR to "reduce average deployment time by
70% by end of Q2 2026."

3. TEAM AND RESPONSIBILITIES
-----------------------------
The project team consists of four engineers and is overseen by Helen Marsh as sponsor.

Bob is the DevOps specialist on the team. He is responsible for setting up the CI/CD
pipeline that will underpin the entire new platform. Bob's deliverable is a fully
configured and tested CI/CD pipeline by April 5. This includes selecting the pipeline
tooling (likely GitHub Actions or Buildkite), configuring build caching, and integrating
with the existing secrets management system.

Carol leads the User Research function. Before we migrate any services, we need to
understand how the existing 120 internal users interact with the current deployment
tooling. Carol will conduct user research sessions by April 10, delivering a report
that captures pain points, workflow patterns, and feature requests that should be
incorporated into the v2 design.

Dan is the database architect. The new microservices architecture requires a fresh look
at our data layer. Rather than a shared database, each service will own its own schema.
Dan's task is to finalize the database schema for each of the seven core services by
April 3. This is the critical path item that all service migration work in Phase 2
depends on.

Eva is the UX designer for the project. The new platform will have a redesigned developer
dashboard and deployment interface. Eva will create wireframes for the key user flows by
April 8. These wireframes will be reviewed by Carol's user research findings and iterated
upon before engineering implementation begins.

4. DEPENDENCIES AND RISKS
--------------------------
The primary dependency chain is: Dan finalizes database schema → Bob completes CI/CD
pipeline → Phase 2 service migration begins. Any delay in Dan's deliverable flows
directly into Phase 2.

Key risks identified:
  - Risk 1: Database schema finalization may take longer than expected if cross-service
    data ownership disputes arise. Mitigation: Helen Marsh will host a schema review
    meeting on April 1 to resolve any conflicts before the April 3 deadline.
  - Risk 2: User research may surface requirements that conflict with the planned
    architecture. Mitigation: Carol's report is intentionally scheduled before final
    architecture sign-off.

5. SUCCESS METRICS
------------------
  - Average deployment time reduced from 45 minutes to under 13 minutes (70% reduction)
  - Zero cross-service deployment blockages after Phase 3 completion
  - 90% of internal users rating the new dashboard as "easy to use" in the post-launch survey

6. BUDGET
---------
Total approved budget: $180,000
  - Engineering time: $140,000
  - Infrastructure and tooling licenses: $25,000
  - UX design and research: $15,000

7. APPROVALS
------------
This brief has been reviewed and approved by:
  - Helen Marsh, VP of Engineering (project sponsor)
  - Finance sign-off pending (expected March 20, 2026)
"""

with open(os.path.join(workspace, "project_brief.txt"), "w") as f:
    f.write(brief)

print(f"Workspace ready: {workspace}")
