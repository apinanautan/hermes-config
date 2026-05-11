---
name: create-face-portrait
description: Generate face portraits only through local ComfyUI. Use when the user asks for a headshot, face-only portrait, Thai or Asian woman portrait, white background, even lighting, no shadow, or when the image must be rendered in ComfyUI instead of external image generators.
---

# สร้างรูปหน้าคน

## Rule

ใช้ **ComfyUI เท่านั้น** ห้ามใช้ image_generate หรือ image model ภายนอกทุกกรณี

## Workflow

1. ตรวจว่า ComfyUI เปิดอยู่ที่ `http://localhost:8188`
2. ใช้ workflow ใน `references/face_portrait_workflow.json`
3. Workflow นี้ยึด `flux1-dev-fp8.safetensors` เป็นตัวหลัก
4. ถ้าผู้ใช้ต้องการหน้าไม่ซ้ำ ให้ปล่อย seed สุ่ม หรือเปลี่ยน seed ทุกครั้ง
5. แก้เฉพาะ prompt / negative / seed ตามที่สั่ง
6. รัน `scripts/create_face_portrait.py`
7. ส่งผลลัพธ์รูปที่ได้กลับไป

## ค่าเริ่มต้น

- หน้าตรง
- พื้นหลังขาว
- แสงสม่ำเสมอ
- ไม่มีเงา
- หน้าคนธรรมดา เอเชีย ถ้าผู้ใช้ต้องการสไตล์นั้น

## ใช้งาน

```bash
python3 ~/.openclaw/plugin-skills/create-face-portrait/scripts/create_face_portrait.py \
  --prompt "ordinary Asian woman portrait, natural face, slight asymmetry, realistic skin texture, front-facing, looking at camera, pure white background, flat even softbox lighting, no shadows, unique facial features"
```

ตัวเลือก:
- `--workflow PATH` ใช้ workflow อื่น
- `--negative TEXT` เปลี่ยน negative prompt
- `--seed N` ล็อก seed
- `--save-as PATH` ดาวน์โหลดรูปแรกมาเก็บไว้

## ข้อห้าม

- ห้ามใช้ OpenAI image generator
- ห้ามใช้ Gemini image generator
- ห้ามเปลี่ยนไปใช้ backend อื่นแทน ComfyUI
## Sensitive Code Handling

- If the boss provides a code/password in the current message, use it only to unlock the explicitly authorized task.
- Never save, copy, summarize, or persist the code/password in skill files, notes, backups, logs, or artifacts.
- After use, remove the code/password from any editable artifact touched in the task and replace it with `[ถามรหัสจากเจ้านายเมื่อจำเป็น]` when a placeholder is needed.

