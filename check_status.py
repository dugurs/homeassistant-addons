#!/usr/bin/env python3
"""[상태 점검] Home Assistant 애드온 상태, 시스템 리소스, 포트(8000/7681) 헬스체크 스크립트."""

import json
import urllib.request
import sys


def check():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/status"
    print(f"[*] Checking Antigravity CLI Add-on Status at {url}...")
    try:
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[OK] Add-on Status : {data.get('status')} (v{data.get('version')})")
            print(f"[OK] RAM Usage     : {data.get('addon_memory_mb')} MB (CPU {data.get('cpu_usage')}%)")
            print(f"[OK] Total Host RAM: {data.get('used_memory_gb')} GB / {data.get('total_memory_gb')} GB ({data.get('memory_percent')}%)")
            print(f"[OK] Tmux Sessions : {data.get('active_sessions')}")
            print(f"[OK] Uptime        : {data.get('uptime')}s")
    except Exception as e:
        print(f"[ERR] Failed to connect to add-on: {e}", file=sys.stderr)


if __name__ == "__main__":
    check()
