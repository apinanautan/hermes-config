---
name: hermes-permission
description: Require explicit user permission before doing anything related to Hermes Agent, including reading, inspecting, configuring, restarting, editing, diagnosing, running commands, services, files, skills, memory, gateway, logs, or any other Hermes-related action. Use whenever a task mentions Hermes, hermes-agent, ~/.hermes, hermes-gateway, Hermes skills, Hermes config, Hermes service, or Hermes troubleshooting.
---

# Hermes Permission

Before doing any Hermes-related action, ask the user for explicit permission first.

This applies to all Hermes-related work, including:

- Reading or inspecting files under `~/.hermes`
- Running `hermes ...` commands
- Checking, starting, stopping, restarting, or inspecting `hermes-gateway.service`
- Editing Hermes config, skills, memory, profiles, logs, sessions, plugins, gateway settings, or service files
- Diagnosing, troubleshooting, migrating, updating, uninstalling, or backing up Hermes
- Using tools to search, index, analyze, or summarize Hermes files or code

Do not treat "look", "check", "diagnose", "summarize", or "ทำความรู้จัก" as permission. Ask first.

Safe response pattern:

```text
ขออนุญาตก่อนครับเจ้านาย งานนี้เกี่ยวกับ Hermes ให้ผมดำเนินการได้ไหมครับ
```

Proceed only after the user clearly approves in the current conversation.
## Sensitive Code Handling

- If the boss provides a code/password in the current message, use it only to unlock the explicitly authorized task.
- Never save, copy, summarize, or persist the code/password in skill files, notes, backups, logs, or artifacts.
- After use, remove the code/password from any editable artifact touched in the task and replace it with `[ถามรหัสจากเจ้านายเมื่อจำเป็น]` when a placeholder is needed.

