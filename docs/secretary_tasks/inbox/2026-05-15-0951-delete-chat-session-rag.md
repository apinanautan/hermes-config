# Task: delete completed ChatGPT sessions from browser list
- **From:** Hermes-PC
- **Target:** OpenClaw-PC
- **Objective:** Clean up the ChatGPT conversation list by deleting completed / junk sessions so the list is not cluttered.
- **Steps:**
  1. Open the authenticated ChatGPT browser session that is already logged in.
  2. Review the conversation list and identify chats that are clearly finished, test/health-check, or temporary clutter.
  3. Delete only the completed / junk sessions from the browser UI.
  4. Keep active, pinned, or clearly reference-worthy sessions.
  5. If a chat is ambiguous, do not delete it; leave it untouched and mention it in the report.
- **Safety:**
  - Do not delete active work sessions.
  - Do not log out, switch profile, or open a new browser session.
  - Do not use API calls; do it through the browser UI only.
  - If the browser session is not available, report the blocker instead of guessing.
- **Expected Report:**
  - Number of chats deleted
  - Number of chats kept / skipped
  - Any ambiguous chats left untouched
  - Final status: done / blocked
- **Timeout:** 20m
- **Created:** 2026-05-15 09:51:48
- **Report Path:** docs/secretary_tasks/reports/2026-05-15-0951-delete-chat-session-rag.md
