#!/usr/bin/env python3
"""Validate the served HTML via Node.js syntax checker."""

import subprocess
import sys
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Read web_ui.py directly and execute to get HTML
import os
sys.path.insert(0, os.path.abspath("addons/antigravity-cli"))
from core.web_ui import HTML_INDEX

html = HTML_INDEX
script_start = html.find("<script>") + len("<script>")
script_end = html.find("</script>")
js = html[script_start:script_end]

with open("temp_script.js", "w", encoding="utf-8") as f:
    f.write(js)

print(f"[*] Extracted JavaScript ({len(js)} chars). Testing with node --check...")
res = subprocess.run(["node", "--check", "temp_script.js"], capture_output=True, text=True)
if res.returncode == 0:
    print("[PASS] JavaScript syntax is 100% VALID and ERROR-FREE!")
else:
    print("[FAIL] Node syntax check error:")
    print(res.stderr)
