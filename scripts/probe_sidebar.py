import asyncio
from playwright.async_api import async_playwright
import sys

async def run():
    port = sys.argv[1]
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        page = browser.contexts[0].pages[0]
        
        print("--- Sidebar Content Probe ---")
        # Try to find the history nav by different labels
        nav = page.locator("nav").filter(has_text="ประวัติการแชต")
        if await nav.count() == 0:
            nav = page.locator("nav").filter(has_text="Chat history")

        if await nav.count() > 0:
            # Look for all buttons inside the navigation
            buttons = nav.locator("button")
            btn_count = await buttons.count()
            print(f"Found {btn_count} buttons in sidebar")
            
            # The '...' button often has no text but has aria-haspopup="menu"
            menu_btns = nav.locator("button[aria-haspopup='menu']")
            print(f"Found {await menu_btns.count()} menu (...) buttons")
            
            if await menu_btns.count() > 0:
                first_menu = menu_btns.first
                print("Clicking first menu button...")
                await first_menu.click()
                await asyncio.sleep(2)
                
                # Capture all visible menu items text
                menu_items = await page.locator("[role='menuitem']").all_inner_texts()
                print(f"Menu items found: {menu_items}")
                
                # Try to click 'ลบ'
                delete_btn = page.locator("[role='menuitem']").filter(has_text="ลบ")
                if await delete_btn.count() > 0:
                    print("Found 'ลบ' button, clicking...")
                    await delete_btn.first.click()
                    await asyncio.sleep(2)
                    
                    # Confirm modal
                    confirm_btn = page.locator("button").filter(has_text="ลบ").last
                    print(f"Confirm button count: {await confirm_btn.count()}")
                    if await confirm_btn.count() > 0:
                        await confirm_btn.click()
                        print("DELETED_SUCCESSFULLY")
                    else:
                        print("Confirmation button not found")
                else:
                    print("Delete option ('ลบ') not found in menu items")
            else:
                print("No menu buttons found")
        else:
            print("History navigation not found")
            
        await page.screenshot(path="sidebar_debug.png")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
