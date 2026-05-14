#!/usr/bin/env bash
# Detect Node Profile — Bash (WSL / macOS / Linux)
# Usage: source scripts/detect-node-profile.sh

echo "=== Hermes Node Detection ==="

case "$OSTYPE" in
    darwin*) OS="macOS" ;;
    linux-gnu*) OS="Linux" ;;
    msys*|cygwin*) OS="Windows (WSL/Git-Bash)" ;;
    *) OS="Unknown ($OSTYPE)" ;;
esac

HOSTNAME=$(hostname 2>/dev/null || echo "unknown")
USER=$(whoami 2>/dev/null || echo "unknown")
echo "  OS: $OS | Host: $HOSTNAME | User: $USER"

if [[ "$OS" =~ Windows ]] && [[ "$USER" == "Apinan" ]]; then
    PROFILE="Hermes-PC"; GIT_MODE="writer"
elif [[ "$OS" == "macOS" ]]; then
    PROFILE="Hermes-Mac"; GIT_MODE="reader"
elif [[ "$OS" == "Linux" ]] && [[ "$USER" == "Apinan" ]]; then
    PROFILE="Hermes-PC"; GIT_MODE="writer"
else
    PROFILE="Unknown"; GIT_MODE="none"
fi

export HERMES_NODE_NAME="$PROFILE"
export HERMES_GIT_MODE="$GIT_MODE"

echo ""
echo ">>> $PROFILE (git=$GIT_MODE)"
echo "=== Complete ==="
