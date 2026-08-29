#!/usr/bin/env python3
"""Verify /api/status response and coordinator compatibility."""

import json
import sys
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def test_status():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/status"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("[*] /api/status Live Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # Check required keys for sensor.py
        required_keys = ["status", "active_sessions", "uptime", "memory_usage", "cpu_usage"]
        for k in required_keys:
            assert k in data, f"Missing required key: {k}"
            print(f"  ✓ {k}: {data[k]}")
        print("\n>>> SENSOR CONTRACT COMPATIBILITY 100% PASS <<<")


if __name__ == "__main__":
    test_status()
