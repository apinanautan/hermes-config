#!/bin/bash
# ~/.hermes/scripts/auto-sync.sh
# Auto-sync ~/.hermes to GitHub via SSH
# Respects .gitignore, excludes secrets/logs/cache

set -e

REPO="$HOME/.hermes"
REMOTE="origin"
BRANCH="master"
LOG="$HOME/.hermes/logs/auto-sync.log"

mkdir -p "$(dirname "$LOG")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

cd "$REPO" || exit 1

# Check git is clean enough
if ! git diff --quiet 2>/dev/null; then
    git add -A
    git commit -m "sync: $(date '+%Y-%m-%d %H:%M')" 2>/dev/null || true
fi

# Check staged changes
if git diff --cached --quiet 2>/dev/null; then
    log "No changes to sync"
    exit 0
fi

# Push
log "Pushing to GitHub..."
if git push "$REMOTE" "$BRANCH" 2>&1 | tee -a "$LOG"; then
    log "Push OK: $(git rev-parse --short HEAD)"
else
    log "Push FAILED"
    exit 1
fi
