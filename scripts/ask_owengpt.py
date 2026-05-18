#!/usr/bin/env python3
"""
ask_owengpt.py — OwenGPT via AdsPower browser CDP

วิธีทำงาน:
1. Scan หา AdsPower browser ที่เปิดอยู่ (จาก process command line)
2. ถ้าไม่เจอ → ลอง port ที่เคยใช้ (saved) → ลอง AdsPower API (ถ้ามี key)
3. เชื่อม CDP → ส่งข้อความ → รอ response

ไม่ต้อง API key ถ้า browser เปิดอยู่แล้ว!

Usage:
  python ask_owengpt.py --message "prompt"
  python ask_owengpt.py --message "prompt" --new --timeout 180
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
import websockets

OWENGPT_URL = "https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot"
PROFILE_ID = "k1cawerp"
PORT_CACHE = Path(r"C:\Users\Apinan\hermes-clean\scripts\.owengpt_port")
ADSPOWER_API = "http://local.adspower.net:50325"


def output(data: dict):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def fail(blocker: str):
    output({"status": "FAIL", "response": "", "blocker": blocker})
    sys.exit(1)


def cdp_alive(port: int) -> bool:
    try:
        return requests.get(f"http://127.0.0.1:{port}/json/version", timeout=3).ok
    except Exception:
        return False


def scan_adspower_debug_ports() -> list[int]:
    """Scan running chrome/sunbrowser processes for debug ports."""
    ports = []
    try:
        result = subprocess.run(
            ["wmic", "process", "where", "name='chrome.exe'", "get", "commandline"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.splitlines():
            m = re.search(r"remote-debugging-port=(\d+)", line)
            if m:
                ports.append(int(m.group(1)))
    except Exception:
        pass
    # Also check sunbrowser
    try:
        result = subprocess.run(
            ["wmic", "process", "where", "name='sunbrowser.exe'", "get", "commandline"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.splitlines():
            m = re.search(r"remote-debugging-port=(\d+)", line)
            if m:
                ports.append(int(m.group(1)))
    except Exception:
        pass
    return list(set(ports))


def find_owengpt_port() -> int | None:
    """Find a live CDP port that has ChatGPT/OwenGPT."""
    # 1. Scan processes
    ports = scan_adspower_debug_ports()

    # 2. Add cached port
    if PORT_CACHE.exists():
        try:
            cached = int(PORT_CACHE.read_text().strip())
            if cached not in ports:
                ports.append(cached)
        except Exception:
            pass

    # 3. Check each port
    for port in ports:
        if cdp_alive(port):
            # Check if it has chatgpt page
            try:
                targets = requests.get(f"http://127.0.0.1:{port}/json/list", timeout=5).json()
                for t in targets:
                    url = t.get("url", "")
                    if "chatgpt.com" in url or "6a0092c4d6048191a3e494dd47f18616" in url:
                        PORT_CACHE.write_text(str(port))
                        return port
                # Even without chatgpt page, if it's alive we can navigate
                if any(t.get("type") == "page" for t in targets):
                    PORT_CACHE.write_text(str(port))
                    return port
            except Exception:
                continue

    # 4. Try DevToolsActivePort from AdsPower cache (written when browser opens)
    cache_root = Path(r"C:\.ADSPOWER_GLOBAL\cache")
    if cache_root.exists():
        for d in sorted(cache_root.glob(f"{PROFILE_ID}_*"), key=lambda p: p.stat().st_mtime, reverse=True):
            port_file = d / "DevToolsActivePort"
            if port_file.exists():
                try:
                    p = int(port_file.read_text().splitlines()[0].strip())
                    if cdp_alive(p):
                        PORT_CACHE.write_text(str(p))
                        return p
                except Exception:
                    pass
            break  # only check most recent

    # 5. Try AdsPower API as last resort
    api_key = os.environ.get("ADSPOWER_API_KEY", "").strip()
    if api_key:
        try:
            r = requests.get(f"{ADSPOWER_API}/api/v1/browser/start",
                             params={"user_id": PROFILE_ID},
                             headers={"Authorization": f"Bearer {api_key}"}, timeout=60)
            data = r.json()
            if data.get("code") == 0:
                port = data.get("data", {}).get("debug_port")
                if port:
                    import threading
                    threading.Thread(target=move_browser_to_screen3, daemon=True).start()
                    time.sleep(3)
                    PORT_CACHE.write_text(str(port))
                    return int(port)
        except Exception:
            pass

    return None


def move_browser_to_screen3():
    """Move AdsPower browser window to screen 2 (X=1536) — polls until window appears."""
    import ctypes
    user32 = ctypes.windll.user32
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    moved = [False]

    def try_move():
        found = []

        def cb(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                pid = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                try:
                    import psutil
                    name = psutil.Process(pid.value).name().lower()
                    if "chrome" in name or "sunbrowser" in name:
                        found.append(hwnd)
                except Exception:
                    pass
            return True

        user32.EnumWindows(WNDENUMPROC(cb), 0)
        for hwnd in found:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            time.sleep(0.2)
            user32.MoveWindow(hwnd, 1536, 0, 1536, 864, True)
        return len(found) > 0

    # Poll up to 30s for window to appear
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if try_move():
            break
        time.sleep(1)


def get_page_ws(port: int) -> str | None:
    try:
        targets = requests.get(f"http://127.0.0.1:{port}/json/list", timeout=5).json()
    except Exception:
        return None
    for t in targets:
        if t.get("type") == "page" and "6a0092c4d6048191a3e494dd47f18616" in (t.get("url") or ""):
            return t.get("webSocketDebuggerUrl")
    for t in targets:
        if t.get("type") == "page" and "chatgpt.com" in (t.get("url") or ""):
            return t.get("webSocketDebuggerUrl")
    for t in targets:
        if t.get("type") == "page":
            return t.get("webSocketDebuggerUrl")
    return None


class CDP:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self._id = 0
        self._ws = None

    async def connect(self):
        self._ws = await websockets.connect(self.ws_url, max_size=2**24)

    async def close(self):
        if self._ws:
            await self._ws.close()

    async def send(self, method: str, params: dict = None) -> dict:
        self._id += 1
        msg = {"id": self._id, "method": method}
        if params:
            msg["params"] = params
        await self._ws.send(json.dumps(msg))
        while True:
            raw = await self._ws.recv()
            data = json.loads(raw)
            if data.get("id") == self._id:
                return data

    async def js(self, expression: str):
        resp = await self.send("Runtime.evaluate", {
            "expression": expression, "returnByValue": True, "awaitPromise": True,
        })
        return resp.get("result", {}).get("result", {}).get("value")

    async def navigate(self, url: str):
        await self.send("Page.navigate", {"url": url})

    async def page_url(self) -> str:
        return (await self.js("window.location.href")) or ""

    async def is_ready(self) -> bool:
        return bool(await self.js(
            "!!(document.getElementById('prompt-textarea') || document.querySelector('textarea'))"
        ))

    async def count_assistant(self) -> int:
        return (await self.js(
            "document.querySelectorAll('[data-message-author-role=\"assistant\"]').length"
        )) or 0

    async def last_assistant_text(self) -> str:
        text = await self.js("""(() => {
            const msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
            if (!msgs.length) return '';
            return (msgs[msgs.length-1].innerText || '').trim();
        })()""")
        return (text or "").strip()

    async def send_message(self, text: str) -> bool:
        await self.js("""(() => {
            const el = document.getElementById('prompt-textarea')
                || document.querySelector('[contenteditable="true"]')
                || document.querySelector('textarea');
            if (el) { el.focus(); el.click(); }
        })()""")
        await asyncio.sleep(0.3)
        # Ctrl+A + Backspace
        await self.send("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "a", "code": "KeyA", "windowsVirtualKeyCode": 65, "modifiers": 2})
        await self.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "windowsVirtualKeyCode": 65, "modifiers": 2})
        await self.send("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Backspace", "code": "Backspace", "windowsVirtualKeyCode": 8, "modifiers": 0})
        await self.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace", "windowsVirtualKeyCode": 8, "modifiers": 0})
        await asyncio.sleep(0.3)
        await self.send("Input.insertText", {"text": text})
        await asyncio.sleep(0.5)
        for _ in range(20):
            ok = await self.js("""(() => {
                const btn = document.querySelector('[data-testid="send-button"]')
                    || document.querySelector('button[aria-label*="Send"]');
                if (btn && !btn.disabled) { btn.click(); return true; }
                return false;
            })()""")
            if ok:
                return True
            await asyncio.sleep(0.5)
        return False

    async def wait_response(self, initial_count: int, timeout: int) -> str:
        deadline = time.monotonic() + timeout
        prev = ""
        stable = 0
        while time.monotonic() < deadline:
            count = await self.count_assistant()
            if count > initial_count:
                text = await self.last_assistant_text()
                # Skip thinking indicators
                if text in ("กำลังคิด", "Thinking…", "Thinking...", ""):
                    await asyncio.sleep(1.5)
                    continue
                if text == prev and text:
                    stable += 1
                    if stable >= 3:
                        return text
                else:
                    stable = 0
                    prev = text
            await asyncio.sleep(1.5)
        return prev

    async def delete_current_chat(self):
        """Delete current chat using ChatGPT API with access token."""
        # Wait for URL to have /c/
        for _ in range(10):
            url = await self.page_url()
            if "/c/" in url:
                break
            await asyncio.sleep(1)

        url = await self.page_url()
        if "/c/" not in url:
            return

        conv_id = url.split("/c/")[-1].split("?")[0].split("#")[0]
        if not conv_id:
            return

        # Get access token + delete
        await self.js(f"""(async () => {{
            const s = await fetch('/api/auth/session');
            const d = await s.json();
            const token = d.accessToken;
            if (!token) return;
            await fetch('/backend-api/conversation/{conv_id}', {{
                method: 'PATCH',
                headers: {{'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}},
                body: JSON.stringify({{is_visible: false}})
            }});
        }})()""")
        await asyncio.sleep(0.3)


async def run(message: str, force_new: bool, timeout: int):
    port = find_owengpt_port()
    if not port:
        fail("ไม่เจอ AdsPower browser ที่เปิดอยู่ — เปิด profile k1cawerp จาก AdsPower app ก่อน")

    page_ws = get_page_ws(port)
    if not page_ws:
        fail("ไม่เจอ page target ใน browser")

    cdp = CDP(page_ws)
    try:
        await cdp.connect()
    except Exception as e:
        fail(f"WebSocket: {e}")

    try:
        # Always navigate to OwenGPT fresh (new session every time)
        await cdp.navigate(OWENGPT_URL)
        await asyncio.sleep(4)

        for _ in range(20):
            if await cdp.is_ready():
                break
            await asyncio.sleep(1)
        else:
            fail("Page not ready / not logged in")

        initial = await cdp.count_assistant()
        if not await cdp.send_message(message):
            fail("Send failed")

        response = await cdp.wait_response(initial, timeout)
        if response:
            # Delete chat history before leaving
            await cdp.delete_current_chat()
            output({"status": "OK", "response": response, "blocker": ""})
        else:
            await cdp.delete_current_chat()
            fail("Timeout waiting for response")
    except Exception as e:
        try:
            await cdp.delete_current_chat()
        except Exception:
            pass
        fail(f"Error: {e}")
    finally:
        await cdp.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", "-m", required=True)
    parser.add_argument("--new", action="store_true")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    asyncio.run(run(args.message, args.new, args.timeout))


if __name__ == "__main__":
    main()
