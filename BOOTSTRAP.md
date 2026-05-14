# Bootstrap — Hermes Node Identity System

## Purpose
เมื่อ Hermes clone repo นี้ครั้งแรก ระบบจะ auto-detect ว่าเป็น node ไหน แล้วโหลด profile rules อัตโนมัติ

## Flow

```
Clone repo
  ↓
detect-node-profile.sh / .ps1
  ↓
  ├── Windows/WSL + Apinan PC → profiles/Hermes-PC.md
  ├── macOS                   → profiles/Hermes-Mac.md
  └── Unknown                 → STOP
  ↓
Load profile → set env/permissions/git-mode
  ↓
Report identity → พร้อมทำงาน
```

## Detection Logic

Detection uses **OS + username** (not hostname), with known hostnames as supplementary check:

| Signal | Target |
|--------|--------|
| OS=Windows/WSL/Linux AND user=Apinan | → Hermes-PC |
| OS=macOS | → Hermes-Mac |
| อื่น ๆ | → Unknown → STOP |

**Known PC hostnames** (for verification only, not primary detection):
- `DESKTOP-F1PJT4S` (Apinan-PC, current)
- Future Apinan Windows machines → add here after identity confirm

## Profile Files

| Profile | File | Git Mode |
|---------|------|----------|
| Hermes-PC | `profiles/Hermes-PC.md` | writer (push allowed) |
| Hermes-Mac | `profiles/Hermes-Mac.md` | reader (read-only) |
| Unknown | none | STOP |

## Quick Start

```bash
# Linux/macOS/WSL
source scripts/detect-node-profile.sh

# Windows PowerShell
. .\scripts\detect-node-profile.ps1
```

## Safety

- Unknown = STOP เสมอ
- ห้าม push จาก node ที่ไม่ใช่ writer
- ห้ามใช้ token/config ข้ามเครื่อง
- `.env.example` เท่านั้น — ห้าม commit `.env` จริง
