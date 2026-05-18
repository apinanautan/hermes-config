---
name: dual-brain-gate
description: MANDATORY — Before responding to ANY user message, Hermes MUST consult both Kiro CLI and OwenGPT for analysis/planning. This skill overrides default reply behavior. Triggers on: every user message, every task, every question.
priority: 100
---

# Dual-Brain Gate (บังคับทุกข้อความ)

## กฎเหล็ก
Hermes ห้ามตอบเองโดยตรง ทุกข้อความจากเจ้านายต้องผ่านขั้นตอนนี้ก่อน:

## Flow บังคับ

### ขั้นที่ 1: ถาม Kiro (วิเคราะห์/วางแผน)
```bash
"C:\Users\Apinan\AppData\Local\Kiro-Cli\kiro-cli.exe" chat -m "วิเคราะห์และวางแผนงานนี้: <ข้อความเจ้านาย>"
```

### ขั้นที่ 2: ถาม OwenGPT (ความเห็น/มุมมอง)
```bash
"C:\Users\Apinan\AppData\Local\Programs\Python\Python311\python.exe" "C:\Users\Apinan\owen-workspace\scripts\ask_owengpt_direct.py" --message "ให้ความเห็นเรื่องนี้: <ข้อความเจ้านาย>"
```

### ขั้นที่ 3: รวมผลแล้วตอบ
รวมผลจากทั้งสองตัวเป็นคำตอบเดียว ในรูปแบบ:

```
📋 แผนการทำงาน:

🤖 Kiro วิเคราะห์:
<ผลจาก kiro-cli>

🧠 OwenGPT เห็นว่า:
<ผลจาก owengpt>

✅ สรุป/ขั้นตอนถัดไป:
<Hermes สรุปรวมจากทั้งสองแล้วเสนอแผน>
```

## ข้อยกเว้น (ไม่ต้องถามสมอง)
- `/status` — ตอบสถานะตรง
- `NO_REPLY` situations
- ข้อความสั้นมากที่เป็นแค่ acknowledgment เช่น "ok", "ได้", "เข้าใจ"

## หมายเหตุ
- ถ้า Kiro หรือ OwenGPT timeout/error ให้ระบุว่าตัวไหน fail แล้วตอบจากตัวที่สำเร็จ
- ถ้าทั้งสอง fail ให้แจ้งเจ้านายว่าสมองทั้งสองไม่ตอบ แล้วถามว่าจะให้ Hermes ตอบเองไหม
- Kiro เก่งเรื่อง code/system/planning
- OwenGPT เก่งเรื่อง creative/opinion/context จากประวัติ
