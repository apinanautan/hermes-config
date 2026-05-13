$ErrorActionPreference = 'SilentlyContinue'

# Find all Chrome processes with debugging port
Write-Host "=== Chrome processes on port 9222 ==="
$chrome9222v4 = Get-NetTCPConnection -LocalPort 9222 -LocalAddress 0.0.0.0 -ErrorAction SilentlyContinue
$chrome9222v6 = Get-NetTCPConnection -LocalPort 9222 -LocalAddress ::1 -ErrorAction SilentlyContinue

$v4pid = if ($chrome9222v4) { $chrome9222v4.OwningProcess } else { $null }
$v6pid = if ($chrome9222v6) { $chrome9222v6.OwningProcess } else { $null }

Write-Host "IPv4 (0.0.0.0:9222) PID: $v4pid"
Write-Host "IPv6 (::1:9222) PID: $v6pid"

# Get process details
if ($v4pid) {
    $p = Get-Process -Id $v4pid
    Write-Host "IPv4 Process: $($p.Path)"
}
if ($v6pid -and $v6pid -ne $v4pid) {
    $p = Get-Process -Id $v6pid
    Write-Host "IPv6 Process: $($p.Path)"
}

# List ALL chrome processes
Write-Host ""
Write-Host "=== All Chrome processes ==="
Get-Process -Name chrome | Select-Object Id,WorkingSet64,Path | Format-Table -AutoSize
