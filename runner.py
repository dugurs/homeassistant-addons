#!/usr/bin/env python3
"""Read final steps of smart home query conversation."""
import os, glob, sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

base_dir = r"\\HOMEASSISTANT\addon_configs\local_antigravity-cli\.gemini\antigravity-cli\brain"
convs = sorted(os.listdir(base_dir), key=lambda d: os.path.getmtime(os.path.join(base_dir, d)))
latest = os.path.join(base_dir, convs[-1])
print(f"Latest conv: {convs[-1]}")

tpath = os.path.join(latest, ".system_generated", "logs", "chunks", "transcript", "00000000.jsonl")
if os.path.exists(tpath):
    with open(tpath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        print(f"Total steps: {len(lines)}")
        for i in range(max(0, len(lines)-10), len(lines)):
            print(f"Step {i}: {lines[i][:300]}")
