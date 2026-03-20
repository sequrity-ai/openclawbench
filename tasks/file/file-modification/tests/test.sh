#!/bin/bash
set -e
WORKSPACE="/workspace"
REWARD_DIR="/logs/verifier"
mkdir -p "$REWARD_DIR"

PASS=1
for user in "Alice Johnson" "Bob Smith" "Carol White"; do
    FILE="$WORKSPACE/users/$user/profile.txt"
    if [ ! -f "$FILE" ]; then
        echo "FAIL: Missing $FILE"
        PASS=0
        continue
    fi
    if ! grep -q "Action Items: 1" "$FILE"; then
        echo "FAIL: $user profile missing 'Action Items: 1'"
        PASS=0
    fi
done

echo $PASS > "$REWARD_DIR/reward.txt"
