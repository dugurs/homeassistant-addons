#!/usr/bin/env python3
"""Verify exact room humidity extraction without battery values or '약' prefixes."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def p(msg: str):
    print(msg, flush=True)


def test_humidity():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"
    prompt = "각 방 습도 알려줘"
    p(f"\n[*] Testing Prompt: '{prompt}' on Mode 3 (Fast)...")

    payload = json.dumps({"prompt": prompt, "is_direct_llm": False, "stream_mode": 3}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    content = ""
    with urllib.request.urlopen(req, timeout=10) as resp:
        for line in resp:
            l = line.decode("utf-8", errors="replace").strip()
            if l.startswith("data:"):
                ev = json.loads(l[5:].strip())
                if ev.get("type") in ("text", "chunk"):
                    content += ev.get("content", "")
                elif ev.get("type") == "done":
                    break

    p("--- [Result Output] ---")
    p(content)

    p("\n--- [Accuracy Verification] ---")
    has_100 = "100%" in content
    has_approx = "약" in content
    p(f"• Contains 100% (Suspicious Battery Value): {'YES [FAIL]' if has_100 else 'NO [PASS]'}")
    p(f"• Contains '약' Prefix                   : {'YES [FAIL]' if has_approx else 'NO [PASS]'}")

    if not has_100 and not has_approx:
        p("\nHUMIDITY ACCURACY TEST PASSED PERFECTLY!")
    else:
        p("\nHUMIDITY TEST FAILED!")


if __name__ == "__main__":
    test_humidity()
