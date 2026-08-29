#!/usr/bin/env python3
"""Inspect HA states to build a comprehensive, rich system summary."""

import json
import urllib.request


def inspect_states():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/status"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=3) as resp:
        print("Add-on status:", resp.read().decode("utf-8"))


if __name__ == "__main__":
    inspect_states()
