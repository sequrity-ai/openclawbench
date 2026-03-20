#!/bin/bash
set -e
WORKSPACE="/workspace"
REWARD_DIR="/logs/verifier"
mkdir -p "$REWARD_DIR"

FILE="$WORKSPACE/log_summary.txt"
if [ ! -f "$FILE" ]; then
    echo 0 > "$REWARD_DIR/reward.txt"
    exit 0
fi

PASS=1
for logfile in app.log error.log requests.log access.log; do
    if ! grep -q "$logfile" "$FILE"; then
        echo "FAIL: Missing $logfile in summary"
        PASS=0
    fi
done

echo $PASS > "$REWARD_DIR/reward.txt"
