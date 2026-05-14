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

async def stable_send_message(page, message, *, max_retries=1):
    """Stable ChatGPT send flow: focus → verify focus → clear → clipboard paste → verify → send → verify bubble."""

    async def _prepare_composer():
        box = page.locator("#prompt-textarea")
        await box.wait_for(state="visible", timeout=30000)
        await box.scroll_into_view_if_needed()
        await box.click()
        await page.wait_for_timeout(300)

        # Verify focus is actually inside the composer
        focused = await page.evaluate("""
        () => {
          const el = document.querySelector('#prompt-textarea');
          if (!el) return false;
          return document.activeElement === el;
        }
        """)
        if not focused:
            raise RuntimeError("composer focus verification failed")

        # Wait until composer is ready for input
        await page.wait_for_timeout(300)
        return box

    async def _compose_and_send():
        box = await _prepare_composer()

        # Clear composer
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await page.wait_for_timeout(250)

        # Clipboard paste only
        await page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin="https://chatgpt.com")
        await page.evaluate("msg => navigator.clipboard.writeText(msg)", message)
        await page.wait_for_timeout(150)
        await page.keyboard.press("Control+V")
        await page.wait_for_timeout(500)

        # Verify composer text
        composer_text = await page.evaluate("""
        () => {
          const el = document.querySelector('#prompt-textarea');
          if (!el) return '';
          return (el.value ?? el.innerText ?? el.textContent ?? '').trim();
        }
        """)
        if composer_text != message.strip():
            # Fallback: keyboard typing (still keyboard-only, no DOM mutation)
            try:
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                await page.wait_for_timeout(150)
                await page.keyboard.type(message, delay=1)
                await page.wait_for_timeout(400)
            except Exception:
                pass
            composer_text = await page.evaluate("""
            () => {
              const el = document.querySelector('#prompt-textarea');
              if (!el) return '';
              return (el.value ?? el.innerText ?? el.textContent ?? '').trim();
            }
            """)
            if composer_text != message.strip():
                raise RuntimeError(f"composer text mismatch: {composer_text[:80]!r}")

        # Wait until send button is enabled
        send_btn = page.locator("button[data-testid='send-button'], button[data-testid='fruitjuice-send-button']")
        enabled = False
        for _ in range(30):
            if await send_btn.count() and await send_btn.first.is_enabled():
                enabled = True
                break
            await page.wait_for_timeout(200)
        if not enabled:
            raise RuntimeError("send button never became enabled")

        # Send
        await send_btn.first.click()

        # Verify outbound bubble
        sent = False
        for _ in range(30):
            await page.wait_for_timeout(250)
            user_msgs = page.locator("[data-message-author-role='user']")
            if await user_msgs.count() > 0:
                last = await user_msgs.nth(await user_msgs.count() - 1).inner_text()
                if message.strip() in last:
                    sent = True
                    break
        if not sent:
            raise RuntimeError("outbound bubble verification failed")

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            await _compose_and_send()
            return
        except Exception as e:
            last_error = e
            if attempt >= max_retries:
                break
            # Recovery: clear composer -> reload once -> repeat once
            try:
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
            except:
                pass
            await page.reload(wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
    raise last_error


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
                await page.bring_to_front()

            await stable_send_message(page, question, max_retries=1)

            # Wait for assistant response completion
            try:
                await page.wait_for_selector("button[data-testid='fruitjuice-stop-button']", timeout=5000)
                await page.wait_for_selector("button[data-testid='fruitjuice-send-button']", timeout=60000)
            except:
                await asyncio.sleep(10)

            await asyncio.sleep(2)

            current_url = page.url
            print(f"---CURRENT_URL: {current_url}---")

            responses = page.locator("[data-message-author-role='assistant']")
            count = await responses.count()
            if count > 0:
                result = await responses.nth(count - 1).inner_text()
                print("---RESPONSE_START---")
                print(result)
                print("---RESPONSE_END---")
            else:
                print("ERROR: Response not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run())
