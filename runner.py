#!/usr/bin/env python3
"""Validate modular Web UI JS syntax."""
import os, sys, re, subprocess

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "addons", "antigravity-cli"))

from core.web_ui import HTML_INDEX

scripts = re.findall(r"<script>(.*?)</script>", HTML_INDEX, flags=re.DOTALL)
print(f"Found {len(scripts)} script blocks. Total HTML size: {len(HTML_INDEX)} bytes.")

for i, s in enumerate(scripts):
    with open("temp_script.js", "w", encoding="utf-8") as f:
        f.write(s)
    res = subprocess.run(["node", "--check", "temp_script.js"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode == 0:
        print(f"Script {i}: JS SYNTAX 100% VALID (PASS)")
    else:
        print(f"Script {i}: JS SYNTAX ERROR:\n{res.stderr}")
