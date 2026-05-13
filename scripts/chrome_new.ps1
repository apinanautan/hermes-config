# Close all Chrome
Get-Process -Name 'chrome' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Verify Chrome is closed
$remaining = Get-Process -Name 'chrome' -ErrorAction SilentlyContinue | Measure-Object
Write-Host "Chrome processes after kill: $($remaining.Count)"

# Launch new Chrome with profile
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$profileDir = "C:\chrome-openclaw"
$url = "https://google.com"

Start-Process -FilePath $chromePath -ArgumentList "--remote-debugging-port=9222","--user-data-dir=`"$profileDir`"",$url -PassThru | ForEach-Object { Write-Host "New Chrome PID: $($_.Id)" }
