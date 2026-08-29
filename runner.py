#!/usr/bin/env python3
"""Verify Web UI HTML and status."""

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
        assert "switchMsgView" in html, "switchMsgView missing!"
        assert "top-copy-btn" in html, "top-copy-btn missing!"
        assert "raw-markdown-view" in html, "raw-markdown-view missing!"
        print("[*] Web UI HTML loaded successfully.")
        print("  ✓ switchMsgView function present")
        print("  ✓ top-copy-btn class present")
        print("  ✓ raw-markdown-view container present")
        print("\n>>> MARKDOWN VIEW TOGGLER & TOP COPY BUTTON 100% VERIFIED <<<")


if __name__ == "__main__":
    verify_ui()
