import asyncio
from playwright.async_api import async_playwright
import sys

async def run():
    port = sys.argv[1]
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        page = browser.contexts[0].pages[0]
        print(f"Current URL: {page.url}")
        
        # Check for user avatar or profile button which indicates logged in
        avatar = page.locator("button[aria-haspopup='menu'] img, button[data-testid='user-menu-button']")
        is_logged_in = await avatar.count() > 0
        print(f"Logged in detected: {is_logged_in}")
        
        # Check for sidebar toggle
        sidebar_toggle = page.locator("button", has_text="Open sidebar")
        if await sidebar_toggle.count() > 0:
            print("Sidebar is closed, opening...")
            await sidebar_toggle.click()
            await asyncio.sleep(2)
        
        # List all buttons to see what's available
        buttons = await page.locator("button").all_inner_texts()
        print(f"Buttons found: {buttons[:20]}")
        
        # New attempt to find history item
        # Sometimes it is inside a <nav>
        nav_text = await page.locator("nav").inner_text() if await page.locator("nav").count() > 0 else "No Nav"
        print(f"Nav content length: {len(nav_text)}")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
