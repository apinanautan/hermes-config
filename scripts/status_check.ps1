$ErrorActionPreference = 'SilentlyContinue'
Write-Host "=== Gateway Port 18789 ==="
Get-NetTCPConnection -LocalPort 18789 | Select-Object LocalAddress,LocalPort,State,OwningProcess | Format-Table

Write-Host "=== Chrome ==="
$chrome = Get-Process -Name chrome
$count = $chrome.Count
$ram = [math]::Round(($chrome | Measure-Object WorkingSet64 -Sum).Sum/1MB, 0)
Write-Host "Processes: $count, RAM: $ram MB"

Write-Host "=== Gateway PID 31612 ==="
$gw = Get-Process -Id 31612
if ($gw) {
    Write-Host "PID: $($gw.Id), RAM: $([math]::Round($gw.WorkingSet64/1MB,0)) MB"
} else {
    Write-Host "Not running"
}
