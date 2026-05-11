---
name: openclaw-gateway-debug
description: Diagnose and fix OpenClaw Gateway service failures (systemd-based, WSL)
tags: [openclaw, systemd, wsl, restart-failure, exit-code-203, exit-code-1, version-mismatch]
triggers:
  - "openclaw ตาย"
  - "openclaw restart"
  - "exit code 203"
  - "EXEC error"
  - "openclaw-gateway.service failed"
  - "requires Node"
  - "version mismatch"
  - "exit code 1"
---

# OpenClaw Gateway Debug Skill

## Core Workflow

```
1. ดูสถานะ systemctl
2. ดู journal logs
3. ตรวจ node binary path ใน service file
4. ตรวจ openclaw.json config (schema validation)
5. Fix + restart
```

## Exit Code 203 — Node Binary Path Wrong

**Symptom:** `Main process exited, code=exited, status=203/EXEC`

**Cause:** systemd service ใช้ path เช่น `/home/apinan/.hermes/node/bin/node` ซึ่งไม่มีอยู่จริง

**Fix:**
```bash
# หา node path ที่ถูกต้อง
which node
/usr/bin/node -v  # ตรวจ version ก่อนใช้

# แก้ systemd unit ใช้ path ที่ถูกต้อง
```

## Exit Code 1 — Node Version Too Old

**Symptom:** `Main process exited, code=exited, status=1/FAILURE`  
**Journal:** `openclaw requires Node >=X.Y.Z. Detected: node A.B.C`

**Cause:** systemd service ใช้ node binary ที่ version ต่ำกว่าที่ openclaw ต้องการ (เช่น node 22.13.1 ต้อง >=22.14.0)

**Fix:**
```bash
# 1. เช็คทุก node path ที่มีในระบบ
which node && node -v
/usr/bin/node -v
/usr/local/bin/node -v 2>/dev/null || true

# 2. เช็ค service file ว่าชี้ path ไหน
cat ~/.config/systemd/user/openclaw-gateway.service | grep ExecStart

# 3. ถ้ามี node path อื่นที่ version พอ (เช่น /usr/bin/node v22.22.2)
#    แก้ service file ใช้ path นั้น
# 4. daemon-reload + restart
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway.service
sleep 3
systemctl --user status openclaw-gateway.service --no-pager
```

**Key insight:** `~/.hermes/node/bin/node` มักเป็น version เก่า/ค้าง stock ระบบที่ `/usr/bin/node` มัก newer กว่า

## Invalid Config — Unrecognized Key

**Symptom:** `Invalid config at /home/apinan/.openclaw/openclaw.json: agents.defaults: Unrecognized key: "instructions"`

**Cause:** `agents.defaults.instructions` ไม่รองรับใน version ปัจจุบัน (v2026.5.7)

**Fix:**
```python
import json
path = '/home/apinan/.openclaw/openclaw.json'
with open(path) as f:
    d = json.load(f)
if 'instructions' in d.get('agents', {}).get('defaults', {}):
    del d['agents']['defaults']['instructions']
with open(path, 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
```

## Quick Verify

```bash
systemctl --user status openclaw-gateway.service
journalctl --user -u openclaw-gateway.service -n 20 --no-pager
```

## Restart Sequence

```bash
systemctl --user stop openclaw-gateway.service
# fix config / path
systemctl --user daemon-reload
systemctl --user start openclaw-gateway.service
sleep 5
systemctl --user status openclaw-gateway.service --no-pager
```

## Fallback: openclaw doctor

ถ้า manual fix ไม่ work ให้ลอง:
```bash
openclaw doctor --fix
```

## Pitfalls

- **Don't** use `~/.hermes/node/bin/node` — it's stale/moved/old-version; use `which node` or `/usr/bin/node` to find real path  
- **Always check version** after finding a node path — existence ≠ sufficient version
- **Don't** restart without `daemon-reload` after editing service file
- **Don't** leave exit code 203 loop running — it hits StartLimitBurst and locks out restart for 60s
- **Same fix, different symptom** — exit code 203 (missing binary) and exit code 1 (old version) both often fixed by changing the ExecStart path in the service file
- **OpenClaw package may live in TWO places** — check both `~/.hermes/node/lib/node_modules/openclaw/` (old) and `~/.openclaw/node/lib/node_modules/openclaw/` (new standalone location) if the module is missing
- **Cascading damage to Hermes** — after OpenClaw moves/deletes files under `~/.hermes/`, check if Hermes source files (`~/.hermes/hermes-agent/*.py` and `~/.hermes/hermes-agent/hermes_cli/`) were also deleted. Restore with:
  ```bash
  rsync -av --exclude='__pycache__' --exclude='node_modules' --exclude='venv' --exclude='.venv' --exclude='.git' ~/hermes-agent/ ~/.hermes/hermes-agent/
  ```
- **Verify Hermes CLI after restore** — run `hermes --version` to confirm the CLI binary works after restoring source files

## Status Check

```bash
ps aux | grep openclaw
systemctl --user list-units | grep openclaw
```