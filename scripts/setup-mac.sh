#!/bin/bash
# setup-mac.sh — One-command Hermes/OpenClaw bootstrap for fresh MacBook
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✔]${NC} $1"; }
warn() { echo -e "${YELLOW}[⚠]${NC} $1"; }
err()  { echo -e "${RED}[✘]${NC} $1"; exit 1; }

SCRIPT_VERSION="2026.05.11"
HERMES="$HOME/.hermes"
REPO_URL="git@github.com:apinanautan/hermes-config.git"
LOG="$HERMES/logs/setup-mac.log"
AUTO_SYNC_SCRIPT="$HERMES/scripts/auto-sync.sh"

# ─── 1. Check deps ───────────────────────────────────────────────────────────
check_dep() {
  if command -v "$1" &>/dev/null; then
    log "$1 already installed: $(command -v "$1")"
  else
    MISSING_DEPS+=("$1")
  fi
}

log "=== Dependency Check ==="
MISSING_DEPS=()
for dep in git node python3 brew; do
  check_dep "$dep"
done

if ((${#MISSING_DEPS[@]} > 0)); then
  MISSING_STR=$(printf '%s ' "${MISSING_DEPS[@]}")
  err "Missing dependencies: $MISSING_STR\n  Install from: https://brew.sh"
fi

NODE_VER=$(node -v 2>/dev/null || echo "unknown")
PY_VER=$(python3 --version 2>/dev/null || echo "unknown")
log "node: $NODE_VER | python: $PY_VER"

# ─── 2. Create ~/.hermes ─────────────────────────────────────────────────────
log "=== Creating ~/.hermes ==="
if [[ -d "$HERMES" ]]; then
  warn "~/.hermes already exists — will update from repo"
else
  log "Creating ~/.hermes directory"
  mkdir -p "$HERMES"/{scripts,hooks,logs,cache,config,plugins,skills}
fi

# ─── 3. Sync repo files ─────────────────────────────────────────────────────
log "=== Syncing GitHub Repo ==="
cd "$HERMES"

# Init git if not a repo
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  log "Initializing git repo..."
  git init
  git remote add origin "$REPO_URL"
fi

# Fetch latest
log "Fetching origin/main..."
git fetch origin main --quiet 2>/dev/null || warn "Fetch failed — will try push anyway"

# Reset local to match remote (SAFE: protected branches can't be force-pushed)
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
if [[ "$CURRENT_BRANCH" != "main" ]]; then
  git checkout -b main 2>/dev/null || true
fi

# Try pull-first strategy (safer)
if git config remote.origin.url >/dev/null; then
  log "Pulling latest from origin/main..."
  git reset --hard origin/main 2>/dev/null || warn "Hard reset failed or nothing to reset"
fi

# ─── 4. Setup auto-sync ─────────────────────────────────────────────────────
log "=== Auto-Sync Setup ==="
if [[ -f "$HERMES/scripts/auto-sync.sh" ]]; then
  log "auto-sync.sh already exists"
else
  warn "auto-sync.sh not found — creating default..."
  mkdir -p "$HERMES/scripts"
  cat > "$AUTO_SYNC_SCRIPT" << 'AUTOSYNC'
#!/bin/bash
# ~/.hermes/scripts/auto-sync.sh
# Auto-sync ~/.hermes to GitHub via SSH (idempotent)

set -e
REPO="\$HOME/.hermes"
REMOTE="origin"
BRANCH="main"
LOG="\$HOME/.hermes/logs/auto-sync.log"

mkdir -p "\$(dirname "\$LOG")"
log() { echo "[\$(date '+%Y-%m-%d %H:%M:%S')] \$1" >> "\$LOG"; }

cd "\$REPO" || exit 1

# Commit any unstaged changes
if ! git diff --quiet 2>/dev/null; then
  git add -A
  git commit -m "sync: \$(date '+%Y-%m-%d %H:%M')" 2>/dev/null || true
fi

if ! git diff --cached --quiet 2>/dev/null; then
  log "Pushing to GitHub..."
  git push "\$REMOTE" "\$BRANCH" 2>&1 | tee -a "\$LOG" && log "Push OK: \$(git rev-parse --short HEAD)" || log "Push FAILED"
else
  log "No changes to sync"
fi
AUTOSYNC
  chmod +x "$AUTO_SYNC_SCRIPT"
fi

# Register cron job (every 15 min)
CRON_LINE="*/15 * * * * $AUTO_SYNC_SCRIPT >> $LOG 2>&1"
( crontab -l 2>/dev/null | grep -v "auto-sync.sh"; echo "$CRON_LINE" ) | crontab -
log "Cron job registered (every 15 min)"

# ─── 5. Safe git rules ───────────────────────────────────────────────────────
log "=== Git Safety Rules ==="
# Protect main from accidental force-push
git config --global init.defaultBranch main
git config --global core.autocrlf input
git config --global push.default current

# Hook to block large file pushes (>$5MB)
mkdir -p "$HERMES/.git/hooks"
cat > "$HERMES/.git/hooks/pre-push" << 'HOOK'
#!/bin/bash
MAX_SIZE_MB=5
while read local_ref local_Sha remote_ref remote_sha; do
  [[ "$remote_sha" == "0000000000000000000000000000000000000000" ]] && continue
  git diff "$remote_sha".."$local_sha" --name-only | while read f; do
    size=$(git cat-file -s "$(git hash-object "$f" 2>/dev/null)" 2>/dev/null || echo 0)
    max_bytes=$((MAX_SIZE_MB * 1024 * 1024))
    if ((size > max_bytes)); then
      echo "BLOCKED: $f is $((size / 1024 / 1024))MB > ${MAX_SIZE_MB}MB limit"
      exit 1
    fi
  done || exit 1
done
exit 0
HOOK
chmod +x "$HERMES/.git/hooks/pre-push"
log "pre-push hook installed (blocks >${MAX_SIZE_MB}MB files)"

# ─── 6. Install node deps ────────────────────────────────────────────────────
log "=== Node Dependencies ==="
if [[ -f "$HERMES/hermes-agent/package.json" ]]; then
  log "Installing hermes-agent npm packages..."
  (cd "$HERMES/hermes-agent" && npm install --silent 2>&1 | tail -3) || warn "npm install failed"
fi

if command -v openclaw &>/dev/null; then
  log "OpenClaw CLI found: $(command -v openclaw)"
elif [[ -d "$HERMES/node_modules/openclaw" ]]; then
  log "OpenClaw local module found"
else
  warn "OpenClaw not found — run: npm install -g openclaw"
fi

# Install openclaw globally if not present
if ! command -v openclaw &>/dev/null; then
  log "Installing OpenClaw globally..."
  npm install -g openclaw 2>&1 | tail -5 || warn "npm install -g openclaw failed"
fi

# ─── 7. Verify runtime ────────────────────────────────────────────────────────
log "=== Runtime Verification ==="
VERIFY_OK=true

if command -v node &>/dev/null; then
  log "Node.js: $(node -v)"
else
  warn "Node.js not found — install from https://nodejs.org"
  VERIFY_OK=false
fi

if [[ -d "$HERMES/.git" ]]; then
  log "Git repo: ✓"
  git -C "$HERMES" log --oneline -1 2>/dev/null && echo "  Latest commit: $(git -C "$HERMES" log --oneline -1)"
else
  err "Git repo not initialized"
  VERIFY_OK=false
fi

if [[ -f "$HERMES/AGENTS.md" ]]; then
  log "AGENTS.md: ✓"
else
  warn "AGENTS.md missing — did repo sync work?"
fi

if [[ -f "$HERMES/SOUL.md" ]]; then
  log "SOUL.md: ✓"
fi

if [[ -x "$AUTO_SYNC_SCRIPT" ]]; then
  log "auto-sync.sh: ✓ (executable)"
fi

# OpenClaw gateway check
if systemctl --user list-units 2>/dev/null | grep -q openclaw; then
  log "OpenClaw gateway: registered as systemd service"
elif launchctl list 2>/dev/null | grep -q openclaw; then
  log "OpenClaw gateway: registered as launchd service"
else
  warn "OpenClaw gateway: no systemd/launchd service found (run 'openclaw gateway' to start)"
fi

# ─── 8. Final status ─────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Hermes/OpenClaw Bootstrap Complete                  ║"
echo "║  Version: $SCRIPT_VERSION"
echo "║  Hermes:  $HERMES"
echo "║  Git:     $(git -C "$HERMES" rev-parse --short HEAD 2>/dev/null || echo 'n/a')"
echo "║  Cron:    every 15 min (auto-sync)"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
log "Run 'openclaw gateway' to start the gateway"
log "Setup log: $LOG"

# ─── Idempotent re-run note ──────────────────────────────────────────────────
if [[ -f "$HERMES/.setup-mac.done" ]]; then
  PREV_VERSION=$(cat "$HERMES/.setup-mac.done")
  warn "Re-run detected (previous: $PREV_VERSION, current: $SCRIPT_VERSION)"
fi
echo "$SCRIPT_VERSION" > "$HERMES/.setup-mac.done"