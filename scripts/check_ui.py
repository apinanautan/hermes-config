import asyncio
from playwright.async_api import async_playwright
import sys

async def run():
    port = sys.argv[1]
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            context = browser.contexts[0]
            # Get the page that is open
            if not context.pages:
                print("No pages open")
                return
            page = context.pages[0]
            await page.screenshot(path="current_gpt_state.png")
            print(f"Screenshot saved to current_gpt_state.png, Title: {await page.title()}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(run())
