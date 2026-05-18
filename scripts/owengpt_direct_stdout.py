#!/usr/bin/env python3
"""
owengpt_direct_stdout.py

Direct stdout client for OwenGPT.
Priority:
1) Use a direct API if one is explicitly available.
2) Otherwise use AdsPower CDP page transport only.

No screenshots. No manual scraping. JSON stdout only.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import websockets

OWENGPT_URL = "https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owengpt"
OWENGPT_URL_ALIASES = {
    OWENGPT_URL,
    "https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot",
}
DEFAULT_ADSPOWER_API = "http://local.adspower.net:50325"
DEFAULT_PROFILE_ID = "k1cawerp"
DEFAULT_TIMEOUT = 120
ADSPOWER_ROOT = Path(r"C:\.ADSPOWER_GLOBAL")
ADSPOWER_BROWSER_ROOT = Path(r"C:\Users\Apinan\AppData\Roaming\adspower_global\cwd_global")


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def empty_report(task_id: str, prompt: str, mode: str = "adspower_cdp") -> dict[str, Any]:
    return {
        "task_id": task_id,
        "status": "FAIL",
        "mode": mode,
        "prompt": prompt,
        "response": "",
        "blocker": "",
        "stage": "init",
        "current_url": "",
        "page_title": "",
        "composer_ready": False,
        "login_status": "unknown",
        "trace": [],
    }


def fail(prompt: str, mode: str, blocker: str, response: str = "") -> None:
    emit({
        "status": "FAIL",
        "mode": mode,
        "prompt": prompt,
        "response": response,
        "blocker": blocker,
    })
    raise SystemExit(1)


def normalize_http(value: str) -> str:
    value = (value or "").strip().strip('"').strip("'")
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value.rstrip("/")
    if value.startswith(("ws://", "wss://")):
        parsed = urlparse(value)
        if parsed.hostname and parsed.port:
            scheme = "https" if parsed.scheme == "wss" else "http"
            return f"{scheme}://{parsed.hostname}:{parsed.port}"
        return value.replace("ws://", "http://", 1).replace("wss://", "https://", 1).rstrip("/")
    if ":" in value:
        return f"http://{value}".rstrip("/")
    if value.isdigit():
        return f"http://127.0.0.1:{value}"
    return value.rstrip("/")


def profile_cache_dir(profile_id: str) -> Path | None:
    cache_root = ADSPOWER_ROOT / "cache"
    if not cache_root.exists():
        return None
    matches = sorted(cache_root.glob(f"{profile_id}_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def browser_exe_path() -> Path | None:
    candidates = sorted(
        ADSPOWER_BROWSER_ROOT.glob("chrome_*/sunbrowser.exe"),
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


def start_profile_via_adspower_api(api_base: str, profile_id: str) -> str | None:
    api_key = os.environ.get("ADSPOWER_API_KEY", "").strip()
    if not api_key:
        return None
    url = api_base.rstrip("/") + "/api/v1/browser/start"
    header_variants = [
        {"api-key": api_key},
        {"apikey": api_key},
        {"x-api-key": api_key},
        {"Authorization": api_key},
        {"Authorization": f"Bearer {api_key}"},
    ]
    for headers in header_variants:
        for attempt in range(3):
            try:
                r = requests.get(url, params={"user_id": profile_id}, headers=headers, timeout=30)
                text = r.text or ""
                if "Require api-key" in text:
                    break
                if "Too many request per second" in text:
                    time.sleep(1 + attempt)
                    continue
                if not r.ok:
                    break
                data = r.json()
            except Exception:
                break

            payload = data.get("data") if isinstance(data, dict) else None
            if isinstance(payload, dict):
                ws = payload.get("ws")
                if isinstance(ws, dict):
                    for key in ("puppeteer", "selenium", "url", "websocket", "ws_url"):
                        value = ws.get(key)
                        if value:
                            value = str(value)
                            if value.startswith("ws"):
                                return normalize_http(value)
                            return normalize_http(value)
                for key in ("ws", "debug_port", "debugPort", "ws_url", "websocket", "url"):
                    value = payload.get(key)
                    if value:
                        value = str(value)
                        if value.startswith("ws"):
                            return value
                        return normalize_http(value)
    return None


def launch_profile_browser(cache_dir: Path) -> str | None:
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


def resolve_cdp_http(profile_id: str, api_base: str, cdp_hint: str = "") -> tuple[str | None, str | None]:
    cdp_http = normalize_http(cdp_hint) if cdp_hint else ""
    if cdp_http and cdp_alive(cdp_http):
        return cdp_http, None

    cache_dir = profile_cache_dir(profile_id)
    if cache_dir:
        info = read_devtools_active_port(cache_dir)
        if info:
            cdp_http, _ = info
            if cdp_alive(cdp_http):
                return cdp_http, str(cache_dir)

    started = start_profile_via_adspower_api(api_base, profile_id)
    if started:
        if started.startswith("ws"):
            return started, str(cache_dir) if cache_dir else None
        if cdp_alive(started):
            return started, str(cache_dir) if cache_dir else None

    if cache_dir:
        launched = launch_profile_browser(cache_dir)
        if launched:
            return launched, str(cache_dir)

    return (cdp_http or None), (str(cache_dir) if cache_dir else None)


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

    async def send(self, method: str, params: dict | None = None) -> dict:
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

    async def evaluate(self, js: str) -> Any:
        resp = await self.send(
            "Runtime.evaluate",
            {
                "expression": js,
                "returnByValue": True,
                "awaitPromise": True,
            },
        )
        return resp.get("result", {}).get("result", {}).get("value")

    async def page_url(self) -> str:
        value = await self.evaluate("window.location.href")
        return value or ""

    async def dom_text(self, selector: str) -> str:
        js = f"(() => {{ const el = document.querySelector({json.dumps(selector)}); return el ? (el.innerText || el.textContent || '') : ''; }})()"
        value = await self.evaluate(js)
        return (value or "").strip()

    async def click(self, selector: str) -> bool:
        js = f"(() => {{ const el = document.querySelector({json.dumps(selector)}); if (!el) return false; el.click(); return true; }})()"
        return bool(await self.evaluate(js))

    async def type_into_composer(self, text: str) -> bool:
        await self.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": 10, "y": 10})
        focused = await self.evaluate(
            "(() => { const el = document.getElementById('prompt-textarea') || document.querySelector('[contenteditable=\"true\"]') || document.querySelector('textarea'); if (!el) return false; el.focus(); el.click(); return true; })()"
        )
        if not focused:
            return False
        await self.send("Input.insertText", {"text": text})
        return True

    async def clear_composer(self):
        await self.evaluate(
            """(() => {
                const el = document.getElementById('prompt-textarea') || document.querySelector('[contenteditable="true"]') || document.querySelector('textarea');
                if (!el) return false;
                try { el.focus(); } catch (_) {}
                if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                    el.value = '';
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                if (el.isContentEditable) {
                    el.innerHTML = '';
                    el.textContent = '';
                    el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'deleteContentBackward', data: null }));
                    return true;
                }
                return false;
            })()"""
        )
        await self.send("Input.dispatchKeyEvent", {
            "type": "rawKeyDown", "windowsVirtualKeyCode": 65, "nativeVirtualKeyCode": 65,
            "key": "a", "code": "KeyA", "modifiers": 2, "text": "", "unmodifiedText": "",
        })
        await self.send("Input.dispatchKeyEvent", {
            "type": "keyUp", "windowsVirtualKeyCode": 65, "nativeVirtualKeyCode": 65,
            "key": "a", "code": "KeyA", "modifiers": 2, "text": "", "unmodifiedText": "",
        })
        await self.send("Input.dispatchKeyEvent", {
            "type": "rawKeyDown", "windowsVirtualKeyCode": 8, "nativeVirtualKeyCode": 8,
            "key": "Backspace", "code": "Backspace", "modifiers": 0, "text": "", "unmodifiedText": "",
        })
        await self.send("Input.dispatchKeyEvent", {
            "type": "keyUp", "windowsVirtualKeyCode": 8, "nativeVirtualKeyCode": 8,
            "key": "Backspace", "code": "Backspace", "modifiers": 0, "text": "", "unmodifiedText": "",
        })
        await asyncio.sleep(0.2)

    async def composer_text(self) -> str:
        for selector in ["#prompt-textarea", "[contenteditable=\"true\"]", "textarea"]:
            text = await self.dom_text(selector)
            if text:
                return text
        return ""

    async def send_prompt(self, prompt: str):
        await self.clear_composer()
        if not await self.type_into_composer(prompt):
            return False
        await asyncio.sleep(0.4)
        composed = await self.composer_text()
        if prompt not in composed and composed not in prompt:
            # fallback for textarea value
            value = await self.evaluate("(document.querySelector('textarea')?.value ?? '')")
            if prompt not in (value or "") and (value or "") not in prompt:
                return False
        send_ok = await self.evaluate(
            "(() => { const btn = document.querySelector('[data-testid=\"send-button\"]') || document.querySelector('button[aria-label*=\"Send\"]') || Array.from(document.querySelectorAll('button')).find(b => /send/i.test(b.innerText || b.getAttribute('aria-label') || '')); if (!btn) return false; btn.click(); return true; })()"
        )
        return bool(send_ok)

    async def login_status(self) -> str:
        js = """(() => {
            const composer = document.getElementById('prompt-textarea')
              || document.querySelector('[data-testid="send-button"]')
              || document.querySelector('textarea')
              || document.querySelector('[contenteditable="true"]')
              || Array.from(document.querySelectorAll('button')).find(b => /send/i.test((b.innerText || b.getAttribute('aria-label') || '')));
            const login = Array.from(document.querySelectorAll('a,button')).find(el => /log in|sign in/i.test((el.innerText || el.getAttribute('aria-label') || '')));
            if (composer) return 'logged_in';
            if (login) return 'login_screen';
            return 'unknown';
        })()"""
        return await self.evaluate(js) or "unknown"

    async def wait_for_response_completion(self, timeout: int) -> str:
        deadline = time.monotonic() + timeout
        previous = ""
        stable_hits = 0
        while time.monotonic() < deadline:
            text = await self.evaluate(
                "(() => Array.from(document.querySelectorAll('[data-message-author-role=\"assistant\"]')).map(el => (el.innerText || el.textContent || '').trim()).filter(Boolean).pop() || '')()"
            )
            text = (text or "").strip()
            if text and text == previous:
                stable_hits += 1
                if stable_hits >= 2:
                    return text
            else:
                stable_hits = 0
                previous = text
            await asyncio.sleep(1)
        return previous.strip()


async def try_direct_api(prompt: str, api_base: str, timeout: int) -> tuple[bool, str, str]:
    # Best-effort probe only. If no recognized direct endpoint exists, fallback to CDP.
    # We intentionally keep the probe narrow so it won't invent a false API.
    for suffix in ("/v1/chat/completions", "/api/chat", "/ask", "/v1/ask"):
        url = api_base.rstrip("/") + suffix
        try:
            r = requests.get(url, timeout=5)
            if r.ok and r.text.strip():
                # A real direct API could be wired here later.
                # For now, only treat as direct if it clearly exposes a non-empty JSON schema we can use.
                data = r.json()
                if isinstance(data, dict) and any(k in data for k in ("response", "message", "answer", "output", "result")):
                    response = str(data.get("response") or data.get("message") or data.get("answer") or data.get("output") or data.get("result") or "")
                    if response:
                        return True, "direct_api", response
        except Exception:
            pass
    return False, "", ""


async def run(prompt: str, profile_id: str, api_base: str, timeout: int) -> dict[str, Any]:
    task_id = uuid.uuid4().hex[:12]
    trace: list[str] = []

    direct_ok, direct_mode, direct_response = await try_direct_api(prompt, api_base, timeout)
    if direct_ok:
        return {
            "task_id": task_id,
            "status": "PASS",
            "mode": direct_mode,
            "prompt": prompt,
            "response": direct_response,
            "blocker": "",
            "stage": "direct_api",
            "current_url": "",
            "page_title": "",
            "composer_ready": False,
            "login_status": "unknown",
            "trace": trace,
        }

    trace.append("resolve_cdp")
    cdp_http, cache_dir = resolve_cdp_http(profile_id, api_base, "")
    if not cdp_http:
        report = empty_report(task_id, prompt)
        report.update({"blocker": f"No live AdsPower CDP endpoint for profile {profile_id}", "trace": trace})
        return report

    try:
        trace.append("list_targets")
        targets = requests.get(f"{cdp_http}/json/list", timeout=5).json()
    except Exception as e:
        report = empty_report(task_id, prompt)
        report.update({"blocker": f"CDP list failed: {e}", "trace": trace})
        return report

    page_target = None
    for t in targets:
        url = t.get("url") or ""
        title = t.get("title") or ""
        if t.get("type") == "page" and (url in OWENGPT_URL_ALIASES or any(alias in url for alias in OWENGPT_URL_ALIASES) or "ChatGPT - OwenGPT" in title):
            page_target = t
            break
    if not page_target:
        for t in targets:
            if t.get("type") == "page":
                page_target = t
                break
    if not page_target or not page_target.get("webSocketDebuggerUrl"):
        report = empty_report(task_id, prompt)
        report.update({"blocker": "No page target found", "trace": trace})
        return report

    cdp = CDP(page_target["webSocketDebuggerUrl"])
    try:
        trace.append("connect_cdp")
        await cdp.connect()
        try:
            trace.append("read_page_state")
            current_url = await cdp.page_url()
            page_title = await cdp.evaluate("document.title") or ""
            composer_ready = (await cdp.login_status()) == "logged_in"
            if OWENGPT_URL not in current_url:
                trace.append("navigate_room")
                await cdp.send("Page.navigate", {"url": OWENGPT_URL})
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    current_url = await cdp.page_url()
                    if OWENGPT_URL in current_url:
                        break
                    await asyncio.sleep(1)
            current_url = await cdp.page_url()
            page_title = await cdp.evaluate("document.title") or page_title
            composer_ready = (await cdp.login_status()) == "logged_in"
            if not composer_ready and OWENGPT_URL not in current_url and not any(alias in current_url for alias in OWENGPT_URL_ALIASES):
                report = empty_report(task_id, prompt)
                report.update({
                    "blocker": f"Navigation failed: {current_url[:120]}",
                    "current_url": current_url,
                    "page_title": page_title,
                    "composer_ready": composer_ready,
                    "login_status": "login_screen" if not composer_ready else "logged_in",
                    "trace": trace,
                })
                return report

            login = await cdp.login_status()
            trace.append(f"login_status={login}")
            if login != "logged_in":
                report = empty_report(task_id, prompt)
                report.update({
                    "blocker": f"Not logged in ({login})",
                    "current_url": current_url,
                    "page_title": page_title,
                    "composer_ready": False,
                    "login_status": login,
                    "trace": trace,
                })
                return report

            trace.append("send_prompt")
            sent = await cdp.send_prompt(prompt)
            if not sent:
                report = empty_report(task_id, prompt)
                report.update({
                    "blocker": "Could not verify composer input or send button",
                    "current_url": current_url,
                    "page_title": page_title,
                    "composer_ready": True,
                    "login_status": login,
                    "trace": trace,
                })
                return report

            trace.append("wait_response")
            response = await cdp.wait_for_response_completion(timeout)
            if not response:
                report = empty_report(task_id, prompt)
                report.update({
                    "blocker": "Timed out waiting for assistant response",
                    "current_url": current_url,
                    "page_title": page_title,
                    "composer_ready": True,
                    "login_status": login,
                    "stage": "waiting",
                    "trace": trace,
                })
                return report

            return {
                "task_id": task_id,
                "status": "PASS",
                "mode": "adspower_cdp",
                "prompt": prompt,
                "response": response,
                "blocker": "",
                "stage": "completed",
                "current_url": current_url,
                "page_title": page_title,
                "composer_ready": True,
                "login_status": login,
                "trace": trace,
            }
        finally:
            await cdp.close()
    except Exception as e:
        report = empty_report(task_id, prompt)
        report.update({"blocker": f"Unexpected error: {e}", "trace": trace})
        return report


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", required=True)
    p.add_argument("--profile-id", default=os.environ.get("ADSPower_USER_ID", DEFAULT_PROFILE_ID))
    p.add_argument("--api", default=DEFAULT_ADSPOWER_API)
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    result = asyncio.run(run(args.prompt, args.profile_id, args.api, args.timeout))
    emit(result)
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
