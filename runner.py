#!/usr/bin/env python3
"""Diagnose agy PTY execution and stream output."""

import json
import urllib.request


def test_ai_chat():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"
    payload = json.dumps({"prompt": "ai 안녕", "is_direct_llm": True}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    print("[*] Testing AI PTY execution with 'ai 안녕'...")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            for line in resp:
                print("SSE:", line.decode("utf-8", errors="replace").strip())
    except Exception as e:
        print("[ERR]", e)


if __name__ == "__main__":
    test_ai_chat()
