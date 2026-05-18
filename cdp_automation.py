#!/usr/bin/env python
# Chrome CDP automation without Puppeteer
import json
import websocket
import subprocess
import time
import os

TARGET_PAGE_ID = "357EB0543D7498C3B6B9673FB7C7184D"
CDP_URL = f"ws://localhost:9222/devtools/page/{TARGET_PAGE_ID}"

def send_cmd(ws, method, params=None):
    """Send CDP command and return response"""
    cmd = {"id": 1, "method": method}
    if params:
        cmd["params"] = params
    ws.send(json.dumps(cmd))
    resp = ws.recv()
    return json.loads(resp)

def main():
    print(f"[1] Connecting to {CDP_URL}...")
    ws = websocket.WebSocket()
    ws.connect(CDP_URL)
    print("[OK] Connected to Chrome CDP")

    # Enable required domains
    send_cmd(ws, "Page.enable")
    send_cmd(ws, "DOM.enable")
    print("[OK] Enable Page/DOM domains")

    # Get document
    doc = send_cmd(ws, "DOM.getDocument")
    root_id = doc["result"]["root"]["nodeId"]
    print(f"[OK] Got document root: {root_id}")

    # Search for any button containing "SCAN" or "overlay"
    print("[2] Searching for SCAN/Overlay button...")
    scripts = [
        "document.querySelectorAll('button')",
        "Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim())"
    ]

    for script in scripts:
        result = send_cmd(ws, "Runtime.evaluate", {"expression": script})
        if "result" in result and "result" in result["result"]:
            val = result["result"]["result"]
            if val.get("type") == "string":
                buttons = json.loads(val.get("value", "[]"))
                print(f"[INFO] Buttons found: {buttons}")

    # Click on first button found (Overlay toggle likely)
    click_code = """
    (function() {
        const buttons = document.querySelectorAll('button');
        if (buttons.length > 0) {
            const btn = buttons[0];
            const rect = btn.getBoundingClientRect();
            return {
                text: btn.textContent.trim(),
                x: rect.left + rect.width/2,
                y: rect.top + rect.height/2
            };
        }
        return null;
    })()
    """
    result = send_cmd(ws, "Runtime.evaluate", {"expression": click_code})
    if result.get("result", {}).get("result", {}).get("type") == "object":
        btn_info = json.loads(result["result"]["result"]["value"])
        print(f"[INFO] Clicking button: {btn_info['text']} at ({btn_info['x']}, {btn_info['y']})")

        # Emit mouse events
        send_cmd(ws, "Input.dispatchMouseEvent", {
            "type": "mouseMoved",
            "x": btn_info["x"],
            "y": btn_info["y"],
            "buttons": 0
        })
        time.sleep(0.1)
        send_cmd(ws, "Input.dispatchMouseEvent", {
            "type": "mousePressed",
            "x": btn_info["x"],
            "y": btn_info["y"],
            "button": "left",
            "clickCount": 1
        })
        time.sleep(0.05)
        send_cmd(ws, "Input.dispatchMouseEvent", {
            "type": "mouseReleased",
            "x": btn_info["x"],
            "y": btn_info["y"],
            "button": "left",
            "clickCount": 1
        })
        print("[OK] Click simulated")

        # Zigzag pattern
        for i in range(10):
            x = btn_info["x"] + (i % 2 == 0 and -20 or 20)
            y = btn_info["y"] + i * 5
            send_cmd(ws, "Input.dispatchMouseEvent", {
                "type": "mouseMoved",
                "x": x,
                "y": y,
                "buttons": 0
            })
            time.sleep(0.05)
        print("[OK] Zigzag pattern done")

    # Take screenshot immediately
    snap = int(time.time() * 1000)
    out_dir = r"C:\Users\Apinan\owen-workspace"
    snap1 = os.path.join(out_dir, f"live_scan_{snap}_01.png")
    snap2 = os.path.join(out_dir, f"live_scan_{snap}_02.png")

    print("[3] Taking screenshot 1 (immediate)...")
    shot1 = send_cmd(ws, "Page.captureScreenshot", {"format": "png"})
    with open(snap1, "wb") as f:
        f.write(bytes(shot1["data"], "latin1"))
    print(f"[OK] Saved: {snap1}")

    print("[3.5] Waiting 1.5s for animation...")
    time.sleep(1.5)

    print("[4] Taking screenshot 2 (after animation)...")
    shot2 = send_cmd(ws, "Page.captureScreenshot", {"format": "png"})
    with open(snap2, "wb") as f:
        f.write(bytes(shot2["data"], "latin1"))
    print(f"[OK] Saved: {snap2}")

    # DOM snapshot
    print("[5] Extracting DOM...")
    dom = send_cmd(ws, "DOM.getOuterHTML", {"nodeId": root_id})
    dom_content = dom["result"]["outerHTML"]
    print(f"[OK] DOM captured ({len(dom_content)} chars)")

    # Verification (check for expected elements)
    print("\n=== VERIFICATION ===")
    checks = {
        "radar/canvas": "canvas" in dom_content.lower() or "svg" in dom_content.lower(),
        "skeleton": "skeleton" in dom_content.lower(),
        "confidence": "confidence" in dom_content.lower() or "progress" in dom_content.lower(),
        "cat alert": "cat detected" in dom_content.lower()
    }
    for name, found in checks.items():
        print(f"  {name}: {'FOUND ✓' if found else 'NOT FOUND ✗'}")

    # Save DOM
    with open(os.path.join(out_dir, f"live_scan_{snap}_dom.txt"), "w", encoding="utf-8") as f:
        f.write(dom_content)
    print(f"[OK] DOM saved")

    ws.close()
    print("\n=== DONE ===")
    print(f"Screenshots: {snap1}, {snap2}")
    print(f"DOM: live_scan_{snap}_dom.txt")
    return True

if __name__ == "__main__":
    try:
        main()
    except websocket.WebSocketException as e:
        print(f"[ERROR] WebSocket: {e}")
        print("[HINT] Maybe Chrome just started or CDP not ready yet — try again in 3s")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
