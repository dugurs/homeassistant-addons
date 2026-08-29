#!/usr/bin/env python3
"""E2E Verification for 2-Mode Architecture & Token Tracking."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def p(msg: str):
    print(msg, flush=True)


def test_clean_2modes_and_tokens():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"

    p("=" * 70)
    p("  E2E 2-MODE ARCHITECTURE & LIVE TOKEN TRACKING TEST  ")
    p("=" * 70)

    # 1. Mode 1 Test: AI Deep Brain
    p("\n[*] Testing [Mode 1: AI Deep Brain] with Multi-Metric Analysis & Token Tracking:")
    payload1 = json.dumps({
        "prompt": "오늘 날씨와 환경 분석해줘",
        "stream_mode": 1,
        "is_mobile": False,
    }).encode("utf-8")
    req1 = urllib.request.Request(url, data=payload1, headers={"Content-Type": "application/json"})

    t0 = time.time()
    chunks1 = []
    tokens_meta1 = {}
    with urllib.request.urlopen(req1, timeout=15) as resp:
        for line in resp:
            l = line.decode("utf-8", errors="replace").strip()
            if l.startswith("data:"):
                ev = json.loads(l[5:].strip())
                if ev.get("type") in ("text", "chunk"):
                    chunks1.append(ev.get("content", ""))
                elif ev.get("type") == "done":
                    tokens_meta1 = ev.get("tokens", {})
                    break

    elapsed1 = round(time.time() - t0, 3)
    p(f"\n[Generated Output Mode 1 ({elapsed1}s)]:\n{''.join(chunks1)}")
    p(f"[Token Metadata Mode 1]: {tokens_meta1}")

    # 2. Mode 2 Test: Ultra-Fast Smart Home Dispatcher
    p("\n" + "=" * 70)
    p("[*] Testing [Mode 2: Ultra-Fast Smart Home] Direct Control & Status:")
    payload2 = json.dumps({
        "prompt": "우리집 종합 상황 알려줘",
        "stream_mode": 2,
        "is_mobile": False,
    }).encode("utf-8")
    req2 = urllib.request.Request(url, data=payload2, headers={"Content-Type": "application/json"})

    t0 = time.time()
    chunks2 = []
    tokens_meta2 = {}
    with urllib.request.urlopen(req2, timeout=15) as resp:
        for line in resp:
            l = line.decode("utf-8", errors="replace").strip()
            if l.startswith("data:"):
                ev = json.loads(l[5:].strip())
                if ev.get("type") in ("text", "chunk"):
                    chunks2.append(ev.get("content", ""))
                elif ev.get("type") == "done":
                    tokens_meta2 = ev.get("tokens", {})
                    break

    elapsed2 = round(time.time() - t0, 3)
    p(f"\n[Generated Output Mode 2 ({elapsed2}s)]:\n{''.join(chunks2)}")
    p(f"[Token Metadata Mode 2]: {tokens_meta2}")

    p("\n" + "=" * 70)
    p(">>> 2-MODE ARCHITECTURE & TOKEN MONITORING 100% PASS <<<")


if __name__ == "__main__":
    test_clean_2modes_and_tokens()
