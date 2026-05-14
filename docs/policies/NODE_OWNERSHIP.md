# Node Ownership Policy

## Policy Statement
Every Hermes node มี identity ชัดเจน — ไม่มี ambiguous node

## Ownership Levels

| Level | Node | Push | Commit | Edit Shared Brain |
|-------|------|------|--------|-------------------|
| **Writer** | Hermes-PC | ✅ | ✅ | ✅ (whitelist only) |
| **Reader** | Hermes-Mac | ❌ | ❌ | ❌ (report only) |
| **Blocked** | Unknown | ❌ | ❌ | ❌ |

## Detection
1. ทุก node ต้องรัน `detect-node-profile.sh` หรือ `.ps1` ก่อนทำงาน
2. Unknown → **STOP**
3. Writer nodes เท่านั้นที่ push ได้

## Git Rules (Mac)
```bash
✅ git status / fetch / pull --ff-only / log / diff
❌ git push / commit / add . / add -A / merge / rebase
```

## Git Rules (PC)
```bash
✅ git add <file> / commit / push / pull --ff-only
❌ git add . / add -A / push --force / rebase / reset --hard
```

## Cross-Node
- ห้ามใช้ path/config/token ข้ามเครื่อง
- `.env.example` เท่านั้น — ห้าม commit `.env` จริง
