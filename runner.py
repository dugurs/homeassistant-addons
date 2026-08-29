#!/usr/bin/env python3
"""Run live test of agy headless streaming CLI."""

import json
import sys
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run_test():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/test_stream"
    print(f"[*] Querying live agy headless test endpoint: {url} ...")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("[*] Diagnostic Test Result:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"[!] Error during test: {e}")


if __name__ == "__main__":
    run_test()
