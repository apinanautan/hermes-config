$c = Get-Process -Name chrome -ErrorAction SilentlyContinue
if ($c) {
    $count = $c.Count
    $ram = [math]::Round(($c | Measure-Object WorkingSet64 -Sum).Sum/1MB, 0)
    Write-Host "Chrome: $count processes, $ram MB RAM"
} else {
    Write-Host "Chrome: not running"
}
