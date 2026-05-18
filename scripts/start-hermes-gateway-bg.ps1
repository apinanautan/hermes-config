$WorkspaceDir = 'C:\Users\Apinan\owen-workspace'
$HermesExe = 'C:\Users\Apinan\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe'
$LogDir = Join-Path $WorkspaceDir 'logs'
$LogFile = Join-Path $LogDir ("hermes-gateway-startup-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

@"
[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Hermes gateway startup launcher
Workspace: $WorkspaceDir
HermesExe: $HermesExe
"@ | Out-File -FilePath $LogFile -Encoding utf8

if (-not (Test-Path $HermesExe)) {
    @"
[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR: hermes.exe not found.
"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append
    exit 1
}

try {
    Start-Process `
        -WindowStyle Hidden `
        -WorkingDirectory $WorkspaceDir `
        -FilePath $HermesExe `
        -ArgumentList @('gateway', 'run') `
        -RedirectStandardOutput $LogFile `
        -RedirectStandardError $LogFile | Out-Null

    @"
[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Hermes gateway launch requested.
"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append
}
catch {
    @"
[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR: $($_.Exception.Message)
"@ | Out-File -FilePath $LogFile -Encoding utf8 -Append
    exit 2
}
