#!/bin/bash
# Anti-Loop: 3 identical responses → STOP & save debug

LOOP_LOG="$HOME/.openclaw/workspace/token-firewall/loop_count.txt"
DEBUG_FILE="$HOME/.openclaw/workspace/token-firewall/debug_logic.txt"

count=$(cat "$LOOP_LOG" 2>/dev/null || echo "0")
last_response="$1"

if [ "$count" -ge 3 ]; then
    echo "=== LOOP DETECTED at $(date) ===" > "$DEBUG_FILE"
    echo "Last response: $last_response" >> "$DEBUG_FILE"
    echo "AUTO_HALT: YES" >> "$DEBUG_FILE"
    echo "0" > "$LOOP_LOG"
    exit 1
fi

echo $((count + 1)) > "$LOOP_LOG"
exit 0