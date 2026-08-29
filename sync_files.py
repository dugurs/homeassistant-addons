#!/usr/bin/env python3
"""Automated Samba Synchronization & Local Gitea Auto-Commit/Push Script."""

import os
import sys
import subprocess

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


def sync_samba():
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
    print(f"Total {count} files synchronized to Samba successfully.")


def git_push_all(msg: str = "auto: Synchronize and push latest updates"):
    # 1. Push homeassistant-addons
    try:
        subprocess.run(["git", "add", "."], cwd=".", check=False)
        subprocess.run(["git", "commit", "-m", msg], cwd=".", check=False)
        res = subprocess.run(["git", "push", "gitea", "main"], cwd=".", capture_output=True, text=True)
        print(f"[Gitea:Addons] {res.stdout.strip() or res.stderr.strip() or 'Up to date'}")
    except Exception as e:
        print(f"[Gitea:Addons ERR] {e}")

    # 2. Push ha-antigravity-cli
    comp_dir = r"..\custom_components\ha-antigravity-cli"
    if os.path.exists(comp_dir):
        try:
            subprocess.run(["git", "add", "."], cwd=comp_dir, check=False)
            subprocess.run(["git", "commit", "-m", msg], cwd=comp_dir, check=False)
            res = subprocess.run(["git", "push", "origin", "main"], cwd=comp_dir, capture_output=True, text=True)
            print(f"[Gitea:Component] {res.stdout.strip() or res.stderr.strip() or 'Up to date'}")
        except Exception as e:
            print(f"[Gitea:Component ERR] {e}")


if __name__ == "__main__":
    commit_msg = sys.argv[1] if len(sys.argv) > 1 else "auto: Synchronize and push latest updates"
    sync_samba()
    git_push_all(commit_msg)
