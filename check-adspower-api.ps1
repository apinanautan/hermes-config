# Check AdsPower API availability on common ports
$ports = @("50325", "20725", "20408", "20409")
foreach ($port in $ports) {
    try {
        $uri = "http://localhost:$port/api/v2/browser?action=login"
        $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -ErrorAction Stop
        Write-Host "[OK] Port $port responds"
    } catch {
        Write-Host "[--] Port $port silent"
    }
}
