import asyncio
import sys
import os
import base64
import time
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
        print("Usage: python test_delete_chat.py <port>")
        return
    port = sys.argv[1]
    win_ip = await get_win_ip()
    cdp_url = f"http://{win_ip}:{port}"
    gpt_url = "https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot"
    prompt = "สร้างรูปหมานอนเล่น"
    output_dir = r"C:\Users\Apinan\owen-workspace\temp_images"
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        print(f"Connecting to CDP: {cdp_url}")
        try:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = await context.new_page()
            
            print(f"Opening GPT: {gpt_url}")
            await page.goto(gpt_url, wait_until="domcontentloaded")
            
            # 1. Send prompt
            box = page.locator("#prompt-textarea").last
            await box.wait_for(state="visible", timeout=30000)
            await box.fill(prompt)
            await box.press("Enter")
            
            print("Prompt sent, waiting for image...")
            # Wait for generation to finish (send button reappears)
            await page.wait_for_selector("button[data-testid='fruitjuice-stop-button']", timeout=10000)
            await page.wait_for_selector("button[data-testid='fruitjuice-send-button']", timeout=120000)
            
            # 2. Extract image
            images = await page.evaluate(
                """() => Array.from(document.images)
                    .map(img => ({ src: img.src, w: img.naturalWidth, h: img.naturalHeight }))
                    .filter(x => x.src.includes('backend-api/estuary/content') || x.src.includes('files.oaiusercontent.com'))
                    .sort((a,b) => (b.w*b.h) - (a.w*a.h))"""
            )
            
            image_path = None
            if images:
                src = images[0]['src']
                print(f"Found image: {src}")
                
                # Fetch image bytes
                img_data = await page.evaluate(
                    """async (url) => {
                        const r = await fetch(url);
                        const b = await r.arrayBuffer();
                        const bytes = new Uint8Array(b);
                        let bin = '';
                        for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
                        return btoa(bin);
                    }""", src
                )
                
                image_path = os.path.join(output_dir, "sleeping_dog.png")
                with open(image_path, "wb") as f:
                    f.write(base64.b64decode(img_data))
                print(f"Image saved to: {image_path}")
            else:
                print("No image found!")

            # 3. Delete the chat
            print("Attempting to delete the chat...")
            # Need to find the chat in the sidebar. 
            # Note: ChatGPT sidebar might be hidden on small screens.
            try:
                # Hover the first item in the history list (the current one)
                # Selector for history item might vary. Usually it's in a list.
                # Look for the '...' menu on the active chat or the first chat.
                
                # Wait a bit for the title to be generated in sidebar
                await asyncio.sleep(5)
                
                # The sidebar items often have a button with '...' (three dots)
                # It usually appears on hover.
                # Let's try to locate the 'active' chat item or the first child of history list
                
                # ChatGPT UI is highly dynamic. Let's try to find the menu button directly.
                # Usually: [aria-label="Chat history"] -> find leaf nodes.
                # Or look for [id^="history-item-"]
                
                # Click the option button for the current active chat if visible
                active_item_menu = page.locator("li[data-testid^='history-item-']").first.locator("button[aria-haspopup='menu']")
                await active_item_menu.hover()
                await active_item_menu.click()
                
                # Click 'Delete' in the menu
                delete_btn = page.locator("div[role='menuitem']", has_text="Delete")
                await delete_btn.click()
                
                # Confirm Delete in modal
                confirm_btn = page.locator("button.btn-danger", has_text="Delete")
                if await confirm_btn.count() == 0:
                     confirm_btn = page.locator("button", has_text="Delete").last
                
                await confirm_btn.click()
                print("Chat deleted successfully.")
            except Exception as delete_error:
                print(f"Could not delete chat: {delete_error}")
                # Take screenshot for debugging if failed
                await page.screenshot(path=os.path.join(output_dir, "delete_failed.png"))

            print(f"FINAL_RESULT: {image_path}")
            
        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
