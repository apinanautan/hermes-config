$task = Get-ScheduledTask -TaskName 'OpenClaw Gateway'
$task.Actions | Format-List *
$task.Principal | Format-List *
