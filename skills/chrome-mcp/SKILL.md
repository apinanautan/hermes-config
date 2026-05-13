---
name: chrome-mcp
description: Chrome browser automation via CDP (Chrome DevTools Protocol) with remote debugging. Use when controlling Chrome browser, automating web interactions, taking screenshots, scraping, or managing multiple browser tabs. Triggers on: Chrome remote debugging, CDP automation, puppeteer-style browser control, or launching Chrome with --remote-debugging-port=9222.
---

# Chrome MCP Skill

Chrome remote debugging via CDP (Chrome DevTools Protocol) on port 9222. Profile directory: `C:\chrome-openclaw`.

## Quick Start

```powershell
# Install & launch (run once)
.\install.ps1
.\launch-chrome.ps1

# Connect via puppeteer
const puppeteer = require('puppeteer');
const browser = await puppeteer.connect({
  browserURL: 'http://localhost:9222'
});
```

## Architecture

- **Debug Port**: 9222 (HTTP)
- **Profile**: `C:\chrome-openclaw` (separate from default Chrome profile)
- **Connection**: CDP over HTTP (not WebSocket) via `puppeteer.connect()`
- **MCP Target**: puppeteer (Node.js)

## Key Scripts

| Script | Purpose |
|--------|---------|
| `install.ps1` | First-time setup: detect Chrome path, create profile dir, validate installation |
| `launch-chrome.ps1` | Launch Chrome with remote debugging flags |

## Workflows

### 1. Install (first time only)

```powershell
.\install.ps1
```

Checks:
- Chrome path auto-detection via registry
- Profile directory creation
- Connectivity validation
- Browser PID confirmation

### 2. Launch Chrome

```powershell
.\launch-chrome.ps1
```

Launches: `chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome-openclaw"`

### 3. Connect (puppeteer)

```javascript
const puppeteer = require('puppeteer');
const browser = await puppeteer.connect({
  browserURL: 'http://localhost:9222'
});
const pages = await browser.pages();
```

## Validation Checklist

- [ ] Chrome path found via registry (`HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe`)
- [ ] Port 9222 is listening (`Test-NetConnection -Port 9222 -ComputerName localhost`)
- [ ] Browser is connectable (`Invoke-RestMethod http://localhost:9222/json`)
- [ ] Multiple tabs supported (iterate `pages()`)
- [ ] Logs written to local file only (no external/network logging)

## Limitations

- No WSL paths — Windows native paths only
- Profile `C:\chrome-openclaw` must exist before launching
- If port 9222 is in use, kill existing chrome or change port

## Logs

All operations log to: `./chrome-mcp.log` (local file only)