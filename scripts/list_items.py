import asyncio
from playwright.async_api import async_playwright
import sys

async def run():
    port = sys.argv[1]
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        page = browser.contexts[0].pages[0]
        
        # Get all li in the history nav
        nav = page.get_by_role("navigation", name="ประวัติการแชต")
        if await nav.count() == 0:
            nav = page.locator("nav").filter(has_text="ประวัติการแชต")
            
        items = await nav.locator("li").all()
        print(f"Found {len(items)} li elements in history nav")
        
        for i, item in enumerate(items[:5]):
            text = await item.inner_text()
            html = await item.innerHTML()
            print(f"Item {i} Text: {text.strip()[:50]}")
            print(f"Item {i} HTML Snippet: {html[:100]}")
            
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
