const { chromium } = require('playwright');

(async () => {
  const PROFILE_PATH = 'C:\\Users\\Apinan\\AppData\\Local\\Google\\Chrome\\User Data';
  const PROFILE_DIR = 'Default';
  
  console.log('Starting Chrome with profile...');
  
  const browser = await chromium.launchPersistentContext(
    `${PROFILE_PATH}\\${PROFILE_DIR}`,
    {
      executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      headless: false,
      timeout: 30000,
      args: ['--remote-debugging-port=9222', '--no-sandbox']
    }
  );
  
  console.log('Browser launched!');
  const page = browser.pages()[0];
  
  // Navigate to ChatGPT
  await page.goto('https://chatgpt.com/', { timeout: 30000 });
  console.log('Waiting for page to fully load...');
  
  // Wait for network idle first
  try {
    await page.waitForLoadState('networkidle', { timeout: 20000 });
    console.log('Network idle reached');
  } catch (e) {
    console.log('Network idle timeout:', e.message);
  }
  
  const title = await page.title();
  console.log('Page title:', title);
  
  // Keep waiting until title is not "รอสักครู่..." (loading)
  let attempts = 0;
  while (title.includes('รอ') && attempts < 20) {
    console.log('Page still loading, waiting...');
    await page.waitForTimeout(2000);
    attempts++;
    console.log('Page title:', await page.title());
  }
  
  // Check what elements are available
  const proseMirror = await page.$('div.ProseMirror');
  console.log('ProseMirror found:', !!proseMirror);
  
  if (proseMirror) {
    await proseMirror.click();
    await page.waitForTimeout(500);
    
    await page.keyboard.type(
      'Generate an image of an elderly Thai woman, silver hair in bun, kind gentle eyes, weathered but peaceful face, traditional Thai style background, soft natural lighting, portrait photography style, high quality detailed'
    );
    await page.waitForTimeout(500);
    
    await page.keyboard.press('Enter');
    console.log('Prompt sent, waiting for image generation...');
    
    await page.waitForTimeout(25000);
    
    await page.screenshot({ path: 'C:\\Users\\Apinan\\Downloads\\elderly-woman.png', fullPage: false });
    console.log('DONE: elderly-woman.png');
  } else {
    await page.screenshot({ path: 'C:\\Users\\Apinan\\Downloads\\chatgpt-state.png', fullPage: false });
    console.log('DONE: chatgpt-state.png (input not found)');
  }
  
  await browser.close();
})();
