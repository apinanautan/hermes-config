---
name: adspower-browser
description: Use when needing to control AdsPower browser profiles for automation, scraping, or multi-account management. Triggers when user mentions AdsPower, browser profile control, or automating browser sessions via AdsPower API.
---

# AdsPower Browser Automation

## Overview

AdsPower is a multi-profile browser automation tool with HTTP API control. It manages multiple browser profiles, each with isolated cookies/sessions.

## What This Skill Provides

- Browser profile start/stop via AdsPower API
- Remote debug port connection for browser control
- Profile state management
- API-based automation (no GUI required after start)

## Quick Reference

| Item | Value |
|------|-------|
| Install | `C:\Program Files\AdsPower Global\AdsPower Global.exe` |
| API Ports | 20408, 20409, 20725, 50325 (one per profile type) |
| Default API | `http://localhost:50325/api/v2/` |
| Debug Port Range | 20000-20999 (mapped per profile) |
| Config Dir | `%APPDATA%\AdsPower Global` |

## API Endpoints

### Base URL
```
http://localhost:<port>/api/v2/
```
Port varies by AdsPower process: try 50325, 20725, 20408, 20409.

### Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/browser?action=login` | Check API alive |
| POST | `/browser/start` | Start profile, get debug URL |
| POST | `/browser/stop` | Stop profile |
| GET | `/browser?action=list` | List all profiles |
| POST | `/profile/start` | Start specific profile |

### Start Profile (example)
```bash
curl -X POST http://localhost:50325/api/v2/browser/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": "<profile_id>"}'
```

Response includes `selenium_remote_debug_address` like `localhost:20304`.

### Stop Profile
```bash
curl -X POST http://localhost:50325/api/v2/browser/stop \
  -H "Content-Type: application/json" \
  -d '{"user_id": "<profile_id>"}'
```

## Finding Available Ports

```powershell
# List AdsPower processes and their ports
Get-Process AdsPower* | ForEach-Object {
  $p = $_
  Get-NetTCPConnection -OwningProcess $p.Id -ErrorAction SilentlyContinue |
    Where-Object { $_.State -eq 'Listen' } |
    ForEach-Object { "$($p.Id):$($_.LocalPort)" }
}
```

## Connecting via Puppeteer

Once profile is started and you have the debug address:
```python
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

debug_url = "localhost:20304"  # from start response
options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", debug_url)
driver = webdriver.Chrome(options=options)
```

Or with Puppeteer:
```javascript
const puppeteer = require('puppeteer');
const browser = await puppeteer.connect({
  browserURL: 'http://localhost:20304'
});
```

## Workflow

1. **Check API available**: `curl http://localhost:50325/api/v2/browser?action=login`
2. **List profiles**: `GET /browser?action=list`
3. **Start profile**: `POST /browser/start` → get debug port
4. **Connect**: Use debug port with Selenium/Puppeteer
5. **Stop profile**: `POST /browser/stop` when done

## Error Handling

- `Bad Request` → Check JSON payload format
- `Not Found` → Wrong port, try another
- Connection refused → AdsPower not running or API disabled
- Profile already running → Stop first or use existing debug port

## Testing Connection

```powershell
# Test which port is active
@("50325","20725","20408","20409") | ForEach-Object {
  $port = $_
  try {
    $r = curl.exe -s "http://localhost:$port/api/v2/browser?action=login"
    if ($r) { Write-Host "[OK] Port $port responds" }
  } catch { Write-Host "[--] Port $port silent" }
}
```

## Profile IDs

Profile IDs are in AdsPower GUI. Right-click profile → Copy ID, or find via:
- API: `GET /browser?action=list` returns profile list with IDs
- GUI: Profile settings → see user_id field

## Notes

- Each AdsPower process handles certain profile types
- API version is v2, not v1
- Remote debug ports are different from API ports
- Browser runs as child of AdsPower process with `--remote-debugging-port` flag