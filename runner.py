#!/usr/bin/env python3
"""Diagnose agy execution inside the add-on container."""

import json
import urllib.request


def check_direct():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"
    # Send a prompt to see stdout in Mode 2 (PTY)
    payload = json.dumps({"prompt": "오늘 날씨와 환경 분석해줘", "is_direct_llm": False, "stream_mode": 3}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        for line in resp:
            print(line.decode("utf-8", errors="replace").strip())


if __name__ == "__main__":
    check_direct()
