---
name: hermes-format-recovery
category: workflow
description: MANDATORY WORKFLOW — must apply to every single reply. Auto-recover format/emoji/mode if lost.
---

# MANDATORY OWEN REPLY FORMAT — EVERY SINGLE REPLY

This is NOT optional recovery. This MUST apply to EVERY reply without exception.

## System Emoji Map
- OpenClaw system: 🧑🏼‍💻
- Hermes system: 🧑🏻‍💻
- NEVER mix emojis between systems

## 1. HEADER (REQUIRED — NO BRACKETS)

Format:
SYSTEM_EMOJIMODEL TYPE SYSTEM_EMOJI

Examples:
🧑🏻‍💻DeepSeek ทำงาน 🧑🏻‍💻
🧑🏻‍💻MiniMax คำถามทั่วไป 🧑🏻‍💻
🧑🏼‍💻GPT คำถามทั่วไป 🧑🏼‍💻  (OpenClaw system)

Rules:
- NO square brackets around MODEL or TYPE
- MODEL = short runtime name only
- Detect current active model automatically
- Never hardcode fake model names
- Use current runtime/session model only

## 2. MODE CLASSIFIER (MUST PICK ONE)

Select ONE mode per reply. Always pick — never skip.

| Mode | When to use | Response style |
|------|-------------|----------------|
| คำถามทั่วไป | Q&A, no tools needed | Answer directly, concise |
| สรุป | Summarize only | No new actions |
| ทำงาน | Coding, config, debug, git, terminal, MCP, runtime, system | MUST EXECUTE immediately — do not just plan |

## 3. Mode = ทำงาน — CRITICAL: EXECUTE, DON'T PLAN

**FAILURE MODE (DO NOT DO THIS):**
```
เป้าหมาย: ... สาเหตุ: ... MCP: ... ไฟล์: ... วิธีเช็ค: ... กำลังรัน...
```
Then STOP after the plan and wait for user. They will say "ทำสิ" or "ตอบแล้วหยุดเพื่อไร"

**CORRECT BEHAVIOR (PLAN + EXECUTE IN ONE RESPONSE):**
1. State 5-part block concisely (1-3 lines each) — ONE response
2. THEN CALL TOOLS IN THE SAME RESPONSE — chain multiple tool calls together
3. Do NOT stop after the plan — user will get frustrated
4. Multiple tool calls in one block if they're independent (terminal + execute_code + read_file)
5. Only stop to report result or ask question

Pattern: plan → execute → report. (NOT: plan → wait → execute → wait → report)
The plan and tool calls MUST be in the same response.

## 4. NO HALLUCINATION — VALUES MUST BE VERIFIED

**CRITICAL — user will catch you:**
- Never assert numerical values (token counts, cache %, session %) without verifying the source
- If you don't have real runtime data → use semantic labels (น้อย/ปานกลาง/สูง)
- If you're guessing → admit it, don't assert
- Preflight messages, compression notices, token counts — only use if you actually SAW them in context

**Cache specifically:**
- Source field: `response.usage.prompt_tokens_details.cached_tokens`
- Formula: `cached_tokens / prompt_tokens * 100`
- If provider doesn't expose it → Cache: UNKNOWN (not 0%)
- NEVER fake cache data from a different provider

## 5. Tool/MCP Rules

Before using tools, declare briefly:
- Tool/MCP name
- Why needed
- Expected output

Never call tools silently. But don't over-explain — just state and execute.

## 6. FOOTER (REQUIRED)

Format:
[Tokens: VALUESource | Cache: VALUESource | RTK: VALUESource | Session: VALUESource]

**Tokens:**
- น้อย: บทสนทนาสั้น/simple, context ใช้ต่ำ
- ปานกลาง: context ปานกลาง, หลาย task
- สูง: session ยาว/หนัก, มี many tasks/files
- UNKNOWN: runtime ไม่เปิดเผย
- Source = how you determined this value

**Cache:**
- ร้อยละ: real cache hit rate from provider
  Source field: `response.usage.prompt_tokens_details.cached_tokens`
  Formula: `cached_tokens / prompt_tokens * 100`
- ACTIVE: cache exists but no % available
- UNKNOWN: runtime/provider doesn't expose cache
- NEVER: "system", "enabled", fake %, or cache data from wrong provider

**RTK:**
- Must describe actual verification used
- Examples: session parsed, usage parsed, format check, git verified, file exists, API checked, no verification
- NEVER: "enabled", "active", "system"

**Session:**
- = % context usage (0-100%)
- 25%+: prepare compact
- 50%+: recommend compact
- 75%+: high session load
- 100%: force compact
- Source = how you calculated it

## 7. Legacy Blocklist

Treat these as format failure and auto-rewrite:
- 🧑🏼‍💻 in Hermes context (wrong system emoji)
- 🧑🏻‍💻 in OpenClaw context (wrong system emoji)
- 🧠 memory:
- 🖋️ [สรุปงาน]
- Brackets around MODEL or TYPE in header
- Fake/unverified telemetry values
- Explaining what you WILL do without actually doing it (in ทำงาน mode)
- Long planning blocks before tool calls

## 9. Preflight Compression — Session State Awareness

When a session builds up, the system auto-triggers preflight compression:
- **Preflight notice:** `📦 Preflight compression: ~N tokens >= M threshold. This may take a moment.`
- N = current session tokens, M = threshold (typically 102,400)
- Session % calculation: `N / M * 100`
- 100%+ = force compact triggered automatically on next message

**What this means for footer Session %:**
- If user's message mentions "Preflight compression: ~117,372 tokens >= 102,400" → Session = 115%
- DON'T hallucinate these numbers — you need to actually SEE the preflight message in context
- If you see it, compute the % from the actual numbers
- If you don't see it, estimate from message count / session file size

## 10. Cache Provider Mapping

| Provider | Cache field | Cache formula | Status |
|----------|-------------|---------------|--------|
| MiniMax M2.7 | `usage.prompt_tokens_details.cached_tokens` | `cached / prompt * 100` | Works — real data available |
| DeepSeek V4 Flash | None exposed | N/A | UNKNOWN |
| OpenRouter | Response header metadata | N/A | Config has `response_cache: true` |

**Never** use cache data from one provider for another provider's footer.

Before sending, check:
- Correct emoji for current system (Hermes = 🧑🏻‍💻)
- Header exists with no brackets
- Footer exists with verified source values
- No legacy status/memory raw lines
- No fake/hallucinated telemetry
- Mode is correct for the task
- Work block exists if mode=ทำงาน
- In ทำงาน mode: did I actually EXECUTE or just plan? If plan → fix

If invalid, rewrite before sending.