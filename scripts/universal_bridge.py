#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║     4-UNIT BRIDGE — Self-Healing + Token Optimized                 ║
║                                                                    ║
║  🟢 UNIT 1 — TRANSLATOR  Qwen2.5-7B-Q4   TH→EN  (Local, vRAM~5G) ║
║  🔵 UNIT 2 — ARCHITECT   MiniMax-M2.7     Plan   (Cloud, retry)   ║
║  🟡 UNIT 3 — CODER       Qwen2.5-Coder-7B Exec   (Local, vRAM~5G) ║
║  🟣 UNIT 4 — REPORTER    MiniMax-M2.7     TH Sum (Cloud, retry)   ║
║                                                                    ║
║  🔑 Self-Healing Key Pool  — Auto-Scavenge/Rotate/Repair          ║
║  📦 Context Optimizer      — Token Compression on demand          ║
║  🧰 MCP Auto-Discovery     — Native Execution + Trace             ║
║  🗑️ Zero Footprint                                              ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json, os, re, shutil, subprocess, sys, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# ── Import skills — use Hermes skills, not OpenClaw ──
SKILLS_DIR = os.path.expanduser("~/.hermes/skills/software-development/minimax-workflow/references")
HERMES_SKILLS = os.path.expanduser("~/.hermes/skills")
sys.path.insert(0, SKILLS_DIR)
sys.path.insert(0, HERMES_SKILLS)

try:
    from key_resilience_skill import KeyPool, get_key_pool
except ImportError:
    # Fallback: inline minimal version
    class KeyPool:
        def __init__(self): self._keys = []
        def scavenge(self): return 0
        def keys(self): return self._keys
        def mark_dead(self, k): pass
        def get_next_alive(self, after=None): return None
        def repair(self, k): return 0
        def call_with_retry(self, url, model, msgs, timeout=120, max_retries=3):
            return "[NO_KEY_POOL]", "none"
    def get_key_pool(): return KeyPool()

try:
    from token_optimizer import ContextOptimizer, count_tokens_via_llm, AUTO_TRIGGER_THRESHOLD
except ImportError:
    class ContextOptimizer:
        def __init__(self, *a, **kw): pass
        def optimize(self, text, force=False):
            return {"compressed": text, "original_tokens": 0, "compressed_tokens": 0, "ratio": "N/A"}
        stats_name = "📦 Context Optimizer (fallback)"
    def count_tokens_via_llm(t, **kw): return len(t.split())
    AUTO_TRIGGER_THRESHOLD = 10000

# ═════════════════════════════════════════════════════════════════
# CONSTANTS
# ═════════════════════════════════════════════════════════════════
BRIDGE_TMP       = "/tmp/bridge"
LOCAL_OLLAMA     = "http://127.0.0.1:11434/v1"
CLOUD_BASE       = "https://ollama-pay.thaigqsoft.com/api/v1"
MODEL_TRANSLATOR = "minimax/MiniMax-M2.7"   # UNIT 1 — MiniMax Official Cloud
MODEL_ARCHITECT  = "minimax/MiniMax-M2.7"
MODEL_CODER      = "qwen2.5-coder:7b-instruct-q4_K_M"
MODEL_REPORTER   = "minimax/MiniMax-M2.7"

WORKSPACE_PATHS = [
    "/home/apinan/.openclaw/workspace",
    "/home/apinan/Downloads",
    "/home/apinan",
]

LOW_VRAM_OPTS = {
    "num_ctx": 2048,
    "num_predict": 512,
    "num_thread": 4,
}

MCP_REGISTRY = {
    "filesystem__list_directory":      {"desc":"List files/dirs","params":["path"],"cat":"fs","native":True},
    "filesystem__list_dir_sizes":      {"desc":"Files + sizes","params":["path","sortBy"],"cat":"fs","native":True},
    "filesystem__directory_tree":      {"desc":"Recursive tree","params":["path"],"cat":"fs","native":True},
    "filesystem__search_files":        {"desc":"Glob search + size filter","params":["path","pattern","min_size"],"cat":"fs","native":True},
    "filesystem__read_file":           {"desc":"Read text file","params":["path","head","tail"],"cat":"fs","native":True},
    "filesystem__get_info":            {"desc":"File metadata","params":["path"],"cat":"fs","native":True},
    "filesystem__find_old":            {"desc":"Files not modified in N days","params":["path","days","pattern"],"cat":"fs","native":True},
    "web_search":                      {"desc":"Search web (DDG)","params":["query"],"cat":"web","native":False},
    "web_fetch":                       {"desc":"Fetch URL content","params":["url","maxChars"],"cat":"web","native":False},
    "ollama__list":                    {"desc":"List local models","params":[],"cat":"ai","native":True},
    "terminal__bash":                  {"desc":"Bash command","params":["command"],"cat":"sys","native":True},
}

def _ensure_tmp(): os.makedirs(BRIDGE_TMP, exist_ok=True)

# ═════════════════════════════════════════════════════════════════
# LOW-VRAM LOCAL CALL
# ═════════════════════════════════════════════════════════════════

def call_local(model: str, prompt: str, *,
               system: str = "", timeout: int = 90) -> str:
    body = {
        "model": model,
        "messages": [],
        "temperature": 0.3,
        "max_tokens": 512,
        "options": LOW_VRAM_OPTS,
    }
    if system:
        body["messages"].append({"role": "system", "content": system})
    body["messages"].append({"role": "user", "content": prompt})

    req = urllib.request.Request(
        f"{LOCAL_OLLAMA}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer ollama"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[LOCAL_ERR]: {e}"

# ═════════════════════════════════════════════════════════════════
# CLOUD CALL WITH KEY-POOL RETRY
# ═════════════════════════════════════════════════════════════════

def call_cloud(model: str, prompt: str, *,
               system: str = "", timeout: int = 120) -> tuple[str, str]:
    """
    Use KeyPool for auto-retry on 401.
    Returns (response_text, key_used)
    """
    system_len = len(system) if system else 0
    prompt_len = len(prompt)
    est_in = (system_len + prompt_len) // 4

    pool = get_key_pool()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp, key = pool.call_with_retry(CLOUD_BASE, model, messages, timeout=timeout)

    # Token log (rough estimate only since KeyPool doesn't expose usage)
    print(f"\n📤 [TOKEN] {model}")
    print(f"   In: ~{est_in} tok (chars: {system_len}+{prompt_len})")
    print(f"   Key: ...{key[-12:]}")

    return resp, key


# ═════════════════════════════════════════════════════════════════
# MCP DISCOVERY
# ═════════════════════════════════════════════════════════════════

def discover_mcp_tools() -> dict:
    avail = {}
    for name, info in MCP_REGISTRY.items():
        ok = info.get("native", False) or _check(info["cat"])
        avail[name] = {
            "description": info["desc"],
            "category": info["cat"],
            "status": "ready" if ok else "unavailable",
            "native": info["native"],
            "params": info["params"],
        }
    return avail

def _check(cat: str) -> bool:
    if cat in ("fs", "sys"): return True
    try:
        subprocess.run(["curl", "-s", "--max-time", "3", "http://127.0.0.1:11434/api/tags"],
                       capture_output=True, timeout=8)
        return True
    except: return False

def format_mcp_context(tools: dict) -> str:
    """สร้าง MCP context แบบกระชับ — ไม่ต้องแสดงทุก tool"""
    lines = ["MCP TOOLS:"]
    by_cat = {}
    for n, t in tools.items():
        by_cat.setdefault(t["category"], []).append((n, t))
    for cat, lst in sorted(by_cat.items()):
        names = ", ".join(f"`{n}`" for n, _ in lst)
        lines.append(f"[{cat.upper()}] {names}")
    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════
# UNIT 1 — TRANSLATOR  🟢 Qwen2.5-7B-Q4  Local Low-VRAM
# ═════════════════════════════════════════════════════════════════

class Translator:
    MODEL = MODEL_TRANSLATOR
    _name = f"🟢 MiniMax-M2.7 [Cloud, TH→EN]"

    def translate(self, th: str) -> tuple[str, bool]:
        r, _ = call_cloud(self.MODEL,  # MiniMax M2.7 Official Cloud
            f"Translate Thai to SHORT technical English. Max 2 sentences. No fluff.\n\nThai: {th}\n\nEnglish:",
            system="You translate Thai→concise technical English. Sharp. Max 50 words.")
        if r.startswith("[CLOUD") or r.startswith("[ALL_KEYS"):
            return th[:200] + "…", False
        return r.strip(), True


# ═════════════════════════════════════════════════════════════════
# UNIT 2 — ARCHITECT  🔵 MiniMax-M2.7  Cloud + Key Retry
# ═════════════════════════════════════════════════════════════════

class Architect:
    MODEL = MODEL_ARCHITECT
    _name = f"🔵 MiniMax-M2.7 [Cloud API, Key-Pool Retry]"

    def plan(self, en: str, mcp_ctx: str = "") -> dict:
        if not mcp_ctx:
            dt = discover_mcp_tools()
            mcp_ctx = format_mcp_context(dt)

        prompt = f"""[SYSTEM ARCHITECT]
Analyze and create executable plan using MCP tools.

{mcp_ctx}

REQUEST: "{en}"

Select MCP tools (exact names: `filesystem__list_directory`, `terminal__bash`, etc.)
Output: 1) Tool + why. 2) Plan steps with ```bash commands using /home/apinan/.openclaw/workspace"""

        resp, key = call_cloud(self.MODEL, prompt,
            system="Architect: select MCP tools + create plan with ```bash commands. Use real paths.",
            timeout=120)

        sel = self._extract_selected(resp)
        return {"raw": resp, "success": not resp.startswith("[CLOUD"),
                "model_used": self.MODEL, "selected_mcp_tools": sel, "key": key[:20]+"..."}

    def _extract_selected(self, text: str) -> list[str]:
        found = []
        for m in re.finditer(r'\*\*Tool\*\*:\s*`?([\w_]+(?:__\w+)?)`?', text):
            found.append(m.group(1))
        if not found:
            for name in MCP_REGISTRY:
                if name in text: found.append(name)
        return found or ["terminal__bash"]


# ═════════════════════════════════════════════════════════════════
# UNIT 3 — CODER  🟡 Qwen2.5-Coder-7B  Local Low-VRAM
# ═════════════════════════════════════════════════════════════════

class Coder:
    MODEL = MODEL_CODER
    EXEC_TO = 45
    _name = f"🟡 Qwen2.5-Coder-7B-Q4_K_M [Local, VRAM~4.5GB, zero-bug]"

    def extract(self, plan: str) -> list[dict]:
        items = []
        for m in re.finditer(r"```(?:ba?sh|shell)?\n?(.*?)```", plan, re.DOTALL):
            for line in m.group(1).strip().split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    items.append({"type": "shell", "command": line})
        if not items:
            for line in plan.split("\n"):
                line = line.strip()
                if any(line.startswith(p) for p in
                       ["find ","du ","ls ","stat ","curl ","wc ","sort ","head ","tail ",
                        "df ","free ","ps ","docker ","python"]):
                    items.append({"type": "shell", "command": line})
        return items

    def _exec_shell(self, cmd: str) -> dict:
        cmd = self._fix_path(os.path.expanduser(cmd))
        try:
            out = subprocess.check_output(
                cmd, shell=True, stderr=subprocess.STDOUT,
                timeout=self.EXEC_TO, text=True).strip()
            return {"ok": True, "command": cmd[:80], "output": out[:2000]}
        except subprocess.TimeoutExpired:
            return {"ok": False, "command": cmd[:80], "output": "⏰ TIMEOUT"}
        except subprocess.CalledProcessError as e:
            return {"ok": False, "command": cmd[:80], "output": (e.output or str(e)).strip()[:500]}
        except Exception as e:
            return {"ok": False, "command": cmd[:80], "output": str(e)[:500]}

    def _exec_mcp_fs(self, tn: str, params: dict) -> dict:
        p = self._resolve(params.get("path", "."))
        try:
            bp = Path(p)
            if tn == "filesystem__list_directory":
                ents = [f"{'📁' if f.is_dir() else '📄'} {f.name}  {_sz(f)}" for f in sorted(bp.iterdir())]
                return {"ok": True, "output": "\n".join(ents) or "(empty)"}

            elif tn == "filesystem__list_dir_sizes":
                ents = []
                for f in sorted(bp.iterdir()):
                    ents.append(f"{'📁' if f.is_dir() else '📄'} {f.name}  {_sz(f)}")
                return {"ok": True, "output": "\n".join(ents) or "(empty)"}

            elif tn == "filesystem__search_files":
                pat = params.get("pattern", "*")
                ms = int(params.get("min_size", 0))
                matched = []
                for f in bp.rglob(pat):
                    if f.is_file() and f.stat().st_size >= ms:
                        ds = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
                        matched.append(f"{f.relative_to(bp)}  [{_sz(f)}]  {ds}")
                        if len(matched) >= 50: break
                return {"ok": True, "output": "\n".join(matched) or "No matches"}

            elif tn == "filesystem__read_file":
                c = bp.read_text()
                if params.get("head"): c = "\n".join(c.split("\n")[:int(params["head"])])
                if params.get("tail"): c = "\n".join(c.split("\n")[-int(params["tail"]):])
                if len(c) > 3000: c = c[:3000] + "\n…"
                return {"ok": True, "output": c}

            elif tn == "filesystem__get_info":
                st = bp.stat()
                return {"ok": True, "output": f"Name:{bp.name} Size:{_sz(bp)} Mod:{datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M}"}

            elif tn == "filesystem__find_old":
                days = int(params.get("days", 30))
                pat = params.get("pattern", "*")
                cutoff = time.time() - days * 86400
                matched = []
                for f in bp.rglob(pat):
                    if f.is_file() and f.stat().st_mtime < cutoff:
                        ago = int((time.time() - f.stat().st_mtime) / 86400)
                        matched.append(f"{f.relative_to(bp)}  [{_sz(f)}]  {ago}d ago")
                        if len(matched) >= 50: break
                return {"ok": True, "output": "\n".join(matched) or f"No files >{days}d old"}

            elif tn == "filesystem__directory_tree":
                lines = [f"{bp.name}/"]
                def _t(pp, pre=""):
                    es = sorted(pp.iterdir())
                    for i, e in enumerate(es):
                        last = i == len(es)-1; c = "└── " if last else "├── "
                        if e.is_dir():
                            lines.append(f"{pre}{c}{e.name}/")
                            _t(e, pre+("    " if last else "│   "))
                        else:
                            lines.append(f"{pre}{c}{e.name} ({_sz(e)})")
                _t(bp)
                return {"ok": True, "output": "\n".join(lines[:80])}

            return {"ok": False, "output": f"Unknown: {tn}"}
        except Exception as e:
            return {"ok": False, "output": str(e)}

    def _exec_mcp_web(self, tn: str, params: dict) -> dict:
        q = params.get("query") or params.get("url", "")
        if not q: return {"ok": False, "output": "No query/url"}
        try:
            if tn == "web_search":
                from urllib.parse import quote
                req = urllib.request.Request(
                    f"https://html.duckduckgo.com/html/?q={quote(q)}",
                    headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    html = r.read().decode(errors="replace")
                text = re.sub(r'<[^>]+>', ' ', html); text = re.sub(r'\s+', ' ', text).strip()
                lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 30]
                return {"ok": True, "output": "\n".join(lines[:12]) or "No results"}
            elif tn == "web_fetch":
                req = urllib.request.Request(q, headers={"User-Agent": "Bridge/1.0"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    raw = r.read().decode(errors="replace")
                text = re.sub(r'<[^>]+>', ' ', raw); text = re.sub(r'\s+', ' ', text).strip()
                return {"ok": True, "output": text[:int(params.get("maxChars", 3000))]}
        except Exception as e:
            return {"ok": False, "output": str(e)}
        return {"ok": False, "output": f"Unknown: {tn}"}

    def _fix_path(self, cmd: str) -> str:
        for bad, good in {
            "/home/apinan/work":"/home/apinan/.openclaw/workspace",
            "/path/to/your":"/home/apinan/.openclaw/workspace",
            "~/work":"/home/apinan/.openclaw/workspace"}.items():
            cmd = cmd.replace(bad, good)
        return cmd

    def _resolve(self, p: str) -> str:
        p = os.path.expanduser(p or ".")
        if Path(p).exists(): return p
        for wp in WORKSPACE_PATHS:
            c = os.path.join(wp, os.path.basename(p))
            if Path(c).exists(): return c
        return p

    def execute(self, plan: str, req: str = "", sel: list = None) -> dict:
        items = self.extract(plan)
        if not items:
            items = self._gen(plan, req)
        if not items:
            return {"commands_run":0,"outputs":[],"success":False,"error":"No commands","mcp_tools_used":[]}

        results = []; mcp = set(sel or [])
        for it in items:
            if it["type"] == "shell":
                r = self._exec_shell(it["command"])
            elif it["type"] == "mcp":
                tn = it.get("mcp_tool",""); mcp.add(tn)
                if tn.startswith("filesystem__"): r = self._exec_mcp_fs(tn, it.get("params",{}))
                elif tn.startswith("web_"): r = self._exec_mcp_web(tn, it.get("params",{}))
                else: r = {"ok": False, "command": tn, "output": "Not implemented"}
                r["command"] = f"[MCP] {tn}"
            else: continue
            results.append(r)

        return {
            "commands_run": len(results), "outputs": results,
            "success": all(r.get("ok") for r in results),
            "raw": "\n".join(f"$ {r.get('command','?')}\n{r.get('output','')}" for r in results),
            "mcp_tools_used": sorted(mcp),
        }

    def _gen(self, plan: str, req: str) -> list[dict]:
        try:
            r = call_local(self.MODEL,
                f"Generate shell commands (one per line) from plan:\n{plan[:1500]}\n\nRequest:{req}\n\nCommands:",
                system="Output only shell commands. No commentary.", timeout=30)
            return [{"type":"shell","command":l.replace("`","").strip()}
                    for l in r.strip().split("\n")
                    if l.strip() and not l.strip().startswith("#")]
        except: return []


# ═════════════════════════════════════════════════════════════════
# UNIT 4 — REPORTER  🟣 MiniMax-M2.7  Cloud + Key Retry
# ═════════════════════════════════════════════════════════════════

class Reporter:
    MODEL = MODEL_REPORTER
    _name = f"🟣 MiniMax-M2.7 [Cloud API, Key-Pool Retry]"

    def summarize(self, req: str, ex: dict, mcp: list = None) -> str:
        """แค่ route/switch — ไม่ summarize ด้วยโมเดล"""
        # ดูว่าสำเร็จไหม
        ok_n = sum(1 for r in ex.get("outputs", []) if r.get("ok"))
        total = len(ex.get("outputs", []))
        success = ex.get("success", False)

        # สรุปสั้นๆ ว่าทำอะไร
        if success:
            return f"✅ รัน {total} คำสั่งสำเร็จ {ok_n}/{total}"
        else:
            failed = [r.get("command","") for r in ex.get("outputs",[]) if not r.get("ok")]
            return f"❌ มีปัญหา: {failed[0] if failed else 'ไม่ทราบ'} ({ok_n}/{total} สำเร็จ)"


# ═════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════

def _sz(p: Path) -> str:
    s = p.stat().st_size if p.is_file() else 0
    if s >= 1e9: return f"{s/1e9:.1f}GB"
    if s >= 1e6: return f"{s/1e6:.1f}MB"
    if s >= 1e3: return f"{s/1e3:.1f}KB"
    return f"{s}B"

class CleanupManager:
    @staticmethod
    def wipe():
        p = Path(BRIDGE_TMP)
        if p.exists(): shutil.rmtree(p, ignore_errors=True)


# ═════════════════════════════════════════════════════════════════
# 4-UNIT BRIDGE — Main Pipeline
# ═════════════════════════════════════════════════════════════════

class FourUnitBridge:
    """
    ╔═══════════════════════════════════════════╗
    ║  4-UNIT + SELF-HEALING + OPTIMIZED       ║
    ║  🟢 Qwen2.5-7B  🔵 MiniMax-M2.7          ║
    ║  🟡 Coder-7B    🟣 MiniMax-M2.7          ║
    ║  🔑 KeyPool  📦 Context Optimizer        ║
    ╚═══════════════════════════════════════════╝
    """

    def __init__(self):
        self.u1 = Translator()
        self.u2 = Architect()
        self.u3 = Coder()
        self.u4 = Reporter()
        self.optimizer = ContextOptimizer()
        self.trace = True
        _ensure_tmp()

    def run(self, thai: str) -> dict:
        T = self._p

        T(f"\n{'═'*50}")
        T("🚀 4-UNIT BRIDGE + SELF-HEALING")
        T(f"{'═'*50}")
        T(f"📥 INPUT: {thai[:120]}")

        # ── Check Shrink It! activation ──
        force_shrink = "shrink it" in thai.lower() or "ย่อ" in thai
        if force_shrink:
            T("\n📦 [CONTEXT OPTIMIZER] Boss wants compression!")
        tk = count_tokens_via_llm(thai)
        T(f"   Tokens: ~{tk}")
        if tk > AUTO_TRIGGER_THRESHOLD:
            T(f"   ⚠️  Context > {AUTO_TRIGGER_THRESHOLD} tokens → Auto-Compress!")
            force_shrink = True

        # ── Shrink if needed ──
        pipeline_input = thai
        if force_shrink:
            T("   Compressing via Cloud...")
            opt = self.optimizer.optimize(thai, force=True)
            if not opt.get("skipped"):
                T(f"   ✅ Ratio: {opt['ratio']} ({opt['original_tokens']}→{opt['compressed_tokens']} tokens)")
                pipeline_input = opt["compressed"]
            else:
                T(f"   ⏭️  Skipped ({opt.get('ratio','')})")

        # ── U1 BYPASS: TH short → skip translator ──
        th_len = len(thai)
        en_len = len(thai)  # placeholder, will update after U1 if called
        bypass_u1 = th_len < 120  # TH under 120 chars → skip U1

        # ── UNIT 1: TRANSLATOR ──
        if bypass_u1:
            T(f"\n🟢 [UNIT 1] BYPASSED (TH short: {th_len} chars < 120)")
            en = thai  # use TH directly
        else:
            T(f"\n🟢 [UNIT 1] {Translator._name}")
            en, ok = self.u1.translate(pipeline_input)
            T(f"   {'✅' if ok else '⚠️'}  → {en[:120]}")

        # ── MCP DISCOVERY ──
        T("\n🧰 [MCP] Scanning tools...")
        mcp_tools = discover_mcp_tools()
        mcp_ctx = format_mcp_context(mcp_tools)
        rd = sum(1 for t in mcp_tools.values() if t["status"]=="ready")
        T(f"   ✅ {rd}/{len(mcp_tools)} ready")

        # ── UNIT 2: ARCHITECT ──
        T(f"\n🔵 [UNIT 2] {Architect._name}")
        plan = self.u2.plan(en, mcp_ctx)
        T(f"   {'✅' if plan['success'] else '❌'}  Plan: {len(plan['raw'])} chars  (key:{plan.get('key','?')})")
        T(f"   🎯 Selected: {', '.join(plan['selected_mcp_tools'])}")

        # ── UNIT 3: CODER ──
        T(f"\n🟡 [UNIT 3] {Coder._name}")
        ex = self.u3.execute(plan["raw"], thai, plan.get("selected_mcp_tools"))
        ok_n = sum(1 for r in ex["outputs"] if r.get("ok"))
        T(f"   {'✅' if ex['success'] else '⚠️'}  {ex['commands_run']} ops ({ok_n} ok)")
        for r in ex["outputs"][:5]:
            icon = "✅" if r.get("ok") else "❌"
            first = r.get("output","").split("\n")[0][:80]
            T(f"      {icon} {r.get('command','')[:50]}")
            T(f"         {first}")

        # ── UNIT 4: REPORTER ──
        T(f"\n🟣 [UNIT 4] {Reporter._name}")
        summary = self.u4.summarize(thai, ex, ex.get("mcp_tools_used"))
        T(f"   ✅ Summary: {summary[:100]}...")

        # ── CLEANUP ──
        CleanupManager.wipe()
        T(f"\n🗑️  Zero Footprint ✅")
        T(f"{'═'*50}\n")

        return {
            "english": en,
            "plan": plan,
            "execution": ex,
            "summary": summary,
            "architect_model": Architect.MODEL,
            "selected_mcp": plan.get("selected_mcp_tools", []),
            "mcp_used": ex.get("mcp_tools_used", []),
            "cleanup": True,
        }

    def _p(self, msg):
        if self.trace: print(msg, flush=True)

    @property
    def models(self) -> dict:
        return {
            "translator": Translator._name,
            "architect":  Architect._name,
            "coder":      Coder._name,
            "reporter":   Reporter._name,
            "optimizer":  self.optimizer.stats_name if hasattr(self.optimizer, 'stats_name') else "📦 Context Optimizer",
        }


# ═════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 universal_bridge.py '<Thai text>'")
        sys.exit(1)

    inp = " ".join(sys.argv[1:])
    bridge = FourUnitBridge()

    # Boot key pool
    pool = get_key_pool()
    pool.scavenge()

    result = bridge.run(inp)

    print("═" * 50)
    print("📋  FINAL REPORT")
    print("═" * 50)
    models = bridge.models
    print(f"🟢 {models['translator']}")
    print(f"🔵 {models['architect']}")
    print(f"🟡 {models['coder']}")
    print(f"🟣 {models['reporter']}")
    print(f"🎯 MCP: {', '.join(result['selected_mcp'])}")
    print(f"🔧 Ops: {result['execution']['commands_run']}")
    print(f"📝 Summary:\n   {result['summary']}")
    print(f"🗑️  Clean: ✅")
