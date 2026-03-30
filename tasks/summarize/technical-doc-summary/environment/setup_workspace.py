#!/usr/bin/env python3
"""Setup workspace for technical-doc-summary task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

docs = """\
DataStream API v2.3 — Developer Documentation
Last Updated: March 1, 2026

OVERVIEW
--------
The DataStream API v2.3 provides real-time data ingestion and streaming capabilities for
developers building event-driven applications. This version introduces improved latency
characteristics, enhanced error handling, and expanded geographic availability compared
to v2.2.

AUTHENTICATION
--------------
All requests to the DataStream API must be authenticated using Bearer tokens. Tokens are
issued through the DataStream developer portal and expire after 24 hours. To authenticate,
include the following header in every request:

    Authorization: Bearer <your_token_here>

Tokens must be refreshed before expiry using the /auth/refresh endpoint. Failed
authentication attempts are logged and three consecutive failures will trigger a
temporary account lock lasting 15 minutes.

ENDPOINTS
---------
The following endpoints are available in v2.3:

POST /stream/start
  Initiates a new data stream session. Required parameters: source_id (string),
  data_format (json|csv|binary), compression (none|gzip|lz4). Returns a stream_id
  that must be included in subsequent requests.

POST /stream/stop
  Terminates an active stream session. Required parameter: stream_id. All buffered
  data is flushed before the session closes. Returns a final delivery receipt.

GET /stream/status
  Returns the current status of an active stream, including bytes transferred,
  message count, and any error conditions.

POST /stream/publish
  Publishes a data payload to an active stream. Maximum payload size is 1 MB per
  request. Supports both synchronous and asynchronous delivery modes.

RATE LIMITS
-----------
The DataStream API enforces the following rate limits to ensure fair usage:

- Standard tier: 1000 requests/hour per API token
- Professional tier: 10,000 requests/hour per API token
- Enterprise tier: Custom limits negotiated per contract

Exceeding rate limits returns HTTP 429 Too Many Requests. The response header
X-RateLimit-Reset indicates when the limit resets. Burst allowances of up to
200% of the hourly limit are permitted for periods not exceeding 5 minutes.

ERROR HANDLING
--------------
The API uses standard HTTP status codes. Retryable errors (503, 429) include a
Retry-After header. Non-retryable errors (400, 401, 403) indicate client-side
issues that require code or credential changes before retrying.

CHANGELOG v2.3
--------------
- Reduced /stream/start latency by 35% compared to v2.2
- Added LZ4 compression support for binary streams
- Expanded availability to 12 new regions including Southeast Asia and South America
- Fixed a race condition in /stream/stop that could cause data loss under high load
"""

with open(os.path.join(workspace, "api_docs.txt"), "w") as f:
    f.write(docs)

print(f"Workspace ready: {workspace}")
