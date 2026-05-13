# Chrome MCP - Launch Chrome with Remote Debugging
# Uses named pipes for stable connection on Windows

$ErrorActionPreference = 'Continue'
$LogFile = "$PSScriptRoot\chrome-mcp.log"
$ChromePath = $null
$ProfileDir = "C:\chrome-openclaw"
$DebugPort = 9222

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts $Message" | Tee-Object -FilePath $LogFile -Append
}

Write-Log "=== Chrome Launch Started ==="

# 1. Detect Chrome path
$chromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
)
foreach ($path in $chromePaths) {
    if (Test-Path $path) { $ChromePath = $path; break }
}
if (-not $ChromePath) {
    try {
        $regPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
        if (Test-Path $regPath) { $ChromePath = (Get-ItemProperty $regPath).'(default)' }
    } catch {}
}
if (-not $ChromePath -or -not (Test-Path $ChromePath)) {
    Write-Log "ERROR: Chrome not found. Run install.ps1 first."
    throw "Chrome not found."
}
Write-Log ("Chrome path: " + $ChromePath)

# 2. Create profile directory if missing
if (-not (Test-Path $ProfileDir)) {
    New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null
    Write-Log ("Created profile directory: " + $ProfileDir)
}

# 3. Kill existing Chrome on port 9222
$existingConn = Get-NetTCPConnection -LocalPort $DebugPort -ErrorAction SilentlyContinue
if ($existingConn) {
    $oldPids = $existingConn.OwningProcess | Get-Unique
    $pidsStr = ($oldPids | ForEach-Object { $_.ToString() }) -join ", "
    Write-Log ("Killing existing Chrome on port " + $DebugPort + " (PIDs: " + $pidsStr + ")...")
    foreach ($p in $oldPids) {
        try { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue } catch {}
    }
    Start-Sleep -Seconds 2
    Write-Log "Port cleared."
}

# 4. Launch Chrome
$chromeArgs = @(
    "--remote-debugging-port=" + $DebugPort,
    "--user-data-dir=`"" + $ProfileDir + "`""
)
Write-Log ("Args: " + ($chromeArgs -join " "))

$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = $ChromePath
$startInfo.Arguments = $chromeArgs -join " "
$startInfo.UseShellExecute = $false
$startInfo.RedirectStandardOutput = $false
$startInfo.RedirectStandardError = $false

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $startInfo
$process.Start() | Out-Null

$chromePid = $process.Id
Write-Log ("Chrome launched with PID: " + $chromePid)

# 5. Wait for Chrome debugger (10 retries x 3 sec = 30 sec max)
Write-Log ("Waiting for debugger on port " + $DebugPort + "...")
$DebuggerUrl = $null
$maxRetries = 10
$connected = $false

for ($i = 1; $i -le $maxRetries; $i++) {
    Start-Sleep -Seconds 3

    # Check port is listening first
    $listening = $false
    try {
        $checkConn = Get-NetTCPConnection -LocalPort $DebugPort -ErrorAction SilentlyContinue
        if ($checkConn) { $listening = $true }
    } catch {}

    if (-not $listening) {
        Write-Log ("Attempt " + $i + "/" + $maxRetries + ": port not yet listening...")
        continue
    }

    # Port is up - try HTTP via .NET
    try {
        $req = [System.Net.HttpWebRequest]::Create("http://localhost:" + $DebugPort + "/json")
        $req.Timeout = 5000
        $req.ServicePoint.ConnectionLeaseTimeout = 5000
        $resp = $req.GetResponse()
        $statusCode = [int]$resp.StatusCode
        $contentLen = $resp.ContentLength

        if ($statusCode -eq 200 -and $contentLen -gt 0) {
            $respStream = $resp.GetResponseStream()
            $streamReader = [System.IO.StreamReader]::new($respStream)
            $body = $streamReader.ReadToEnd()
            $streamReader.Close()
            $resp.Close()

        if ($body) {
                $json = $body | ConvertFrom-Json -ErrorAction SilentlyContinue
                if ($json -and $json.Count -gt 0) {
                    $DebuggerUrl = $json[0].webSocketDebuggerUrl
                    Write-Log ("Debugger ready after " + $i + " attempt(s)")
                    Write-Log ("WebSocket URL: " + $DebuggerUrl)
                    $connected = $true
                    $i = $maxRetries
                }
            }
        }
    } catch {
        $exMsg = $_.Exception.Message
        if ($exMsg.Length -gt 60) { $exMsg = $exMsg.Substring(0, 60) }
        Write-Log ("Attempt " + $i + "/" + $maxRetries + ": " + $exMsg)
    }
}

if (-not $connected) {
    Write-Log "WARNING: Debugger endpoint not ready after " + $maxRetries + " retries."
    Write-Log ("Chrome still running with PID: " + $chromePid)
}

Write-Log "=== Chrome Launch Complete ==="
Write-Log ("Chrome PID: " + $chromePid)
Write-Log ("Debugger: http://localhost:" + $DebugPort)