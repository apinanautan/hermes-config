# owen-gpt

ติดต่อและสอบถามความเห็นจาก OwenGPT (Owenzzz Bot) บน ChatGPT ผ่าน AdsPower profile ที่ยืนยันตัวตนแล้วเท่านั้น

## ข้อมูลพื้นฐาน
- **GPT URL:** `https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot`
- **Script:** `/mnt/c/Users/Apinan/owen-workspace/scripts/ask_owengpt_direct.py`

## กฎบังคับ
- ใช้ **AdsPower only**
- ใช้ **profile ที่เจ้านายกำหนดเท่านั้น**
- ใช้ **CDP/debug endpoint ของ profile นั้น**
- ต้องคง **logged-in ChatGPT session** ไว้
- ห้ามใช้ CloakBrowser
- ห้ามเปิด default Chrome
- ห้ามสร้าง temp profile
- ห้าม switch profile อัตโนมัติ
- ถ้า profile / CDP / login ไม่พร้อม → STOP และรายงาน blocker

## รูปแบบสคริปต์
- `ask_owengpt_direct.py` รับ `--cdp` ได้
- ไม่ hardcode `9222`
- พ่นผลลัพธ์เป็น **JSON only**

## กลไกการทำงาน
1. ใช้ AdsPower profile ที่ล็อกไว้แล้ว
2. ต่อเข้า CDP/debug endpoint ของ profile นั้น
3. ตรวจว่ามีแท็บ OwenGPT / composer พร้อมใช้งาน
4. ถ้าพร้อม ให้ถาม OwenGPT ใน session เดิม
5. รายงานกลับด้วย JSON ที่มีฟิลด์ที่กำหนด

## ฟีเจอร์การรักษาแชท
- หากมีแท็บ OwenGPT ที่ล็อกอินอยู่แล้ว ให้ reuse แท็บเดิมก่อน
- ถ้าจำเป็นค่อยเปิดแท็บใหม่ **ภายใน profile เดิม** เท่านั้น
- ห้ามสลับ browser หรือ profile อื่นอัตโนมัติ
