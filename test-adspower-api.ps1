# AdsPower API tester
$ports = @("50325", "20725", "20408", "20409")
$endpoints = @(
    "/api/v2/browser?action=login",
    "/api/v2/browser",
    "/api/v2/browser?action=list",
    "/api/v2/profile",
    "/api/v2/profile?action=list"
)

foreach ($port in $ports) {
    Write-Host "Testing port $port..."
    foreach ($ep in $endpoints) {
        $url = "http://localhost:$port$ep"
        try {
            $resp = Invoke-WebRequest -Uri $url -Method POST -UseBasicParsing -ErrorAction SilentlyContinue
            Write-Host "  [OK] $url -> status: $($resp.StatusCode)"
            Write-Host "  Response: $($resp.Content)"
        } catch {
            # silently skip
        }
    }
}
