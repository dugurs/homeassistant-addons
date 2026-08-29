#!/usr/bin/env python3
"""E2E Verification for newly integrated ha-mcp Fast Mode features."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def p(msg: str):
    print(msg, flush=True)


def test_prompt(prompt: str):
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"
    p(f"\n========================================================")
    p(f"[*] Testing Prompt: '{prompt}' (Mode 3 Fast)")
    p(f"========================================================")

    payload = json.dumps({"prompt": prompt, "is_direct_llm": False, "stream_mode": 3}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    t0 = time.time()
    chunks = []
    tools = []

    with urllib.request.urlopen(req, timeout=10) as resp:
        for line in resp:
            l = line.decode("utf-8", errors="replace").strip()
            if l.startswith("data:"):
                ev = json.loads(l[5:].strip())
                etype = ev.get("type")
                if etype == "tool":
                    tools.append(ev.get("content", ""))
                elif etype in ("text", "chunk"):
                    chunks.append(ev.get("content", ""))
                elif etype == "done":
                    break

    elapsed = round(time.time() - t0, 3)
    content = "".join(chunks)
    p(f"[Latency: {elapsed}s | Tool Events: {len(tools)}]")
    p("--- [Result Output] ---")
    p(content)
    return len(content) > 0


def main():
    p("[ha-mcp Fast Mode Feature Verification Suite Starting]...")
    tests = [
        "자동화 목록",
        "시스템 헬스체크",
        "안방 상태 알려줘",
        "할 일 목록 보여줘",
    ]

    all_pass = True
    for t in tests:
        success = test_prompt(t)
        if not success:
            all_pass = False

    p("\n" + "=" * 56)
    p(f"OVERALL RESULT: {'ALL TESTS PASSED [PASS]' if all_pass else 'TEST FAILED [FAIL]'}")


if __name__ == "__main__":
    main()
