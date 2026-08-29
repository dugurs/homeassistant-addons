#!/usr/bin/env python3
"""Test agy CLI commands directly."""

import json
import sys
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def check():
    ha_ip = "192.168.0.14"
    status_url = f"http://{ha_ip}:8000/api/status"
    req = urllib.request.Request(status_url)
    with urllib.request.urlopen(req, timeout=5) as resp:
        st_data = json.loads(resp.read().decode("utf-8"))
        print("[*] CPU & Hardware Status:")
        print(f"  ✓ AVX Supported: {st_data['hw_info']['has_avx']}")
        print(f"  ✓ AVX2 Supported: {st_data['hw_info']['has_avx2']}")
        print(f"  ✓ AES-NI Supported: {st_data['hw_info']['has_aes']}")
        print(f"  ✓ Antigravity Stream Supported: {st_data['agy_stream_supported']}")


if __name__ == "__main__":
    check()
