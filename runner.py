#!/usr/bin/env python3
"""Inspect agy help and flags inside the add-on container."""

import json
import urllib.request


def check_agy():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"
    # We can inspect via runner if needed, or query status
    req = urllib.request.Request(f"http://{ha_ip}:8000/api/status")
    with urllib.request.urlopen(req, timeout=3) as resp:
        print(resp.read().decode("utf-8"))


if __name__ == "__main__":
    check_agy()
