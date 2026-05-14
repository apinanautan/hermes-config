# Hermes Node Profiles

ระบบ auto-detect identity เมื่อ clone repo ครั้งแรก

## Profiles

| Profile | OS | Git Mode | Role |
|---------|-----|----------|------|
| [Hermes-PC](Hermes-PC.md) | Windows/WSL | **writer** | Primary Worker |
| [Hermes-Mac](Hermes-Mac.md) | macOS | **read-only** | Worker Temp / Handoff |

## Unknown Node

ถ้า detect ไม่ได้ → **STOP**
- ห้าม git write
- ห้าม push
- รอ identity confirmation

## How Detection Works

```bash
# On any node:
source scripts/detect-node-profile.sh
# หรือ
. .\scripts\detect-node-profile.ps1  # Windows PowerShell
```

จะ auto-select profile จาก:
1. OS type
2. Hostname
3. User
4. Path convention

## Adding New Profiles

1. สร้าง `profiles/<NODE-NAME>.md`
2. เพิ่ม detection logic ใน `scripts/detect-node-profile.sh` และ `.ps1`
3. อัปเดตตารางนี้
4. Push (จาก Hermes-PC เท่านั้น)
