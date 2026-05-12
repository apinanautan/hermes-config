import asyncio
from playwright.async_api import async_playwright
import sys

async def run():
    port = sys.argv[1]
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            page = browser.contexts[0].pages[0]
            
            # Find history nav
            nav = page.locator("nav").filter(has_text="ประวัติการแชต")
            # The actual history items are often inside an <a> but the menu is a sibling button
            # Or the li contains the <a> and the button
            
            # Find all li that contain a link (history items usually link to the chat)
            real_items = nav.locator("li:has(a)")
            
            count = await real_items.count()
            print(f"Found {count} chat items")
            
            if count > 0:
                first_chat = real_items.first
                print(f"Targeting chat: {await first_chat.inner_text()}")
                
                await first_chat.hover()
                # Look for the menu button. It often has aria-haspopup="menu"
                menu_btn = first_chat.locator("button[aria-haspopup='menu']")
                
                if await menu_btn.count() == 0:
                    # Fallback: look for button with specific classes or three dots icon
                    menu_btn = first_chat.locator("button.flex.items-center") # Just a guess
                
                if await menu_btn.count() > 0:
                    print("Clicking menu button...")
                    await menu_btn.first.click()
                    await asyncio.sleep(1) # Wait for menu to appear
                    
                    # Delete option
                    # In Thai, it's 'ลบ' (Delete)
                    delete_opt = page.locator("[role='menuitem']").filter(has_text="ลบ")
                    if await delete_opt.count() == 0:
                         delete_opt = page.locator("div").filter(has_text="ลบ").last
                    
                    if await delete_opt.count() > 0:
                        print("Clicking Delete...")
                        await delete_opt.first.click()
                        await asyncio.sleep(1)
                        
                        # Confirmation modal button 'ลบ'
                        confirm_btn = page.locator("button").filter(has_text="ลบ").last
                        await confirm_btn.wait_for(state="visible", timeout=5000)
                        await confirm_btn.click()
                        print("Deletion triggered successfully")
                    else:
                        print("Delete option not found in open menu")
                else:
                    print("Could not find menu button for history item")
            else:
                print("No chat items found in sidebar")

            await browser.close()
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == '__main__':
    asyncio.run(run())
