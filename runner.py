#!/usr/bin/env python3
"""E2E Verification for Web UI chat stream & HTTP Index loading."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def p(msg: str):
    print(msg, flush=True)


def test_ui():
    ha_ip = "192.168.0.14"
    url_index = f"http://{ha_ip}:8000/"
    url_chat = f"http://{ha_ip}:8000/api/chat"

    # 1. Test Index
    p("[*] Step 1: Testing Web UI Index endpoint...")
    req_index = urllib.request.Request(url_index)
    with urllib.request.urlopen(req_index, timeout=5) as resp:
        html = resp.read().decode("utf-8")
        p(f"[PASS] Index loaded: HTTP {resp.status} ({len(html)} bytes)")

    # 2. Test Chat API
    p("\n[*] Step 2: Testing /api/chat stream endpoint with prompt '안녕'...")
    payload = json.dumps({"prompt": "안녕", "is_direct_llm": False, "stream_mode": 3}).encode("utf-8")
    req_chat = urllib.request.Request(url_chat, data=payload, headers={"Content-Type": "application/json"})
    
    t0 = time.time()
    chunks = []
    with urllib.request.urlopen(req_chat, timeout=10) as resp:
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
    p(f"[PASS] Chat stream received in {elapsed}s: '{content}'")
    p("\nALL WEB UI CHAT ENDPOINTS OPERATIONAL!")


if __name__ == "__main__":
    test_ui()
