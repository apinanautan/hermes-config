import asyncio
import sys
from playwright.async_api import async_playwright

async def run():
    cdp_url = sys.argv[1]
    gpt_url = "https://chatgpt.com/g/g-6a0092c4d6048191a3e494dd47f18616-owenzzz-bot"
    question = "คุณคืออะไร และมีหน้าที่เกี่ยวกับอะไรบ้างครับ? ช่วยอธิบายรายละเอียดหน่อย"

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0]
        page = await context.new_page()
        
        print(f"Navigating to {gpt_url}...")
        await page.goto(gpt_url, wait_until="domcontentloaded", timeout=60000)
        
        # Wait for prompt textarea
        box = page.locator("#prompt-textarea")
        await box.wait_for(state="visible", timeout=30000)
        
        print("Sending question...")
        await box.fill(question)
        await box.press("Enter")
        
        # Wait for response (look for the last assistant message)
        print("Waiting for response...")
        # ChatGPT response items often have [data-testid^='conversation-turn-'] 
        # and inside that, a div with class 'markdown' or similar.
        # We wait for the 'Stop generating' button to disappear or the response to stabilize.
        
        # A simple way is to wait for the latest assistant turn to stop animating or have content.
        await page.wait_for_timeout(5000) # Give it head start
        
        # Wait until the "Stop generating" button is gone (meaning it's done typing)
        stop_btn = page.locator("button[aria-label='Stop generating']")
        try:
            await stop_btn.wait_for(state="hidden", timeout=60000)
        except:
            pass # Timeout or already hidden
            
        # Extract the last assistant response
        responses = page.locator("[data-message-author-role='assistant']")
        count = await responses.count()
        if count > 0:
            last_response = await responses.nth(count - 1).inner_text()
            print("--- RESPONSE START ---")
            print(last_response)
            print("--- RESPONSE END ---")
        else:
            print("Could not find assistant response.")
            
        await page.close()
        await browser.disconnect()

if __name__ == "__main__":
    asyncio.run(run())
