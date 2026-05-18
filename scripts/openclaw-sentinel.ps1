# OpenClaw Sentinel - Watchdog Monitor
# Runs every 1-2 min via Scheduled Task "\OpenClaw Sentinel"
# Checks if gateway is alive; restarts if dead

$LogDir = "C:\Users\Apinan\owen-workspace\openclaw\logs"
$SentinelLog = "$LogDir\sentinel.log"
$StartScript = "C:\Users\Apinan\owen-workspace\openclaw\scripts\start-openclaw-bg.ps1"
$Port = 18789
$MaxLogLines = 200

# Rotate log if too big
if (Test-Path $SentinelLog) {
    $lines = (Get-Content $SentinelLog | Measure-Object).Count
    if ($lines -gt $MaxLogLines) {
        $ts = Get-Date -Format "yyyyMMdd-HHmmss"
        Move-Item $SentinelLog "$LogDir\sentinel-$ts.log" -Force
    }
}

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts $msg" | Out-File $SentinelLog -Append -Encoding utf8
}

# Check if port 18789 is responding
$alive = $false
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $task = $tcp.ConnectAsync('127.0.0.1', $Port)
    if ($task.Wait(5000) -and $tcp.Connected) {
        $alive = $true
    }
    $tcp.Dispose()
} catch {
    # port not responding
}

if ($alive) {
    # Gateway is alive - nothing to do
    exit 0
}

# Gateway is DOWN - try to restart
Write-Log "WARN: Gateway not responding on port $Port. Attempting restart..."

# Kill any zombie gateway process holding port 18789
$portOwner = netstat -ano | Select-String ":$Port.*LISTENING"
if ($portOwner) {
    $pidStr = ($portOwner -split '\s+')[-1]
    if ($pidStr -match '^\d+$') {
        $zombiePid = [int]$pidStr
        $zombieProc = Get-Process -Id $zombiePid -ErrorAction SilentlyContinue
        if ($zombieProc -and $zombieProc.Id -ne $PID) {
            Write-Log "WARN: Killing zombie gateway (pid $zombiePid) holding port $Port"
            Stop-Process -Id $zombiePid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        }
    }
}

# Check if start script is already running (avoid duplicate starts)
$runningScript = Get-WmiObject Win32_Process -Filter "CommandLine LIKE '%start-openclaw-bg.ps1%'" -ErrorAction SilentlyContinue
if ($runningScript -and $runningScript.ProcessId -ne $PID) {
    Write-Log "INFO: start-openclaw-bg.ps1 already running (pid $($runningScript.ProcessId)). Skipping."
    exit 0
}

# Start gateway using the bg script (hidden window, no popup)
try {
    $proc = Start-Process -FilePath "powershell.exe" -WindowStyle Hidden -PassThru `
        -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$StartScript`""
    Write-Log "OK: Started gateway launcher (pid $($proc.Id))"
} catch {
    Write-Log "ERROR: Failed to start gateway: $($_.Exception.Message)"
    exit 1
}

exit 0
