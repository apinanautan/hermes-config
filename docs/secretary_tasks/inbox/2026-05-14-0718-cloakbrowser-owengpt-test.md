# Task: CloakBrowser Persistent Profile — OwenGPT Test

- **From:** Hermes-PC (routed from Telegram)
- **Target:** OpenClaw-PC
- **Objective:** ใช้ session ChatGPT จริงที่ login ค้างอยู่ เพื่อคุยกับ OwenGPT ผ่าน browser automation
- **Created:** 2026-05-14 07:18

## Steps

1. **หา CloakBrowser profile จริงที่ใช้งานประจำ** — ตรวจ profile directories ที่มีอยู่:
   - `C:/Users/Apinan/.cloakbrowser/profiles/`
   - `C:/Users/Apinan/AppData/Local/CloakBrowser/profiles/`
   - `C:/Users/Apinan/AppData/Roaming/CloakBrowser/profiles/`
   - หรือ paths อื่นที่มี `--user-data-dir` หรือ `--profile-directory`

2. **ใช้ persistent user-data-dir/profile เดิม** — ห้ามใช้ sandbox/temp/incognito

3. **ห้าม:**
   - logout session
   - replace cookies
   - close existing chats
   - open sandbox session

4. **เปิด URL ตรง:**
   ```
   https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot
   ```

5. **Verify login status** — ตรวจว่ายัง login ค้างอยู่จริง (ไม่ต้องกด login ใหม่)

6. **หา composer/input** — รอให้ page โหลดเสร็จ แล้วหา input field สำหรับส่ง message

7. **ส่ง message:**
   ```
   Hermes-PC connected. Test message.
   ```

8. **Verify** — ตรวจว่าข้อความถูกส่งจริง (message ปรากฏใน chat)

## Fallback (ถ้า CloakBrowser ไม่มี)

- **pywinauto** — UI automation บน Windows
- **UFO** — ถ้ามี UFO framework
- **UI automation** — Windows UI automation API

## Expected Report

- **profile path ที่ใช้:** absolute path ของ user-data-dir ที่ใช้จริง
- **login status:** logged in / logged out / needs re-login
- **current URL:** URL หลังโหลดเสร็จ
- **message sent:** สำเร็จ / ล้มเหลว
- **verification:** ข้อความปรากฏจริงใน chat

## Timeout

- **30 นาที** (พอสำหรับ browser automation + manual intervention ถ้าจำเป็น)
