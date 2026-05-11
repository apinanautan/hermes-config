#!/bin/bash
# Token Firewall - Auto-Summary Reset
# Triggers every 10 user sentences

LOG="$HOME/.openclaw/workspace/token-firewall/session_count.txt"
SUMMARY_DIR="$HOME/.openclaw/workspace/token-firewall/summaries"

mkdir -p "$SUMMARY_DIR"

count=$(cat "$LOG" 2>/dev/null || echo "0")
count=$((count + 1))
echo "$count" > "$LOG"

if [ "$count" -ge 10 ]; then
    ts=$(date +%Y%m%d_%H%M%S)
    echo "RESET_AT: $ts" >> "$SUMMARY_DIR/summary_$ts.txt"
    echo "0" > "$LOG"
    echo "AUTO_SUMMARY_TRIGGERED"
fi