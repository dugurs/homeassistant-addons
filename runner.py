#!/usr/bin/env python3
"""Check HA logs for antigravity_cli component errors."""

import json
import os
import sys
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def check_logs():
    ha_ip = "192.168.0.14"
    # Read status from addon API to see system stats
    status_url = f"http://{ha_ip}:8000/api/status"
    try:
        req = urllib.request.Request(status_url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[*] Addon /api/status response:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"[!] Error fetching /api/status: {e}")


if __name__ == "__main__":
    check_logs()
