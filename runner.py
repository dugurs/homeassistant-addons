#!/usr/bin/env python3
"""Comprehensive E2E Regression Test Suite following ha_engine.py modularization."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def p(msg: str):
    print(msg, flush=True)


def run_test(name: str, prompt: str, mode: int, is_mobile: bool):
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"
    payload = json.dumps({
        "prompt": prompt,
        "is_direct_llm": False,
        "stream_mode": mode,
        "is_mobile": is_mobile,
        "client_width": 375 if is_mobile else 1280
    }).encode("utf-8")
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
    passed = len(content) > 0 and len(tools) > 0
    p(f"[*] {name:<35} | Mode {mode} | Latency: {elapsed}s | {'[PASS]' if passed else '[FAIL]'}")
    return content, passed


def main():
    p("=" * 70)
    p("   MODULARIZED HA_ENGINE COMPREHENSIVE E2E REGRESSION SUITE   ")
    p("=" * 70)

    tests = [
        ("Mode 1 Desktop AI Advice", "오늘 날씨와 환경 분석해줘", 1, False),
        ("Mode 1 Mobile AI Advice", "오늘 날씨와 환경 분석해줘", 1, True),
        ("Mode 2 Desktop CLI Terminal", "오늘 날씨와 환경 분석해줘", 2, False),
        ("Mode 2 Mobile CLI Terminal", "오늘 날씨와 환경 분석해줘", 2, True),
        ("Mode 3 Desktop Fast Dashboard", "오늘 날씨와 환경 분석해줘", 3, False),
        ("Mode 3 Mobile Fast Dashboard", "오늘 날씨와 환경 분석해줘", 3, True),
        ("Mode 3 Automations Query", "자동화 목록", 3, False),
        ("Mode 3 System Health Check", "시스템 헬스체크", 3, False),
        ("Mode 3 Room Full Status", "안방 상태 알려줘", 3, False),
    ]

    all_pass = True
    for name, prompt, mode, is_mobile in tests:
        _, ok = run_test(name, prompt, mode, is_mobile)
        if not ok:
            all_pass = False

    p("\n" + "=" * 70)
    p(f"FINAL RESULT: {'ALL 9 TESTS PASSED PERFECTLY [PASS]' if all_pass else 'SOME TESTS FAILED [FAIL]'}")


if __name__ == "__main__":
    main()
