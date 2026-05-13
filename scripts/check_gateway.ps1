try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:18789/health' -TimeoutSec 3 -ErrorAction Stop
    Write-Host "Gateway OK: $($r.StatusCode)"
} catch {
    Write-Host "Gateway error: $($_.Exception.Message)"
}
