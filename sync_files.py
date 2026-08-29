#!/usr/bin/env python3
"""Automated Samba Synchronization Script for Home Assistant Addon and Custom Component."""

import os
import sys

SYNC_PAIRS = [
    (
        r"..\custom_components\ha-antigravity-cli\custom_components\antigravity_cli\conversation.py",
        r"\\HOMEASSISTANT\config\custom_components\antigravity_cli\conversation.py",
    ),
    (
        r"..\custom_components\ha-antigravity-cli\custom_components\antigravity_cli\sensor.py",
        r"\\HOMEASSISTANT\config\custom_components\antigravity_cli\sensor.py",
    ),
    (
        r"..\custom_components\ha-antigravity-cli\custom_components\antigravity_cli\coordinator.py",
        r"\\HOMEASSISTANT\config\custom_components\antigravity_cli\coordinator.py",
    ),
    (
        r"..\custom_components\ha-antigravity-cli\custom_components\antigravity_cli\strings.json",
        r"\\HOMEASSISTANT\config\custom_components\antigravity_cli\strings.json",
    ),
    (
        r"..\custom_components\ha-antigravity-cli\custom_components\antigravity_cli\translations\ko.json",
        r"\\HOMEASSISTANT\config\custom_components\antigravity_cli\translations\ko.json",
    ),
    (
        r"addons\antigravity-cli\antigravity_api.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\antigravity_api.py",
    ),
    (
        r"addons\antigravity-cli\run.sh",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\run.sh",
    ),
    (
        r"addons\antigravity-cli\config.yaml",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\config.yaml",
    ),
    (
        r"addons\antigravity-cli\Dockerfile",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\Dockerfile",
    ),
]


def sync():
    count = 0
    for src, dst in SYNC_PAIRS:
        if os.path.exists(src):
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(src, "rb") as f_src:
                    data = f_src.read()
                with open(dst, "wb") as f_dst:
                    f_dst.write(data)
                print(f"[OK] {src} -> {dst}")
                count += 1
            except Exception as e:
                print(f"[ERR] {src} -> {dst}: {e}", file=sys.stderr)
    print(f"Total {count} files synchronized successfully.")


if __name__ == "__main__":
    sync()
