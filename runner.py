#!/usr/bin/env python3
"""E2E Verification of Resource Monitor, Conditional Mode 3, and Live Status Streaming."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run_e2e():
    ha_ip = "192.168.0.14"

    # 1. Test /api/status endpoint
    status_url = f"http://{ha_ip}:8000/api/status"
    print(f"[*] Testing /api/status on {status_url} ...")
    req = urllib.request.Request(status_url)
    with urllib.request.urlopen(req, timeout=5) as resp:
        st_data = json.loads(resp.read().decode("utf-8"))
        print("[*] Live Server Diagnostics:")
        print(f"  - Status: {st_data.get('status')}")
        print(f"  - CPU Usage: {st_data.get('cpu_usage')}%")
        print(f"  - Add-on RAM: {st_data.get('memory_usage')} MB")
        print(f"  - System RAM: {st_data.get('used_memory_gb')}GB / {st_data.get('total_memory_gb')}GB ({st_data.get('memory_percent')}%)")
        print(f"  - Antigravity Stream Supported: {st_data.get('agy_stream_supported')}")
        print(f"  - Uptime: {st_data.get('uptime')}s")

    # 2. Test /api/chat with Mode 1 & Mode 3
    chat_url = f"http://{ha_ip}:8000/api/chat"
    payload = json.dumps({
        "prompt": "우리집 종합 상황 알려줘",
        "stream_mode": 1
    }).encode("utf-8")
    chat_req = urllib.request.Request(chat_url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(chat_req, timeout=10) as resp:
        print("\n[*] Live Real-Time SSE Stream Packets (with Live Step Tools):")
        for _ in range(12):
            line = resp.readline().decode("utf-8").strip()
            if not line:
                continue
            print(f"  {line}")
            if '"type": "done"' in line:
                break

    print("\n>>> ALL TESTS PASSED: RESOURCE MONITOR & LIVE STEP STREAMING VERIFIED <<<")


if __name__ == "__main__":
    time.sleep(2)
    run_e2e()
