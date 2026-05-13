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
    $OpenClawCmd = (Get-Command openclaw).Source
    $OpenClawVer = openclaw --version 2>&1
    @"
OpenClaw CLI: $OpenClawCmd
Version: $($OpenClawVer -join ', ')
WorkingDir: $(Get-Location)

"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append
} catch {
    $err = "ERROR: Cannot find 'openclaw' command. Ensure npm global bin is in PATH."
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

# ---- Start gateway (foreground -- blocks until exit) ----
try {
    @"
[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Starting OpenClaw Gateway...
[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Command: openclaw gateway

"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append

    # Update status
    @"
status=running
pid=$PID
log=$LogFile
timestamp=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@ | Out-File -FilePath $StatusFile -Encoding utf8

    # Run gateway -- ensure correct working directory so openclaw resolves paths correctly
    Set-Location $WorkspaceDir
    openclaw gateway *>&1 | Out-File -FilePath $LogFile -Encoding utf8 -Append

    # If we get here, gateway exited cleanly
    @"

[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Gateway exited cleanly.
"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append
    @"
status=stopped
pid=$PID
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

