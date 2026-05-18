#!/usr/bin/env python
# Simplified Chrome automation — use attach mode, no quit
import time, os

from selenium import webdriver
from selenium.webdriver.common.by import By

# Configuration
CDP_PORT = 9222
PAGE_URL = "http://127.0.0.1:8563/static/live_scan.html"
OUT_DIR = r"C:\Users\Apinan\owen-workspace"

# Get timestamp for unique filenames
snap_time = int(time.time() * 1000)
snap1 = os.path.join(OUT_DIR, f"live_scan_auto_{snap_time}_01.png")
snap2 = os.path.join(OUT_DIR, f"live_scan_auto_{snap_time}_02.png")
dom_file = os.path.join(OUT_DIR, f"live_scan_auto_{snap_time}_dom.txt")

print("[1] Connecting to Chrome via CDP (port 9222)...")
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("debuggerAddress", f"localhost:{CDP_PORT}")

driver = None
try:
    # Launch chrome with the debugger port
    from selenium.webdriver.chrome.service import Service
    # No binary path — will find existing Chrome
    driver = webdriver.Chrome(options=chrome_options)
    print("[OK] Connected to existing Chrome")
    
    # Open the target page
    print("[2] Opening page...")
    driver.get(PAGE_URL)
    time.sleep(3)  # Wait for full render
    print(f"[OK] Page loaded: '{driver.title}'")
    
    # Capture DOM before interaction
    print("[3] Capturing DOM...")
    dom = driver.page_source
    with open(dom_file, "w", encoding="utf-8") as f:
        f.write(dom)
    print(f"[OK] DOM saved ({len(dom)} chars)")
    
    # Verification
    print("\n=== VERIFICATION ===")
    html_lower = dom.lower()
    checks = {
        "radar/canvas": "canvas" in html_lower or "svg" in html_lower,
        "skeleton": "skeleton" in html_lower,
        "confidence": "confidence" in html_lower or "progress" in html_lower,
        "cat alert": "cat detected" in html_lower
    }
    for name, found in checks.items():
        print(f"  {name}: {'FOUND ✓' if found else 'NOT FOUND ✗'}")
    
    # Interaction
    print("[4] Clicking first button...")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"   Found {len(buttons)} buttons")
    
    if len(buttons) > 0:
        btn = buttons[0]
        btn_text = btn.text.strip()
        print(f"[5] Clicking button: '{btn_text}'")
        
        # Screenshot before click
        print("[6] Taking screenshot 1...")
        driver.save_screenshot(snap1)
        print(f"[OK] Saved: {snap1} ({os.path.getsize(snap1)} bytes)")
        
        # Click
        print("[7] Clicking...")
        btn.click()
        print("[OK] Clicked")
        
        # After animation
        print("[8] Waiting 1.5s...")
        time.sleep(1.5)
        
        print("[9] Taking screenshot 2...")
        driver.save_screenshot(snap2)
        print(f"[OK] Saved: {snap2} ({os.path.getsize(snap2)} bytes)")
        
        # Post-click DOM
        dom_after = driver.page_source
        with open(dom_file.replace("_dom.txt", "_after.txt"), "w", encoding="utf-8") as f:
            f.write(dom_after)
        
        # Final report
        print(f"\n=== RESULT ===")
        print(f"Screenshot 1: {snap1}")
        print(f"Screenshot 2: {snap2}")
        print(f"DOM: {dom_file}")
        print(f"Verification: radar={checks['radar/canvas']}, skeleton={checks['skeleton']}, confidence={checks['confidence']}, catAlert={checks['cat alert']}")
    else:
        print("[!] No buttons found")
        
finally:
    print("\n[!] DO NOT CALL driver.quit() — leaving Chrome running")
    # NOT calling driver.quit() — browser stays open for next automation
