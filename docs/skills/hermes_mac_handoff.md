# Hermes-Mac Handoff Mode

## Role
**Hermes-Mac = WORKER TEMP / HANDOFF NODE เท่านั้น**

## Permissions
| Action | Allowed |
|--------|---------|
| pull/fetch | ✅ |
| read files | ✅ |
| run scripts | ✅ |
| check status | ✅ |
| report | ✅ |
| push git | ❌ ห้ามเด็ดขาด |
| autopush | ❌ ห้ามเด็ดขาด |
| edit shared brain | ❌ ยกเว้นได้รับ task |
| use PC path/token | ❌ ห้ามเด็ดขาด |

## Workflow
1. รับ task จาก inbox/
2. pull --ff-only
3. ทำงาน
4. report ลง reports/
5. ถ้าต้อง push → NEEDS_PC_PUSH

## Report Template
```markdown
# Report: <TASK_ID>
- machine: Hermes-Mac
- status: DONE | NEEDS_PC_PUSH | BLOCKED
- files_touched: [...]
- next_action: ...
```
