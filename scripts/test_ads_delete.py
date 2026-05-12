import asyncio
import sys
import os
import subprocess
from playwright.async_api import async_playwright

async def get_win_ip():
    if os.name == 'nt':
        return "127.0.0.1"
    try:
        res = subprocess.check_output("ip route show | grep default | awk '{print $3}'", shell=True)
        return res.decode().strip()
    except:
        return "127.0.0.1"

async def run():
    if len(sys.argv) < 2:
        print("Usage: python test_ads_delete.py <port>")
        return
    port = sys.argv[1]
    win_ip = await get_win_ip()
    cdp_url = f"http://{win_ip}:{port}"
    gpt_url = "https://chatgpt.com/"  # Standard ChatGPT or OwenGPT
    prompt = "This is a test message for automation deletion. Please reply briefly."

    async with async_playwright() as p:
        print(f"Connecting to AdsPower CDP: {cdp_url}")
        try:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = await context.new_page()
            
            print(f"Opening ChatGPT: {gpt_url}")
            await page.goto(gpt_url, wait_until="domcontentloaded")
            
            # Send prompt
            print(f"Sending prompt: {prompt}")
            box = page.locator("#prompt-textarea").last
            await box.wait_for(state="visible", timeout=30000)
            await box.fill(prompt)
            await box.press("Enter")
            
            # Wait for response
            print("Waiting for response...")
            await asyncio.sleep(10) # Simple wait for reply

            # Attempt deletion
            print("Attempting to delete the current chat...")
            try:
                # Wait for sidebar/header to settle
                await asyncio.sleep(5)
                
                # Option 1: Top Right Menu Button (Newer ChatGPT UI)
                # It's usually inside the header.
                header_menu = page.locator("button[aria-label='Chat settings'], button:has(svg):has-text('...')").last
                if await header_menu.is_visible():
                    print("Found header menu button.")
                    await header_menu.click()
                else:
                    # Option 2: Sidebar Menu Button
                    print("Trying sidebar menu...")
                    first_chat = page.locator("ol li").first
                    await first_chat.hover()
                    menu_btn = first_chat.locator("button[aria-haspopup='menu']")
                    await menu_btn.click()
                
                # Click 'Delete' in the popup menu
                # Sometimes it's a div, sometimes a button. Use text search.
                delete_item = page.locator("[role='menuitem'], button", has_text="Delete chat").first
                if await delete_item.count() == 0:
                     delete_item = page.locator("[role='menuitem'], button", has_text="Delete").first
                
                await delete_item.click()
                
                # Confirm in modal
                print("Clicking confirm delete...")
                confirm_btn = page.locator("button.btn-danger, button:has-text('Delete')").last
                await confirm_btn.click()
                print("SUCCESS: Chat deleted.")
            except Exception as e:
                print(f"FAILED to delete chat: {e}")
                await page.screenshot(path="C:/Users/Apinan/owen-workspace/temp_images/delete_debug_v2.png")
            
        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
