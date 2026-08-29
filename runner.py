#!/usr/bin/env python3
import json
import sys
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ha_ip = "192.168.0.14"
url = f"http://{ha_ip}:8000/api/test_stream"
print(f"[*] Calling {url} ...", flush=True)

try:
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(json.dumps(data, indent=2, ensure_ascii=False), flush=True)
except Exception as e:
    print(f"[!] Error: {e}", flush=True)
