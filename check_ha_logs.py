#!/usr/bin/env python3
"""[로그 진단] 애드온 에러 로그 및 시스템 진단 스크립트."""

import json
import sys
import urllib.request


def check_logs():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"
    print("[*] Fetching Home Assistant error log summary...")
    payload = json.dumps({"prompt": "시스템 에러 로그 확인", "is_direct_llm": False}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            for line in resp:
                l = line.decode("utf-8", errors="replace").strip()
                if l.startswith("data:"):
                    try:
                        ev = json.loads(l[5:].strip())
                        if ev.get("type") in ("text", "chunk"):
                            sys.stdout.buffer.write(ev.get("content", "").encode("utf-8") + b"\n")
                    except Exception:
                        pass
    except Exception as e:
        print(f"[ERR] Log diagnosis error: {e}", file=sys.stderr)


if __name__ == "__main__":
    check_logs()
