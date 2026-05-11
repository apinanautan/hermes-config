#!/bin/bash
# verify-sync.sh — Quick verification of hermes git sync status

set -e

echo "=== SSH TEST ==="
ssh -T git@github.com 2>&1 | grep -E "(authenticated|shell)" || echo "SSH may not be configured"

echo ""
echo "=== REMOTE ==="
git remote -v | grep fetch

echo ""
echo "=== STATUS ==="
git status --short

echo ""
echo "=== IGNORED SECRETS ==="
for f in .env secret_test.env test.log logs/test.log secrets/test.txt; do
    if git check-ignore "$f" >/dev/null 2>&1; then
        echo "OK: $f is ignored"
    else
        echo "WARN: $f is NOT ignored"
    fi
done

echo ""
echo "=== FILES IN REPO ==="
git ls-tree -r --name-only HEAD | wc -l
echo "files tracked"

echo ""
echo "=== TOP-LEVEL STRUCTURE ==="
git ls-tree --name-only HEAD | sort

echo ""
echo "=== LARGE DIRS (check before push) ==="
for d in node/ hermes-agent/ config-source/; do
    if [ -d "$HOME/.hermes/$d" ]; then
        size=$(du -sh "$HOME/.hermes/$d" 2>/dev/null | cut -f1)
        echo "$d: $size"
        # Warn if > 500MB (potential push issue)
        bytes=$(du -sb "$HOME/.hermes/$d" 2>/dev/null | cut -f1)
        if [ "$bytes" -gt 524288000 ]; then
            echo "  WARN: $d exceeds 500MB — may cause pre-receive hook rejection"
        fi
    fi
done

echo ""
echo "=== CRON CHECK ==="
crontab -l 2>/dev/null | grep auto-sync || echo "No auto-sync cron"

echo ""
echo "=== LAST COMMIT ==="
git log --oneline -1
echo "HEAD: $(git rev-parse --short HEAD)"