#!/bin/bash
# Sync Owen Workspace to GitHub
cd /mnt/c/Users/Apinan/owen-workspace
git add .
git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main
