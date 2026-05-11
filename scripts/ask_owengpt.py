import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def run():
    if len(sys.argv) < 3:
        print("Usage: python ask_owengpt.py <cdp_url> <prompt>")
        return

    cdp_url = sys.argv[1]
    question = sys.argv[2]
    gpt_url = "https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = await context.new_page()
            
            # Navigate
            await page.goto(gpt_url, wait_until="domcontentloaded", timeout=60000)
            
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
                
            await page.close()
            # No disconnect() here, playwright handles it in the 'async with' or just use browser.close()
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run())
