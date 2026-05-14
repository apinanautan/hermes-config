# Hermes-PC Profile

## Identity
- **node_name:** Hermes-PC
- **host_os:** Windows 10 (WSL/Git-Bash)
- **primary_user:** Apinan
- **machine:** Apinan-PC (Windows physical)
- **role:** Primary Worker / Sync / Maintenance / Browser Automation

## Git Mode: **WRITER**
- ✅ push allowed
- ✅ commit/push via safe-autopush
- ✅ whitelist add only
- ❌ no `git add .` / `git add -A`
- ❌ no force-push / rebase / merge

## Allowed Tools
| Tool | Status |
|------|--------|
| terminal (WSL/Git-Bash) | ✅ |
| PowerShell (Windows) | ✅ |
| git | ✅ (writer) |
| CDP (Chrome DevTools) | ✅ |
| CloakBrowser | ✅ |
| AdsPower | ✅ |
| UFO/pywinauto | ✅ |
| Obsidian | ✅ |
| GPT Consultation | ✅ |
| browser automation | ✅ |
| secretary_tasks | ✅ |
| safe-autopush | ✅ |

## Primary Tasks
- worker execution
- git sync / maintenance
- browser/UI automation
- GPT consultation
- Obsidian vault sync
- task routing / delegation
- recovery / report

## Repositories
- `hermes-config` (this repo) — writer
- `Owenzzz_Brain` — writer
- `OpenClaw` — read (runtime on separate Windows process)

## Path Convention
- Hermes runtime: `C:\Users\Apinan\AppData\Local\hermes\`
- Workspace: `C:\Users\Apinan\hermes-clean\`
- Vault: `C:\Users\Apinan\ObsidianVaults\Owenzzz_Brain\`
- WSL bridge: use `[::1]:9222` for CDP (IPv6 loopback)

## Env File
Copy `.env.example` to `.env` and fill in your local values.
**Never commit `.env` to git.**
