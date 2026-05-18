#!/usr/bin/env python3
"""
Hermes Brain Dispatcher v2 — Real Flow with Progress Notifications
=====================================================================
- /model : inline keyboard (provider → model)
- /help, /status, /new : basic commands
- Q&A mode : direct LLM call
- Work mode : REAL Kiro + OwenGPT calls + step-by-step notifications

Flow (work mode):
  1. รับงาน → ส่ง "📋 รับงาน: [task]"
  2. ส่ง "🤖 กำลังถาม Kiro..." → spawn kiro-cli.exe
  3. เมื่อ Kiro เสร็จ → ส่ง "✅ ได้รับคำตอบจาก Kiro แล้ว"
  4. ส่ง "🧠 กำลังถาม OwenGPT..." → spawn ask_owengpt.py
  5. เมื่อ Owen เสร็จ → ส่ง "✅ ได้รับคำตอบจาก OwenGPT แล้ว"
  6. ส่ง "📋 ได้รับคำตอบทั้งสอง — แผน:\n[plan]\n\nให้ทำเลยไหมครับ?"
  7. รอยืนยัน → Worker (LLM) ทำตามแผน
  8. รายงานผล TH
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

# ── Config ──
OWNER_ID = 1060942816

# Load env
_ENV_FILE = Path(r"C:\Users\Apinan\AppData\Local\hermes\.env")
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            if _k.strip() and _v.strip():
                os.environ.setdefault(_k.strip(), _v.strip())

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
KIRO_CLI = r"C:\Users\Apinan\AppData\Local\Kiro-Cli\kiro-cli.exe"
PYTHON = r"C:\Users\Apinan\AppData\Local\Programs\Python\Python311\python.exe"
OWENGPT_SCRIPT = r"C:\Users\Apinan\hermes-clean\scripts\ask_owengpt.py"
OFFSET_FILE = Path(r"C:\Users\Apinan\hermes-clean\scripts\.dispatcher_offset.json")
LOG_FILE = Path(r"C:\Users\Apinan\runtime\dispatcher.log")
STATE_FILE = Path(r"C:\Users\Apinan\hermes-clean\scripts\.dispatcher_state.json")

# Provider config
PROVIDERS = {
    "opencode-go": {
        "base_url": "https://opencode.ai/zen/go/v1",
        "key_env": "OPENCODE_GO_API_KEY",
        "models": [
            "deepseek-v4-flash", "deepseek-v4-pro", "minimax-m2.7", "minimax-m2.5",
            "kimi-k2.6", "kimi-k2.5", "glm-5.1", "qwen3.6-plus", "qwen3.5-plus", "mimo-v2-pro"
        ]
    },
    "ollama-pay": {
        "base_url": "https://ollama-pay.thaigqsoft.com/api/v1",
        "key_env": "OLLAMA_PAY_API_KEY",
        "models": [
            "deepseek-v3.1:671b-cloud", "deepseek-v4-flash:cloud", "deepseek-v4-pro:cloud",
            "gemini-3-flash-preview:cloud", "gemma4:31b-cloud", "glm-5.1:cloud",
            "gpt-oss:120b-cloud", "kimi-k2.5:cloud", "kimi-k2.6:cloud",
            "kimi-k2-thinking:cloud", "minimax-m2.5:cloud", "minimax-m2.7:cloud",
            "nemotron-3-nano:30b-cloud", "nemotron-3-super:cloud",
            "qwen3-coder:480b-cloud", "qwen3-coder-next:cloud", "qwen3.5:397b-cloud"
        ]
    }
}

# Load persistent state (current model)
def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except: pass
    return {"provider": "ollama-pay", "model": "glm-5.1:cloud"}

def save_state():
    STATE_FILE.write_text(json.dumps({"provider": CURRENT_PROVIDER, "model": CURRENT_MODEL}))

_state = load_state()
CURRENT_PROVIDER = _state["provider"]
CURRENT_MODEL = _state["model"]

WORK_KEYWORDS = {
    "เขียน", "แก้", "สร้าง", "ลบ", "config", "code", "script", "deploy",
    "debug", "install", "build", "fix", "update", "edit", "โค้ด", "ไฟล์",
    "คอนฟิก", "ติดตั้ง", "แก้บัค", "เพิ่ม", "ทำ", "setup", "run", "รัน"
}

# Per-chat state
pending_work = {}  # chat_id -> {"prompt", "summary", "kiro_result", "owen_result"}


# ── Telegram API ──
def tg(method, params=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = json.dumps(params).encode() if params else None
    req = urllib.request.Request(url, data, {"Content-Type": "application/json"}) if data else urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"TG error {method}: {e}")
        return {"ok": False}


def send(chat_id, text):
    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        tg("sendMessage", {"chat_id": chat_id, "text": chunk})


def send_kb(chat_id, text, buttons):
    tg("sendMessage", {"chat_id": chat_id, "text": text, "reply_markup": {"inline_keyboard": buttons}})


def edit(chat_id, msg_id, text, buttons=None):
    p = {"chat_id": chat_id, "message_id": msg_id, "text": text}
    if buttons:
        p["reply_markup"] = {"inline_keyboard": buttons}
    tg("editMessageText", p)


def typing(chat_id):
    tg("sendChatAction", {"chat_id": chat_id, "action": "typing"})


# ── LLM (worker / Q&A) ──
def llm_call(prompt, system="", timeout=90):
    prov = PROVIDERS.get(CURRENT_PROVIDER, {})
    key = os.environ.get(prov.get("key_env", "OLLAMA_PAY_API_KEY"), "")
    url = prov.get("base_url", "https://ollama-pay.thaigqsoft.com/api/v1")
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    data = json.dumps({"model": CURRENT_MODEL, "messages": msgs, "stream": False}).encode()
    req = urllib.request.Request(
        f"{url}/chat/completions", data,
        {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read())
            return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[LLM error: {e}]"


# ── Brain calls ──
def ask_kiro(prompt_en, timeout=300):
    """Spawn kiro-cli, return output."""
    try:
        proc = subprocess.Popen(
            [KIRO_CLI, "chat", "--no-interactive", "--trust-all-tools",
             "--model", "claude-sonnet-4.6", prompt_en],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        def feed_yes():
            while proc.poll() is None:
                try:
                    proc.stdin.write("y\n"); proc.stdin.flush()
                except: break
                time.sleep(0.5)

        threading.Thread(target=feed_yes, daemon=True).start()
        stdout, _ = proc.communicate(timeout=timeout)
        return re.sub(r'\x1b\[[0-9;]*m', '', stdout).strip()
    except subprocess.TimeoutExpired:
        proc.kill()
        return "[Kiro timeout]"
    except Exception as e:
        return f"[Kiro error: {e}]"


def ask_owen(prompt_en, timeout=180):
    """Spawn ask_owengpt.py, return output."""
    try:
        result = subprocess.run(
            [PYTHON, OWENGPT_SCRIPT, "--message", prompt_en, "--timeout", "120"],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "ADSPOWER_API_KEY": os.environ.get("ADSPOWER_API_KEY", "")}
        )
        try:
            data = json.loads(result.stdout)
            if data.get("status") == "OK":
                return data["response"]
            return f"[OwenGPT fail: {data.get('blocker', 'unknown')}]"
        except json.JSONDecodeError:
            return f"[OwenGPT parse error: {result.stdout[:200]}]"
    except subprocess.TimeoutExpired:
        return "[OwenGPT timeout]"
    except Exception as e:
        return f"[OwenGPT error: {e}]"


# ── Mode detection ──
def is_work(text):
    return any(kw in text.lower() for kw in WORK_KEYWORDS)


def is_confirm(text):
    return any(w in text.lower() for w in ["ทำเลย", "ใช่", "ได้", "เลย", "ทำ", "ok", "yes", "ลุย"])


# ── Handlers ──
def handle_message(chat_id, text):
    # Confirmation for pending work
    if chat_id in pending_work:
        state = pending_work[chat_id]
        if state.get("phase") == "awaiting_confirm" and is_confirm(text):
            pending_work.pop(chat_id, None)
            execute_work(chat_id, state)
            return
        elif state.get("phase") == "awaiting_confirm":
            # User said something else → cancel
            pending_work.pop(chat_id, None)
            send(chat_id, "❌ ยกเลิกงาน")
            return

    if is_work(text):
        start_work_flow(chat_id, text)
    else:
        # Q&A mode
        typing(chat_id)
        answer = llm_call(text, system="ตอบเป็นไทย สั้น ตรง เป็นเลขาส่วนตัวชื่อโอเว่น เรียกผู้ใช้ว่าเจ้านาย")
        if answer and not answer.startswith("[LLM error"):
            send(chat_id, answer)
        else:
            send(chat_id, f"❌ {answer}")


def start_work_flow(chat_id, original_prompt):
    """Step 1-6: รับงาน → ถาม Kiro → ถาม Owen → สรุป → ขอยืนยัน"""
    typing(chat_id)
    
    # Step 1: รับงาน
    send(chat_id, f"📋 รับงาน: {original_prompt[:200]}")
    
    # แปล EN
    typing(chat_id)
    prompt_en = llm_call(
        f"Translate to concise English (output only the translation):\n{original_prompt}",
        timeout=30
    )
    if prompt_en.startswith("[LLM error"):
        send(chat_id, f"❌ ไม่สามารถแปลคำสั่งได้: {prompt_en}")
        return
    
    # Step 2-3: ถาม Kiro
    send(chat_id, "🤖 กำลังถาม Kiro...")
    typing(chat_id)
    kiro_result = ask_kiro(prompt_en)
    kiro_ok = bool(kiro_result) and not kiro_result.startswith("[")
    if kiro_ok:
        send(chat_id, f"✅ ได้รับคำตอบจาก Kiro แล้ว ({len(kiro_result)} chars)")
    else:
        send(chat_id, f"⚠️ Kiro ไม่ตอบ: {kiro_result[:100]}")
    
    # Step 4-5: ถาม OwenGPT
    send(chat_id, "🧠 กำลังถาม OwenGPT...")
    typing(chat_id)
    owen_result = ask_owen(prompt_en)
    owen_ok = bool(owen_result) and not owen_result.startswith("[")
    if owen_ok:
        send(chat_id, f"✅ ได้รับคำตอบจาก OwenGPT แล้ว ({len(owen_result)} chars)")
    else:
        send(chat_id, f"⚠️ OwenGPT ไม่ตอบ: {owen_result[:100]}")
    
    # Bail if both failed
    if not kiro_ok and not owen_ok:
        send(chat_id, "❌ สมองทั้งสองไม่ตอบ — ยกเลิกงาน")
        return
    
    # Step 6: สรุปแผน + ขอยืนยัน
    typing(chat_id)
    brain_ctx = ""
    if kiro_ok:
        brain_ctx += f"Kiro:\n{kiro_result[:2000]}\n\n"
    if owen_ok:
        brain_ctx += f"OwenGPT:\n{owen_result[:1500]}"
    
    plan = llm_call(
        f"จากคำตอบของสมองทั้งสอง สรุปเป็นแผนงานสั้นๆ 3-5 ข้อเป็นภาษาไทย:\n\n{brain_ctx}",
        system="สรุปสั้น ชัด เป็นภาษาไทย"
    )
    
    send(chat_id, f"📋 ได้รับคำตอบทั้งสอง — แผน:\n\n{plan}\n\n❓ ให้ทำเลยไหมครับ? (ตอบ \"ทำเลย\"/\"ใช่\")")
    
    # Save state
    pending_work[chat_id] = {
        "phase": "awaiting_confirm",
        "prompt": original_prompt,
        "prompt_en": prompt_en,
        "kiro_result": kiro_result if kiro_ok else "",
        "owen_result": owen_result if owen_ok else "",
        "plan": plan,
    }


def execute_work(chat_id, state):
    """Step 7-8: Worker ทำตามแผน → รายงาน"""
    typing(chat_id)
    send(chat_id, "⚙️ Worker กำลังทำตามแผน...")
    
    brain_ctx = ""
    if state.get("kiro_result"):
        brain_ctx += f"Kiro's analysis:\n{state['kiro_result'][:2000]}\n\n"
    if state.get("owen_result"):
        brain_ctx += f"OwenGPT's advice:\n{state['owen_result'][:1500]}\n\n"
    
    worker_result = llm_call(
        f"""You are a worker executing a plan.
Original task: {state['prompt']}
Plan: {state['plan']}

{brain_ctx}

Execute the plan now. Output the actual code/config/commands needed.""",
        system="You are a code worker. Output complete implementation: code, commands, file contents.",
        timeout=120
    )
    
    if worker_result.startswith("[LLM error"):
        send(chat_id, f"❌ Worker ล้มเหลว: {worker_result}")
        return
    
    # สรุป TH
    typing(chat_id)
    final = llm_call(
        f"สรุปผลงานเป็นไทยสั้นๆ:\n{worker_result[:2500]}",
        system="สรุปเป็นไทย: สิ่งที่ทำ + ผลลัพธ์",
        timeout=60
    )
    
    if final and not final.startswith("[LLM error"):
        send(chat_id, f"✅ ผลงาน:\n\n{final}\n\n📋 รายละเอียด:\n{worker_result[:2500]}")
    else:
        send(chat_id, f"✅ ผลงาน:\n{worker_result[:3500]}")


# ── Inline keyboard callback ──
def handle_callback(update):
    global CURRENT_PROVIDER, CURRENT_MODEL
    cb = update.get("callback_query", {})
    if not cb:
        return
    data = cb.get("data", "")
    cb_id = cb.get("id", "")
    chat_id = cb.get("message", {}).get("chat", {}).get("id")
    msg_id = cb.get("message", {}).get("message_id")
    if not data or not chat_id:
        return
    
    tg("answerCallbackQuery", {"callback_query_id": cb_id})
    
    if data.startswith("mp:"):
        provider = data[3:]
        if provider not in PROVIDERS:
            return
        models = PROVIDERS[provider]["models"]
        buttons = [[{"text": m, "callback_data": f"mm:{provider}:{i}"}] for i, m in enumerate(models)]
        buttons.append([{"text": "◀ Back", "callback_data": "mb"}, {"text": "✗ Cancel", "callback_data": "mx"}])
        edit(chat_id, msg_id, f"📦 Provider: {provider}\n\nเลือก Model:", buttons)
    
    elif data.startswith("mm:"):
        parts = data[3:].rsplit(":", 1)
        provider, idx = parts[0], int(parts[1])
        models = PROVIDERS[provider]["models"]
        if 0 <= idx < len(models):
            old = CURRENT_MODEL
            CURRENT_MODEL = models[idx]
            CURRENT_PROVIDER = provider
            save_state()
            log(f"Model: {old} → {CURRENT_MODEL} ({provider})")
            edit(chat_id, msg_id, f"✅ เปลี่ยนเป็น: {CURRENT_MODEL}\n📦 Provider: {provider}")
    
    elif data == "mb":
        buttons = [[{"text": f"📦 {n}", "callback_data": f"mp:{n}"}] for n in PROVIDERS.keys()]
        buttons.append([{"text": "✗ Cancel", "callback_data": "mx"}])
        edit(chat_id, msg_id, f"🤖 ปัจจุบัน: {CURRENT_MODEL} ({CURRENT_PROVIDER})\n\nเลือก Provider:", buttons)
    
    elif data == "mx":
        edit(chat_id, msg_id, "❌ ยกเลิก")


def cmd_model(chat_id):
    buttons = [[{"text": f"📦 {n}", "callback_data": f"mp:{n}"}] for n in PROVIDERS.keys()]
    buttons.append([{"text": "✗ Cancel", "callback_data": "mx"}])
    send_kb(chat_id, f"🤖 ปัจจุบัน: {CURRENT_MODEL} ({CURRENT_PROVIDER})\n\nเลือก Provider:", buttons)


def cmd_help(chat_id):
    send(chat_id, """🤖 Hermes Brain Dispatcher

📝 คำสั่ง:
• /model — เลือก provider + model (inline keyboard)
• /status — สถานะระบบ
• /new — รีเซ็ต pending work
• /help — ดูคำสั่ง

💬 ใช้งาน:
• คำถามทั่วไป → ตอบเลย
• สั่งงาน → ถาม Kiro + OwenGPT → ขอยืนยัน → Worker ทำ → รายงาน

🧠 Flow โหมดงาน:
  1. รับงาน
  2. ถาม Kiro → แจ้งเมื่อได้คำตอบ
  3. ถาม OwenGPT → แจ้งเมื่อได้คำตอบ
  4. สรุปแผน → ขอยืนยัน "ทำเลย"
  5. Worker ทำตามแผน → รายงาน TH""")


def cmd_status(chat_id):
    send(chat_id, f"""✅ Brain Dispatcher v2

🤖 Model: {CURRENT_MODEL}
📦 Provider: {CURRENT_PROVIDER}
📋 Pending: {len(pending_work)} chat
🧠 Kiro: {'✅' if Path(KIRO_CLI).exists() else '❌'}
🧠 OwenGPT: {'✅' if Path(OWENGPT_SCRIPT).exists() else '❌'}""")


def cmd_new(chat_id):
    pending_work.pop(chat_id, None)
    send(chat_id, "🔄 รีเซ็ต — เริ่มใหม่ได้")


# ── Main loop ──
def load_offset():
    if OFFSET_FILE.exists():
        try:
            return json.loads(OFFSET_FILE.read_text()).get("offset", 0)
        except: pass
    return 0


def save_offset(offset):
    OFFSET_FILE.write_text(json.dumps({"offset": offset}))


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except: pass


def main():
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)
    
    log(f"Dispatcher v2 started — model: {CURRENT_MODEL} ({CURRENT_PROVIDER})")
    offset = load_offset()
    
    while True:
        try:
            resp = tg("getUpdates", {
                "offset": offset, "timeout": 20,
                "allowed_updates": ["message", "callback_query"]
            })
            if resp.get("ok") and resp.get("result"):
                for update in resp["result"]:
                    offset = update["update_id"] + 1
                    
                    if "callback_query" in update:
                        threading.Thread(target=handle_callback, args=(update,), daemon=True).start()
                        continue
                    
                    msg = update.get("message", {})
                    chat_id = msg.get("chat", {}).get("id")
                    user_id = msg.get("from", {}).get("id")
                    text = (msg.get("text") or "").strip()
                    
                    if not text or user_id != OWNER_ID:
                        continue
                    
                    log(f"Msg: {text[:80]}")
                    
                    if text == "/model":
                        cmd_model(chat_id)
                    elif text == "/help":
                        cmd_help(chat_id)
                    elif text == "/status":
                        cmd_status(chat_id)
                    elif text == "/new":
                        cmd_new(chat_id)
                    else:
                        # Run in thread (work flow takes long)
                        threading.Thread(target=handle_message, args=(chat_id, text), daemon=True).start()
                
                save_offset(offset)
        except KeyboardInterrupt:
            log("Stopped")
            break
        except Exception as e:
            log(f"Loop error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
