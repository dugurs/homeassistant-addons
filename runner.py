#!/usr/bin/env python3
"""Check live Web UI JS from HTTP response."""
import urllib.request, re, subprocess

url = "http://192.168.0.14:8000/"
with urllib.request.urlopen(url) as resp:
    html = resp.read().decode("utf-8")

scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.DOTALL)
print(f"Live scripts found: {len(scripts)}")
for i, s in enumerate(scripts):
    with open("temp_script.js", "w", encoding="utf-8") as f:
        f.write(s)
    res = subprocess.run(["node", "--check", "temp_script.js"], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"Live Script {i}: JS SYNTAX 100% VALID (PASS)")
    else:
        print(f"Live Script {i}: JS SYNTAX ERROR:\n{res.stderr}")
