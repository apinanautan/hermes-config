---
name: model-selector
description: >
  Manual model selector for Telegram. Handles /model and /model_current commands.
  Uses ReplyKeyboardMarkup buttons (Telegram native) for provider and model selection.
  Does NOT use inline keyboards (requires gateway callback support).
  State is persisted in ~/.openclaw/model-selector-state.json.
user-invocable: true
triggers:
  - /model
  - /model_current
---

# Model Selector Skill

## Overview
Provides a manual model selection flow via Telegram. The user sends `/model`, gets a ReplyKeyboardMarkup with providers, selects one, then picks a model. The selection is saved to a state file and applied as a session model override.

## State File
- Path: `~/.openclaw/model-selector-state.json`
- Key: `telegram:<user_id>` (e.g. `telegram:1060942816`)
- Fields:
  - `phase`: `"select_provider"` | `"select_model"` | `"done"`
  - `selected_provider`: string or null
  - `selected_model`: string or null

## Helper Script
- Path: `~/.openclaw/scripts/tg_model_selector.py`
- Usage: `python <script> <action> <chat_id> [args...]`

## Detection Logic
When receiving a message, check:
1. If message starts with `/model_current` → show current model (call `tg_model_selector.py show_current`)
2. If message starts with `/model` → begin provider selection (call `tg_model_selector.py show_providers`)
3. If user is in phase `select_provider` and message matches a known provider label → show models (call `tg_model_selector.py show_models`)
4. If user is in phase `select_model` and message matches a known model → confirm + set (call `tg_model_selector.py confirm_model`, then `session_status` with model override)

## Provider ↔ Label Mapping
Providers and their labels:
- `ollama-pay` → 🔵 ollama-pay
- `ollama-claude` → 🟣 ollama-claude (Anthropic API)
- `deepseek` → 🔴 deepseek
- `minimax` → 🟡 minimax
- `openai` → 🟢 openai
- `openai-codex` → 💻 openai-codex

## After Model Selection
After user confirms model selection:
1. Call `tg_model_selector.py` only if the keyboard needs to be removed (otherwise state is already saved)
2. Call `session_status(sessionKey="current", model="<provider>/<model>")` to set per-session model override
3. Reply to user with confirmation

## Important Notes
- The script `tg_model_selector.py` already calls the Telegram API directly (not through OpenClaw's channel)
- The bot token is read from openclaw.json at runtime
- State file is persisted even after gateway restart; if the session is lost, the default model from openclaw.json is used
- No gateway config changes needed
- The `session_status` tool's `model` parameter sets a per-session override that persists for the duration of the session
