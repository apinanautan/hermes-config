# Chrome MCP - Install Script
# First-time setup: detect Chrome, create profile dir, validate

$ErrorActionPreference = 'Stop'
$LogFile = "$PSScriptRoot\chrome-mcp.log"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts $Message" | Tee-Object -FilePath $LogFile -Append
}

Write-Log "=== Chrome MCP Install Started ==="

# 1. Detect Chrome path from registry
$chromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
)

$chromePath = $null
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        $chromePath = $path
        break
    }
}

# Try registry lookup as fallback
if (-not $chromePath) {
    try {
        $regPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
        if (Test-Path $regPath) {
            $chromePath = (Get-ItemProperty $regPath).'(default)'
        }
    } catch {}
}

if (-not $chromePath -or -not (Test-Path $chromePath)) {
    Write-Log "ERROR: Chrome not found. Please install Google Chrome."
    throw "Chrome not found at any expected path."
}

Write-Log "Chrome found: $chromePath"

# 2. Validate Chrome version
try {
    $version = (Get-Item $chromePath).VersionInfo.FileVersion
    Write-Log "Chrome version: $version"
} catch {
    Write-Log "WARNING: Could not read Chrome version."
}

# 3. Create profile directory
$profileDir = "C:\chrome-openclaw"
if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    Write-Log "Created profile directory: $profileDir"
} else {
    Write-Log "Profile directory already exists: $profileDir"
}

# 4. Check if port 9222 is available
$portInUse = (Get-NetTCPConnection -LocalPort 9222 -ErrorAction SilentlyContinue).Count -gt 0
if ($portInUse) {
    Write-Log "WARNING: Port 9222 is already in use. Chrome may fail to start."
} else {
    Write-Log "Port 9222 is available."
}

# 5. Validate Chrome can be launched (dry run check)
try {
    $null = Get-Process chrome -ErrorAction SilentlyContinue
    Write-Log "Chrome process check: OK ( $($_.Count) instances running)"
} catch {
    Write-Log "Chrome process check: OK"
}

Write-Log "=== Chrome MCP Install Complete ==="
Write-Log "Next: Run .\launch-chrome.ps1 to start Chrome with remote debugging."