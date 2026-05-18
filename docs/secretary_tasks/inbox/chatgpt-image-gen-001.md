# Task: chrome_image_gen

- **task_id:** chrome-gen-image-001
- **target:** OpenClaw-PC
- **type:** chrome_image_generation
- **objective:** เปิด ChatGPT แล้วสร้างรูป "หญิงสาว" สวย ๆ ตาม prompt นี้
- **steps:**
  1. เปิด Chrome → ไปที่ https://chatgpt.com/g/g-699b39eeedc4819180aeb6ad24c464d9
  2. รอหน้าโหลด
  3. ส่ง prompt: "สร้างรูปหญิงสาวสวย ๆ คนไทย หน้าตาน่ารัก เป็นธรรมชาติ ถ่าย portrait"
  4. รอรูปเสร็จ
  5. ดาวน์โหลดภาพมาไว้ที่ `~/Desktop/gpt-girl.png` หรือ path ที่เข้าถึงได้
  6. สรุป prompt ที่ใช้ + path ภาพ
- **safety:** ห้ามคลิก login/payment/signup
- **expected_report:** path รูป + prompt ที่ใช้ + status
- **timeout:** 300s
- **retry_limit:** 1
- **created:** 2026-05-14T21:40:00+07:00