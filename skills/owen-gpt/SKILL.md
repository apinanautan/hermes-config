# owen-gpt

ติดต่อและสอบถามความเห็นจาก OwenGPT (Owenzzz Bot) บน ChatGPT ผ่านกลไก "ตัวแทนตัวเล็ก" (Sub-agent Bridge) เพื่อประหยัดโทเค็นของ Session หลัก

## ข้อมูลพื้นฐาน
- **GPT URL:** `https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot`
- **Script:** `/mnt/c/Users/Apinan/owen-workspace/scripts/ask_owengpt.py`

## กลไกการทำงาน (Sub-agent Bridge - บังคับใช้)
เพื่อไม่ให้ Session หลักเสียโทเค็นในการอ่านคำตอบยาวๆ จาก ChatGPT:
1. **Main Agent (ผม):** จะไม่รันงานเอง แต่ทำหน้าที่เป็น "คนสั่งงาน" เท่านั้น
2. **Sub-agent (ตัวเล็ก):** ผมจะเรียก `sessions_spawn` โดยใช้โมเดลเล็ก (ปกติคือ `ollama/qwen2.5:3b`)
3. **Direct Delivery:** ตั้งค่า `delivery: { mode: "announce" }` ในตัวเล็ก เพื่อให้ผลลัพธ์จาก ChatGPT ถูกส่งตรงไปยัง Telegram ของเจ้านายทันที โดยไม่ไหลกลับเข้า Context ของผม
4. **No Post-Processing:** เมื่อตัวเล็กส่งงานเสร็จ ผมจะไม่สรุปงานหรืออ่านผลซ้ำ ยกเว้นเจ้านายจะถามเพิ่ม

## ขั้นตอนการส่งงาน (Execution Flow)
1. **Sync ข้อมูล:** รัน `scripts/sync_to_git.sh` เพื่อให้ OwenGPT เห็น Code ล่าสุดบน GitHub
2. **เปิด Bridge:** เรียก `sessions_spawn` ด้วยการตั้งค่าดังนี้:
   - `model`: "ollama/qwen2.5:3b"
   - `task`: "รัน scripts/ask_owengpt.py และส่งข้อความจาก OwenGPT (ChatGPT) ให้เจ้านายทันที"
   - `delivery`: `{ "mode": "announce", "to": "telegram:1060942816" }`
3. **จบ Turn:** ผมจะแจ้งเจ้านายว่า "ส่งงานให้ตัวเล็กคุยกับ OwenGPT แล้วครับ" และจบ Turn ทันที
