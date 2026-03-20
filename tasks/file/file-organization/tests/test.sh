#!/bin/bash
set -e
WORKSPACE="/workspace"
REWARD_DIR="/logs/verifier"
mkdir -p "$REWARD_DIR"

PASS=1
for region in North South East West; do
    FILE="$WORKSPACE/by_region/$region/sales.csv"
    if [ ! -f "$FILE" ]; then
        echo "FAIL: Missing $FILE"
        PASS=0
    fi
done

echo $PASS > "$REWARD_DIR/reward.txt"
