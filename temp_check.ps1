# Process check
Get-Process -Name 'node','chrome','powershell','pwsh' -ErrorAction SilentlyContinue | Format-Table -Property Name,Id,CPU,WorkingSet64,Path -AutoSize

# Log files
Get-ChildItem -Path "$env:USERPROFILE\AppData\Roaming\npm\node_modules\openclaw\logs" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,Length,LastWriteTime | Format-List
