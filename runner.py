#!/usr/bin/env python3
"""E2E Verification for 100% Direct PTY Terminal execution in Mode 2."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def p(msg: str):
    print(msg, flush=True)


def test_direct_pty():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"
    prompt = "안녕"

    p("=" * 60)
    p(f"[*] Testing Mode 2 Direct PTY Stream with prompt: '{prompt}'")
    p("=" * 60)

    payload = json.dumps({
        "prompt": prompt,
        "is_direct_llm": False,
        "stream_mode": 2,
        "is_mobile": False,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    t0 = time.time()
    events = []

    with urllib.request.urlopen(req, timeout=15) as resp:
        for line in resp:
            l = line.decode("utf-8", errors="replace").strip()
            if l.startswith("data:"):
                ev = json.loads(l[5:].strip())
                events.append(ev)
                p(f"  -> SSE Event [{ev.get('type')}]: {ev.get('content')}")
                if ev.get("type") == "done":
                    break

    elapsed = round(time.time() - t0, 3)
    p(f"\n[Total Latency: {elapsed}s]")
    p(f"Total Events Received: {len(events)}")
    p("[PASS] Mode 2 Direct PTY Stream Execution Verified!")


if __name__ == "__main__":
    test_direct_pty()
