Stop-ScheduledTask -TaskName "OpenClaw Gateway" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
Start-ScheduledTask -TaskName "OpenClaw Gateway"
Write-Host "Gateway restart triggered"
