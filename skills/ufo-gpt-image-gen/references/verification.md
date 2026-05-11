# Verification Gates

All generated images must pass **two verification gates** before being saved.

## Gate 1: Technical Gate

Checks applied to every candidate image:

| Check | Requirement | Reject Reason |
|-------|------------|---------------|
| URL | Must contain `backend-api/estuary/content` | ไม่ใช่ ChatGPT estuary content URL |
| HTTP status | `ok == true` | fetch ไม่สำเร็จ status=X |
| Content-Type | Must contain `image` | content-type ไม่ใช่รูป: X |
| Resolution (full) | >= 1000x700 | resolution ต่ำเกินไป/น่าจะ thumbnail: XxY |
| Size (full) | >= 300,000 bytes | ไฟล์เล็กเกินไป/น่าจะ preview: X bytes |
| Resolution (preview) | >= 768x768 | resolution ต่ำเกินไป: XxY (with `--allow-preview`) |
| Size (preview) | >= 120,000 bytes | ไฟล์เล็กเกินไป: X bytes (with `--allow-preview`) |

This gate filters out:
- 512x512 JPEG thumbnails
- Avatars and UI icons
- Cached previews from previous generations
- Non-ChatGPT images on the page

## Gate 2: Vision + Text Judge

If an image passes the technical gate, it is verified semantically:

1. **Moondream** (`moondream:latest`) describes the image in English
2. **qwen2.5:3b** compares the description against the original prompt
3. Returns JSON: `{"matches_prompt": bool, "confidence": 0.0-1.0, "detected_subject": "...", "reason": "..."}`

Decision rule: `matches_prompt == true AND confidence >= 0.75`

### Scoring Guidelines

- **matches_prompt = true**: Caption clearly shows the requested main objects
  - Style words like "3D prop", "low detail", "smooth" are NOT required
  - If the core subject is present and recognizable, pass
- **matches_prompt = false**: Main subject is missing or clearly wrong
- **Style constraints** (white background, no people, no text) reduce confidence only when **clearly violated**

### Thai Prompt Handling

The text judge translates Thai intent:
| Thai | Interpreted as |
|------|---------------|
| ร้านขายผ้า | cloth/fabric shop or stall |
| กระท่อมเล็กๆ | small hut/cottage |
| ผ้าหลากสี | colorful cloth/towels/fabric hanging or folded |
| (any prop/object name) | Look for that object as the main subject |

## Verify Single Image

```powershell
py 'C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Desktop\Work Auto\ufo-gpt-image-gen\verify_image_moondream.py' 'C:\path\to\image.png' 'ร้านขายผ้า'
```

Outputs a JSON report with vision model result.

## Rejection Flow

```
New image detected on page
    │
    ▼
Technical Gate ──FAIL──▶ Skip, try next image
    │
   PASS
    │
    ▼
Fetch image bytes via CDP (b64 encoded)
    │
    ▼
Moondream caption ──empty──▶ Skip
    │
    ▼
Text Judge (qwen2.5:3b)
    │
    ├── matches_prompt=false OR confidence<0.75 → Skip, try next image
    │
    └── matches_prompt=true AND confidence>=0.75 → ✅ SAVE PNG
```

## CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `prompt` | (required) | Thai prompt to send to ChatGPT |
| `--output`, `-o` | auto-timestamped | Output PNG path |
| `--cdp` | `http://[::1]:9222` | Chrome CDP endpoint |
| `--timeout` | 150 | Max seconds to wait for image |
| `--vision-model` | `moondream:latest` | Ollama vision model |
| `--min-confidence` | 0.75 | Minimum confidence threshold |
| `--allow-preview` | false | Allow lower-res preview images |