#!/usr/bin/env python
# Simplified Chrome automation — no quit, no graceful close
import selenium
import time, os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

snap_time = int(time.time() * 1000)
out_dir = r"C:\Users\Apinan\owen-workspace"
snap1 = os.path.join(out_dir, f"live_scan_auto_{snap_time}_01.png")
snap2 = os.path.join(out_dir, f"live_scan_auto_{snap_time}_02.png")
dom_file = os.path.join(out_dir, f"live_scan_auto_{snap_time}_dom.txt")

print("[1] Prepare Chrome options...")
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")

# DO NOT call driver.quit() — leave browser open
chrome_options.add_argument("--disable-backgrounding-occluded-windows")
chrome_options.add_argument("--disable-extended-private-vm-cache")

# Try to find existing Chrome session instead
print("[2] Attempting to attach to existing Chrome...")

# Create a driver but avoid quit at exit
class NoQuitDriver:
    def __init__(self):
        self.driver = None
    
    def connect(self):
        print("[3] Connecting to Chrome CDP (port 9222)...")
        self.driver = webdriver.Chrome(options=chrome_options)
        print("[OK] Connected to Chrome")
        return self.driver
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        # NO-op — DO NOT quit
        print("[!] Skipping driver.quit() — browser stays open")

driver = None
try:
    with NoQuitDriver() as nd:
        driver = nd.connect()
        
        print("[4] Opening target URL...")
        driver.get("http://127.0.0.1:8563/static/live_scan.html")
        time.sleep(3)
        print(f"[OK] Loaded: {driver.title}")
        
        # Get DOM
        print("[5] Capturing DOM...")
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
        
        # Click
        print("[6] Clicking first button...")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"   Found {len(buttons)} buttons")
        
        if len(buttons) > 0:
            btn = buttons[0]
            print(f"[7] Button text: '{btn.text.strip()}'")
            
            # Screenshot before click
            print("[8] Taking screenshot 1...")
            driver.save_screenshot(snap1)
            print(f"[OK] Saved: {snap1}")
            
            # Click
            print("[9] Clicking button...")
            btn.click()
            print("[OK] Clicked")
            
            # Wait and screenshot
            print("[10] Waiting 1.5s...")
            time.sleep(1.5)
            
            print("[11] Taking screenshot 2...")
            driver.save_screenshot(snap2)
            print(f"[OK] Saved: {snap2}")
            
            # Post-click DOM
            dom_after = driver.page_source
            with open(dom_file.replace("_dom.txt", "_after.txt"), "w", encoding="utf-8") as f:
                f.write(dom_after)
            
            print(f"\n=== RESULT ===")
            print(f"Screenshots: {snap1}, {snap2}")
            print(f"DOM: {dom_file}")
            print(f"Verification: radar={checks['radar/canvas']}, skeleton={checks['skeleton']}, confidence={checks['confidence']}, catAlert={checks['cat alert']}")
        
finally:
    print("\n[DONE] Driver not quit — Chrome stays open")
    print("Screenshots exist if script ran successfully")
