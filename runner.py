#!/usr/bin/env python3
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("H: exists:", os.path.exists(r"H:\custom_components"), flush=True)
print("I: exists:", os.path.exists(r"I:\antigravity-cli"), flush=True)
