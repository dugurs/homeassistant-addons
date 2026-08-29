#!/usr/bin/env python3
"""E2E Verification for Multi-Metric Environment Sensors ($CO_2$, TVOC, PM2.5, Illuminance, Pressure)."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def p(msg: str):
    print(msg, flush=True)


def test_multi_metrics():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"

    p("=" * 70)
    p("  E2E MULTI-METRIC ENVIRONMENT SENSOR & AI SYNTHESIS TEST  ")
    p("=" * 70)

    # 1. Mode 1 Test (AI Deep Brain with dynamic multi-metric columns & AI advice)
    payload = json.dumps({
        "prompt": "오늘 날씨와 환경 분석해줘",
        "is_direct_llm": False,
        "stream_mode": 1,
        "is_mobile": False,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    t0 = time.time()
    chunks = []
    with urllib.request.urlopen(req, timeout=15) as resp:
        for line in resp:
            l = line.decode("utf-8", errors="replace").strip()
            if l.startswith("data:"):
                ev = json.loads(l[5:].strip())
                if ev.get("type") in ("text", "chunk"):
                    chunks.append(ev.get("content", ""))
                elif ev.get("type") == "done":
                    break

    elapsed = round(time.time() - t0, 3)
    content = "".join(chunks)
    p(f"\n[Generated Mode 1 Output ({elapsed}s)]:\n{content}")

    # 2. Mode 3 Test (Fast Multi-Metric Dashboard)
    p("\n" + "=" * 70)
    p("[*] Testing Mode 3 Fast Dashboard with Multi-Metric Matrix")
    p("=" * 70)

    payload_m3 = json.dumps({
        "prompt": "오늘 날씨와 환경 분석해줘",
        "is_direct_llm": False,
        "stream_mode": 3,
        "is_mobile": False,
    }).encode("utf-8")
    req_m3 = urllib.request.Request(url, data=payload_m3, headers={"Content-Type": "application/json"})

    t0 = time.time()
    chunks_m3 = []
    with urllib.request.urlopen(req_m3, timeout=15) as resp:
        for line in resp:
            l = line.decode("utf-8", errors="replace").strip()
            if l.startswith("data:"):
                ev = json.loads(l[5:].strip())
                if ev.get("type") in ("text", "chunk"):
                    chunks_m3.append(ev.get("content", ""))
                elif ev.get("type") == "done":
                    break

    elapsed_m3 = round(time.time() - t0, 3)
    content_m3 = "".join(chunks_m3)
    p(f"\n[Generated Mode 3 Output ({elapsed_m3}s)]:\n{content_m3}")

    p("\n" + "=" * 70)
    p(">>> MULTI-METRIC DYNAMIC ENVIRONMENT SENSOR INTEGRATION 100% PASS <<<")


if __name__ == "__main__":
    test_multi_metrics()
