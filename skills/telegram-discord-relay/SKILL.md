---
name: telegram-discord-relay
description: Auto-relay Telegram agent replies to Discord DM without prefix. Use whenever responding to Telegram messages when bridge-active exists and Discord relay is needed. Triggers on: sending Telegram reply to Discord, Telegram->Discord bridge, relay agent response to Discord.
---

# Telegram → Discord Relay Skill

## When to Use

Use this skill automatically when:
- Responding to Telegram messages from owner (robberzaz, ID 1060942816)
- The file `~/.openclaw/workspace/bridge-active` exists
- User wants Discord notifications for agent replies

## Quick Command

After composing any reply to Telegram, run:

```bash
python3 ~/.openclaw/workspace/tg-to-dc.py "ข้อความที่ตอบ"
```

## Rules

1. **Only relay AGENT replies** — never relay user's inbound messages
2. **No prefix** — send plain text, do NOT add `[TG]`, `[DC]`, or any prefix
3. **Skip empty messages** — do not relay empty or whitespace-only replies
4. **Always use this after responding to Telegram when bridge is active**
## Sensitive Code Handling

- If the boss provides a code/password in the current message, use it only to unlock the explicitly authorized task.
- Never save, copy, summarize, or persist the code/password in skill files, notes, backups, logs, or artifacts.
- After use, remove the code/password from any editable artifact touched in the task and replace it with `[ถามรหัสจากเจ้านายเมื่อจำเป็น]` when a placeholder is needed.

