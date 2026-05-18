#!/usr/bin/env python
# Chrome automation without CDP flags — uses undetected-chromedriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, time, uuid

# Create unique output paths
snap_time = int(time.time() * 1000)
out_dir = r"C:\Users\Apinan\owen-workspace"
snap1 = os.path.join(out_dir, f"live_scan_{snap_time}_01.png")
snap2 = os.path.join(out_dir, f"live_scan_{snap_time}_02.png")
dom_file = os.path.join(out_dir, f"live_scan_{snap_time}_dom.txt")

print(f"[1] Launching Chrome (undetected)...")
driver = uc.Chrome(version_main=148)  # force matched version
print("[OK] Chrome launched")

try:
    print("[2] Opening live_scan.html...")
    driver.get("http://127.0.0.1:8563/static/live_scan.html")
    time.sleep(2)
    print(f"[OK] Loaded: {driver.title}")

    # Get DOM snapshot
    print("[3] Capturing DOM...")
    dom_content = driver.page_source
    with open(dom_file, "w", encoding="utf-8") as f:
        f.write(dom_content)
    print(f"[OK] DOM saved ({len(dom_content)} chars)")

    # Verify elements
    print("\n=== VERIFICATION ===")
    html_lower = dom_content.lower()

    has_radar = "canvas" in html_lower or "svg" in html_lower
    has_skeleton = "skeleton" in html_lower
    has_confidence = "confidence" in html_lower or "progress" in html_lower
    has_cat = "cat detected" in html_lower

    print(f"  Radar/canvas: {'FOUND ✓' if has_radar else 'NOT FOUND ✗'}")
    print(f"  Skeleton: {'FOUND ✓' if has_skeleton else 'NOT FOUND ✗'}")
    print(f"  Confidence: {'FOUND ✓' if has_confidence else 'NOT FOUND ✗'}")
    print(f"  CAT DETECTED: {'FOUND ✓' if has_cat else 'NOT FOUND ✗'}")

    # Find and click button
    print("[4] Looking for buttons...")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"   Found {len(buttons)} buttons")

    if len(buttons) > 0:
        btn = buttons[0]
        btn_text = btn.text.strip()
        print(f"[5] Clicking button: '{btn_text}'")

        # Get position for gesture
        rect = btn.rect
        cx = rect["x"] + rect["width"] / 2
        cy = rect["y"] + rect["height"] / 2
        print(f"[6] Button center: ({cx:.1f}, {cy:.1f})")

        # Simulate zigzag
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(driver)
        actions.move_to_element(btn).perform()
        print("[7] Mouse moved over button")

        for i in range(15):
            x_offset = -40 if i % 2 == 0 else 40
            y_offset = i * 4
            actions.move_by_offset(x_offset, y_offset).perform()
        print("[8] Zigzag pattern completed")

        # Click
        actions.click().perform()
        print("[9] Button clicked")

        # Take screenshot 1 (immediate)
        print("[10] Taking screenshot 1...")
        driver.save_screenshot(snap1)
        print(f"[OK] Saved: {snap1} ({os.path.getsize(snap1)} bytes)")

        # Wait for animation
        print("[11] Waiting 1.5s for animation...")
        time.sleep(1.5)

        # Take screenshot 2
        print("[12] Taking screenshot 2...")
        driver.save_screenshot(snap2)
        print(f"[OK] Saved: {snap2} ({os.path.getsize(snap2)} bytes)")

        # Update DOM after interaction
        print("[13] Updating DOM after click...")
        dom_after = driver.page_source
        with open(dom_file.replace("_dom.txt", "_after_dom.txt"), "w", encoding="utf-8") as f:
            f.write(dom_after)

        print(f"\n=== RESULT ===")
        print(f"Screenshot 1: {snap1}")
        print(f"Screenshot 2: {snap2}")
        print(f"DOM: {dom_file}")
        print(f"Verification: radar={has_radar}, skeleton={has_skeleton}, confidence={has_confidence}, catAlert={has_cat}")

    else:
        print("[!] No buttons found — screenshot will be empty check")

finally:
    try:
        if driver:
            driver.quit()
    except Exception:
        pass
    print("\n[DONE] Chrome closed (or force-closed)")
