#!/usr/bin/env python3
"""Setup workspace for gog-gmail/count-unread task.

Uses the `gog` CLI (gogcli) to:
  1. Create a unique test label in the user's Gmail.
  2. Send 8 test emails to self.
  3. Wait for delivery, then label all messages and mark 5 as read / 3 as unread.
  4. Write the label name and manifest to workspace for later cleanup.

Authentication (one of):
  Local:   gog auth credentials <file> && gog auth login  (uses OS keychain)
  Daytona: export GOG_TOKEN_FILE=~/.gog-token.json        (refresh token, auto-refreshes)
           Token file created via: gog auth tokens export <email> --output ~/.gog-token.json

Required environment:
  GOG_TEST_EMAIL – the Gmail address to send test emails to (your own address)
  GOG_TOKEN_FILE – (Daytona only) path to exported gog refresh token file
"""

import json
import os
import subprocess
import sys
import time
import uuid

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

test_email = os.environ.get("GOG_TEST_EMAIL")
if not test_email:
    print("ERROR: GOG_TEST_EMAIL environment variable is required", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gog(*args: str, parse_json: bool = False):
    """Run a gog command, optionally parsing JSON output."""
    cmd = ["gog"] + list(args)
    if parse_json:
        cmd.append("--json")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"gog command failed: {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    if parse_json:
        return json.loads(result.stdout)
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# 1. Create a unique label for this test run
# ---------------------------------------------------------------------------

run_id = uuid.uuid4().hex[:8]
label_name = f"openclawbench-{run_id}"

print(f"Creating label: {label_name}")
gog("gmail", "labels", "create", label_name)

# ---------------------------------------------------------------------------
# 2. Clean up any leftover messages from previous runs (idempotency)
# ---------------------------------------------------------------------------

old_labels_output = gog("gmail", "search", "label:openclawbench-", "--max", "100", parse_json=True)
if old_labels_output:
    old_ids = []
    if isinstance(old_labels_output, list):
        for msg in old_labels_output:
            msg_id = msg.get("id") or msg.get("messageId") or msg.get("Id")
            if msg_id:
                old_ids.append(str(msg_id))
    if old_ids:
        print(f"Cleaning up {len(old_ids)} leftover messages from previous runs")
        gog("gmail", "batch", "delete", *old_ids)

# ---------------------------------------------------------------------------
# 3. Send 8 test emails to self
# ---------------------------------------------------------------------------

EMAIL_DATA = [
    {"subject": f"[{label_name}] Q1 Budget Review",            "body": "Please find attached the Q1 budget review.", "unread": False},
    {"subject": f"[{label_name}] Re: Project Phoenix Timeline", "body": "The timeline looks good to me.",              "unread": True},
    {"subject": f"[{label_name}] PR #42 opened by jsmith",     "body": "jsmith opened pull request #42.",             "unread": False},
    {"subject": f"[{label_name}] Performance Reviews",          "body": "Please complete your self-assessment.",       "unread": True},
    {"subject": f"[{label_name}] Partnership Agreement Draft",  "body": "Please review sections 3 and 7.",            "unread": False},
    {"subject": f"[{label_name}] Scheduled Maintenance",        "body": "Maintenance on March 20 from 2-4 AM UTC.",   "unread": False},
    {"subject": f"[{label_name}] Brand Guidelines Released",    "body": "Updated brand guidelines on the intranet.",  "unread": False},
    {"subject": f"[{label_name}] Expense Report Reminder",      "body": "Submit your February expense report.",        "unread": True},
]

EXPECTED_UNREAD = sum(1 for e in EMAIL_DATA if e["unread"])  # 3

print(f"Sending {len(EMAIL_DATA)} test emails to {test_email} ...")
for email in EMAIL_DATA:
    gog("gmail", "send",
        "--to", test_email,
        "--subject", email["subject"],
        "--body", email["body"])
    time.sleep(0.5)  # small delay to avoid rate limits

# ---------------------------------------------------------------------------
# 4. Wait for emails to arrive and collect message IDs
# ---------------------------------------------------------------------------

print("Waiting for emails to arrive ...")
max_wait = 60  # seconds
poll_interval = 5
elapsed = 0
message_ids = []

while elapsed < max_wait:
    time.sleep(poll_interval)
    elapsed += poll_interval
    results = gog("gmail", "search", f"subject:{label_name}", "--max", "20", parse_json=True)
    if isinstance(results, list):
        message_ids = []
        for msg in results:
            msg_id = msg.get("id") or msg.get("messageId") or msg.get("Id")
            if msg_id:
                message_ids.append(str(msg_id))
    if len(message_ids) >= len(EMAIL_DATA):
        break
    print(f"  ... found {len(message_ids)}/{len(EMAIL_DATA)} messages after {elapsed}s")

if len(message_ids) < len(EMAIL_DATA):
    print(f"WARNING: only {len(message_ids)}/{len(EMAIL_DATA)} emails arrived after {max_wait}s",
          file=sys.stderr)

print(f"Collected {len(message_ids)} message IDs")

# ---------------------------------------------------------------------------
# 5. Apply the test label to all messages
# ---------------------------------------------------------------------------

if message_ids:
    gog("gmail", "batch", "modify", *message_ids, "--add", label_name)
    print(f"Applied label '{label_name}' to {len(message_ids)} messages")

# ---------------------------------------------------------------------------
# 6. Mark read/unread based on EMAIL_DATA
#    After sending, all messages arrive as unread in INBOX.
#    Mark the ones that should be "read" by removing UNREAD label.
# ---------------------------------------------------------------------------

# Mark all as read first, then mark the specific ones back as unread.
if message_ids:
    # Mark all as read
    gog("gmail", "batch", "modify", *message_ids, "--remove", "UNREAD")
    print("Marked all messages as read")

# Now find and mark the 3 that should be unread by searching for their subjects
unread_subjects = [e["subject"] for e in EMAIL_DATA if e["unread"]]
unread_ids = []
for subject in unread_subjects:
    results = gog("gmail", "search", f'subject:"{subject}"', "--max", "1", parse_json=True)
    if isinstance(results, list) and results:
        msg_id = results[0].get("id") or results[0].get("messageId") or results[0].get("Id")
        if msg_id:
            unread_ids.append(str(msg_id))

if unread_ids:
    gog("gmail", "batch", "modify", *unread_ids, "--add", "UNREAD")
    print(f"Marked {len(unread_ids)} messages as unread")

# ---------------------------------------------------------------------------
# 7. Write manifest for teardown and label for the agent
# ---------------------------------------------------------------------------

manifest = {
    "label": label_name,
    "message_ids": message_ids,
    "expected_unread": EXPECTED_UNREAD,
    "test_email": test_email,
}

with open(os.path.join(workspace, ".manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

with open(os.path.join(workspace, "test_label.txt"), "w") as f:
    f.write(label_name)

print(f"Workspace ready: {workspace}")
print(f"Label: {label_name}, Expected unread: {EXPECTED_UNREAD}")
