# Baseline capture
$chrome = Get-Process -Name 'chrome' -ErrorAction SilentlyContinue | Measure-Object
$node = Get-Process -Name 'node' -ErrorAction SilentlyContinue | Measure-Object
$chromeMem = (Get-Process -Name 'chrome' -ErrorAction SilentlyContinue | Measure-Object -Property WorkingSet64 -Sum).Sum / 1MB
$nodeMem = (Get-Process -Name 'node' -ErrorAction SilentlyContinue | Measure-Object -Property WorkingSet64 -Sum).Sum / 1MB

Write-Host "=== BASELINE ==="
Write-Host "Chrome processes: $($chrome.Count)"
Write-Host "Chrome RAM: $([math]::Round($chromeMem,0)) MB"
Write-Host "Node processes: $($node.Count)"
Write-Host "Node RAM: $([math]::Round($nodeMem,0)) MB"
