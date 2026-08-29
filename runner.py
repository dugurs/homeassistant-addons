#!/usr/bin/env python3
"""Find all brain and transcript directories in the add-on container."""

import json
import urllib.request


def check():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/status"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=3) as resp:
        print("Status:", resp.read().decode("utf-8"))


if __name__ == "__main__":
    check()
