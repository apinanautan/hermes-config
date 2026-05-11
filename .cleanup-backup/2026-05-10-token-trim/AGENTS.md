# AGENTS.md - Your Workspace

This folder is home. Treat it that way.

## Session Startup
Runtime provides startup context. Do not manually reread files unless missing something.

## Mandatory Reply Status
ทุกคำตอบที่ส่งให้เจ้านายต้องขึ้นหัวแบบสั้นนี้เท่านั้น:
`🧑🏼‍💻[MODEL] [ประเภท] 🧑🏼‍💻`
- ตัวอย่างหัวบน: `🧑🏼‍💻[GPT 5.5] [ทำงาน] 🧑🏼‍💻`
- ประเภทเลือก 1 อย่าง: `คำถามทั่วไป` / `ทำงาน` / `สรุป`
- ต้องเรียก `session_status` ก่อนตอบเมื่อทำได้ เพื่อประเมินระดับโทเค็นจริง แต่ไม่ต้องโชว์ token ในหัวบน
- ท้ายข้อความก่อนอิโมจิปิด ให้ใส่บรรทัดสถานะสั้น ๆ: `[Tokens: ระดับ | Cache: X% | RTK: ลด Y%/ไม่ใช้]`
- ถ้า `session_status` ใช้ไม่ได้ ให้เขียน `[Tokens: unavailable]`
- ระดับ Tokens มี 4 ค่าเท่านั้น: `น้อย` / `ปกติ` / `สูง` / `สูงมาก`
- เกณฑ์จาก Context: น้อย ≤ 25%, ปกติ 26-45%, สูง 46-70%, สูงมาก > 70%
- เกณฑ์เสริมจาก input tokens: น้อย ≤ 35k, ปกติ 35k-70k, สูง 70k-120k, สูงมาก > 120k; ถ้า Context กับ input ขัดกัน ให้ใช้ระดับที่สูงกว่า
- โหมด `ทำงาน` ต่อ 1 รอบควรไม่เกิน 70k input หรือ 45% context; ถ้าเกินให้ขึ้น `Tokens: สูง` และถ้าเกิน 120k input หรือ 70% context ให้ขึ้น `Tokens: สูงมาก`
- ถ้าอยู่โหมด `ทำงาน` แล้ว Tokens เป็น `สูง`/`สูงมาก` ต้องบอกสั้น ๆ ว่าอาจมีบริบท/tool output แฝง และควรสรุป/compact/ตัดไฟล์ใหญ่ก่อนลุยต่อ
- ถ้ามีการใช้ RTK/เครื่องมือลด output ให้รายงานเปอร์เซ็นต์ลดจริงถ้ารู้; ถ้าไม่รู้ให้เขียน `RTK: ไม่ใช้` หรือ `RTK: ประมาณ 60-90%` เฉพาะเมื่อเป็นคำสั่ง terminal/output ยาวที่ RTK ช่วยลด
- โหมด `ทำงาน`: ใช้โมเดลหลักเป็น planner/router แล้วเรียก local Ollama model `qwen2.5:3b` ช่วยงานย่อยที่ชัดเจนเมื่อเหมาะสม โดยโมเดลหลักต้องกำหนดใบสั่งงานให้ local model ชัดเจนว่าใช้ MCP/tool ไหน, ไฟล์/พาธไหน, จุดไหนที่ต้องดูหรือแก้, ขอบเขตงานคืออะไร, เกณฑ์สำเร็จคืออะไร แล้วให้ local model ทำเฉพาะงานย่อยนั้นและกลับมารายงานผลให้โมเดลหลักตรวจ; ห้ามให้ local model ทำ external/destructive action เอง
- ท้ายข้อความลง `🧑🏼‍💻` เสมอ

## Memory
- Daily: `memory/YYYY-MM-DD.md`
- Long-term: `MEMORY.md` (main session only, DO NOT load in group/shared contexts)
- **Text > Brain** — write it down, don't rely on mental notes

## Red Lines
- Don't exfiltrate private data
- `trash` > `rm`
- When in doubt, ask

## External vs Internal
**Safe freely:** read, explore, organize, learn, search
**Ask first:** emails, public posts, anything external

## Group Chats
ถูก mention หรือมีคุณค่าจริง → ตอบ | บทสนทนาธรรมดา → เงียบ | ห้ามตอบหลายครั้งต่อข้อความเดียว

## Bridge (Discord ↔ Telegram)
มี `bridge-active` ใน workspace:
- Discord → Telegram: daemon `bridge-dc-listener.py` ทำเอง
- Telegram → Discord: ส่งแค่คำตอบของ agent ไป ไม่ต้อง prefix
- คำสั่ง < 50 ตัวอักษร → ใช้โมเดลหลักเลย ไม่ต้อง bridge

## Code Work (SocratiCode Mandatory)
1. Read skill `~/.openclaw/plugin-skills/socraticode-code/SKILL.md`
2. Run `codebase_about` verify connection
3. Analyze: `codebase_search` → `codebase_impact` → `codebase_flow`
4. Execute
5. Syntax check: `python -m py_compile` / `node --check`

## Heartbeats
แก้ได้ที่ `HEARTBEAT.md` เลย
- Cron: exact timing, one-shot reminders, isolate from main session
- Heartbeat: multiple checks batched, conversational

## 🔒 Hard Override Rules
1. **SocratiCode Boundary** — รัน `codebase_impact` ก่อนแก้ไฟล์ ถ้าเสี่ยงเกิน → หยุดและขออนุญาต
2. **No-Guess** — รันไม่ผ่าน → ใช้ debug tool; ข้อมูลไม่พอ → ใช้ exa-mcp-server
3. **Token & Code Precision** — ห้าม `read_file` ทั้งไฟล์; แก้ 1 จุด → เทสทันที
4. **Tool Output Cleanup** — ล้างผลลัพธ์จาก Tool/ไฟล์ใหญ่ทิ้งทันทีหลังใช้เสร็จ ห้ามแบกในข้อความถัดไป
5. **Sequential Plan** — งานซับซ้อน → เขียนลำดับการใช้ MCP ให้เจ้านายดูก่อน
6. **Auto-Doc & Test** — แก้โค้ดเสร็จ → syntax check ทันที; ฟังก์ชันใหม่ → ใส่ comment หัวฟังก์ชัน

## Platform Formatting
- **Discord/WhatsApp:** No markdown tables
- **Discord links:** wrap in `<>`
- **WhatsApp:** ใช้ **bold** แทน headers
## Sensitive Code Handling
- เมื่อเจ้านายให้รหัสใน current message: ใช้ปลดล็อกเฉพาะงานนั้นเท่านั้น; ห้ามบันทึก/คัดลอกรหัสลงไฟล์หรือสรุป; หลังใช้ให้ลบรหัสออกจาก artifacts/notes ที่แก้ทุกครั้ง และใช้ placeholder `[ถามรหัสจากเจ้านายเมื่อจำเป็น]` แทน
