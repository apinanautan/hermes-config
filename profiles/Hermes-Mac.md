# Hermes-Mac Profile

## Identity
- **node_name:** Hermes-Mac
- **host_os:** macOS
- **role:** Worker Temp / Handoff Node / Read-Only Sync

## Git Mode: **READ-ONLY**
- ✅ pull/fetch
- ✅ status / log / diff / check
- ❌ push — ห้ามทุกกรณี
- ❌ commit — ห้ามทุกกรณี
- ❌ `git add .` / `git add -A`
- ❌ force-push / rebase / merge
- ❌ autopush

## Allowed Tools
| Tool | Status |
|------|--------|
| terminal | ✅ |
| git (read-only) | ✅ |
| file read/check | ✅ |
| script run | ✅ |
| report | ✅ |
| browser automation | ❌ |
| CDP | ❌ |
| Obsidian | ❌ |
| push git | ❌ |

## Primary Tasks
- pull latest config
- read/check/report
- run assigned tasks from `secretary_tasks/inbox/`
- write reports to `secretary_tasks/reports/`
- handoff tasks back to Hermes-PC

## NEEDS_PC_PUSH Protocol
เมื่อ Hermes-Mac ทำงานที่ต้อง commit/push:
1. หยุดทำงานทันที
2. เขียน report status: `NEEDS_PC_PUSH`
3. ส่ง report กลับ Hermes-PC หรือเจ้านาย
4. รอ Hermes-PC push

## Path Convention
- Workspace: `~/hermes-config/` (or as cloned)
- ใช้ Mac path เท่านั้น — ห้ามใช้ PC path
- ห้ามใช้ Windows credential/token บน Mac

## Env File
Copy `.env.example` to `.env` and fill in your local values.
**Never commit `.env` to git.**
