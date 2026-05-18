const puppeteer = require('puppeteer');

(async () => {
  console.log('[1] Connecting to Chrome via CDP...');
  const browser = await puppeteer.connect({
    browserURL: 'http://localhost:9222'
  });
  
  const pages = await browser.pages();
  console.log(`[2] Found ${pages.length} pages`);
  
  // Target URL
  const url = 'http://127.0.0.1:8563/static/live_scan.html';
  
  // Use first available page and navigate
  const page = pages[0];
  console.log(`[3] Using existing page: ${page.url()}`);
  
  console.log(`[4] Navigating to ${url}...`);
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  } catch(e) {
    console.log('[!] Navigation error:', e.message);
    // Try to just use the page anyway
  }
  
  await new Promise(r => setTimeout(r, 2000));
  
  console.log('[5] Page loaded, looking for SCAN button...');
  
  // Get page title and URL
  const title = await page.title();
  console.log(`   Page title: ${title}`);
  const currentUrl = page.url();
  console.log(`   Current URL: ${currentUrl}`);
  
  // Find all buttons
  const allButtons = await page.$$('button');
  console.log(`[6] Found ${allButtons.length} buttons`);
  
  // Print button texts
  for (const btn of allButtons) {
    const text = await btn.evaluate(el => el.textContent.trim());
    console.log(`   Button: "${text}"`);
  }
  
  // Get DOM snapshot before interaction
  const domBefore = await page.evaluate(() => document.documentElement.outerHTML);
  console.log(`[7] DOM snapshot captured (${domBefore.length} chars)`);
  
  // Find and click SCAN button
  let clicked = false;
  for (const btn of allButtons) {
    const text = await btn.evaluate(el => el.textContent.trim());
    if (text.toUpperCase().includes('SCAN')) {
      console.log(`[8] Found SCAN button: "${text}"`);
      
      // Get button position for gesture
      const box = await btn.boundingBox();
      if (box) {
        const cx = box.x + box.width / 2;
        const cy = box.y + box.height / 2;
        console.log(`[9] Button position: (${cx}, ${cy}), simulating zigzag gesture...`);
        
        // Zigzag pattern
        for (let i = 0; i < 15; i++) {
          const xOffset = (i % 2 === 0) ? -40 : 40;
          const yOffset = i * 4;
          await page.mouse.move(cx + xOffset, cy + yOffset);
          await new Promise(r => setTimeout(r, 40));
        }
        await page.mouse.move(cx, cy);
        await new Promise(r => setTimeout(r, 100));
      }
      
      await btn.click();
      clicked = true;
      console.log('[10] SCAN button clicked');
      break;
    }
  }
  
  if (!clicked) {
    console.log('[!] SCAN button not found, clicking first button...');
    if (allButtons.length > 0) {
      const text = await allButtons[0].evaluate(el => el.textContent.trim());
      console.log(`   Clicking: "${text}"`);
      await allButtons[0].click();
      clicked = true;
    }
  }
  
  // Take screenshot immediately after click
  const screenshotPath = 'C:/Users/Apinan/owen-workspace/live_scan_screenshot.png';
  await page.screenshot({ path: screenshotPath, fullPage: false });
  console.log(`[11] Screenshot saved: ${screenshotPath}`);
  
  // Wait for animations
  await new Promise(r => setTimeout(r, 1500));
  
  // Take post-animation screenshot
  const screenshotPath2 = 'C:/Users/Apinan/owen-workspace/live_scan_screenshot_after.png';
  await page.screenshot({ path: screenshotPath2, fullPage: false });
  console.log(`[12] Post-click screenshot: ${screenshotPath2}`);
  
  // Get post-click DOM
  const domAfter = await page.evaluate(() => document.documentElement.outerHTML);
  console.log(`[13] Post-click DOM snapshot (${domAfter.length} chars)`);
  
  // Verification
  console.log('\n=== VERIFICATION ===');
  
  const hasRadar = await page.evaluate(() => {
    return !!(document.querySelector('canvas') || 
              document.querySelector('[class*="radar"]') ||
              document.querySelector('[id*="radar"]') ||
              document.querySelector('svg'));
  });
  console.log(`Radar/canvas element: ${hasRadar ? 'FOUND ✓' : 'NOT FOUND ✗'}`);
  
  const hasSkeleton = await page.evaluate(() => {
    return !!(document.querySelector('[class*="skeleton"]') ||
              document.querySelector('[id*="skeleton"]'));
  });
  console.log(`Skeleton overlay: ${hasSkeleton ? 'FOUND ✓' : 'NOT FOUND ✗'}`);
  
  const hasConfidenceBar = await page.evaluate(() => {
    return !!(document.querySelector('[class*="confidence"]') ||
              document.querySelector('[class*="progress"]') ||
              document.querySelector('[class*="bar"]'));
  });
  console.log(`Confidence bar: ${hasConfidenceBar ? 'FOUND ✓' : 'NOT FOUND ✗'}`);
  
  const bodyText = await page.evaluate(() => document.body ? document.body.innerText : '');
  const hasCatAlert = /CAT.*(DETECTED|ALERT|FOUND)|FOUND.*CAT/i.test(bodyText);
  console.log(`CAT DETECTED alert: ${hasCatAlert ? 'FOUND ✓' : 'NOT FOUND ✗'}`);
  
  console.log('\n=== BODY TEXT (first 1000 chars) ===');
  console.log(bodyText.substring(0, 1000));
  
  console.log('\n=== DOM BEFORE (first 1500 chars) ===');
  console.log(domBefore.substring(0, 1500));
  
  console.log('\n=== FINAL RESULT ===');
  console.log(`Screenshots: ${screenshotPath}`);
  console.log(`                 ${screenshotPath2}`);
  console.log(`Verification: radar=${hasRadar}, skeleton=${hasSkeleton}, confidence=${hasConfidenceBar}, catAlert=${hasCatAlert}`);
  
  await browser.disconnect();
  console.log('[DONE]');
  process.exit(0);
})().catch(e => {
  console.error('Error:', e.message);
  process.exit(1);
});