#!/bin/bash
# ======================================================================
# code-task-gate.sh — SocratiCode gate check
# ใช้ก่อน edit/repo/config งานทุกครั้งที่ต้องแก้ code
# ถ้า evidence ไม่ผ่าน gate → STOP ห้าม edit
# ======================================================================
# Expected env vars (หรือ report file):
#   socraticode_used        "true" or "false"
#   socraticode_tools_called  comma-separated list of tools used
#   relevant_files          comma-separated list of files identified
#   impact_area              description of what will be affected
# ======================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPORT_FILE="${1:-}"

# --- Helper: read value from env or report file ---
read_value() {
    local key="$1"
    local val=""

    # Try env first
    val="${!key:-}"

    # Try report file if provided and env is empty
    if [ -z "$val" ] && [ -n "$REPORT_FILE" ] && [ -f "$REPORT_FILE" ]; then
        val="$(grep -E "^${key}=" "$REPORT_FILE" 2>/dev/null | head -1 | cut -d= -f2-)"
    fi

    echo "$val"
}

# --- Gate checks ---
check_gate() {
    local errors=0

    echo "[gate] === SocratiCode Gate Check ==="

    # 1. socraticode_used
    local used
    used="$(read_value "socraticode_used")"
    if [ "$used" != "true" ]; then
        echo "[gate] ❌ socraticode_used != true  (got: '${used:-empty}')"
        errors=$((errors + 1))
    else
        echo "[gate] ✅ socraticode_used = true"
    fi

    # 2. socraticode_tools_called
    local tools
    tools="$(read_value "socraticode_tools_called")"
    if [ -z "$tools" ]; then
        echo "[gate] ❌ socraticode_tools_called is empty"
        errors=$((errors + 1))
    else
        echo "[gate] ✅ socraticode_tools_called = ${tools}"
    fi

    # 3. relevant_files
    local files
    files="$(read_value "relevant_files")"
    if [ -z "$files" ]; then
        echo "[gate] ❌ relevant_files is empty"
        errors=$((errors + 1))
    else
        echo "[gate] ✅ relevant_files = ${files}"
    fi

    # 4. impact_area
    local impact
    impact="$(read_value "impact_area")"
    if [ -z "$impact" ]; then
        echo "[gate] ❌ impact_area is empty"
        errors=$((errors + 1))
    else
        echo "[gate] ✅ impact_area = ${impact}"
    fi

    echo "[gate] === Result: $errors error(s) ==="

    return "$errors"
}

# --- Main ---
check_gate
exit $?
