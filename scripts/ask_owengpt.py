#!/usr/bin/env python3
"""
ask_owengpt.py — Reliable OwenGPT sender+receiver via AdsPower CDP

Fixes:
- Handles new chat vs existing chat correctly
- Waits for response and returns it
- Handles ChatGPT URL changes after send (e.g. /g/xxx → /c/xxx)
- Single JSON output to stdout

Usage:
  python ask_owengpt.py --message "your prompt here"
  python ask_owengpt.py --message "prompt" --new   (force new chat)
  python ask_owengpt.py --message "prompt" --timeout 180
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
import websockets

OWENGPT_URL = "https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot"
DEFAULT_PROFILE_ID = "k1cawerp"
ADSPOWER_ROOT = Path(r"C:\.ADSPOWER_GLOBAL")
ADSPOWER_BROWSER_ROOT = Path(r"C:\Users\Apinan\AppData\Roaming\adspower_global\cwd_global")


def output(data: dict):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def profile_cache_dir(profile_id: str) -> Path | None:
    cache_root = ADSPOWER_ROOT / "cache"
    if not cache_root.exists():
        return None
    matches = sorted(cache_root.glob(f"{profile_id}_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def browser_exe_path() -> Path | None:
    candidates = sorted(
        ADSPOWER_BROWSER_ROOT.glob("chrome_*/sunbrowser.exe"),
        key=lambda p: p.as_posix(), reverse=True,
    )
    return candidates[0] if candidates else None


def read_devtools_port(cache_dir: Path) -> str | None:
    f = cache_dir / "DevToolsActivePort"
    if not f.exists():
        return None
    try:
        lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        if lines and lines[0].strip().isdigit():
            return f"http://127.0.0.1:{lines[0].strip()}"
    except Exception:
        pass
    return None


def cdp_alive(url: str) -> bool:
    try:
        return requests.get(f"{url}/json/version", timeout=3).ok
    except Exception:
        return False


def launch_browser(cache_dir: Path) -> str | None:
    exe = browser_exe_path()
    if not exe:
        return None
    subprocess.Popen(
        [str(exe), f"--user-data-dir={cache_dir}", "--no-first-run",
         "--disable-background-networking", "--remote-debugging-port=0"],
        cwd=str(exe.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        cdp_http = read_devtools_port(cache_dir)
        if cdp_http and cdp_alive(cdp_http):
            return cdp_http
        time.sleep(1)
    return None


def get_cdp_endpoint(profile_id: str) -> str | None:
    cache_dir = profile_cache_dir(profile_id)
    if not cache_dir:
        return None
    cdp_http = read_devtools_port(cache_dir)
    if cdp_http and cdp_alive(cdp_http):
        return cdp_http
    return launch_browser(cache_dir)


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
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
        })
        return resp.get("result", {}).get("result", {}).get("value")

    async def navigate(self, url: str):
        await self.send("Page.navigate", {"url": url})

    async def page_url(self) -> str:
        return (await self.js("window.location.href")) or ""

    async def is_logged_in(self) -> bool:
        result = await self.js("""(() => {
            return !!(document.getElementById('prompt-textarea')
                || document.querySelector('[data-testid="send-button"]')
                || document.querySelector('textarea'));
        })()""")
        return bool(result)

    async def count_assistant_messages(self) -> int:
        return (await self.js(
            "document.querySelectorAll('[data-message-author-role=\"assistant\"]').length"
        )) or 0

    async def get_last_assistant_text(self) -> str:
        text = await self.js("""(() => {
            const msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
            if (!msgs.length) return '';
            const last = msgs[msgs.length - 1];
            return (last.innerText || last.textContent || '').trim();
        })()""")
        return (text or "").strip()

    async def focus_and_clear(self):
        await self.js("""(() => {
            const el = document.getElementById('prompt-textarea')
                || document.querySelector('[contenteditable="true"]')
                || document.querySelector('textarea');
            if (!el) return;
            el.focus(); el.click();
        })()""")
        await asyncio.sleep(0.3)
        # Ctrl+A
        await self.send("Input.dispatchKeyEvent", {
            "type": "rawKeyDown", "key": "a", "code": "KeyA",
            "windowsVirtualKeyCode": 65, "nativeVirtualKeyCode": 65, "modifiers": 2,
        })
        await self.send("Input.dispatchKeyEvent", {
            "type": "keyUp", "key": "a", "code": "KeyA",
            "windowsVirtualKeyCode": 65, "nativeVirtualKeyCode": 65, "modifiers": 2,
        })
        # Backspace
        await self.send("Input.dispatchKeyEvent", {
            "type": "rawKeyDown", "key": "Backspace", "code": "Backspace",
            "windowsVirtualKeyCode": 8, "nativeVirtualKeyCode": 8, "modifiers": 0,
        })
        await self.send("Input.dispatchKeyEvent", {
            "type": "keyUp", "key": "Backspace", "code": "Backspace",
            "windowsVirtualKeyCode": 8, "nativeVirtualKeyCode": 8, "modifiers": 0,
        })
        await asyncio.sleep(0.3)

    async def type_text(self, text: str):
        await self.send("Input.insertText", {"text": text})

    async def click_send(self) -> bool:
        return bool(await self.js("""(() => {
            const btn = document.querySelector('[data-testid="send-button"]')
                || document.querySelector('button[aria-label*="Send"]');
            if (!btn || btn.disabled) return false;
            btn.click();
            return true;
        })()"""))

    async def wait_send_enabled(self, timeout: float = 10) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            enabled = await self.js("""(() => {
                const btn = document.querySelector('[data-testid="send-button"]')
                    || document.querySelector('button[aria-label*="Send"]');
                return btn && !btn.disabled;
            })()""")
            if enabled:
                return True
            await asyncio.sleep(0.5)
        return False

    async def wait_response(self, initial_count: int, timeout: int) -> str:
        """Wait for a new assistant message that stabilizes."""
        deadline = time.monotonic() + timeout
        prev_text = ""
        stable = 0

        while time.monotonic() < deadline:
            count = await self.count_assistant_messages()
            if count > initial_count:
                text = await self.get_last_assistant_text()
                if text and text == prev_text:
                    stable += 1
                    if stable >= 3:
                        return text
                else:
                    stable = 0
                    prev_text = text
            # Also check if streaming indicator is gone
            streaming = await self.js("""(() => {
                return !!(document.querySelector('[data-testid="stop-button"]')
                    || document.querySelector('button[aria-label*="Stop"]'));
            })()""")
            if not streaming and prev_text and stable >= 1:
                return prev_text
            await asyncio.sleep(1.5)
        return prev_text


async def run(message: str, profile_id: str, force_new: bool, timeout: int):
    # 1. Get CDP endpoint
    cdp_http = get_cdp_endpoint(profile_id)
    if not cdp_http:
        output({"status": "FAIL", "response": "", "blocker": f"No CDP for profile {profile_id}"})
        return

    # 2. Find OwenGPT page or any page
    try:
        targets = requests.get(f"{cdp_http}/json/list", timeout=5).json()
    except Exception as e:
        output({"status": "FAIL", "response": "", "blocker": f"CDP list: {e}"})
        return

    ws_url = None
    is_owengpt_tab = False
    for t in targets:
        if t.get("type") == "page" and "6a0092c4d6048191a3e494dd47f18616" in (t.get("url") or ""):
            ws_url = t.get("webSocketDebuggerUrl")
            is_owengpt_tab = True
            break
    # Also match /c/ URLs that came from OwenGPT
    if not ws_url:
        for t in targets:
            if t.get("type") == "page" and "chatgpt.com" in (t.get("url") or ""):
                ws_url = t.get("webSocketDebuggerUrl")
                break
    if not ws_url:
        for t in targets:
            if t.get("type") == "page":
                ws_url = t.get("webSocketDebuggerUrl")
                break
    if not ws_url:
        output({"status": "FAIL", "response": "", "blocker": "No page target"})
        return

    # 3. Connect
    cdp = CDP(ws_url)
    try:
        await cdp.connect()
    except Exception as e:
        output({"status": "FAIL", "response": "", "blocker": f"WS connect: {e}"})
        return

    try:
        # 4. Navigate to OwenGPT if needed or forced new
        current_url = await cdp.page_url()
        need_navigate = force_new or (
            "6a0092c4d6048191a3e494dd47f18616" not in current_url
            and "chatgpt.com" not in current_url
        )

        if need_navigate:
            await cdp.navigate(OWENGPT_URL)
            await asyncio.sleep(4)

        # 5. Wait for page ready
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if await cdp.is_logged_in():
                break
            await asyncio.sleep(1)
        else:
            output({"status": "FAIL", "response": "", "blocker": "Not logged in / page not ready"})
            return

        # 6. Record current assistant message count
        initial_count = await cdp.count_assistant_messages()

        # 7. Focus, clear, type
        await cdp.focus_and_clear()
        await asyncio.sleep(0.3)
        await cdp.type_text(message)
        await asyncio.sleep(0.5)

        # 8. Wait send enabled + click
        if not await cdp.wait_send_enabled(timeout=10):
            output({"status": "FAIL", "response": "", "blocker": "Send button not enabled"})
            return

        if not await cdp.click_send():
            output({"status": "FAIL", "response": "", "blocker": "Click send failed"})
            return

        # 9. Wait for response
        response = await cdp.wait_response(initial_count, timeout)
        if response:
            output({"status": "OK", "response": response, "blocker": ""})
        else:
            output({"status": "FAIL", "response": "", "blocker": "Timeout waiting for response"})

    except Exception as e:
        output({"status": "FAIL", "response": "", "blocker": f"Error: {e}"})
    finally:
        await cdp.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", "-m", required=True)
    parser.add_argument("--profile-id", default=os.environ.get("ADSPOWER_USER_ID", DEFAULT_PROFILE_ID))
    parser.add_argument("--new", action="store_true", help="Force new chat")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    asyncio.run(run(args.message, args.profile_id, args.new, args.timeout))


if __name__ == "__main__":
    main()
