#!/usr/bin/env python3
"""E2E Verification for 3 Modes following Pipeline Implementation Plan."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def p(msg: str):
    print(msg, flush=True)


def test_mode(mode_num: int, prompt: str, is_mobile: bool = False):
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"

    p("\n" + "=" * 65)
    p(f"[*] Testing [Mode {mode_num}] with prompt: '{prompt}' (is_mobile={is_mobile})")
    p("=" * 65)

    payload = json.dumps({
        "prompt": prompt,
        "is_direct_llm": False,
        "stream_mode": mode_num,
        "is_mobile": is_mobile,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    t0 = time.time()
    tools = []
    chunks = []

    with urllib.request.urlopen(req, timeout=15) as resp:
        for line in resp:
            l = line.decode("utf-8", errors="replace").strip()
            if l.startswith("data:"):
                ev = json.loads(l[5:].strip())
                etype = ev.get("type")
                if etype == "tool":
                    tools.append(ev.get("content", ""))
                    p(f"  [TOOL] {ev.get('content')}")
                elif etype in ("text", "chunk"):
                    chunks.append(ev.get("content", ""))
                elif etype == "done":
                    break

    elapsed = round(time.time() - t0, 3)
    content = "".join(chunks)
    p(f"\n[Response Content Preview]:\n{content}")
    p(f"[Latency: {elapsed}s | Tools: {len(tools)} | Content Chars: {len(content)}]")
    return len(content) > 0


def main():
    p("=" * 65)
    p("       E2E PIPELINE SYSTEMATIC VERIFICATION SUITE       ")
    p("=" * 65)

    # 1. Mode 2: Direct prompt "뭘 할수 있니?"
    res_m2 = test_mode(2, "뭘 할수 있니?")

    # 2. Mode 1: AI Deep Brain
    res_m1 = test_mode(1, "오늘 날씨와 환경 분석해줘")

    # 3. Mode 3: Fast Native
    res_m3 = test_mode(3, "오늘 날씨와 환경 분석해줘")

    p("\n" + "=" * 65)
    if res_m1 and res_m2 and res_m3:
        p(">>> ALL 3 PIPELINE MODES FULLY VERIFIED & OPERATIONAL! [PASS] <<<")
    else:
        p(">>> VERIFICATION FAILED [FAIL] <<<")


if __name__ == "__main__":
    main()
