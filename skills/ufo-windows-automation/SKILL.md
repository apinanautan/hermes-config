---
name: ufo-windows-automation
description: Use when user needs Windows GUI automation, controlling ChatGPT Web in Chrome, automating app clicks/types, or any Windows desktop automation via Microsoft UFO. Triggers when user mentions UFO, windows automation, controlling browser, or downloading images via ChatGPT Web.
---

# UFO Windows Automation

Microsoft UFO (UFO² / UFO³ Galaxy) is a Windows desktop agent framework. Use this skill whenever you need to automate Windows GUI actions.

## What UFO Is

**UFO²** = Single Windows desktop automation. HostAgent launches apps, AppAgents control each app via ReAct loop.

**UFO³ Galaxy** = Multi-device orchestration with DAG-based task flow (more complex, rarely needed).

For ChatGPT Web image generation → use **UFO² AppAgent** controlling Chrome.

## Quick Command

```powershell
cd C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Tools\UFO
.\.venv\Scripts\python.exe -m ufo --task <TASK_NAME> --request "<USER_REQUEST>"
```

Or use the wrapper:
```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Tools\UFO\run-ufo.ps1 -Task <TASK> -Request "<REQUEST>"
```

## How UFO Works

```
User Request
    ↓
HostAgent (orchestrator)
    ↓ (launches app + creates AppAgent)
AppAgent (per-app, ReAct loop)
    ↓
UI Control (UIA/pywinauto) + LLM reasoning
    ↓
Action execution (click/type/API)
    ↓
Observation → next step or finish
```

## Key Concepts

| Concept | Meaning |
|---------|---------|
| **HostAgent** | Orchestrates overall goal, decides which apps to open |
| **AppAgent** | Controls one specific app, runs ReAct loop |
| **UIA** | Windows UI Automation (backend for control detection) |
| **VISUAL_MODE** | Send screenshots to LLM (needs vision model) |
| **Control** | A UI element (button, edit box, etc.) |
| **Desktop screenshot** | Full screen capture for context |

## Running UFO

### Prerequisites
- Windows OS (UFO only runs on Windows)
- Python 3.10+ in venv at `C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Tools\UFO\.venv`
- API key configured in `config\ufo\agents.yaml`

### Simple run
```powershell
cd C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Tools\UFO
.\.venv\Scripts\python.exe -m ufo --task mytask --request "Open Notepad and type hello"
```

### With debug logging
```powershell
.\.venv\Scripts\python.exe -m ufo --task mytask --request "Open Notepad" --log-level DEBUG
```

### Check if UFO is working (no-op test)
```powershell
.\.venv\Scripts\python.exe -m ufo --task smoke --request "Do not open or change any app. Just answer that you are ready, then stop." --log-level ERROR
```
Expected: `FINISH` status with comment containing "UFO is ready"

## JSON Parsing (Important!)

UFO expects AppAgent responses as JSON with lowercase keys:
```json
{"observation": "...", "thought": "...", "plan": [...], "action": {...}}
```

UFO's `json_parser` in `ufo/utils/__init__.py` handles:
1. Strips `<think>...` thinking blocks (MiniMax style)
2. Strips markdown code fences (` ```json `)
3. Finds JSON object if stray text surrounds it
4. **Lowercases all keys** (Observation → observation) for pydantic validation

If parsing fails after these fixes, UFO falls back to plain text mode.

## API Configuration

Config file: `C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Tools\UFO\config\ufo\agents.yaml`

Current working config (MiniMax):
```yaml
HOST_AGENT:
  API_TYPE: "openai"
  API_BASE: "https://api.minimax.io/v1"
  API_MODEL: "MiniMax-M2.7"
  API_KEY: "<key>"      # DO NOT PRINT
  VISUAL_MODE: False    # MiniMax has no vision; keep off
  TOP_P: 1.0
  TEMPERATURE: 0.0
```

The `VISUAL_MODE: False` is important because MiniMax-M2.7 is NOT a vision model. If you use a vision model later (e.g., GPT-4V, Gemini), set `VISUAL_MODE: True`.

## Files Reference

| File/Dir | Purpose |
|----------|---------|
| `run-ufo.ps1` | PowerShell wrapper for easy runs |
| `config/ufo/agents.yaml` | API keys and model config (PRIVATE) |
| `config/ufo/system.yaml` | System-wide settings (MAX_STEP, TIMEOUT, etc.) |
| `ufo/utils/__init__.py` | JSON parser with think-block stripping |
| `ufo/llm/openai.py` | OpenAI-compatible LLM client |
| `ufo/agents/agent/app_agent.py` | AppAgent implementation |
| `ufo/agents/processors/strategies/app_agent_processing_strategy.py` | Main processing strategy |
| `logs/` | UFO run logs |

## Common Workflows

### Open app and do something
```powershell
.\.venv\Scripts\python.exe -m ufo --task mytask --request "Open Chrome and go to chatgpt.com"
```

### Open specific app by name
```powershell
.\.venv\Scripts\python.exe -m ufo --task mytask --request "Open Notepad"
```

### Automate ChatGPT Web (image generation)
1. Open Chrome via UFO: `Open Chrome and go to <URL>`
2. AppAgent will control Chrome via UIA
3. For complex flows, use UFO's AppAgent with proper prompts

## Debugging

- **No response / hung**: Check if MiniMax API is accessible
- **Wrong app selected**: Use `select_application_window` with exact app name
- **Action not working**: May need `MAXIMIZE_WINDOW: True` in system.yaml
- **JSON parse errors**: Check if LLM is outputting proper JSON format

## Important Rules

1. **NEVER print `agents.yaml`** - contains API keys
2. **VISUAL_MODE** must match model capability - vision model = True, text-only = False
3. **MiniMax sends `<think>...`** - UFO's json_parser strips these automatically
4. **PowerShell path**: Use full Windows paths like `C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Tools\UFO`
5. **WSL path equivalent**: `/mnt/c/Users/[ถามรหัสจากเจ้านายเมื่อจำเป็น]/Tools/UFO`

## MiniMax Compatibility Fixes (Already Applied)

These patches are in the installed UFO at `C:\Users\[ถามรหัสจากเจ้านายเมื่อจำเป็น]\Tools\UFO`:

1. **`ufo/utils/__init__.py`** - `json_parser()` strips `<think>...` and lowercases keys
2. **`ufo/llm/openai.py`** - catches structured-output probe failures and falls back to plain text

Do NOT revert these patches unless MiniMax behavior changes.
## Sensitive Code Handling

- If the boss provides a code/password in the current message, use it only to unlock the explicitly authorized task.
- Never save, copy, summarize, or persist the code/password in skill files, notes, backups, logs, or artifacts.
- After use, remove the code/password from any editable artifact touched in the task and replace it with `[ถามรหัสจากเจ้านายเมื่อจำเป็น]` when a placeholder is needed.

