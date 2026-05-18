# move_windows_screen2.ps1 — ย้ายหน้าต่าง Hermes/PowerShell/AdsPower ไปจอ 3 (X=1536)
$code = @'
using System;
using System.Runtime.InteropServices;
public class W {
    [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int h2, bool r);
}
'@
Add-Type -TypeDefinition $code -Language CSharp
Get-Process | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero -and $_.ProcessName -match 'powershell|pwsh|python|hermes|conhost|chrome|sunbrowser' } | ForEach-Object {
    [W]::MoveWindow($_.MainWindowHandle, 1536, 0, 800, 600, $true) | Out-Null
}
