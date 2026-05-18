<#
.SYNOPSIS
    Start OpenClaw Gateway as a background PowerShell process
.DESCRIPTION
    Designed to be called from:
    Start-Process powershell -WindowStyle Hidden -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File "<path>\start-openclaw-bg.ps1"'
.NOTES
    Logs: <workspace>\logs\gateway-YYYY-MM-DD-HHmmss.log
    PID:  <workspace>\logs\gateway.pid
    Status: <workspace>\logs\gateway.status
#>

$ScriptPath   = $MyInvocation.MyCommand.Path
$ScriptDir    = Split-Path -Parent $ScriptPath
$WorkspaceDir = Resolve-Path "$ScriptDir\.."
$OpenClawPs1  = Join-Path $env:APPDATA 'npm\openclaw.ps1'
$LogDir       = "$WorkspaceDir\logs"
$LogFile      = "$LogDir\gateway-$(Get-Date -Format 'yyyy-MM-dd-HHmmss').log"
$PidFile      = "$LogDir\gateway.pid"
$StatusFile   = "$LogDir\gateway.status"

# Ensure log directory exists
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# ---- Write initial status ----
@"
status=starting
pid=$PID
log=$LogFile
timestamp=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@ | Out-File -FilePath $StatusFile -Encoding utf8

# ---- Write PID ----
$PID | Out-File -FilePath $PidFile -Encoding utf8

# ---- Prepare log header ----
@"

============================================
OpenClaw Gateway -- Background Launcher
Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
PID:     $PID
Script:  $ScriptPath
Workspace: $WorkspaceDir
============================================

"@ | Out-File -FilePath $LogFile -Encoding utf8

# ---- Resolve openclaw CLI ----
try {
    if (-not (Test-Path $OpenClawPs1)) {
        throw "Cannot find OpenClaw wrapper at $OpenClawPs1"
    }
    $OpenClawVer = & $OpenClawPs1 --version 2>&1
    @"
OpenClaw CLI: $OpenClawPs1
Version: $($OpenClawVer -join ', ')
WorkingDir: $(Get-Location)

"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append
} catch {
    $err = "ERROR: Cannot start OpenClaw wrapper directly."
    $err += "`n$($_.Exception.Message)"
    $err | Out-File -FilePath $LogFile -Encoding utf8 -Append
    @"
status=error
pid=$PID
error=$err
timestamp=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@ | Out-File -FilePath $StatusFile -Encoding utf8
    exit 1
}

# ---- Start gateway (background, fully hidden) ----
try {
    @"
[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Starting OpenClaw Gateway (background, hidden window)...

"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append

    Set-Location $WorkspaceDir

    # Start gateway process with window hidden - no flash, no popup
    $GatewayProc = Start-Process -FilePath powershell.exe -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $OpenClawPs1,
        'gateway'
    ) -WindowStyle Hidden -PassThru

    $GatewayPid = $GatewayProc.Id
    $GatewayPid | Out-File -FilePath $PidFile -Encoding utf8

    @"
[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Gateway PID: $GatewayPid
"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append

    # Update status
    @"
status=running
pid=$GatewayPid
log=$LogFile
timestamp=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@ | Out-File -FilePath $StatusFile -Encoding utf8

    # ---- Wait for gateway port to respond (up to 60s) ----
    $ready = $false
    $port  = 18789
    for ($i = 1; $i -le 30; $i++) {
        Start-Sleep -Seconds 2
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $task = $tcp.ConnectAsync('127.0.0.1', $port)
            if ($task.Wait(2000) -and $tcp.Connected) {
                $ready = $true
                $tcp.Dispose()
                @"
[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Gateway ready (port $port open after $($i*2)s)
"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append
                break
            }
            $tcp.Dispose()
        } catch {}
    }

    if (-not $ready) {
        @"
[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] WARNING: Gateway did not respond on port $port within 60s
"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append
    }

    # ---- Send Telegram notification ----
    if ($ready) {
        try {
            $msgResult = openclaw message send --channel telegram --target 1060942816 --message "Openclaw Online 🟢" 2>&1
            @"
[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Telegram notification sent: "Openclaw Online 🟢"
$msgResult
"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append
        } catch {
            @"
[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] WARNING: Failed to send Telegram notification: $($_.Exception.Message)
"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append
        }
    }

    # ---- Keep script alive while gateway runs ----
    $GatewayProc.WaitForExit()

    @"

[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Gateway exited cleanly.
"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append
    @"
status=stopped
pid=$GatewayPid
log=$LogFile
timestamp=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@ | Out-File -FilePath $StatusFile -Encoding utf8

} catch {
    $errMsg = $_.Exception.Message
    @"

[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR: Gateway crashed
$errMsg
"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append
    @"
status=error
pid=$PID
log=$LogFile
error=$errMsg
timestamp=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@ | Out-File -FilePath $StatusFile -Encoding utf8
    exit 2
}

