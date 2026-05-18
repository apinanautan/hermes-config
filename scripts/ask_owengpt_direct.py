#!/usr/bin/env python3
"""
ask_owengpt_direct.py — Deterministic OwenGPT sender via CDP

Flow:
  Connect existing CDP → find/navigate OwenGPT tab → verify login →
  focus composer → clear → paste message → verify text →
  wait send enabled → click send → verify outbound bubble

Hardcoded:
  - CloakBrowser / CDP 9222
  - OwenGPT: https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot

Output: single JSON report to stdout.
"""

import argparse
import asyncio
import glob
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
import websockets

# ---- hardcoded ----
OWENGPT_URL = (
    "https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot"
)
DEFAULT_PROFILE_ID = "k1cawerp"
ADSPower_ROOT = Path(r"C:\.ADSPOWER_GLOBAL")
ADSPower_BROWSER_ROOT = Path(r"C:\Users\Apinan\AppData\Roaming\adspower_global\cwd_global")

# ---- helpers ----
FAIL_REPORT = {"status": "FAIL", "login": False, "url_match": False, "message_sent": False, "blocker": ""}


def fail(blocker: str):
    FAIL_REPORT["blocker"] = blocker
    print(json.dumps(FAIL_REPORT, ensure_ascii=False, indent=2))
    sys.exit(1)


def normalize_cdp_http(value: str) -> str:
    value = (value or "").strip().strip('"').strip("'")
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value.rstrip("/")
    if value.startswith(("ws://", "wss://")):
        return value.replace("ws://", "http://", 1).replace("wss://", "https://", 1).rstrip("/")
    if ":" in value:
        return f"http://{value}".rstrip("/")
    if value.isdigit():
        return f"http://127.0.0.1:{value}"
    return value.rstrip("/")


def build_cdp_http(port_or_url: str) -> str:
    return normalize_cdp_http(port_or_url)


def profile_cache_dir(profile_id: str) -> Path | None:
    cache_root = ADSPower_ROOT / "cache"
    if not cache_root.exists():
        return None
    matches = sorted(cache_root.glob(f"{profile_id}_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def browser_exe_path() -> Path | None:
    candidates = sorted(
        ADSPower_BROWSER_ROOT.glob("chrome_*/sunbrowser.exe"),
        key=lambda p: p.as_posix(),
        reverse=True,
    )
    return candidates[0] if candidates else None


def read_devtools_active_port(cache_dir: Path) -> tuple[str, str] | None:
    f = cache_dir / "DevToolsActivePort"
    if not f.exists():
        return None
    try:
        lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return None
    if len(lines) < 2:
        return None
    port = lines[0].strip()
    path = lines[1].strip()
    if not port.isdigit():
        return None
    return f"http://127.0.0.1:{port}", path


def cdp_alive(cdp_http: str) -> bool:
    try:
        r = requests.get(f"{cdp_http}/json/version", timeout=3)
        return r.ok and bool(r.text)
    except Exception:
        return False


def launch_profile_browser(profile_id: str, cache_dir: Path) -> str | None:
    exe = browser_exe_path()
    if not exe:
        return None
    args = [
        str(exe),
        f"--user-data-dir={cache_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-sync",
        "--remote-debugging-port=0",
    ]
    subprocess.Popen(args, cwd=str(exe.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        info = read_devtools_active_port(cache_dir)
        if info:
            cdp_http, _ = info
            if cdp_alive(cdp_http):
                return cdp_http
        time.sleep(1)
    return None


def resolve_cdp_http(profile_id: str | None, cdp_hint: str | None = None) -> tuple[str | None, str | None, str]:
    profile_id = profile_id or DEFAULT_PROFILE_ID
    cache_dir = profile_cache_dir(profile_id)
    cdp_http = build_cdp_http(cdp_hint) if cdp_hint else ""
    if cdp_http and cdp_alive(cdp_http):
        return cdp_http, (str(cache_dir) if cache_dir else None), profile_id
    if cache_dir:
        info = read_devtools_active_port(cache_dir)
        if info:
            cdp_http, _ = info
            if cdp_alive(cdp_http):
                return cdp_http, str(cache_dir), profile_id
        launched = launch_profile_browser(profile_id, cache_dir)
        if launched:
            return launched, str(cache_dir), profile_id
    return (cdp_http or None), (str(cache_dir) if cache_dir else None), profile_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("message", nargs="?", default="", help="Prompt text to send; omit to only open OwenGPT")
    parser.add_argument("--profile-id", default=os.environ.get("ADSPower_USER_ID", DEFAULT_PROFILE_ID))
    parser.add_argument("--cdp", default="", help="CDP HTTP endpoint or port")
    parser.add_argument("--url", default=OWENGPT_URL)
    return parser.parse_args()

class CDP:
    """Minimal CDP client over WebSocket."""

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
        # read until we get our response
        while True:
            raw = await self._ws.recv()
            data = json.loads(raw)
            if data.get("id") == self._id:
                return data
            # events are ignored

    async def evaluate(self, js: str) -> dict:
        """Run JS in page context. Returns result dict."""
        resp = await self.send("Runtime.evaluate", {
            "expression": js,
            "returnByValue": True,
            "awaitPromise": True,
        })
        return resp.get("result", {})

    async def get_composer_text(self) -> str:
        r = await self.evaluate(
            "(document.getElementById('prompt-textarea') || "
            "document.querySelector('[contenteditable=\"true\"]') || "
            "document.querySelector('textarea'))?.innerText ?? ''"
        )
        val = r.get("result", {}).get("value", "")
        return (val or "").strip()

    async def focus_composer(self):
        await self.evaluate(
            "(() => { "
            "  const el = document.getElementById('prompt-textarea') "
            "    || document.querySelector('[contenteditable=\"true\"]') "
            "    || document.querySelector('textarea'); "
            "  if (el) { el.focus(); el.click(); return true; } "
            "  return false; "
            "})()"
        )

    async def type_in_composer(self, text: str):
        """Use insertText via Input.insertText CDP command."""
        await self.send("Input.insertText", {"text": text})

    async def clear_composer(self):
        """Ctrl+A then Backspace via Input.dispatchKeyEvent."""
        # Ctrl+A
        await self.send("Input.dispatchKeyEvent", {
            "type": "rawKeyDown", "windowsVirtualKeyCode": 65,
            "nativeVirtualKeyCode": 65, "key": "a",
            "code": "KeyA", "modifiers": 2, "text": "", "unmodifiedText": "",
        })
        await self.send("Input.dispatchKeyEvent", {
            "type": "keyUp", "windowsVirtualKeyCode": 65,
            "nativeVirtualKeyCode": 65, "key": "a",
            "code": "KeyA", "modifiers": 2, "text": "", "unmodifiedText": "",
        })
        # Backspace
        await self.send("Input.dispatchKeyEvent", {
            "type": "rawKeyDown", "windowsVirtualKeyCode": 8,
            "nativeVirtualKeyCode": 8, "key": "Backspace",
            "code": "Backspace", "modifiers": 0, "text": "", "unmodifiedText": "",
        })
        await self.send("Input.dispatchKeyEvent", {
            "type": "keyUp", "windowsVirtualKeyCode": 8,
            "nativeVirtualKeyCode": 8, "key": "Backspace",
            "code": "Backspace", "modifiers": 0, "text": "", "unmodifiedText": "",
        })
        # small pause to let DOM settle
        await asyncio.sleep(0.3)

    async def click_send(self) -> bool:
        """Click send button. Returns True if found+clicked."""
        r = await self.evaluate(
            "(() => { "
            "  const btn = document.querySelector('[data-testid=\"send-button\"]') "
            "    || document.querySelector('button[aria-label=\"Send prompt\"]') "
            "    || Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Send')); "
            "  if (!btn) return false; "
            "  const rect = btn.getBoundingClientRect(); "
            "  return JSON.stringify({x: rect.x + rect.width/2, y: rect.y + rect.height/2}); "
            "})()"
        )
        val = r.get("result", {}).get("value")
        if not val:
            return False
        try:
            coords = json.loads(val)
        except Exception:
            return False
        x, y = coords["x"], coords["y"]
        # mouse click
        await self.send("Input.dispatchMouseEvent", {
            "type": "mousePressed", "x": x, "y": y,
            "button": "left", "clickCount": 1,
        })
        await self.send("Input.dispatchMouseEvent", {
            "type": "mouseReleased", "x": x, "y": y,
            "button": "left", "clickCount": 1,
        })
        return True

    async def wait_for_send_enabled(self, timeout: float = 10) -> bool:
        """Poll until send button is enabled (not disabled)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            r = await self.evaluate(
                "(() => { "
                "  const btn = document.querySelector('[data-testid=\"send-button\"]') "
                "    || Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Send')); "
                "  if (!btn) return 'not-found'; "
                "  return btn.disabled ? 'disabled' : 'enabled'; "
                "})()"
            )
            val = r.get("result", {}).get("value", "")
            if val == "enabled":
                return True
            if val == "not-found":
                return False
            await asyncio.sleep(0.5)
        return False

    async def verify_outbound_bubble(self, timeout: float = 15) -> bool:
        """Check for outbound message bubble after sending."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            r = await self.evaluate(
                "(() => { "
                "  const items = document.querySelectorAll('[data-message-author-role=\"user\"]'); "
                "  return items.length; "
                "})()"
            )
            count = r.get("result", {}).get("value", 0)
            if count and count > 0:
                return True
            await asyncio.sleep(0.5)
        return False

    async def check_login(self) -> bool:
        """Detect if logged in to ChatGPT."""
        r = await self.evaluate(
            "(() => { "
            "  const loginBtn = document.querySelector('button:has(div:contains(\"Log in\"))'); "
            "  const chatInterface = document.getElementById('prompt-textarea') "
            "    || document.querySelector('[data-testid=\"send-button\"]'); "
            "  const nav = document.querySelector('nav'); "
            "  if (chatInterface || nav?.querySelector('a[href*=\"chat\"]')) return 'logged_in'; "
            "  if (loginBtn || document.querySelector('a[href*=\"login\"]')) return 'login_screen'; "
            "  return 'unknown'; "
        "})()"
        )
        val = r.get("result", {}).get("value", "")
        return val == "logged_in"


async def main():
    args = parse_args()
    message = args.message or ""

    # ---- 1. Resolve CDP ----
    cdp_http, cache_dir, profile_id = resolve_cdp_http(args.profile_id, args.cdp)
    if not cdp_http:
        fail(f"No live AdsPower CDP endpoint for profile {profile_id}")

    try:
        resp = requests.get(f"{cdp_http}/json", timeout=5)
        targets = resp.json()
    except Exception as e:
        fail(f"CDP connect: {e}")

    if not targets:
        fail("No CDP targets available")

    # ---- 2. Find or create OwenGPT tab ----
    target = None
    for t in targets:
        url = t.get("url", "")
        if args.url in url:
            target = t
            break

    ws_url = None
    if target:
        ws_url = target.get("webSocketDebuggerUrl")
        url_match = True
    else:
        for t in targets:
            if t.get("type") == "page":
                ws_url = t.get("webSocketDebuggerUrl")
                break
        if not ws_url:
            fail("No page target found")
        url_match = False
        target = next(t for t in targets if t.get("webSocketDebuggerUrl") == ws_url)

    if not ws_url:
        fail("WebSocket URL not found")

    # ---- 3. Connect WebSocket ----
    cdp = CDP(ws_url)
    try:
        await cdp.connect()
    except Exception as e:
        fail(f"WebSocket connect: {e}")

    try:
        # ---- 4. Navigate if needed ----
        if not url_match:
            await cdp.send("Page.navigate", {"url": args.url})
            await asyncio.sleep(3)
            r = await cdp.evaluate("window.location.href")
            cur_url = r.get("result", {}).get("value", "")
            if args.url not in cur_url:
                await cdp.close()
                fail(f"Navigation failed, current URL: {cur_url[:80]}")
            url_match = True

        # ---- 5. Wait for page load ----
        await asyncio.sleep(2)

        # ---- 6. Verify login ----
        logged_in = await cdp.check_login()
        if not logged_in:
            await cdp.close()
            print(json.dumps({
                "status": "FAIL",
                "login": False,
                "url_match": True,
                "message_sent": False,
                "blocker": "Not logged in to ChatGPT",
            }, ensure_ascii=False, indent=2))
            sys.exit(1)

        if not message:
            await cdp.close()
            print(json.dumps({
                "status": "PASS",
                "login": logged_in,
                "url_match": url_match,
                "message_sent": False,
                "blocker": "",
            }, ensure_ascii=False, indent=2))
            return

        # ---- 7. Focus composer ----
        await cdp.focus_composer()
        await asyncio.sleep(0.5)

        # ---- 8. Clear existing text ----
        await cdp.clear_composer()
        await asyncio.sleep(0.3)

        # ---- 9. Type message ----
        await cdp.type_in_composer(message)
        await asyncio.sleep(0.5)

        # ---- 10. Verify composer text ----
        composed = await cdp.get_composer_text()
        if message not in composed and composed not in message:
            r2 = await cdp.evaluate("(document.querySelector('textarea')?.value ?? '')")
            val2 = r2.get("result", {}).get("value", "") or ""
            if message not in val2 and val2 not in message:
                await cdp.close()
                fail(
                    f"Composer text mismatch. Expected: '{message[:40]}...', "
                    f"Got textarea: '{val2[:40]}', innerText: '{composed[:40]}'"
                )

        # ---- 11. Wait for send enabled ----
        send_ready = await cdp.wait_for_send_enabled(timeout=10)
        if not send_ready:
            await cdp.close()
            fail("Send button not enabled or not found")

        # ---- 12. Click send ----
        clicked = await cdp.click_send()
        if not clicked:
            await cdp.close()
            fail("Could not find/click send button")

        # ---- 13. Verify outbound bubble ----
        bubble_ok = await cdp.verify_outbound_bubble(timeout=15)

        await cdp.close()

        print(json.dumps({
            "status": "PASS" if bubble_ok else "FAIL",
            "login": logged_in,
            "url_match": url_match,
            "message_sent": bubble_ok,
            "blocker": "" if bubble_ok else "Outbound bubble not detected",
        }, ensure_ascii=False, indent=2))

    except Exception as e:
        await cdp.close()
        fail(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
