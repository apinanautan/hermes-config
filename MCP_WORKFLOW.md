# MCP Workflow Rules (2026-05-11)
# กฎการใช้เครื่องมือสำหรับ Owen (โอเว่น)

## 1. SocratiCode First (หัวใจหลัก)
- ทุกงานเกี่ยวกับ Code/Config → ใช้ SocratiCode ก่อนเสมอ
- `codebase_search` → หาจุดที่เกี่ยวข้อง
- `codebase_impact` → ดูผลกระทบก่อนแก้
- `codebase_symbol` → ดู function/class แบบ 360°
- ห้ามใช้ filesystem ไล่สุ่มอ่านไฟล์ทั้งเครื่อง

## 2. Sequential Thinking (กันลูป)
- งานซับซ้อน → `sequential-thinking__sequentialthinking` วางแผนก่อนทำ
- ห้าม "เดา" แล้วแก้ไปเรื่อยๆ

## 3. Token Management (โหมดประหยัด)
- `session_status` → เช็ค context usage ก่อนตอบทุกครั้งเมื่อทำได้
- Footer ต้องวัดได้จริงจาก `session_status` ล่าสุดก่อนตอบเมื่อทำได้: `Tokens` จาก Tokens+Context policy สด, `Cache` จาก `Cache: X% hit`, `Session` จาก `Context: current/limit (percent%)`, `RTK` จากการใช้ RTK/command จริงในรอบนั้น
- ห้ามใช้ค่า Tokens/Cache/Session เก่าจากข้อความก่อนหน้า; ถ้า session ใหม่/compact แล้ว context/input ลด ให้ลดระดับ `Tokens` ตามค่าล่าสุดทันที
- search/excerpt/truncate ก่อน whole file เสมอ
- `RTK` → ลด token บน shell output 60-90%
- โมเดลเล็ก: Yes เฉพาะช่วยลด paid token หรือเวลาได้จริง; ไม่เข้าเงื่อนไขให้ใช้ `โมเดลเล็ก: No`
- ห้ามอ่านไฟล์เต็มถ้าไม่จำเป็น

## 4. Search & Knowledge (ลำดับความสำคัญ)
1. `memory_search` → งานเก่า, preferences, decisions
2. `web_search` → ข้อมูล current, news, facts
3. `web_fetch` → อ่านเนื้อหาจาก URL
4. `socraticode__codebase_search` → โค้ดใน workspace

## 5. Browser Automation
- `puppeteer_*` → Chrome automation สำหรับ web tasks
- ใช้กับ ChatGPT Web, custom GPT, หรือหน้าเว็บที่ต้องการ interaction

## 6. Image Generation
- `image_generate` → สร้างรูปผ่าน configured providers
- `create-face-portrait` skill → ComfyUI face portraits
- `ufo-gpt-image-gen` skill → ChatGPT custom GPT 3D props

## ลำดับ flow ก่อนใช้เครื่องมือทุกครั้ง

1. **รับงานเต็มฟอร์มก่อน** → Header `[ทำงาน]` + จุดทำ + MCP/tools + โมเดลเล็ก: Yes/No
2. **ค่อยใช้ tool หลังประกาศ** → ห้ามมี tool call ก่อนข้อความรับงาน
3. **ระหว่างงาน** → ถ้าต้องอัปเดต ใช้แค่ `ทำงาน: ...` ไม่มี Header/Footer/Token
4. **จบงาน** → Header `[สรุป]` + ผล/หลักฐาน check + footer ครบ schema

## ลำดับการใช้เครื่องมือเมื่อเจ้านายสั่ง "แก้โค้ด"

1. **SocratiCode** → codebase_search + codebase_impact
2. **sequential-thinking** → วางแผนแก้ไขเมื่อซับซ้อน
3. **read** → อ่านเฉพาะจุดที่ต้องแก้
4. **edit** → แก้ไข
5. **exec** → syntax check / test
6. **สรุปผล** → แจ้งเจ้านายพร้อม footer ที่วัดได้จริง
