import asyncio
import sys
import json
import os
import subprocess
from playwright.async_api import async_playwright

async def get_win_ip():
    if os.name == 'nt':
        return "127.0.0.1"
    try:
        # Get host IP from ip route (WSL2 standard)
        res = subprocess.check_output("ip route show | grep default | awk '{print $3}'", shell=True)
        return res.decode().strip()
    except:
        return "127.0.0.1"

async def run():
    if len(sys.argv) < 3:
        print("Usage: python ask_owengpt.py <cdp_url_or_proxy> <prompt> [--new]")
        return

    # Auto-fix IP if it's from WSL
    win_ip = await get_win_ip()
    cdp_url = sys.argv[1].replace("127.0.0.1", win_ip).replace("localhost", win_ip)
    # Remove extra quotes often passed from cmd.exe
    cdp_url = cdp_url.strip('"').strip("'")
    question = sys.argv[2]
    force_new = "--new" in sys.argv
    gpt_url = "https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot"

    print(f"Connecting to CDP: {cdp_url}")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            
            # Find existing page for OwenZZZ or Create new
            page = None
            if not force_new:
                for p_in_ctx in context.pages:
                    if "6a0092c4d6048191a3e494dd47f18616" in p_in_ctx.url:
                        page = p_in_ctx
                        print(f"Reusing existing page: {page.url}")
                        break
            
            if not page:
                print(f"Opening new chat: {gpt_url}")
                page = await context.new_page()
                await page.goto(gpt_url, wait_until="domcontentloaded", timeout=60000)
            else:
                # Bring to front if possible
                await page.bring_to_front()
            
            # Wait for textarea
            box = page.locator("#prompt-textarea")
            await box.wait_for(state="visible", timeout=30000)
            
            # Input and Send
            await box.fill(question)
            await box.press("Enter")
            
            # Wait for response completion
            # Simple check: Wait for 'Stop generating' to appear and then disappear
            try:
                stop_btn = page.locator("button[aria-label='Stop font-size: 0;']") # Some variations use different labels
                # Alternative: wait for the send button to reappear (usually it becomes a stop button while generating)
                await page.wait_for_selector("button[data-testid='fruitjuice-stop-button']", timeout=5000)
                await page.wait_for_selector("button[data-testid='fruitjuice-send-button']", timeout=60000)
            except:
                # Fallback: just wait for some time and check if typing finished
                await asyncio.sleep(10)
            
            # Extra wait for safety
            await asyncio.sleep(2)

            # Get URL before closing
            current_url = page.url
            print(f"---CURRENT_URL: {current_url}---")

            # Get the last assistant message
            responses = page.locator("[data-message-author-role='assistant']")
            count = await responses.count()
            if count > 0:
                result = await responses.nth(count - 1).inner_text()
                print("---RESPONSE_START---")
                print(result)
                print("---RESPONSE_END---")
            else:
                print("ERROR: Response not found")
                
            # Keep page alive for next turn in AdsPower
            # await page.close()
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run())
