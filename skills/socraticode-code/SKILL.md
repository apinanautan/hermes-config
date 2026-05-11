---
name: socraticode-code
description: |
  Primary code analysis tool — MUST be loaded and used BEFORE reading, editing, or
  reasoning about any code, scripts, automation, config files, or development tasks.
  NEVER edit code without first searching and analyzing with SocratiCode.
  Triggers on: analyzing, debugging, editing, refactoring, creating, modifying,
  inspecting, or tracing code; build failures; file exploration; symbol lookup;
  dependency analysis; workflow inspection; impact assessment. ALWAYS use SocratiCode
  first to search, trace, and understand the codebase before taking any action.
---

# SocratiCode สำหรับงานโค้ด

## หลักใช้

ถ้างานเกี่ยวกับโค้ดทุกชนิด ให้ใช้ SocratiCode เป็นเครื่องมือหลักก่อนเสมอ:
- อ่านภาพรวมโปรเจกต์ด้วย `codebase_context`, `codebase_status`, `codebase_graph_status`
- หาโค้ดที่เกี่ยวข้องด้วย `codebase_search` / `codebase_context_search`
- เจาะจงจุดทำงานด้วย `codebase_symbol`, `codebase_symbols`, `codebase_flow`
- ตรวจผลกระทบก่อนแก้ด้วย `codebase_impact`, `codebase_graph_query`, `codebase_graph_circular`
- ใช้ `codebase_index` / `codebase_update` / `codebase_watch` เมื่อดัชนียังไม่พร้อมหรือไฟล์เปลี่ยน

## ลำดับทำงาน

1. ระบุโปรเจกต์หรือพาธโค้ด
2. ใช้ SocratiCode หาไฟล์ โหนด และเส้นทางการทำงานก่อนแตะโค้ด
3. ถ้าเป็นการแก้บั๊ก ให้ค้นสาเหตุจาก symbol/flow/impact ก่อนเดา
4. ค่อยแก้ไฟล์ด้วยเครื่องมือแก้ไขไฟล์
5. ตรวจยืนยันด้วย SocratiCode ซ้ำถ้าต้องเช็กความสัมพันธ์หรือผลกระทบ

## กติกา

- **บังคับ:** ต้องใช้ SocratiCode ก่อนแก้โค้ดทุกครั้ง — ห้ามข้าม
- ถ้า SocratiCode ใช้ไม่ได้ (fail/timeout) → บอกเจ้านายทันที แล้วใช้ exec/read/edit ธรรมดาแทน
- อย่าเดาไฟล์โค้ดถ้า SocratiCode หาได้
- ถ้าโปรเจกต์ยังไม่ถูก index ให้ index ก่อนค้นหา
- ถ้าผลลัพธ์ไม่ชัด ให้ค้นซ้ำด้วยคำถามอื่นหรือขอบเขตที่แคบลง
- ถ้างานไม่ใช่โค้ดจริง ๆ ไม่ต้องฝืนใช้สกิลนี้

## ขอบเขต

ใช้กับ:
- source code ทุกภาษา
- scripts และ automation
- workflow JSON / YAML / config ที่ควบคุมพฤติกรรมโค้ด
- test, build, lint, dependency, architecture, refactor
- การวิเคราะห์ผลกระทบก่อนลบหรือเปลี่ยนชื่อ
## Sensitive Code Handling

- If the boss provides a code/password in the current message, use it only to unlock the explicitly authorized task.
- Never save, copy, summarize, or persist the code/password in skill files, notes, backups, logs, or artifacts.
- After use, remove the code/password from any editable artifact touched in the task and replace it with `[ถามรหัสจากเจ้านายเมื่อจำเป็น]` when a placeholder is needed.

