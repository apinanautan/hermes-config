---
name: hermes-mac-handoff
description: Handoff mode สำหรับ Hermes-Mac — WORKER TEMP, ห้าม push git, ห้ามแก้ brain โดยไม่ได้รับ task
version: 1.0.0
category: hermes
---

# Hermes-Mac Handoff Mode

## Role
Hermes-Mac = **WORKER TEMP / HANDOFF NODE**
ไม่ใช่ primary worker, ไม่ใช่ writer, ไม่ใช่ architect

## Permissions
✅ pull/fetch, read, run, check, report
❌ push, autopush, git add ., edit shared brain, use PC path

## Workflow
1. รับ task → pull → ทำงาน → report
2. NEEDS_PC_PUSH ถ้าต้อง commit/push

## Report Header
```markdown
# Report: <TASK_ID>
- machine: Hermes-Mac
- status: DONE | NEEDS_PC_PUSH | BLOCKED
- files_touched: [...]
- next_action: ...
```
