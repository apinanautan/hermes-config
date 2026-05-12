import asyncio
from playwright.async_api import async_playwright
import sys

async def run():
    port = sys.argv[1]
    async with async_playwright() as p:
        try:
            print(f"Connecting to port {port}")
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Navigate to ChatGPT home to ensure we are in the main UI
            print("Navigating to ChatGPT...")
            await page.goto("https://chatgpt.com", wait_until="networkidle")
            await asyncio.sleep(3) # Wait for UI to settle
            
            await page.screenshot(path="gpt_check.png")
            print(f"Page title: {await page.title()}")
            
            # Debug: List elements that might be the history menu
            items = await page.locator("li[data-testid^='history-item-']").count()
            print(f"Found {items} history items.")
            
            if items > 0:
                # Try to click the menu button (...) of the first (most recent) item
                print("Clicking menu of first chat item...")
                first_item = page.locator("li[data-testid^='history-item-']").first
                menu_btn = first_item.locator("button[aria-haspopup='menu']")
                
                # Make sure it's visible (hover if needed)
                await first_item.hover()
                await menu_btn.wait_for(state="visible", timeout=5000)
                await menu_btn.click()
                
                # Click Delete
                # ChatGPT menu items often use role="menuitem"
                # The text is "Delete" or "Delete chat"
                print("Looking for Delete option...")
                delete_opt = page.locator("[role='menuitem']", has_text="Delete")
                if await delete_opt.count() == 0:
                    delete_opt = page.locator("div", has_text="Delete").last
                
                await delete_opt.wait_for(state="visible", timeout=5000)
                await delete_opt.click()
                
                # Confirm modal
                print("Confirming deletion...")
                # The confirmation button is usually red or has specific text
                confirm_btn = page.locator("button", has_text="Delete").last
                await confirm_btn.wait_for(state="visible", timeout=5000)
                await confirm_btn.click()
                
                print("SUCCESS_FLAG: Delete sequence completed")
            else:
                # Try dropdown at the top navigation (for active chat)
                print("No history items found. Checking top header for active chat...")
                # The header title is often a button
                header_btn = page.locator("header button[aria-haspopup='menu']").first
                if await header_btn.count() > 0:
                    await header_btn.click()
                    # Look for Delete in this menu
                    delete_opt = page.locator("[role='menuitem']", has_text="Delete chat")
                    if await delete_opt.count() > 0:
                        await delete_opt.click()
                        confirm_btn = page.locator("button", has_text="Delete").last
                        await confirm_btn.click()
                        print("SUCCESS_FLAG: Delete sequence via header completed")
                    else:
                        print("Delete option not found in header menu")
                else:
                    print("No active chat menu found in header")
            
            await browser.close()
        except Exception as e:
            print(f"ERROR: {e}")
            if 'page' in locals():
                await page.screenshot(path="gpt_error.png")

if __name__ == '__main__':
    asyncio.run(run())
