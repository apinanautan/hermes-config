WSL git repo at ~/.hermes with SSH to GitHub. hermes-config repo has branches: main (protected, rejects large pushes), config-sync, new-default. Local master reset to d500e4b. Working tree has hermes-agent/, skills/, inventory/, scripts/ (hermes-agent has node_modules/). config-source/ and config-source.old/ missing from working tree (were in cde7e91 but got lost during resets). User confirmed: hermes-agent is safe to include but must exclude its node_modules/.
§
Owen emoji: light skin person at laptop Fitzpatrick type 1-2
§
Hermes: 🧑🏻‍💻 / OpenClaw: 🧑🏼‍💻 — never mix. Format: 🧑🏻‍💻MODEL TYPE 🧑🏻‍💻 no brackets. Footer: [Tokens/Cache/RTK/Session] — no fake values. Mode ทำงาน needs 5-part work block. hermes-format-recovery is MANDATORY for every reply.
§
hermes-format-recovery is MANDATORY WORKFLOW — must apply to every single reply, not just when lost.
§
Hermes emoji light skin / OpenClaw emoji medium-light — never mix. Header no brackets. Footer real values only. Mode ทำงาน needs 5-part work block.
§
Hermes source lives in TWO places: ~/hermes-agent/ (development checkout with all files) and ~/.hermes/hermes-agent/ (deployed copy used by the gateway). If .hermes/hermes-agent/ gets deleted/corrupted, restore via rsync from ~/hermes-agent/ (excluding __pycache__, node_modules, venv, .venv, .git). OpenClaw standalone runtime is at ~/.openclaw/node/ — its lib/node_modules/openclaw/ has session-archive.runtime.js if the old ~/.hermes/node/ location is empty.
§
Bot2 (@Hermacc_bot) profile ถูกลบออกจาก Hermes แล้ว — bot2 ไม่มีอยู่แล้ว