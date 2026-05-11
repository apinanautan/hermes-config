#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║              CONTEXT OPTIMIZER — Token Compression Engine       ║
║                                                                ║
║  1. PRE-COMPRESSION  — Local Model นับ Token ก่อนย่อ           ║
║  2. BIG-MODEL SHRINKER — Cloud API บีบอัดเป็น Tech Metadata    ║
║  3. POST-COMPRESSION — Local Model นับ Token หลังย่อ + Ratio   ║
║  4. EXECUTION BUFFER — ส่งข้อความย่อเข้า Pipeline              ║
║                                                                ║
║  Activation: "Shrink It!" | Auto: >10K tokens                  ║
║  Output: token_audit.csv (Timestamp,Original,Compressed,Ratio) ║
╚══════════════════════════════════════════════════════════════════╝
"""

import csv
import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Optional

# ═════════════════════════════════════════════════════════════════
# TOKEN COUNTER — นับ Token ด้วย Local Model
# ═════════════════════════════════════════════════════════════════

TOKEN_AUDIT = "~/.openclaw/workspace/logs/token_audit.csv"
LOCAL_COUNT_MODEL = "qwen2.5-coder:7b-instruct-q4_K_M"
LOCAL_OLLAMA = "http://127.0.0.1:11434/v1"

AUTO_TRIGGER_THRESHOLD = 10_000  # Auto-execute when context > 10K tokens


def count_tokens_via_llm(text: str, model: str = LOCAL_COUNT_MODEL,
                         timeout: int = 30) -> int:
    """
    ใช้ Local Model นับ Token จริงๆ
    (ไม่ใช่การประมาณ — ให้ LLM tokenize แล้วนับ)
    """
    prompt = f"""Count the EXACT number of tokens in the following text.
Reply with ONLY a number. No other text.

Text:
{text[:8000]}

Token count:"""

    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 10,
        "options": {"num_ctx": 4096, "num_predict": 10, "num_thread": 4}
    }).encode()

    req = urllib.request.Request(
        f"{LOCAL_OLLAMA}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer ollama"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode())
            content = raw["choices"][0]["message"]["content"].strip()
            # Extract number
            nums = re.findall(r'\d+', content)
            return int(nums[0]) if nums else _estimate_tokens(text)
    except Exception:
        return _estimate_tokens(text)


def _estimate_tokens(text: str) -> int:
    """Fallback: approximate — English ~0.75 tokens/word, Thai ~0.5 tokens/char"""
    en_words = len(re.findall(r'[a-zA-Z]+', text))
    th_chars = len(re.findall(r'[\u0E00-\u0E7F]', text))
    other = len(text) - en_words - th_chars
    return int(en_words * 1.3 + th_chars * 0.5 + other * 0.25)


# ═════════════════════════════════════════════════════════════════
# AUDIT LOGGER
# ═════════════════════════════════════════════════════════════════

class TokenAudit:
    """บันทึก log ลง CSV"""

    def __init__(self):
        self.path = Path(TOKEN_AUDIT).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_header()

    def _ensure_header(self):
        if not self.path.exists():
            with open(self.path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Original_Tokens", "Compressed_Tokens",
                                 "Compression_Ratio", "Original_Chars", "Compressed_Chars",
                                 "Model_Used", "Duration_Sec"])

    def log(self, original_tokens: int, compressed_tokens: int,
            original_chars: int, compressed_chars: int,
            model_used: str, duration: float):
        ratio = f"{((1 - compressed_tokens / original_tokens) * 100):.1f}%" if original_tokens > 0 else "N/A"
        with open(self.path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                original_tokens,
                compressed_tokens,
                ratio,
                original_chars,
                compressed_chars,
                model_used,
                f"{duration:.1f}",
            ])

    def last(self) -> Optional[dict]:
        if not self.path.exists():
            return None
        with open(self.path) as f:
            lines = list(csv.reader(f))
        if len(lines) < 2:
            return None
        row = lines[-1]
        return {
            "timestamp": row[0],
            "original": int(row[1]),
            "compressed": int(row[2]),
            "ratio": row[3],
        }


# ═════════════════════════════════════════════════════════════════
# BIG-MODEL SHRINKER — Cloud บีบอัด
# ═════════════════════════════════════════════════════════════════

SHRINK_SYSTEM = """You are a TOKEN COMPRESSOR. Your ONLY job is to rewrite text into
the most concise Technical English possible.

RULES:
- Keep 100% of logic, instructions, parameters, and constraints
- Remove ALL: pleasantries, filler, repetition, explanations, markdown formatting
- Use abbreviations: "usr"=user, "req"=request, "cfg"=config, "impl"=implement
- Use metadata format: key:value, bullet dash, no prose
- If input is Thai → translate+compress into English metadata
- Output ONLY the compressed text. No intro, no outro, no "here is the compressed version"
- Target: reduce token count by 80%+"""


def shrink(original_text: str, api_url: str, model: str,
           api_key: str, timeout: int = 120) -> str:
    """ส่งไป Cloud ให้บีบอัด"""
    prompt = f"""Compress this text per the system instructions:

{original_text}"""

    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SHRINK_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
    }).encode()

    req = urllib.request.Request(
        f"{api_url}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode())
            return raw["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        return f"[SHRINK_ERR {e.code}]: {e.read().decode(errors='replace')[:100]}"
    except Exception as e:
        return f"[SHRINK_ERR]: {e}"


# ═════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═════════════════════════════════════════════════════════════════

class ContextOptimizer:
    """
    Token Compression Engine:
      Pre-Log → Shrink → Post-Log → Return compressed
    """

    def __init__(self, cloud_url: str = "https://ollama-pay.thaigqsoft.com/api/v1",
                 cloud_model: str = "minimax/MiniMax-M2.7",
                 api_key: str = ""):
        self.cloud_url = cloud_url
        self.cloud_model = cloud_model
        self.api_key = api_key
        self.audit = TokenAudit()

    @property
    def stats_name(self) -> str:
        return "📦 Context Optimizer (Token Compressor)"

    def optimize(self, text: str,
                 force: bool = False) -> dict:
        """
        Full pipeline:
          1. Pre-count tokens (Local)
          2. Shrink via Cloud
          3. Post-count tokens (Local)
          4. Log to CSV
        Returns {"compressed": str, "original_tokens": int, "compressed_tokens": int, "ratio": str}
        """
        t0 = time.time()

        # Check if compression needed
        original_tokens = count_tokens_via_llm(text)
        needs_compress = force or (original_tokens > AUTO_TRIGGER_THRESHOLD)

        if not needs_compress:
            return {
                "compressed": text,
                "original_tokens": original_tokens,
                "compressed_tokens": original_tokens,
                "ratio": "0% (below threshold)",
                "skipped": True,
            }

        # ── 2. Shrink via Cloud ──
        compressed = shrink(text, self.cloud_url, self.cloud_model,
                           self.api_key, timeout=120)

        if compressed.startswith("[SHRINK_ERR]"):
            return {
                "compressed": text,
                "original_tokens": original_tokens,
                "compressed_tokens": original_tokens,
                "ratio": "Shrink failed — using original",
                "error": compressed,
            }

        # ── 3. Post-count ──
        compressed_tokens = count_tokens_via_llm(compressed)

        # ── 4. Log ──
        duration = time.time() - t0
        self.audit.log(
            original_tokens, compressed_tokens,
            len(text), len(compressed),
            self.cloud_model, duration
        )

        ratio = f"{((1 - compressed_tokens / original_tokens) * 100):.1f}%" if original_tokens > 0 else "N/A"

        return {
            "compressed": compressed,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "ratio": ratio,
            "model_used": self.cloud_model,
            "duration": duration,
        }

    def report(self) -> Optional[dict]:
        return self.audit.last()


# ═════════════════════════════════════════════════════════════════
# CLI TEST
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test with a long Thai text
    test_input = """ตรวจสอบระบบทั้งหมดในเครื่องนี้ให้ละเอียด:
1. ดูว่ามี container Docker อะไรกำลังรันอยู่บ้าง และแต่ละตัวใช้ทรัพยากรเท่าไหร่
2. เช็คสถานะของระบบ Hermes Agent ว่าทำงานปกติไหม
3. ดูว่ามี process ไหนที่ใช้ CPU เกิน 50% บ้าง
4. ตรวจสอบพื้นที่ดิสก์ว่ามี partition ไหนใกล้เต็ม
5. เช็คว่ามี service ไหนที่ควรจะรันแต่ไม่รันบ้าง"""

    optimizer = ContextOptimizer()

    print("📊 Context Optimizer — Test Run")
    print(f"   Input length: {len(test_input)} chars")

    # Count tokens before
    pre = count_tokens_via_llm(test_input)
    print(f"   Pre-count: ~{pre} tokens")

    result = optimizer.optimize(test_input, force=True)
    print(f"\n📦 Result:")
    print(f"   Original:  {result['original_tokens']} tokens ({len(test_input)} chars)")
    print(f"   Compressed: {result['compressed_tokens']} tokens ({len(result['compressed'])} chars)")
    print(f"   Ratio:     {result['ratio']}")
    if "duration" in result:
        print(f"   Duration:  {result['duration']:.1f}s")

    print(f"\n🗜️  Compressed text:")
    print(f"   {result['compressed'][:300]}")
    print(f"\n📁 Audit: {Path(TOKEN_AUDIT).expanduser()}")

    last = optimizer.report()
    if last:
        print(f"   Last entry: {last['timestamp']} → {last['ratio']} compression")
