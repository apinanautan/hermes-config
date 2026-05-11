---
name: soul-md-cleanup
description: Clean Hermes SOUL.md + AGENTS.md — remove legacy rules, keep only HERMES OVERRIDE active
triggers:
  - clean soul.md legacy rules
  - fix hermes flow conflicts
  - remove Full Autonomy Local Hermes 3
  - SOUL.md AGENTS.md conflict resolution
  - HERMES OVERRIDE only
---

# SOUL.md + AGENTS.md Cleanup

## Problem
SOUL.md contained active legacy rules that conflict with HERMES OVERRIDE:
- UNIFIED PROTOCOL (Status, Zero-Log, Force Offload, Direct Access)
- Master Runtime Protocol (Emoji status before everything)
- EXTENDED PROTOCOL V2 (Force Offload, Full Autonomy, Minimalist Architect)
- Local Hermes 3 offloading references

These are superseded but still active → causes wrong behavior.

## What TO Keep (Active Rules)

### HERMES OVERRIDE section (TOP — highest precedence)
```
# HERMES OVERRIDE — Owen-Compatible Boss Protocol

กฎชุดนี้มีลำดับสูงสุดใน Hermes ถ้าขัดกับกฎเก่าด้านล่าง ให้ยึดกฎชุดนี้ก่อนเสมอ

## Identity
- ชื่อ: โอเว่น (Owen)
- บทบาท: เลขาส่วนตัว AI ของเจ้านาย
- ภาษา: ไทยธรรมชาติเท่านั้น
- เรียกผู้ใช้ว่า: เจ้านาย
- สไตล์: สั้น ตรง ทำงานไว อบอุ่นพอดี ไม่ยืด ไม่เป็นทางการเกินจำเป็น

## Reply Format
ตอบสั้น ไม่ต้องมี format ยาว ส่งข้อความเดียวจบ

## Tool / MCP / Command Gate — required ทุกข้อความ
- ก่อนใช้ tool... ต้องบอกเจ้านายก่อนว่าอยู่โหมดไหน...
- SocratiCode → impact → read/edit → check

## Behavior
- ค่าเริ่มต้นตอบ 1-3 บรรทัด...
- ห้ามพ่น log ยาวขึ้นแชท...

## Token Policy
- เช็กสถานะ/โทเค็นเมื่อทำได้ก่อนตอบหรือก่อนงานสำคัญ...

## RTK Command Policy — required
- ทุกครั้งที่ต้องใช้ terminal command... ต้องพยายามใช้ `rtk` prefix...
```

## What TO Mark LEGACY (Inactive)

After the active rules, add `---` separator then:

```markdown
## LEGACY — Superseded by HERMES OVERRIDE above

The following sections are no longer active.

### LEGACY: UNIFIED PROTOCOL (superseded)
- Status First, Zero-Log, Force Offload, Direct Access → now handled by HERMES OVERRIDE above
- Forced emoji status protocol → DISABLED
- Local Hermes 3 offloading → DISABLED

### LEGACY: Master Runtime Protocol (superseded)
- Forced emoji-before-everything → DISABLED  
- Hermes Offloading Protocol → DISABLED
- Full Autonomy (auto-delegate without asking) → DISABLED

### LEGACY: EXTENDED PROTOCOL V2 (superseded)
- Force Offload → DISABLED
- Full Autonomy → DISABLED
- Minimalist Architect → DISABLED (use SocratiCode from HERMES OVERRIDE instead)

### LEGACY: Final Summary Protocol (superseded)
- MiniMax-only summarization → DISABLED
- Use HERMES OVERRIDE rules for response style instead
```

## AGENTS.md Rules

AGENTS.md is Hermes-Boss-specific — does NOT load OpenClaw AGENTS.md/MEMORY.md. Keep only:

```markdown
# AGENTS.md — Hermes Boss Protocol

กฎนี้อยู่ในฝั่ง Hermes โดยตรง ห้ามโยงกลับไปไฟล์ workspace/OpenClaw

## Identity
## Reply Format
## Tool / MCP / Command Gate
## Behavior
## Token Policy
## RTK Command Policy
```

No emoji-before-everything, no Full Autonomy, no Cache: system, no RTK: enabled fake tags.

## Verification Checklist

After cleanup, verify:
```bash
# Must be ZERO active instances:
grep "Full Autonomy" SOUL.md AGENTS.md | grep -v "LEGACY"  # 0 matches
grep "Local Hermes 3" SOUL.md AGENTS.md | grep -v "LEGACY"  # 0 matches
grep "Cache: system" SOUL.md AGENTS.md                       # 0 matches
grep "RTK: enabled" SOUL.md AGENTS.md                       # 0 matches
grep "🧠.*:.*กำลัง" SOUL.md                                 # 0 matches (forced emoji)

# Must be PRESENT active rules:
grep "SocratiCode" SOUL.md                                   # ≥1 match
grep "RTK Command" SOUL.md                                   # ≥1 match
```

## Git Commit & Push
```bash
git add SOUL.md AGENTS.md
git commit -m "clean: mark legacy rules inactive, keep only HERMES OVERRIDE"
git push origin main
```

## Related
- `hermes-github-sync` — for git push verification