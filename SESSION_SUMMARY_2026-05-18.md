# Hermes Session Summary — 2026-05-18 (UPDATED 21:17)

## สถาปัตยกรรมปัจจุบัน

- **Dispatcher v2** (รัน): `C:\Users\Apinan\hermes-clean\scripts\dispatcher.py` PID 18964
- **Hermes Gateway**: ❌ หยุดถาวร — `Hermes_Gateway` scheduled task = Disabled
- เหตุผลที่ทิ้ง gateway: gateway LLM **แต่ง mock log "Kiro:..., Owen:..." เอง** ไม่เรียก script จริง — bypass flow ได้
- Dispatcher v2 = strict state machine บังคับ flow ใน Python ไม่ใช่ prompt

## Flow

```
Telegram → dispatcher.py
├── Q&A → llm_call() ตอบเลย
└── Work mode (keyword: เขียน/แก้/สร้าง/ลบ/code/script/file/...)
    1. send "📋 รับงาน"
    2. send "🤖 กำลังถาม Kiro..." → subprocess kiro-cli.exe (REAL)
    3. send "✅ ได้รับคำตอบจาก Kiro แล้ว"
    4. send "🧠 กำลังถาม OwenGPT..." → subprocess ask_owengpt.py (REAL)
    5. send "✅ ได้รับคำตอบจาก OwenGPT แล้ว"
    6. send "📋 ได้รับคำตอบทั้งสอง — แผน:... ให้ทำเลยไหม?"
    7. รอ "ทำเลย" → Worker LLM ทำ → รายงานผล TH
```

## Commands
- `/model` — inline keyboard provider→model (state ที่ `.dispatcher_state.json`)
- `/help`, `/status`, `/new`

## Files หลัก
```
C:\Users\Apinan\hermes-clean\scripts\
├── dispatcher.py            ← MAIN (รันตลอด)
├── ask_owengpt.py           ← OwenGPT via AdsPower CDP
├── .dispatcher_state.json   ← current model/provider
├── .dispatcher_offset.json  ← Telegram offset
└── .owengpt_port            ← cached CDP port (52631)
```

## API Keys
ที่ `C:\Users\Apinan\AppData\Local\hermes\.env`:
- `TELEGRAM_BOT_TOKEN` (8717275013:AAFl... = @MeszzzBot)
- `ADSPOWER_API_KEY` (ใช้ Bearer prefix)
- `OLLAMA_PAY_API_KEY`
- `OPENCODE_GO_API_KEY`

🚨 OwenGPT เตือน: keys อาจ exposed ใน config — ควร rotate

## Providers/Models
- **Default**: `glm-5.1:cloud` via `ollama-pay` (ใช้งานได้แน่)
- **opencode-go**: 10 models (deepseek-v4, minimax, kimi, glm, qwen, mimo)
- **ollama-pay**: 17 models (รวม deepseek-v4-flash:cloud, gpt-oss:120b-cloud)
- ⚠️ `qwen3.5:397b-cloud` server timeout บ่อย

## AdsPower / OwenGPT
- Profile: `k1cawerp`
- API: `http://local.adspower.net:50325`
- OwenGPT URL: `https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot`
- ทุกครั้ง: เปิด page → ส่ง → wait response → ลบ chat (PATCH is_visible:false)

## Kiro CLI
- Path: `C:\Users\Apinan\AppData\Local\Kiro-Cli\kiro-cli.exe`
- `kiro-cli.exe chat --no-interactive --trust-all-tools --model claude-sonnet-4.6 "<EN>"`
- Auto-approve: feed `y\n` ผ่าน stdin threading

## บัคที่แก้แล้ว
1. qwen3.5 timeout → เปลี่ยน default เป็น glm-5.1:cloud
2. /model พิมพ์เลข → ทำเป็น inline keyboard
3. Gateway ไม่ enforce flow → ลบ gateway, สร้าง dispatcher v2
4. tool_use_enforcement auto→off
5. Kiro ถาม approval → --trust-all-tools + y\n stdin

## คำแนะนำจาก OwenGPT (consultation 21:08)

**หลักคิด**: dispatcher = controller, Hermes runtime = tool executor only

**Architecture ที่ควรเพิ่ม:**
```
Brain (Kiro+Owen) → User confirm → classify_execution_mode:
  ├── plain_llm     → llm_call()
  ├── hermes_tools  → hermes_tool_worker.py (subprocess bridge)
  └── human_required → ถามเจ้านาย
```

**Next steps (ยังไม่ทำ):**
1. Task JSON schema (task_id, plan, execution_mode, required_tools, risk, status, acceptance_checks)
2. `classify_execution_mode()` — LLM ตอบ JSON validate ด้วย code
3. **`hermes_tool_worker.py`** — subprocess bridge เรียก Hermes CLI/runtime
4. Route `/skill_view` ผ่าน Hermes Tool Worker
5. Health checks (Kiro timeout/approval detector, Owen AdsPower check)
6. Persistent session memory (SQLite/JSONL)
7. Tiny intent classifier แทน keyword

**กฎเหล็ก:**
- ❌ ห้าม re-enable Hermes_Gateway scheduled task
- ❌ ห้ามย้าย Telegram polling กลับ gateway
- ✅ Hermes runtime = executor only (หลัง user confirm)
- ✅ งาน code ใช้ SocratiCode gate

## ปัญหาคงค้าง (a-j)
- (a) Dispatcher ไม่มี Hermes tools native
- (b) Worker = plain chat ไม่มี tool calling
- (c) Brain แนะนำ tool แต่ worker เรียกไม่ได้
- (d) /skill_view ยังไม่ implement
- (e) hermes config/skills ไม่ถูกโหลด
- (f) Kiro y\n stdin เปราะ
- (g) ask_owengpt.py ไม่มี healthcheck
- (h) Keyword classifier false positive
- (i) ไม่มี persistent memory
- (j) เพิ่ม tools ใหม่ยาก

## Cleanup ที่ค้าง
ลบไฟล์ขึ้นต้น `_` ใน `C:\Users\Apinan\hermes-clean\scripts\`:
- `_consult_owengpt.py`, `_read_chatgpt.py` (test consultation)
- (อื่นๆ ถ้ามีจาก loop tests)

## Status เมื่อปิด session
- ✅ dispatcher v2 PID 18964 รันอยู่
- ❌ hermes.exe ไม่มี
- ❌ Hermes_Gateway task = Disabled
- ✅ AdsPower CDP port 52631 active

## TODO ลำดับ priority
1. Cleanup test scripts (_*)
2. Implement Task JSON + classify_execution_mode
3. สร้าง hermes_tool_worker.py
4. Route /skill_view ผ่าน Hermes Tool Worker
5. Health checks
6. Persistent session memory
7. Rotate API keys (ถ้าจำเป็น)
