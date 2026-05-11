User expects FULL end-to-end automation — "มึงต้องสร้างรูปให้กูเลย" (create and send image, don't ask user to do anything). Frustrated when asked to perform manual steps.
§
For Telegram Mes_bot / @Owenzzz_bot requests, user wants changes limited strictly to the Telegram/OpenClaw bot and does not want unrelated Hermes Workspace edits.
§
AiFace/Character Creator v4.52: ใช้แค่ใบหน้า ผมไม่สำคัญ ต้องการหน้าต่างกันชัด — user ให้แค่ ชื่อ/เพศ/วัย ให้กูกำหนด face features เองที่เหลือ
§
Pain point: Zero-Log — ชี้บ่อย "ทำไมมึงยังทำไม่ได้"; ต้องการ auto-cleanup ระบบไม่ใช่ model พยายามเอง; ห้ามพ่นหลายข้อความระหว่าง process ต้อง auto-unsend ช่วง local ทำงาน เหลือแค่รายงานผล/สรุป
§
Data Handling: เมื่อเจ้านายส่ง Path ไฟล์มา ให้รีบเรียกใช้ filesystem tool เพื่ออ่านผ่าน Hermes 3 ทันที ไม่ต้องรอให้ user สั่งซ้ำ
§
ผู้ใช้ต้องการให้ OpenClaw ใช้งานได้ตามปกติ ห้ามลบ OpenClaw/gateway/service/config อีก และงานใดๆ ที่แตะ OpenClaw ต้องถามกลับก่อนพร้อมรออนุญาตชัดเจนจากผู้ใช้ก่อนเสมอ
§
| เจ้านาย: robberzaz (Telegram @Owenzzz_bot) | ชื่อ: เมท | ใช้ [MiniMax] status
§
§ robberzaz (@Owenzzz_bot, เมท, ID:1060942816) | MiniMax status | Thai | zero-log
§ ชอบ test ก่อน activate — fix ต้อง test แล้วสรุป ห้ามตั้งเลยแล้วรันเลย
§ HARDCODED: ทุกข้อความ → รัน minimax-workflow ผ่าน universal_bridge.py
§ ประหยัด token: ปิด skill index แล้ว (~1,600 tok/msg saved)