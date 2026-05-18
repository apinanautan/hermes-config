@echo off
echo Fixing OpenClaw Gateway restart loop...
echo.
echo 1. Deleting old task with RestartOnFailure(999)...
schtasks /delete /tn "\OpenClaw Gateway" /f
echo.
echo 2. Creating new task without restart loop...
schtasks /create /tn "\OpenClaw Gateway" /xml "C:\Users\Apinan\owen-workspace\openclaw\scripts\fix-gateway-task.xml" /f
echo.
echo Done! OpenClaw Gateway will no longer restart-loop.
echo To start it manually: schtasks /run /tn "\OpenClaw Gateway"
pause
