Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public class MoveWin {
    [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int hh, bool r);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
}
'@ -Language CSharp

Get-Process | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero -and $_.ProcessName -match 'chrome|sunbrowser|SunBrowser' } | ForEach-Object {
    [MoveWin]::ShowWindow($_.MainWindowHandle, 9)
    Start-Sleep -Milliseconds 300
    [MoveWin]::MoveWindow($_.MainWindowHandle, 1536, 0, 1536, 864, $true)
}
