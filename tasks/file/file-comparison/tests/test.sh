#!/bin/bash
set -e
WORKSPACE="/workspace"
REWARD_DIR="/logs/verifier"
mkdir -p "$REWARD_DIR"

FILE="$WORKSPACE/config_diff.txt"
if [ ! -f "$FILE" ]; then
    echo 0 > "$REWARD_DIR/reward.txt"
    exit 0
fi

CONTENT=$(cat "$FILE" | tr '[:upper:]' '[:lower:]')
PASS=1
# Check key differences are mentioned
echo "$CONTENT" | grep -q "localhost" || PASS=0
echo "$CONTENT" | grep -q "prod-db" || PASS=0
echo "$CONTENT" | grep -q "pool" || PASS=0
echo "$CONTENT" | grep -q "debug" || PASS=0

echo $PASS > "$REWARD_DIR/reward.txt"
