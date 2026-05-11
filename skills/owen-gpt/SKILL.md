# owen-gpt

ติดต่อและสอบถามความเห็นจาก OwenGPT (Owenzzz Bot) บน ChatGPT เพื่อวางแผน วิเคราะห์ หรือขอคำปรึกษาเชิง Architecture

## ข้อมูลพื้นฐาน
- **GPT URL:** `https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot`
- **AdsPower User:** `k1cawerp`
- **Script:** `/mnt/c/Users/Apinan/owen-workspace/scripts/ask_owengpt.py`

## เงื่อนไขการใช้งาน (Trigger)
- เมื่อเจ้านายสั่ง "ปรึกษา OwenGPT", "ถามความเห็นจาก GPT", "ถามโอเว่น (GPT)", หรือ "OwenGPT ว่าไง"
- เมื่อต้องการแตกงานใหญ่เป็นขั้นตอน (Task Decomposition) ในระดับสูง

## ขั้นตอนการทำงาน
1. **เตรียมสภาพแวดล้อม และ Sync ข้อมูล:**
   - ใช้ `exec` รัน `/mnt/c/Users/Apinan/owen-workspace/scripts/sync_to_git.sh` เพื่อให้ข้อมูลบน GitHub ล่าสุดที่สุด
   - ใช้ `exec` รัน curl เพื่อเปิด AdsPower (Profile `k1cawerp`) พร้อมพารามิเตอร์ `&headless=1`
   - ตัวอย่าง: `curl -s "http://127.0.0.1:50325/api/v1/browser/start?user_id=k1cawerp&api_key=[API_KEY]&headless=1"`
2. **ดึงข้อมูลเชื่อมต่อ:**
   - สกัด `ws.puppeteer` จากผลลัพธ์ของ AdsPower API
3. **รันคำสั่งถาม GPT:**
   - ใช้ `exec` รัน Python script พร้อมส่ง CDP URL และคำถามของเจ้านาย
   - ตัวอย่าง: `python scripts/ask_owengpt.py "[CDP_URL]" "[คำถาม]"`
4. **สรุปผล:**
   - นำคำตอบจาก OwenGPT มาสรุปให้เจ้านายฟัง โดยคงรูปแบบหัวบทสนทนาของ Owen ไว้
5. **ปิดหน้าจอ:**
   - เรียก `browser/stop` เพื่อคืนทรัพยากรทุกครั้ง

## ข้อควรระวัง
- ห้ามดึงข้อมูลความลับ/รหัสผ่านไปถาม GPT
- รันแบบ `headless=1` เสมอเพื่อไม่ให้กวนหน้าจอเจ้านาย
- หาก GPT มีการตอบโต้ที่ต้องการการตัดสินใจ ให้แจ้งเจ้านายก่อนดำเนินการต่อ
