#!/usr/bin/env python3
"""Verify dynamic rooms and dynamic AI recommendations."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def p(msg: str):
    print(msg, flush=True)


def test_dynamic():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"

    # Test Mode 1 (AI Deep Brain with dynamic rooms and dynamic advice)
    p("=" * 70)
    p("[*] Testing Mode 1 AI Deep Brain Dynamic Recommendations")
    p("=" * 70)

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
    p(f"\n[Generated Output ({elapsed}s)]:\n{content}")


if __name__ == "__main__":
    test_dynamic()
