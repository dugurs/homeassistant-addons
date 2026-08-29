#!/usr/bin/env python3
"""Verify clean Web UI HTML without tool-box."""

import sys
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def verify_ui():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as resp:
        html = resp.read().decode("utf-8")
        assert "tool-box" not in html, "tool-box still present in HTML template!"
        assert "mode-badge" in html, "mode-badge missing from HTML template!"
        print("[*] Web UI HTML Clean Verification:")
        print("  ✓ tool-box completely removed")
        print("  ✓ mode-badge present")
        print("\n>>> CLEAN BUBBLE HEADER 100% VERIFIED <<<")


if __name__ == "__main__":
    verify_ui()
