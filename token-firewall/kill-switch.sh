#!/bin/bash
# Kill-Switch: Token usage > 200,000/hour → STOP & Alert

TOKEN_LOG="$HOME/.openclaw/workspace/token-firewall/hourly_tokens.txt"
TELEGRAM_ALERT="curl -s 'https://api.telegram.org/bot$(cat $HOME/.openclaw/.telegram_token 2>/dev/null)/sendMessage?chat_id=1060942816&text=TURING_KILL: 200K+ tokens/hour detected. SYSTEM_HALTED.'"

hour=$(date +%Y%m%d%H)
current=$(cat "$TOKEN_LOG" 2>/dev/null | grep "^$hour:" | cut -d: -f2)

if [ -n "$current" ] && [ "$current" -gt 200000 ]; then
    echo "KILL_SWITCH_ACTIVATED at $(date)" >> "$HOME/.openclaw/workspace/token-firewall/kill_log.txt"
    pkill -f "openclaw" 2>/dev/null || true
    eval "$TELEGRAM_ALERT" 2>/dev/null
fi