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
            
            print(f"URL: {page.url}")
            
            # 1. Look for the first chat item in history
            # The structure is usually li -> a (the chat link)
            # and a button for settings (three dots)
            
            # Find the nav for history
            nav = page.locator("nav[aria-label='ประวัติการแชต'], nav[aria-label='Chat history']")
            if await nav.count() == 0:
                print("Could not find history nav")
                await page.screenshot(path="no_nav.png")
                return

            # Find history items (li tags)
            items = nav.locator("li[data-testid^='history-item-']")
            count = await items.count()
            print(f"Found {count} items in history nav")
            
            if count > 0:
                target = items.first
                print("Hovering first item...")
                await target.hover()
                
                # Find the menu button (...) inside this item
                menu_btn = target.locator("button[aria-haspopup='menu']")
                if await menu_btn.count() > 0:
                    await menu_btn.click()
                    print("Menu clicked")
                    
                    # Look for Delete option (ลบ)
                    delete_opt = page.locator("[role='menuitem']").filter(has_text="ลบ")
                    if await delete_opt.count() == 0:
                        delete_opt = page.locator("[role='menuitem']").filter(has_text="Delete")
                    
                    if await delete_opt.count() > 0:
                        await delete_opt.first.click()
                        print("Delete option clicked")
                        
                        # Wait for confirmation modal
                        # Usually a button with text 'ลบ' in a modal
                        confirm_btn = page.locator("button").filter(has_text="ลบ").last
                        if await confirm_btn.count() == 0:
                             confirm_btn = page.locator("button").filter(has_text="Delete").last
                        
                        await confirm_btn.wait_for(state="visible", timeout=5000)
                        await confirm_btn.click()
                        print("Confirm clicked. Deletion should be complete.")
                    else:
                        print("Delete option not found in menu")
                else:
                    print("Menu button not found in first item")
            else:
                print("No history items to delete")
            
            await browser.close()
        except Exception as e:
            print(f"ERROR: {e}")
            if 'page' in locals():
                await page.screenshot(path="last_error.png")

if __name__ == '__main__':
    asyncio.run(run())
