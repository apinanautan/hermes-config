# Force stop gateway via openclaw gateway stop
& openclaw gateway stop 2>$null
Start-Sleep -Seconds 3

# Also kill by PID if still running
$gatewayPid = 31612
if ($null -ne (Get-Process -Id $gatewayPid -ErrorAction SilentlyContinue)) {
    Stop-Process -Id $gatewayPid -Force -ErrorAction SilentlyContinue
    Write-Host "Killed gateway PID $gatewayPid"
}
Start-Sleep -Seconds 2

# Verify port is free
$portCheck = Get-NetTCPConnection -LocalPort 18789 -ErrorAction SilentlyContinue
Write-Host "Port 18789 status after stop: $portCheck"
