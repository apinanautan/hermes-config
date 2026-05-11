---
name: ufo-gpt-image-gen
description: |
  Generate 3D prop/object images via ChatGPT Custom GPT using Chrome CDP automation.
  Use when boss wants to create images for 3D modeling workflow.
  Triggers: boss asks to generate an image, provides a Thai prompt for a prop/object,
  using ChatGPT to create images for 3D printing/modeling, or any image generation request
  that uses the Custom GPT at chatgpt.com/g/g-69e8e8cd64fc81918d57af195508f4b1.
  This skill replaces manual ChatGPT Web usage — it runs gpt_background_image.py which
  handles Chrome CDP connection, prompt submission via DOM, dual verification gates
  (technical + Moondream vision), and auto-cleanup.
---

# ufo-gpt-image-gen

Generate images via ChatGPT Custom GPT for 3D modeling using Chrome CDP automation.

## Quick Usage

```bash
bash "/mnt/c/Users/[ถามรหัสจากเจ้านายเมื่อจำเป็น]/Desktop/Work Auto/ufo-gpt-image-gen/generate_bg.sh" "ร้านขายผ้าสีสันสดใส"
```

Output: PNG saved to `C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Desktop\Work Auto\รูป 3D\`

## Workflow

1. **Start Chrome CDP** via `start_chrome_bg.ps1` (verifies port 9222 is listening)
2. **Run `gpt_background_image.py`** — connects Chrome, submits prompt via DOM, waits for generated image
3. **Technical Gate** — image URL must be `backend-api/estuary/content`, resolution >= 1000x700, size >= 300KB
4. **Vision Gate** — Moondream describes image, qwen2.5:3b judges match (confidence >= 0.75)
5. **Save & cleanup** — PNG to output folder, delete `runtime 🏃💨` temp folder

## Key Paths

| Purpose | Windows Path |
|---------|-------------|
| **Output folder** | `C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Desktop\Work Auto\รูป 3D\` |
| **Tool root** | `C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Desktop\Work Auto\ufo-gpt-image-gen\` |
| **Runtime temp** | `C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Desktop\Work Auto\ufo-gpt-image-gen\runtime 🏃💨\` |
| **Chrome CDP** | `http://[::1]:9222` |
| **GPT URL** | `https://chatgpt.com/g/g-69e8e8cd64fc81918d57af195508f4b1` |

## Scripts

| Script | Purpose |
|--------|---------|
| `generate_bg.sh` | Main entry — call from WSL/Linux |
| `start_chrome_bg.ps1` | Start/verify Chrome remote debugging |
| `gpt_background_image.py` | Core automation (CDP connect → DOM input → verify → save) |
| `verify_image_moondream.py` | Single image verification tool |

## Verification Gates

See [references/verification.md](references/verification.md) for full details.

## Notes

- No real keyboard/mouse — all via CDP/DOM only
- Runtime temp folder is auto-deleted after completion
- Rejects thumbnails, previews, avatars automatically
- Only ChatGPT estuary content URLs are accepted
## Sensitive Code Handling

- If the boss provides a code/password in the current message, use it only to unlock the explicitly authorized task.
- Never save, copy, summarize, or persist the code/password in skill files, notes, backups, logs, or artifacts.
- After use, remove the code/password from any editable artifact touched in the task and replace it with `[ถามรหัสจากเจ้านายเมื่อจำเป็น]` when a placeholder is needed.

