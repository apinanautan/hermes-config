# Task: consultation-first gate for Hermes routing
- **From:** Hermes-PC (routed from Telegram)
- **Target:** OpenClaw-PC
- **Objective:** Make consultation-first routing real in the Hermes/OpenClaw workflow so analysis / planning / design requests go to Opus/GPT consultation before any direct answer, and only then proceed to execution tasks.
- **Steps:**
  1. Inspect the Hermes runtime entry path for prompt assembly and routing, starting with `C:/Users/Apinan/AppData/Local/hermes/hermes-agent/agent/prompt_builder.py` and any nearby entry/gate logic.
  2. Identify the earliest safe enforcement point where user turns can be classified into `DIRECT`, `CONSULTATION`, or `SECRETARY` before an answer is generated.
  3. Implement a fail-closed consultation-first gate so planning/design/analysis requests are routed to consultation first; only trivial/mechanical requests may remain direct.
  4. Keep the existing task flow intact (`inbox/ -> in_progress/ -> reports/ -> done/`) and do not break current secretary task handling.
  5. Verify the change by showing the exact file(s) changed and the logic path that now routes consultation before direct answer.
- **Safety:**
  - Do not modify secrets, tokens, credentials, or unrelated runtime files.
  - Do not change the folder workflow structure.
  - Do not mark success unless the gate is actually enforced in runtime code or the earliest practical entry point.
- **Expected Report:**
  - `status` of the work
  - exact file paths changed
  - short explanation of the gate logic
  - verification result
  - anything blocked or still unresolved
- **Timeout:** 30m
- **Created:** 2026-05-18
