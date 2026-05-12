import asyncio
from playwright.async_api import async_playwright
import sys

async def run():
    port = sys.argv[1]
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            context = browser.contexts[0]
            page = context.pages[0]
            
            # 1. Try to expand sidebar if closed
            expand_btn = page.locator("button").filter(has_text="เปิดแถบข้าง")
            if await expand_btn.count() > 0:
                print("Sidebar closed, expanding...")
                await expand_btn.click()
                await asyncio.sleep(1)

            # 2. Look for ANY button with '...' or that looks like a menu
            # Often ChatGPT uses aria-label="เมนูการตั้งค่าแชต" or similar
            # Let's find buttons with dots or menu roles inside history area
            menu_btns = page.locator("button[aria-haspopup='menu']").all()
            btns = await menu_btns
            print(f"DEBUG: Found {len(btns)} menu buttons")

            if len(btns) > 0:
                # Target the most recent one (usually near the top)
                target_btn = btns[0]
                print("Clicking first menu button found...")
                await target_btn.click()
                await asyncio.sleep(1)

                # 3. Look for 'ลบ' in the popup
                delete_option = page.get_by_role("menuitem").filter(has_text="ลบ")
                if await delete_option.count() > 0:
                    print("Found 'ลบ' menu item, clicking...")
                    await delete_option.first.click()
                    await asyncio.sleep(1)

                    # 4. Confirm Delete in Modal
                    # Modal buttons usually say 'ลบ' (Red) and 'ยกเลิก'
                    confirm_btn = page.locator("button").filter(has_text="ลบ").last
                    if await confirm_btn.count() > 0:
                        await confirm_btn.click()
                        print("ACTION_COMPLETE: Deleted successfully")
                    else:
                        print("ERROR: Confirm button not found in modal")
                else:
                    print("ERROR: 'Delete' (ลบ) option not found in menu")
            else:
                print("ERROR: No chat menu dots found. Is sidebar empty?")

            await page.screenshot(path="final_attempt.png")
            await browser.close()
        except Exception as e:
            print(f"CRITICAL_ERROR: {str(e)}")

if __name__ == '__main__':
    asyncio.run(run())
