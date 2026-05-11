# Pending Tasks

## งานหลัก: ChatGPT Web → รูป prop → Telegram
- [x] หา/ติดตั้ง Microsoft UFO ให้เจอ path ชัดเจน: `C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Tools\UFO`
- [x] สร้าง venv + install requirements ของ UFO แล้ว: `C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Tools\UFO\.venv`
- [x] Smoke test UFO: imports/API/help/no-op run ผ่าน
- [ ] ตั้ง/ทดสอบ UFO ให้คุม Chrome/ChatGPT Web + custom GPT ได้จริง
- [ ] ทำ wrapper command สำหรับ custom GPT: https://chatgpt.com/g/g-69e8e8cd64fc81918d57af195508f4b1
- [ ] ตั้ง output folder สำหรับรูปที่ download
- [ ] ทดสอบ workflow: รับ prop → generate → download → ส่ง MEDIA กลับ Telegram

## หมายเหตุ
- ห้ามใช้ image generator ตัวอื่นแทน ChatGPT Web custom GPT เว้นแต่เจ้านายสั่งชัดเจน
- ถ้าเริ่มหลุด/มั่ว ให้กลับมาอ่านไฟล์นี้กับ MEMORY.md ก่อนทำงานต่อ

## UFO provider
- [x] สลับ UFO ไปใช้ MiniMax OpenAI-compatible (`https://api.minimax.io/v1`, `MiniMax-M2.7`) พร้อม patch parser สำหรับ `<think>` แล้ว
- [x] เช็ค OpenAI Codex: ใช้ตรงกับ UFO ไม่ได้ เพราะไม่ใช่ `/chat/completions` API ปกติ
