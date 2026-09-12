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
        # NOTE: this flag bypasses agy's whole permissions.allow/deny engine
        # (settings.json, sourced from bundled/hooks/deny_rules.json) -- a
        # global agy behavior, not Mode-3-specific, confirmed by asking the
        # Antigravity agent itself to read its own binary's permission-
        # matching code. So editing deny_rules.json does NOT protect this
        # remote-control session while dangerous_mode stays on (the
        # deliberate choice here -- turning it off would leave remote tool
        # calls hanging forever on an approval prompt nothing can answer).
        # What DOES still protect HA-critical files here, unconditionally,
        # is the PreToolUse hook (bundled/hooks/ha_file_guard.py) -- hooks
        # fire regardless of this flag, per antigravity.google/docs/hooks/.
        cmd.append("--dangerously-skip-permissions")

    env = os.environ.copy()
    env["HOME"] = "/root"
    env["USER"] = "root"
    # Go runtime memory optimization: aggressive GC and memory limit
    env["GOMEMLIMIT"] = "384MiB"
    env["GOGC"] = "50"

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


def _daemon_log_path(pid: int):
    """Find the daemon's own cli-*.log by inspecting its open file
    descriptors (/proc/<pid>/fd) -- NOT by picking "whatever cli-*.log has
    the newest mtime", since any other agy invocation (a chat prompt, a
    hardware check) writes its own cli-*.log to the same directory and
    would otherwise be picked up by mistake. Confirmed via live
    investigation: agy's own logging redirects fd 1/2 to this exact file
    once its logger initializes."""
    try:
        fd_dir = f"/proc/{pid}/fd"
        for fd in os.listdir(fd_dir):
            target = os.readlink(os.path.join(fd_dir, fd))
            if "/log/cli-" in target:
                return target
    except Exception:
        pass
    return None


_BUSY_WINDOW_SEC = 20

_BRAIN_DIR_CANDIDATES = [
    "/root/.gemini/antigravity-cli/brain",
    "/config/.gemini/antigravity-cli/brain",
]


def _log_has_recent_pattern(log_path: str, patterns: list, window_sec: int) -> bool:
    """Whether `log_path` was modified within the last `window_sec` seconds
    AND its tail contains one of `patterns`. The recency check first is
    what keeps this from reporting "busy" forever just because the
    pattern appeared once, long ago."""
    try:
        if time.time() - os.path.getmtime(log_path) > window_sec:
            return False
        with open(log_path, "r", errors="replace") as f:
            tail = f.readlines()[-50:]
    except Exception:
        return False
    return any(p in ln for ln in tail for p in patterns)


def _active_brain_transcript(window_sec: int):
    """Most recently modified brain/<conversation-id>/.../transcript.jsonl,
    if it was touched within `window_sec` seconds. Confirmed by asking the
    Antigravity agent itself: this is the most reliable place to see an
    in-flight tool call (a `tool_calls` entry with no matching result line
    yet). Using "most recently modified" rather than resolving the exact
    remote-control conversation id is a deliberate simplification that
    only holds because this addon's only long-lived agy session is the
    remote-control daemon -- every other invocation (a chat prompt, a
    hardware check) is short-lived and exits well before its transcript
    could be mistaken for "currently active" under this same recency
    window.
    """
    brain_root = next((d for d in _BRAIN_DIR_CANDIDATES if os.path.isdir(d)), None)
    if not brain_root:
        return None
    best, best_mtime = None, 0
    try:
        for name in os.listdir(brain_root):
            transcript = os.path.join(brain_root, name, ".system_generated", "logs", "transcript.jsonl")
            if os.path.isfile(transcript):
                mtime = os.path.getmtime(transcript)
                if mtime > best_mtime:
                    best_mtime, best = mtime, transcript
    except Exception:
        return None
    if best and (time.time() - best_mtime) <= window_sec:
        return best
    return None


def is_busy() -> dict:
    """Best-effort "is the daemon actively generating a response or
    running a file-write tool right now" check, used to lock the stop
    button.

    Confirmed live (see CHANGELOG) that `write_to_file`/
    `replace_file_content` write directly to the target file -- no
    temp-file+rename step -- so a SIGKILL mid-write can leave a
    truncated/corrupted file. Neither signal below is an official API;
    both are inferred from log content within a short recency window, so
    this can have false positives (stays "busy" briefly after activity
    actually ended) but is deliberately biased against false negatives
    (never reporting "safe to stop" while a write might still be in
    flight).
    """
    if not is_running():
        return {
            "busy": False,
            "reason": None,
            "activity_state": "stopped",
            "current_tool": None,
            "target_file": None,
        }

    # 1. Check in-flight chat stream in streamer if present
    try:
        from core.streamer import _RUNNING_STREAMS, _RUNNING_STREAMS_LOCK
        with _RUNNING_STREAMS_LOCK:
            if _RUNNING_STREAMS:
                return {
                    "busy": True,
                    "reason": "chat_generating",
                    "activity_state": "thinking",
                    "current_tool": None,
                    "target_file": None,
                }
    except Exception:
        pass

    # 2. Check active transcript in brain directory
    transcript = _active_brain_transcript(_BUSY_WINDOW_SEC)
    if transcript:
        try:
            with open(transcript, "r", errors="replace") as f:
                lines = [ln.strip() for ln in f.readlines()[-10:] if ln.strip()]
            for ln in reversed(lines):
                try:
                    data = json.loads(ln)
                except Exception:
                    continue

                tool_calls = data.get("tool_calls") or []
                if tool_calls and isinstance(tool_calls, list):
                    tc = tool_calls[0]
                    tname = tc.get("name") or tc.get("tool_name", "")
                    args = tc.get("args") or tc.get("arguments") or {}
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {}
                    target_file = (
                        args.get("TargetFile")
                        or args.get("target_file")
                        or args.get("AbsolutePath")
                        or args.get("file_path")
                    )
                    base_name = os.path.basename(target_file) if target_file else None
                    if tname in ("replace_file_content", "write_to_file"):
                        return {
                            "busy": True,
                            "reason": "writing_file",
                            "activity_state": "file_working",
                            "current_tool": tname,
                            "target_file": base_name,
                        }
                    return {
                        "busy": True,
                        "reason": f"running_tool:{tname}",
                        "activity_state": "executing_tool",
                        "current_tool": tname,
                        "target_file": base_name,
                    }

                thinking = data.get("thinking")
                if thinking or data.get("type") == "PLANNER_RESPONSE":
                    return {
                        "busy": True,
                        "reason": "generating",
                        "activity_state": "thinking",
                        "current_tool": None,
                        "target_file": None,
                    }
        except Exception:
            pass

    # 3. Check daemon's own log for generation activity
    pid = _read_pid()
    log_path = _daemon_log_path(pid)
    if log_path and _log_has_recent_pattern(log_path, ["streamGenerateContent"], _BUSY_WINDOW_SEC):
        return {
            "busy": True,
            "reason": "generating",
            "activity_state": "thinking",
            "current_tool": None,
            "target_file": None,
        }

    return {
        "busy": False,
        "reason": None,
        "activity_state": "idle",
        "current_tool": None,
        "target_file": None,
    }


def get_activity_status() -> dict:
    """Return structured activity status for HA integration and Web UI."""
    info = is_busy()
    return {
        "state": info.get("activity_state", "idle" if is_running() else "stopped"),
        "is_busy": info.get("busy", False),
        "reason": info.get("reason"),
        "current_tool": info.get("current_tool"),
        "target_file": info.get("target_file"),
    }


def status_detail() -> dict:
    """Best-effort remote-control status.

    `agy remote-control status` itself is not useful here: confirmed live
    that its "Daemon status:" field shells out to `systemctl --user`
    internally, which doesn't exist in this container, so it always comes
    back empty (still returned as `raw` since it does carry the instance
    name). The actually useful signal -- whether the daemon's connection
    to the web dashboard is up -- comes from tailing its own cli-*.log for
    the "Connection status: <value>" line it writes on
    connect/reconnect/disconnect (there is no other documented API for
    this; see CHANGELOG for how this was confirmed).
    """
    if not is_running():
        return {"running": False, "raw": None, "connection_status": None}

    pid = _read_pid()
    try:
        p = subprocess.run(
            [_AGY_BIN, "remote-control", "status"],
            capture_output=True, text=True, timeout=5, errors="replace",
        )
        raw = (p.stdout or p.stderr).strip()
    except Exception:
        raw = None

    connection_status = None
    log_path = _daemon_log_path(pid)
    if log_path:
        try:
            with open(log_path, "r", errors="replace") as f:
                for line in f:
                    if "Connection status:" in line:
                        connection_status = line.split("Connection status:", 1)[1].strip()
        except Exception:
            pass

    busy = is_busy()
    return {
        "running": True, "raw": raw, "connection_status": connection_status,
        "busy": busy["busy"], "busy_reason": busy["reason"],
        "activity_state": busy.get("activity_state"),
        "current_tool": busy.get("current_tool"),
        "target_file": busy.get("target_file"),
    }


def stop() -> dict:
    pid = _read_pid()
    if pid is None or not _pid_alive(pid):
        try:
            os.remove(_PID_FILE)
        except Exception:
            pass
        return {"ok": True, "running": False, "was_running": False}

    busy = is_busy()
    if busy["busy"]:
        return {
            "ok": False,
            "running": True,
            "error": "busy",
            "busy_reason": busy["reason"],
            "activity_state": busy.get("activity_state"),
            "current_tool": busy.get("current_tool"),
            "target_file": busy.get("target_file"),
            "message": f"에이전트가 현재 {busy.get('activity_state', '작업')} 중입니다. 파일 및 데이터 손상을 방지하기 위해 정지가 잠겨 있습니다.",
        }

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
