#!/usr/bin/env python3
"""Setup workspace for compare-two-documents task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

proposal_a = """\
Proposal A — Web Platform Redesign
Submitted by: Team Alpha
Date: March 15, 2026

EXECUTIVE SUMMARY
-----------------
Team Alpha proposes a complete redesign of the customer-facing web platform using a
modern React + Node.js technology stack. Our approach prioritizes speed of delivery and
developer experience, leveraging our team's deep expertise in JavaScript ecosystems.

TECHNICAL APPROACH
------------------
The frontend will be built using React 18 with TypeScript, employing a component-driven
development methodology. The backend API layer will use Node.js with the Fastify framework,
chosen for its high throughput and low overhead. We will deploy on AWS using containerized
microservices via ECS Fargate.

State management will use Zustand, avoiding the complexity of Redux while maintaining
predictable data flow. For the database layer, we will use PostgreSQL with Prisma ORM,
enabling type-safe database access.

TIMELINE
--------
Team Alpha estimates a delivery timeline of 3 months from project kickoff to production
launch. This is achievable because three of our five engineers have worked on this codebase
before and require minimal onboarding. We plan two-week sprints with bi-weekly client
demos throughout the engagement.

BUDGET
------
Total project budget: $50,000

Breakdown:
- Engineering (5 engineers × 3 months): $42,000
- Infrastructure setup and DevOps: $4,000
- QA and testing: $3,000
- Project management: $1,000

TEAM
----
Team Alpha consists of five senior engineers with an average of 7 years of experience.
The team lead, Jordan Rivera, has delivered 12 similar redesign projects in the past four years.

CONCLUSION
----------
Team Alpha offers the fastest delivery timeline in the market at $50,000. Our React + Node.js
expertise means fewer surprises and a production-ready platform in 3 months.
"""

proposal_b = """\
Proposal B — Web Platform Redesign
Submitted by: Team Beta
Date: March 15, 2026

EXECUTIVE SUMMARY
-----------------
Team Beta proposes a web platform redesign using Django + Vue.js, a proven combination
for scalable, maintainable web applications. Our approach emphasizes long-term
maintainability, security, and total cost of ownership over raw delivery speed.

TECHNICAL APPROACH
------------------
The backend will be built on Django 4.2 with Django REST Framework, providing a robust
admin interface, built-in security features (CSRF protection, SQL injection prevention),
and a mature ORM. The frontend will use Vue.js 3 with the Composition API and Pinia for
state management.

We selected Django for its batteries-included philosophy: authentication, permissions,
content management, and admin tooling come built-in, reducing the surface area for
security vulnerabilities and accelerating feature development after initial setup.

Deployment will use Google Cloud Platform with Cloud Run for serverless container
execution, minimizing infrastructure management overhead and providing automatic scaling.

TIMELINE
--------
Team Beta estimates a delivery timeline of 5 months from project kickoff. This longer
timeline reflects our commitment to thorough documentation, security audits at each sprint,
and a more extensive QA process including penetration testing. We believe rushing a platform
redesign creates technical debt that costs far more than the time saved.

BUDGET
------
Total project budget: $35,000

Breakdown:
- Engineering (4 engineers × 5 months): $28,000
- Infrastructure setup and cloud configuration: $3,000
- QA, security audit, and penetration testing: $3,000
- Documentation and knowledge transfer: $1,000

TEAM
----
Team Beta consists of four engineers specializing in Python/Django development. Our lead
engineer, Yuki Tanaka, has 10 years of Django experience and has previously worked on
two government-sector platform migrations requiring high security standards.

CONCLUSION
----------
Team Beta offers the most cost-effective solution at $35,000 — $15,000 less than competing
proposals — while delivering a secure, maintainable platform built on mature technology.
The 5-month timeline reflects the thoroughness of our process, not inefficiency.
"""

with open(os.path.join(workspace, "proposal_a.txt"), "w") as f:
    f.write(proposal_a)

with open(os.path.join(workspace, "proposal_b.txt"), "w") as f:
    f.write(proposal_b)

print(f"Workspace ready: {workspace}")
