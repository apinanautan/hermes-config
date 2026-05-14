# Detect Node Profile — PowerShell (Windows)
# Usage: . .\scripts\detect-node-profile.ps1

$OS = (Get-CimInstance Win32_OperatingSystem).Caption
$Hostname = $env:COMPUTERNAME
$User = $env:USERNAME

Write-Host "=== Hermes Node Detection ==="
Write-Host "  OS: $OS"
Write-Host "  Hostname: $Hostname"
Write-Host "  User: $User"

# Detection logic
if ($OS -match "Windows" -and $User -eq "Apinan") {
    $PROFILE = "Hermes-PC"
    $GIT_MODE = "writer"
    Write-Host ""
    Write-Host ">>> DETECTED: Hermes-PC (Windows/WSL Worker)"
    Write-Host ">>> Git Mode: WRITER (push allowed)"
}
else {
    Write-Host ""
    Write-Host ">>> UNKNOWN NODE — STOP"
    $PROFILE = "Unknown"
    $GIT_MODE = "none"
}

$env:HERMES_NODE_NAME = $PROFILE
$env:HERMES_GIT_MODE = $GIT_MODE

Write-Host ""
Write-Host "Identity: node_name=$PROFILE git_mode=$GIT_MODE"
Write-Host "=== Complete ==="
