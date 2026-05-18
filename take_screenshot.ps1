Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphic = [System.Drawing.Graphics]::FromImage($bitmap)
$graphic.CopyFromScreen($screen.Left, $screen.Top, 0, 0, $bitmap.Size)
$outputFile = 'C:\Users\Apinan\owen-workspace\screenshot_pose.png'
$bitmap.Save($outputFile, [System.Drawing.Imaging.ImageFormat]::Png)
Write-Host "Saved to $outputFile"
$graphic.Dispose()
$bitmap.Dispose()
