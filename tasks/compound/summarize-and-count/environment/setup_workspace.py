#!/usr/bin/env python3
"""Setup workspace for summarize-and-count task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

log_lines = [
    "2026-01-15 08:00:01 INFO  Server started on port 8080",
    "2026-01-15 08:00:05 INFO  Connected to database",
    "2026-01-15 08:01:12 INFO  User admin logged in",
    "2026-01-15 08:02:33 WARN  High memory usage: 78%",
    "2026-01-15 08:03:45 INFO  Request GET /api/users processed in 12ms",
    "2026-01-15 08:04:01 ERROR Failed to connect to cache server: timeout",
    "2026-01-15 08:04:15 INFO  Retrying cache connection",
    "2026-01-15 08:05:22 WARN  Slow query detected: 2.3s",
    "2026-01-15 08:06:00 INFO  Cache reconnected successfully",
    "2026-01-15 08:07:11 ERROR Disk write failed: /var/log/app.log permission denied",
    "2026-01-15 08:08:30 INFO  Background job started: email_queue",
    "2026-01-15 08:09:44 INFO  Processed 250 emails",
    "2026-01-15 08:10:05 ERROR Database query timeout after 30s",
    "2026-01-15 08:11:18 WARN  Connection pool nearly exhausted: 95/100",
    "2026-01-15 08:12:00 INFO  Health check passed",
    "2026-01-15 08:13:22 ERROR Authentication service unavailable",
    "2026-01-15 08:14:45 INFO  Fallback authentication used",
    "2026-01-15 08:15:01 INFO  Request POST /api/login processed in 8ms",
    "2026-01-15 08:16:33 WARN  SSL certificate expires in 30 days",
    "2026-01-15 08:17:00 ERROR Failed to write metrics to InfluxDB",
    "2026-01-15 08:18:12 INFO  Metrics buffer flushed locally",
    "2026-01-15 08:19:44 INFO  User guest123 logged out",
    "2026-01-15 08:20:05 ERROR Rate limit exceeded for IP 192.168.1.45",
    "2026-01-15 08:21:18 WARN  Unusual login pattern detected",
    "2026-01-15 08:22:00 INFO  Security alert sent to admin",
    "2026-01-15 08:23:30 ERROR Webhook delivery failed: connection refused",
    "2026-01-15 08:24:45 INFO  Webhook queued for retry",
    "2026-01-15 08:25:01 INFO  Configuration reload triggered",
    "2026-01-15 08:26:12 WARN  Config value 'max_retries' deprecated",
    "2026-01-15 08:27:33 ERROR NullPointerException in PaymentProcessor.process()",
    "2026-01-15 08:28:00 INFO  Transaction rolled back",
    "2026-01-15 08:29:44 INFO  Payment system restarted",
    "2026-01-15 08:30:05 ERROR File upload exceeded size limit: 52MB",
    "2026-01-15 08:31:18 INFO  Upload rejected, user notified",
    "2026-01-15 08:32:00 INFO  Scheduled maintenance window starting",
    "2026-01-15 08:33:30 WARN  Maintenance mode active",
    "2026-01-15 08:34:45 ERROR External API response malformed: JSON parse error",
    "2026-01-15 08:35:01 INFO  Using cached API response",
    "2026-01-15 08:36:12 INFO  Cache hit rate: 82%",
    "2026-01-15 08:37:33 ERROR Session store write failed: Redis READONLY",
    "2026-01-15 08:38:00 WARN  Switching to in-memory session store",
    "2026-01-15 08:39:44 INFO  Sessions migrated to memory store",
    "2026-01-15 08:40:05 ERROR Scheduled report generation failed: out of memory",
    "2026-01-15 08:41:18 INFO  Report generation rescheduled",
    "2026-01-15 08:42:00 INFO  System load normal: 0.42",
    "2026-01-15 08:43:30 WARN  Backup job running late",
    "2026-01-15 08:44:45 INFO  Backup destination check complete",
    "2026-01-15 08:45:01 INFO  Backup retrying with alternate endpoint",
    "2026-01-15 08:46:12 INFO  Backup completed successfully",
    "2026-01-15 08:47:33 INFO  Server uptime: 2h 47m",
]

log_file = os.path.join(workspace, "log.txt")
with open(log_file, "w") as f:
    f.write("\n".join(log_lines) + "\n")

# Verify count
error_count = sum(1 for line in log_lines if " ERROR " in line)
print(f"Workspace ready: {workspace}")
print(f"Created: {log_file} ({len(log_lines)} lines, {error_count} ERROR lines)")
