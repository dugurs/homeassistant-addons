#!/usr/bin/env python3
"""E2E Verification for Mode 2 Responsive Terminal Markdown (Mobile vs Desktop)."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def p(msg: str):
    print(msg, flush=True)


def test_mode2_viewport(is_mobile: bool):
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"
    mode_name = "Mobile (<768px)" if is_mobile else "Desktop (>=768px)"
    prompt = "오늘 날씨와 환경 분석해줘"

    p(f"\n========================================================")
    p(f"[*] Testing Mode 2 PTY Stream under [{mode_name}] Viewport")
    p(f"========================================================")

    payload = json.dumps({
        "prompt": prompt,
        "is_direct_llm": False,
        "stream_mode": 2,
        "is_mobile": is_mobile,
        "client_width": 375 if is_mobile else 1280
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    t0 = time.time()
    chunks = []

    with urllib.request.urlopen(req, timeout=10) as resp:
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
    p(f"[Latency: {elapsed}s]")
    p("--- [Rendered Output Preview] ---")
    p(content)

    if is_mobile:
        pass_mobile = "MOBILE MONITOR" in content
        p(f"\n• Mode 2 Mobile Compact Table Verification: {'YES [PASS]' if pass_mobile else 'NO [FAIL]'}")
        return pass_mobile
    else:
        pass_desktop = "ENVIRONMENT MONITOR" in content and "HOST RAM" in content
        p(f"\n• Mode 2 Desktop Full Grid Verification  : {'YES [PASS]' if pass_desktop else 'NO [FAIL]'}")
        return pass_desktop


def main():
    p("[Mode 2 Responsive Terminal Viewport Verification Suite Starting]...")
    res_desktop = test_mode2_viewport(is_mobile=False)
    res_mobile = test_mode2_viewport(is_mobile=True)

    p("\n" + "=" * 60)
    p(f"MODE 2 RESPONSIVE RESULT: {'ALL PASSED [PASS]' if res_desktop and res_mobile else 'FAILED [FAIL]'}")


if __name__ == "__main__":
    main()
