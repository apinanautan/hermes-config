# Chrome MCP - Connection Guide

How to connect to Chrome remote debugging via puppeteer.

## Prerequisites

1. Chrome must be running with `--remote-debugging-port=9222`
2. Run `.\launch-chrome.ps1` to start Chrome

## Connect via Puppeteer

```javascript
const puppeteer = require('puppeteer');

async function connectToChrome() {
  const browser = await puppeteer.connect({
    browserURL: 'http://localhost:9222',
    timeout: 30000
  });

  // Get all pages (tabs)
  const pages = await browser.pages();
  console.log(`Found ${pages.length} tab(s)`);

  // Attach to specific tab or create new one
  if (pages.length > 0) {
    const page = pages[0];
    await page.goto('https://example.com');
  }

  return browser;
}
```

## CDP Direct Connection

```javascript
// Alternative: CDP client for fine-grained control
const CDP = require('chrome-remote-interface');

CDP(async (client) => {
  const { Page, Network, Runtime } = client;

  await Page.enable();
  await Network.enable();

  Page.loadEventFired((params) => {
    console.log('Page loaded:', params.timestamp);
  });

  await Page.navigate({ url: 'https://example.com' });
});
```

## Validate Connection

```powershell
# Check if Chrome is listening on 9222
Test-NetConnection -Port 9222 -ComputerName localhost

# Get debugger info
Invoke-RestMethod http://localhost:9222/json
```

## Multiple Tabs

```javascript
// List all tabs
const pages = await browser.pages();

// Create new tab
const newPage = await browser.newPage();

// Switch between tabs
await page.bringToFront();

// Close tab
await page.close();
```

## Common Issues

| Issue | Fix |
|-------|-----|
| Port 9222 not responding | Chrome not launched with debugging flag. Re-run `launch-chrome.ps1` |
| Connection refused | Another process using port 9222. Run `netstat -ano \| findstr 9222` |
| Empty pages array | Chrome has no open tabs. Open a tab first or navigate manually |
| Profile locked | Close all Chrome instances and retry |

## Profile Directory

- Path: `C:\chrome-openclaw`
- Separate from default Chrome profile
- All cookies, cache, and settings stored here