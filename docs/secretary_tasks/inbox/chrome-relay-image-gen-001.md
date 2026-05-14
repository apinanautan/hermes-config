# Task: chrome_question_relay

- **task_id:** chrome-relay-image-gen-001
- **target:** OpenClaw-PC
- **type:** chrome_question_relay
- **question:** ทำยังไงให้ Hermes-Agent สร้างรูป (image generation) ผ่าน ChatGPT/GPT ได้ ขอ workflow และ technical steps ที่เป็นไปได้ อ้างอิงจาก GPT ตัวนี้: https://chatgpt.com/g/g-699b39eeedc4819180aeb6ad24c464d9
- **context:** |
    Hermes-Agent (WSL/Windows) ต้องการ integrate กับ ChatGPT image generation tool
    ให้หาวิธีที่ practical สำหรับ Hermes-PC ซึ่งใช้ Hermes framework อยู่
    - มี image_generate tool อยู่แล้ว (built-in)
    - ต้องการรู้ว่า GPT นั้นใช้ approach อะไร
- **expected_output:** |
    - Summary ของ approach ที่ GPT ใช้
    - Code/command ที่เอาไป implement ได้เลย
    - รูปแบบ output ที่คาดหวัง
- **report_path:** docs/secretary_tasks/reports/chrome-relay-image-gen-001.md
- **timeout_seconds:** 300
- **retry_limit:** 1
- **created:** 2026-05-14T21:35:00+07:00