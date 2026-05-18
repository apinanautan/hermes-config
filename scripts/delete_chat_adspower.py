#!/usr/bin/env python3
"""
delete_chat_adspower.py

Delete a ChatGPT conversation from an authenticated AdsPower CDP session.
JSON stdout only.

Known-good selectors from live DOM:
- chat menu button: button[aria-haspopup="menu"] with aria-label "เปิดตัวเลือกบทสนทนาสำหรับ <title>"
- menu item: "ลบ" / "Delete"
- confirm dialog: "ต้องการลบแชตนี้ใช่ไหม"
- confirm button: "ลบ" / "Delete"
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
OWEN_PATH = SCRIPT_DIR / "owengpt_direct_stdout.py"
OWENGPT_URL = "https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owengpt"


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def load_owen_module():
    spec = importlib.util.spec_from_file_location("owen_helpers", str(OWEN_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load helpers from {OWEN_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--title", required=True, help="Exact chat title to delete")
    p.add_argument("--profile-id", default="k1cawerp")
    p.add_argument("--api", default="http://local.adspower.net:50325")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


async def run(title: str, profile_id: str, api_base: str, dry_run: bool) -> dict[str, Any]:
    mod = load_owen_module()
    cdp_http, _ = mod.resolve_cdp_http(profile_id, api_base, "")
    if not cdp_http:
        return {
            "status": "FAIL",
            "title": title,
            "deleted": False,
            "blocker": f"No live AdsPower CDP endpoint for profile {profile_id}",
        }

    try:
        targets = requests.get(f"{cdp_http}/json/list", timeout=10).json()
    except Exception as e:
        return {
            "status": "FAIL",
            "title": title,
            "deleted": False,
            "blocker": f"CDP list failed: {e}",
        }

    page_target = None
    for t in targets:
        if t.get("type") == "page" and "chatgpt.com" in (t.get("url") or ""):
            page_target = t
            break
    if not page_target or not page_target.get("webSocketDebuggerUrl"):
        return {
            "status": "FAIL",
            "title": title,
            "deleted": False,
            "blocker": "No ChatGPT page target found",
        }

    cdp = mod.CDP(page_target["webSocketDebuggerUrl"])
    try:
        await cdp.connect()
        try:
            current_url = await cdp.page_url()
            if OWENGPT_URL not in current_url:
                await cdp.send("Page.navigate", {"url": OWENGPT_URL})
                deadline = asyncio.get_event_loop().time() + 30
                while asyncio.get_event_loop().time() < deadline:
                    current_url = await cdp.page_url()
                    if OWENGPT_URL in current_url:
                        break
                    await asyncio.sleep(1)

            nav_probe = await cdp.evaluate(r"""(() => {
              const nav = Array.from(document.querySelectorAll('nav')).find(n => /เมื่อเร็วๆ นี้|Recently|ChatGPT|ประวัติการแชต|แชตใหม่/i.test(n.innerText||'')) || null;
              return nav ? (nav.innerText || '').includes(%s) : false;
            })()""" % json.dumps(title))
            if not nav_probe:
                return {
                    "status": "FAIL",
                    "title": title,
                    "deleted": False,
                    "blocker": "Target chat title not visible in sidebar",
                }

            if dry_run:
                return {
                    "status": "PASS",
                    "title": title,
                    "deleted": False,
                    "blocker": "",
                    "dry_run": True,
                }

            result = await cdp.evaluate(f"""(async () => {{
              const title = {json.dumps(title)};
              const menuBtn = Array.from(document.querySelectorAll('button[aria-haspopup="menu"]'))
                .find(b => (b.getAttribute('aria-label') || '').includes(title));
              if (!menuBtn) return {{ok:false, step:'menu_btn_missing'}};
              menuBtn.click();
              await new Promise(r => setTimeout(r, 250));

              const deleteItem = Array.from(document.querySelectorAll('[role="menuitem"]'))
                .find(i => /^(ลบ|Delete)$/i.test((i.innerText || i.textContent || '').trim()));
              if (!deleteItem) return {{ok:false, step:'delete_menu_missing', items: Array.from(document.querySelectorAll('[role="menuitem"]')).map(i => (i.innerText || i.textContent || '').trim())}};
              deleteItem.click();
              await new Promise(r => setTimeout(r, 300));

              const dialog = Array.from(document.querySelectorAll('[role="dialog"]')).pop() || null;
              if (!dialog) return {{ok:false, step:'dialog_missing'}};
              const confirmBtn = Array.from(dialog.querySelectorAll('button')).find(b => /^(ลบ|Delete)$/i.test((b.innerText || b.getAttribute('aria-label') || '').trim()));
              if (!confirmBtn) return {{ok:false, step:'confirm_missing', dialogText: (dialog.innerText || dialog.textContent || '').trim()}};
              confirmBtn.click();
              await new Promise(r => setTimeout(r, 1000));

              const nav = Array.from(document.querySelectorAll('nav')).find(n => /เมื่อเร็วๆ นี้|Recently/i.test(n.innerText || '')) || null;
              const stillVisible = !!(nav && (nav.innerText || '').includes(title));
              return {{ok:true, stillVisible}};
            }})()""")

            if not isinstance(result, dict) or not result.get("ok"):
                return {
                    "status": "FAIL",
                    "title": title,
                    "deleted": False,
                    "blocker": f"Delete flow failed: {result}",
                }

            return {
                "status": "PASS",
                "title": title,
                "deleted": not bool(result.get("stillVisible")),
                "blocker": "" if not result.get("stillVisible") else "Chat still visible after delete click",
                "selectors": {
                    "menu_button": 'button[aria-haspopup="menu"]',
                    "menu_item_delete": 'role=menuitem text=ลบ|Delete',
                    "confirm_dialog": 'role=dialog',
                    "confirm_button": 'button text=ลบ|Delete',
                },
            }
        finally:
            await cdp.close()
    except Exception as e:
        return {
            "status": "FAIL",
            "title": title,
            "deleted": False,
            "blocker": f"Unexpected error: {e}",
        }


def main() -> int:
    args = parse_args()
    result = asyncio.run(run(args.title, args.profile_id, args.api, args.dry_run))
    emit(result)
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
