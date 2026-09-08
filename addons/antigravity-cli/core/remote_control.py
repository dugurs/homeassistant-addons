"""Start/stop/status control for the `agy remote-control serve` daemon.

Tracked by a PID file (rather than a `pgrep`-style name match) so start/
stop/status all agree on exactly which process is "the" daemon, even if
some unrelated `agy` invocation happens to be running at the same time.
Both the web UI toggle and the HA integration's switch entity go through
these three functions via the REST endpoints in antigravity_api.py.
"""

import json
import os
import signal
import subprocess
import time

_PID_FILE = "/data/antigravity_remote_control.pid"
_LOG_FILE = "/data/antigravity_remote_control.log"
_AGY_BIN = "/usr/local/bin/agy"


def _read_dangerous_mode() -> bool:
    """Same addon-config flag (default on) that gates the chat headless
    path in core/streamer.py -- kept as a single shared setting so the
    daemon and chat never disagree on whether prompts are auto-approved."""
    if os.path.exists("/data/options.json"):
        try:
            with open("/data/options.json", "r") as f:
                return bool(json.load(f).get("dangerous_mode", True))
        except Exception:
            pass
    return True


def _read_pid():
    if not os.path.exists(_PID_FILE):
        return None
    try:
        with open(_PID_FILE, "r") as f:
            return int(f.read().strip())
    except Exception:
        return None


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def is_running() -> bool:
    pid = _read_pid()
    if pid is None:
        return False
    if _pid_alive(pid):
        return True
    # Stale PID file left behind by a crashed/killed process -- clear it so
    # the next check doesn't keep reporting a dead process as running.
    try:
        os.remove(_PID_FILE)
    except Exception:
        pass
    return False


def start() -> dict:
    if is_running():
        return {"ok": True, "running": True, "already_running": True, "pid": _read_pid()}

    if not os.path.exists(_AGY_BIN):
        return {"ok": False, "running": False, "error": f"agy binary not found at {_AGY_BIN}"}

    cmd = [_AGY_BIN, "remote-control", "serve"]
    if _read_dangerous_mode():
        cmd.append("--dangerously-skip-permissions")

    env = os.environ.copy()
    env["HOME"] = "/root"
    env["USER"] = "root"

    try:
        with open(_LOG_FILE, "a") as log:
            proc = subprocess.Popen(
                cmd, stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                env=env, start_new_session=True,
            )
    except Exception as ex:
        return {"ok": False, "running": False, "error": str(ex)}

    with open(_PID_FILE, "w") as f:
        f.write(str(proc.pid))

    return {"ok": True, "running": True, "already_running": False, "pid": proc.pid}


def stop() -> dict:
    pid = _read_pid()
    if pid is None or not _pid_alive(pid):
        try:
            os.remove(_PID_FILE)
        except Exception:
            pass
        return {"ok": True, "running": False, "was_running": False}

    try:
        os.kill(pid, signal.SIGTERM)
    except Exception as ex:
        return {"ok": False, "running": is_running(), "error": str(ex)}

    for _ in range(20):
        if not _pid_alive(pid):
            break
        time.sleep(0.2)
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass

    try:
        os.remove(_PID_FILE)
    except Exception:
        pass
    return {"ok": True, "running": False, "was_running": True}
