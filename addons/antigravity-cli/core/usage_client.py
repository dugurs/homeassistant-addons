"""Non-interactive Antigravity quota (/usage) client for Mode 3.

agy v1.1.11 added non-interactive answers for read-only slash commands in
print mode -- `agy -p "/usage"` (alias `/quota`) returns a report "without
starting an agent turn, spending quota, or leaving a conversation behind",
emitting "one tab-separated record per line". The official docs
(antigravity.google/docs/cli/commands/usage/) describe the interactive TUI
panel's *content* (per-model weekly/5-hour remaining) but not this
print-mode record's exact column layout, so the parser below scans each
line/JSON entry for family + time-window + percentage rather than assuming
fixed column positions. `raw_json`/`raw_text` are kept on the snapshot so a
mismatch can be diagnosed from a real container instead of guessed at.
"""

import json
import os
import re
import subprocess
import threading
import time

from core.models_catalog import FAMILY_LABELS
from core.system_info import check_agy_hardware_support

AGY_BIN = "/usr/local/bin/agy"

_CACHE = {"data": None, "ts": 0.0}
_CACHE_TTL_SEC = 60.0
_REFRESH_LOCK = threading.Lock()

_PCT_RE = re.compile(r"(\d{1,3})\s*%")
_ISO_RE = re.compile(r"(\d{4}-\d{2}-\d{2}T[\d:]+Z)")


def _agy_env() -> dict:
    env = os.environ.copy()
    env["HOME"] = "/root"
    env["USER"] = "root"
    env["PATH"] = f"/root/.local/bin:/usr/local/bin:/usr/bin:/bin:{env.get('PATH', '')}"
    env["FORCE_COLOR"] = "0"
    env["TERM"] = "dumb"
    return env


def _run_usage_print(output_format: str):
    """Run `agy -p "/usage" --output-format <fmt>` and return (returncode, stdout, stderr)."""
    cmd = [AGY_BIN, "-p", "/usage", "--output-format", output_format]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15, env=_agy_env())
    return proc.returncode, proc.stdout, proc.stderr


def _run_credits_print(output_format: str):
    """Run `agy -p "/credits" --output-format <fmt>`. Separate slash command from
    /usage (per official CLI reference, /usage covers per-model weekly/5-hour
    quota while /credits is G1 credit balance) -- confirmed live that /usage's
    own JSON response carries no credit field, so this needs its own call."""
    cmd = [AGY_BIN, "-p", "/credits", "--output-format", output_format]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15, env=_agy_env())
    return proc.returncode, proc.stdout, proc.stderr


def _classify_family(text: str):
    lower = text.lower()
    if "gemini" in lower:
        return "gemini"
    if "claude" in lower or "gpt" in lower or "oss" in lower:
        return "claude_gpt"
    return None


def _classify_window(text: str):
    lower = text.lower()
    if "week" in lower or "주간" in lower:
        return "weekly"
    if "five" in lower or "5시간" in lower or ("5" in lower and ("hour" in lower or "시간" in lower)):
        return "five_hour"
    return None


def _parse_tsv(raw: str) -> dict:
    """Best-effort scan of the tab-separated print-mode report for family/window/percent."""
    result = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        family = _classify_family(line)
        window = _classify_window(line)
        pct_match = _PCT_RE.search(line)
        if family and window and pct_match:
            bucket_stats = result.setdefault(family, {})
            bucket_stats[f"{window}_remaining_pct"] = int(pct_match.group(1))
            iso_match = _ISO_RE.search(line)
            if iso_match:
                bucket_stats[f"{window}_reset_time"] = iso_match.group(1)
    return result


def _parse_json(raw: str) -> dict:
    """Parse `agy -p "/usage" --output-format json`'s real response shape.

    Confirmed against a live response (2026-09-01): the print-mode answer for
    a read-only slash command comes back as a normal agent-turn envelope
    (`status`, `response`, `usage`, ...) with the actual quota data under
    `command.data.groups[]`. Each group's `name` matches a FAMILY_LABELS
    value verbatim ("Gemini Models" / "Claude and GPT models"); each bucket
    has a `window` (only "weekly" observed so far -- anything else is
    treated as the 5-hour/sprint bucket, since only those two windows are
    documented) and a `remaining_fraction` in [0, 1], not a ready percentage.
    A family with no 5-hour bucket in the response (as seen live) simply has
    no five_hour_remaining_pct key -- the UI already renders that as "-".
    """
    data = json.loads(raw)
    command_data = (data.get("command") or {}).get("data", {})
    groups = command_data.get("groups") or data.get("groups") or []
    policy_description = command_data.get("description") or ""

    name_to_family = {label: fam for fam, label in FAMILY_LABELS.items()}
    result = {}
    for group in groups:
        if not isinstance(group, dict):
            continue
        group_name = str(group.get("name", ""))
        family = name_to_family.get(group_name) or _classify_family(group_name)
        if not family:
            continue
        bucket_stats = result.setdefault(family, {})
        if group.get("description"):
            bucket_stats["group_description"] = group["description"]
        for bucket in group.get("buckets") or []:
            if not isinstance(bucket, dict):
                continue
            fraction = bucket.get("remaining_fraction")
            if not isinstance(fraction, (int, float)):
                continue
            window = str(bucket.get("window", "")).lower()
            prefix = "weekly" if window == "weekly" else "five_hour"
            bucket_stats[f"{prefix}_remaining_pct"] = round(fraction * 100)
            reset_time = bucket.get("reset_time")
            if reset_time:
                bucket_stats[f"{prefix}_reset_time"] = reset_time
            # agy's own human-readable status line (e.g. "You have used some
            # of your weekly limit, it will fully refresh in 6 days, 2
            # hours.") -- preferred over any locally-generated hint text.
            if bucket.get("description"):
                bucket_stats[f"{prefix}_description"] = bucket["description"]
    return result, policy_description


def get_usage_snapshot(force: bool = False) -> dict:
    """Return the cached (<=60s old) quota snapshot, refreshing from `agy` when stale.

    `agy -p "/usage"` itself takes 10+ seconds, and the frontend both
    prefetches this in the background and can fetch it on demand -- without
    this lock, two requests arriving while the cache is stale would each
    spawn their own `agy` subprocess. The lock makes the second caller just
    wait for the first's result instead.
    """
    now = time.time()
    if not force and _CACHE["data"] is not None and (now - _CACHE["ts"]) < _CACHE_TTL_SEC:
        return _CACHE["data"]

    with _REFRESH_LOCK:
        now = time.time()
        if not force and _CACHE["data"] is not None and (now - _CACHE["ts"]) < _CACHE_TTL_SEC:
            return _CACHE["data"]
        return _refresh_usage_snapshot(now)


def _refresh_usage_snapshot(now: float) -> dict:
    if not check_agy_hardware_support().get("supported", False) or not os.path.exists(AGY_BIN):
        snapshot = {
            "available": False,
            "reason": "agy가 이 호스트에서 지원되지 않거나 설치되어 있지 않습니다.",
            "families": {},
            "family_labels": FAMILY_LABELS,
        }
        _CACHE.update(data=snapshot, ts=now)
        return snapshot

    raw_json, raw_text, err = "", "", ""
    families = {}
    policy_description = ""
    try:
        ret, out, stderr = _run_usage_print("json")
        if ret == 0 and out.strip():
            raw_json = out
            families, policy_description = _parse_json(out)
    except Exception as e:
        err = str(e)

    if not families:
        try:
            ret, out, stderr2 = _run_usage_print("text")
            if out.strip():
                raw_text = out
                families = _parse_tsv(out)
            err = err or stderr2
        except Exception as e:
            err = err or str(e)

    snapshot = {
        "available": bool(families),
        "families": families,
        "family_labels": FAMILY_LABELS,
        "policy_description": policy_description,
        "reason": None if families else (err or "`agy -p /usage`가 파싱 가능한 응답을 반환하지 않았습니다."),
        "raw_json": raw_json[:4000],
        "raw_text": raw_text[:4000],
        "fetched_at": now,
    }
    _CACHE.update(data=snapshot, ts=now)
    return snapshot


_CREDITS_CACHE = {"data": None, "ts": 0.0}
_CREDITS_REFRESH_LOCK = threading.Lock()


def get_credits_snapshot(force: bool = False) -> dict:
    """Same caching contract as get_usage_snapshot(), for `agy -p "/credits"`.

    Unlike /usage, the /credits response shape has not been confirmed against
    a live container yet (backlog item -- see docs/... coverage report), so
    this doesn't assume a schema: it surfaces `command.data`/`response`
    verbatim under best-effort keys rather than parsed percentages, so the
    caller can decide whether there's anything real to show.
    """
    now = time.time()
    if not force and _CREDITS_CACHE["data"] is not None and (now - _CREDITS_CACHE["ts"]) < _CACHE_TTL_SEC:
        return _CREDITS_CACHE["data"]

    with _CREDITS_REFRESH_LOCK:
        now = time.time()
        if not force and _CREDITS_CACHE["data"] is not None and (now - _CREDITS_CACHE["ts"]) < _CACHE_TTL_SEC:
            return _CREDITS_CACHE["data"]
        return _refresh_credits_snapshot(now)


def _refresh_credits_snapshot(now: float) -> dict:
    if not check_agy_hardware_support().get("supported", False) or not os.path.exists(AGY_BIN):
        snapshot = {
            "available": False,
            "reason": "agy가 이 호스트에서 지원되지 않거나 설치되어 있지 않습니다.",
            "fetched_at": now,
        }
        _CREDITS_CACHE.update(data=snapshot, ts=now)
        return snapshot

    raw_json, err = "", ""
    parsed = None
    try:
        ret, out, stderr = _run_credits_print("json")
        raw_json = out
        if ret == 0 and out.strip():
            try:
                parsed = json.loads(out)
            except Exception:
                parsed = None
        else:
            err = stderr
    except Exception as e:
        err = str(e)

    snapshot = {
        "available": parsed is not None,
        "reason": None if parsed is not None else (err or "`agy -p /credits`가 파싱 가능한 응답을 반환하지 않았습니다."),
        "raw_json": (raw_json or "")[:4000],
        "fetched_at": now,
    }
    if parsed is not None:
        command = parsed.get("command") or {}
        snapshot["command_name"] = command.get("name")
        snapshot["data"] = command.get("data")
        snapshot["response_text"] = parsed.get("response")
    _CREDITS_CACHE.update(data=snapshot, ts=now)
    return snapshot
