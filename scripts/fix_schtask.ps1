$ErrorActionPreference = 'Stop'
$taskName = "OpenClaw Gateway"
$scriptPath = "C:\Users\Apinan\owen-workspace\openclaw\scripts\start-openclaw-bg.ps1"
$workingDir = "C:\Users\Apinan\owen-workspace\openclaw"

Write-Host "Updating Scheduled Task WorkingDirectory..."

# Correct schtasks /Change syntax for working directory
schtasks /Change /TN $taskName /WORKINGDIR $workingDir 2>&1

Write-Host "Done."
