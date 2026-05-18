import asyncio, json, requests, websockets

PORT = 52631

async def main():
    targets = requests.get(f"http://127.0.0.1:{PORT}/json/list", timeout=5).json()
    ws_url = next((t["webSocketDebuggerUrl"] for t in targets if t.get("type") == "page"), None)
    async with websockets.connect(ws_url, max_size=2**24) as ws:
        _id = [0]
        async def js(e):
            _id[0] += 1
            await ws.send(json.dumps({"id": _id[0], "method": "Runtime.evaluate",
                "params": {"expression": e, "returnByValue": True, "awaitPromise": True}}))
            while True:
                d = json.loads(await ws.recv())
                if d.get("id") == _id[0]:
                    return d.get("result", {}).get("result", {}).get("value")

        expr = "Array.from(document.querySelectorAll('.bubble')).slice(-10).map(b => { var txt = b.querySelector('.message') || b.querySelector('.message-content'); var from = b.classList.contains('is-out') ? 'ME' : 'BOT'; return from + ': ' + (txt ? txt.innerText.substring(0,200) : '(empty)'); }).join(' ||| ')"
        result = await js(expr)
        if result:
            for msg in result.split(" ||| "):
                print(msg)
        else:
            print("no bubbles found")

asyncio.run(main())
