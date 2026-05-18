import asyncio, json, requests, websockets, time, subprocess, os, re

PORT = 52631
TG_BOT = "https://web.telegram.org/k/#@MeszzzBot"


async def main():
    targets = requests.get(f"http://127.0.0.1:{PORT}/json/list", timeout=5).json()
    ws_url = next(
        (t["webSocketDebuggerUrl"] for t in targets if t.get("type") == "page" and "chatgpt" in t.get("url", "")),
        next((t["webSocketDebuggerUrl"] for t in targets if t.get("type") == "page"), None)
    )
    print(f"Page: {next((t.get('url','')[:60] for t in targets if t.get('type')=='page'), None)}")

    async with websockets.connect(ws_url, max_size=2**24) as ws:
        _id = [0]

        async def cmd(m, p=None):
            _id[0] += 1
            msg = {"id": _id[0], "method": m}
            if p:
                msg["params"] = p
            await ws.send(json.dumps(msg))
            while True:
                d = json.loads(await ws.recv())
                if d.get("id") == _id[0]:
                    return d

        async def js(e):
            r = await cmd("Runtime.evaluate", {"expression": e, "returnByValue": True, "awaitPromise": True})
            return r.get("result", {}).get("result", {}).get("value")

        # Navigate to Telegram bot
        await cmd("Page.navigate", {"url": TG_BOT})
        print("Navigating to Telegram...")
        await asyncio.sleep(8)

        url = await js("window.location.href")
        title = await js("document.title")
        print(f"URL: {url}")
        print(f"Title: {title}")

        # Check login
        sidebar = await js("!!document.querySelector('.chatlist-top, .sidebar-left-section')")
        print(f"Sidebar: {sidebar}")

        # Get all visible text
        body_text = await js("(document.body || {}).innerText || ''")
        if body_text:
            print(f"Body (200): {body_text[:200]}")

        # Try to find message input
        inp = await js(
            "document.querySelector('.input-message-input, [contenteditable][class*=input], .composer-rich-textarea') ? 'found' : 'not found'"
        )
        print(f"Message input: {inp}")

        if inp == "found":
            # Test 1: General question
            print("\n--- Test 1: General question ---")
            await js("var el = document.querySelector('.input-message-input, [contenteditable][class*=input]'); if(el){el.focus();el.click();}")
            await asyncio.sleep(0.5)
            await cmd("Input.insertText", {"text": "สวัสดีครับ"})
            await asyncio.sleep(0.3)
            await cmd("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13})
            await cmd("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13})
            print("Sent 'สวัสดีครับ'. Waiting 15s...")
            await asyncio.sleep(15)

            msgs = await js(
                "Array.from(document.querySelectorAll('.bubble')).slice(-5).map(b => { var t = b.querySelector('.message,.message-content'); return (b.classList.contains('is-out')?'ME:':'BOT:') + (t?t.innerText.substring(0,150):''); }).join(' || ')"
            )
            print(f"Chat: {msgs}")

            # Test 2: Work task  
            print("\n--- Test 2: Work task ---")
            await js("var el = document.querySelector('.input-message-input, [contenteditable][class*=input]'); if(el){el.focus();el.click();}")
            await asyncio.sleep(0.5)
            await cmd("Input.insertText", {"text": "สร้าง hello world python"})
            await asyncio.sleep(0.3)
            await cmd("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13})
            await cmd("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13})
            print("Sent work task. Waiting 10s for confirmation...")
            await asyncio.sleep(10)

            msgs2 = await js(
                "Array.from(document.querySelectorAll('.bubble')).slice(-5).map(b => { var t = b.querySelector('.message,.message-content'); return (b.classList.contains('is-out')?'ME:':'BOT:') + (t?t.innerText.substring(0,200):''); }).join(' || ')"
            )
            print(f"After work: {msgs2}")

            # Test 3: Confirm
            print("\n--- Test 3: Confirm ---")
            await js("var el = document.querySelector('.input-message-input, [contenteditable][class*=input]'); if(el){el.focus();el.click();}")
            await asyncio.sleep(0.3)
            await cmd("Input.insertText", {"text": "ทำเลย"})
            await asyncio.sleep(0.3)
            await cmd("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13})
            await cmd("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13})
            print("Sent 'ทำเลย'. Waiting 90s for brain + worker...")
            await asyncio.sleep(90)

            msgs3 = await js(
                "Array.from(document.querySelectorAll('.bubble')).slice(-8).map(b => { var t = b.querySelector('.message,.message-content'); return (b.classList.contains('is-out')?'ME:':'BOT:') + (t?t.innerText.substring(0,300):''); }).join(' ||| ')"
            )
            if msgs3:
                for m in msgs3.split(" ||| "):
                    print(m)
        else:
            print("Cannot find message input - may need to login first")


asyncio.run(main())
