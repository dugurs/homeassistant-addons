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
        r"addons\antigravity-cli\core\__init__.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\__init__.py",
    ),
    (
        r"addons\antigravity-cli\core\system_info.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\system_info.py",
    ),
    (
        r"addons\antigravity-cli\core\ha_client.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\ha_client.py",
    ),
    (
        r"addons\antigravity-cli\core\sensors.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\sensors.py",
    ),
    (
        r"addons\antigravity-cli\core\renderers.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\renderers.py",
    ),
    (
        r"addons\antigravity-cli\core\web_ui.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\web_ui.py",
    ),
    (
        r"addons\antigravity-cli\core\ui\__init__.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\ui\__init__.py",
    ),
    (
        r"addons\antigravity-cli\core\ui\styles.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\ui\styles.py",
    ),
    (
        r"addons\antigravity-cli\core\ui\templates.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\ui\templates.py",
    ),
    (
        r"addons\antigravity-cli\core\ui\scripts.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\ui\scripts.py",
    ),
    (
        r"addons\antigravity-cli\core\ha_engine.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\ha_engine.py",
    ),
    (
        r"addons\antigravity-cli\core\streamer.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\streamer.py",
    ),
    (
        r"addons\antigravity-cli\core\markdown_parser.py",
        r"\\HOMEASSISTANT\local_apps\antigravity-cli\core\markdown_parser.py",
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


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


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
                print(f"[OK] {src} -> {dst}", flush=True)
                count += 1
            except Exception as e:
                print(f"[ERR] {src} -> {dst}: {e}", file=sys.stderr, flush=True)
    print(f"Total {count} files synchronized to Samba successfully.", flush=True)


def generate_meaningful_commit_msg() -> str:
    """Generate a concise, high-level summary of the core work done."""
    try:
        res = subprocess.run(["git", "diff", "--name-only", "HEAD~1"], capture_output=True, text=True, check=False)
        st_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=False)
        lines = [l.strip() for l in (res.stdout + "\n" + st_res.stdout).splitlines() if l.strip()]
        files = list(set([l.split()[-1] for l in lines]))
        
        # Summarize core task achievements
        if any("session" in f for f in files):
            return "feat: conversation_id 기반 대화 세션 지속(Resume) 및 다중 모드 통합 체계 구축 (#2)"
        elif any("conversation.py" in f for f in files):
            return "feat: Home Assistant 어시스턴트 대화(Conversation) 파이프라인 연동 개선"
        elif any("web_ui" in f or "templates" in f or "styles" in f for f in files):
            return "feat: 웹 UI 다크모드 및 반응형 대시보드 레이아웃 개선"
        elif any("ha_client" in f or "sensors" in f or "streamer" in f for f in files):
            return "feat: 실시간 SSE 스트리밍 및 초고속 스마트홈 기기 제어 엔진 개선"
        elif any("COMMUNICATION_SPEC" in f or "AGENTS.md" in f or "GEMINI.md" in f for f in files):
            return "docs: 통신 규격서 및 하네스 운영 규칙 동기화"
        else:
            return "refactor: 애드온 및 통합구성요소 기능 개선 및 동기화"
    except Exception:
        return "feat: 애드온 기능 업데이트 및 동기화"


def git_push_all(msg: str = None):
    if not msg:
        msg = generate_meaningful_commit_msg()
    # 1. Push homeassistant-addons
    try:
        subprocess.run(["git", "add", "."], cwd=".", check=False, timeout=10)
        subprocess.run(["git", "commit", "-m", msg], cwd=".", check=False, timeout=10)
        res = subprocess.run(["git", "push", "gitea", "main"], cwd=".", capture_output=True, text=True, timeout=10)
        print(f"[Gitea:Addons] ({msg}) -> {res.stdout.strip() or res.stderr.strip() or 'Up to date'}")
    except Exception as e:
        print(f"[Gitea:Addons ERR] {e}")

    # 2. Push ha-antigravity-cli
    comp_dir = r"..\custom_components\ha-antigravity-cli"
    if os.path.exists(comp_dir):
        try:
            subprocess.run(["git", "add", "."], cwd=comp_dir, check=False, timeout=10)
            subprocess.run(["git", "commit", "-m", msg], cwd=comp_dir, check=False, timeout=10)
            res = subprocess.run(["git", "push", "origin", "main"], cwd=comp_dir, capture_output=True, text=True, timeout=10)
            print(f"[Gitea:Component] ({msg}) -> {res.stdout.strip() or res.stderr.strip() or 'Up to date'}")
        except Exception as e:
            print(f"[Gitea:Component ERR] {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Synchronize files to Samba and optionally push to Gitea.")
    parser.add_argument("--push", action="store_true", help="Push changes to Gitea remote repository")
    parser.add_argument("-m", "--message", default=None, help="Git commit message")
    args = parser.parse_args()

    sync_samba()
    if args.push:
        git_push_all(args.message)
    else:
        print("[INFO] Samba sync completed. (Gitea push skipped - use --push to commit & push)")
