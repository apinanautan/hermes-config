#!/usr/bin/env bash
set -euo pipefail

ROOT="${HOME}/.hermes"
ENV_FILE="${ROOT}/.env.local"

echo "[hermes-mac] setup start"

mkdir -p "${ROOT}/runtime" "${ROOT}/logs" "${ROOT}/cache"

if [ ! -f "${ENV_FILE}" ]; then
  cat > "${ENV_FILE}" <<'ENV'
DEVICE_NAME=macbook
MACHINE_ROLE=secondary
TELEGRAM_ENABLED=false
HERMES_MODE=dev

# Fill locally only. Do not commit.
MINIMAX_API_KEY=
OPENROUTER_API_KEY=
DEEPSEEK_API_KEY=
API_SERVER_KEY=
BOT_TOKEN=
ENV
fi

chmod 600 "${ENV_FILE}"

echo "[hermes-mac] env: ${ENV_FILE}"
echo "[hermes-mac] done"
echo "Next: fill API keys locally, keep TELEGRAM_ENABLED=false until Mac becomes primary."
