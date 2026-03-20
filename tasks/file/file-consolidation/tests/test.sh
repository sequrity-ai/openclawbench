#!/bin/bash
set -e
WORKSPACE="/workspace"
REWARD_DIR="/logs/verifier"
mkdir -p "$REWARD_DIR"

FILE="$WORKSPACE/users_summary.csv"
if [ ! -f "$FILE" ]; then
    echo "FAIL: users_summary.csv not found"
    echo 0 > "$REWARD_DIR/reward.txt"
    exit 0
fi

# Check columns and data
PASS=1
if ! head -1 "$FILE" | grep -qi "name"; then
    PASS=0
fi
LINES=$(wc -l < "$FILE")
if [ "$LINES" -lt 4 ]; then
    PASS=0
fi

echo $PASS > "$REWARD_DIR/reward.txt"
