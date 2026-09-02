"""Live Antigravity model discovery for Mode 3 (`agy`).

Confirmed against a real `agy models` response (2026-09, via the addon's own
`GET /api/models?force=1`):

    gemini-3.7-flash-high\tGemini 3.7 Flash (High)
    gemini-3.7-flash-medium\tGemini 3.7 Flash (Medium)
    gemini-3.7-flash-low\tGemini 3.7 Flash (Low)
    gemini-3.6-flash-high\tGemini 3.6 Flash (High)
    ...
    claude-sonnet-4-6\tClaude Sonnet 4.6 (Thinking)
    claude-opus-4-6-thinking\tClaude Opus 4.6 (Thinking)
    gpt-oss-120b-medium\tGPT-OSS 120B (Medium)

Two things this disproves about the original static catalog (sourced from
antigravity.google/docs/models/, which described --model and --effort as
separate flags):
  1. Reasoning effort is not a separate `--effort` flag at all -- it's baked
     into the model slug itself. "gemini-3.7-flash-high/-medium/-low" are
     three distinct, independently selectable slugs.
  2. Slugs use dots ("gemini-3.7-flash"), not dashes
     ("gemini-3-7-flash" as the old catalog guessed), and this account's
     lineup has no gemini-3.5-flash at all.

So this module parses `agy models`'s tab-separated `slug<TAB>label` output,
groups slugs that share a `...-high`/`-medium`/`-low` suffix into one picker
entry with several selectable *variant slugs*, and treats anything else
(claude-sonnet-4-6, claude-opus-4-6-thinking, gpt-oss-120b-medium) as its
own single, non-adjustable entry. `--effort` is never sent to `agy` --
selecting an effort just switches which variant slug is used as `--model`.
"""

import json
import os
import re
import subprocess
import threading
import time

from core.models_catalog import DEFAULT_MODEL_SLUG, FAMILY_LABELS, MODEL_CATALOG
from core.system_info import check_agy_hardware_support

AGY_BIN = "/usr/local/bin/agy"

_CACHE = {"data": None, "ts": 0.0}
_CACHE_TTL_SEC = 300.0  # the model lineup rarely changes within a session
_REFRESH_LOCK = threading.Lock()

_EFFORT_SUFFIX_RE = re.compile(r"^(?P<base>.+)-(?P<effort>high|medium|low)$")
_LABEL_SUFFIX_RE = re.compile(r"\s*\((?:High|Medium|Low)\)\s*$", re.IGNORECASE)

# Picker display order (low -> high), independent of whatever order `agy
# models` happens to list variants in (observed as high/medium/low).
_EFFORT_DISPLAY_ORDER = ["low", "medium", "high"]


def _sort_efforts(efforts: list) -> list:
    return sorted(efforts, key=lambda e: _EFFORT_DISPLAY_ORDER.index(e) if e in _EFFORT_DISPLAY_ORDER else 99)


def _agy_env() -> dict:
    env = os.environ.copy()
    env["HOME"] = "/root"
    env["USER"] = "root"
    env["PATH"] = f"/root/.local/bin:/usr/local/bin:/usr/bin:/bin:{env.get('PATH', '')}"
    env["FORCE_COLOR"] = "0"
    env["TERM"] = "dumb"
    return env


def _classify_family(text: str) -> str:
    lower = text.lower()
    if "claude" in lower or "gpt" in lower or "oss" in lower:
        return "claude_gpt"
    return "gemini"


def _derive_badge(base_slug: str, label: str) -> str:
    lower = f"{base_slug} {label}".lower()
    if "flash" in lower:
        return "Fast"
    if "pro" in lower:
        return "Pro"
    if "opus" in lower:
        return "Opus"
    if "claude" in lower:
        return "Claude"
    if "gpt" in lower or "oss" in lower:
        return "OSS"
    return ""


def _parse_models_tsv(raw: str) -> list:
    """Parse `agy models`'s `<slug>\\t<label>` lines into grouped picker entries."""
    groups = {}
    order = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        slug = parts[0].strip()
        label = parts[1].strip() if len(parts) > 1 else slug
        if not slug:
            continue

        m = _EFFORT_SUFFIX_RE.match(slug.lower())
        if m:
            base, effort = m.group("base"), m.group("effort")
            clean_label = _LABEL_SUFFIX_RE.sub("", label).strip()
        else:
            base, effort, clean_label = slug, "", label

        if base not in groups:
            groups[base] = {"label": clean_label, "variants": {}, "efforts_order": []}
            order.append(base)
        groups[base]["variants"][effort] = slug
        if effort and effort not in groups[base]["efforts_order"]:
            groups[base]["efforts_order"].append(effort)
        if len(clean_label) < len(groups[base]["label"]):
            groups[base]["label"] = clean_label

    out = []
    for base in order:
        g = groups[base]
        efforts = _sort_efforts(g["efforts_order"])
        # Prefer "high" as the default (most capable) regardless of display
        # order; fall back to whichever effort sorts highest if this account's
        # lineup doesn't offer "high" for this model.
        default_effort = "high" if "high" in efforts else (efforts[-1] if efforts else "")
        out.append({
            "slug": base,
            "label": g["label"],
            "family": _classify_family(f"{base} {g['label']}"),
            "badge": _derive_badge(base, g["label"]),
            "efforts": efforts,
            "default_effort": default_effort,
            "variant_slugs": g["variants"],
        })
    return out


def _parse_models_json(raw: str) -> list:
    """Speculative JSON path, kept in case a future agy build supports `--output-format json`
    for this subcommand -- not yet observed to work (the confirmed-working path is the
    plain-text TSV `agy models` output parsed by _parse_models_tsv)."""
    data = json.loads(raw)
    entries = data if isinstance(data, list) else (data.get("models") or (data.get("data") or {}).get("models") or [])
    lines = []
    for e in entries:
        if isinstance(e, dict):
            slug = e.get("slug") or e.get("id") or e.get("name")
            if slug:
                lines.append(f"{slug}\t{e.get('label') or e.get('name') or ''}")
        elif isinstance(e, str):
            lines.append(e)
    return _parse_models_tsv("\n".join(lines))


def _static_fallback_snapshot(reason: str, raw_json: str = "", raw_text: str = "") -> dict:
    return {
        "available": False,
        "models": MODEL_CATALOG,
        "family_labels": FAMILY_LABELS,
        "default_model": DEFAULT_MODEL_SLUG,
        "reason": reason,
        "raw_json": raw_json[:4000],
        "raw_text": raw_text[:4000],
        "source": "static",
    }


def get_live_model_catalog(force: bool = False) -> dict:
    """Return the live model catalog, falling back to the static one if `agy models` is unusable."""
    now = time.time()
    if not force and _CACHE["data"] is not None and (now - _CACHE["ts"]) < _CACHE_TTL_SEC:
        return _CACHE["data"]

    with _REFRESH_LOCK:
        now = time.time()
        if not force and _CACHE["data"] is not None and (now - _CACHE["ts"]) < _CACHE_TTL_SEC:
            return _CACHE["data"]
        return _refresh_model_catalog(now)


def _refresh_model_catalog(now: float) -> dict:
    if not check_agy_hardware_support().get("supported", False) or not os.path.exists(AGY_BIN):
        snapshot = _static_fallback_snapshot("agy가 이 호스트에서 지원되지 않거나 설치되어 있지 않아 내장 카탈로그를 사용합니다.")
        _CACHE.update(data=snapshot, ts=now)
        return snapshot

    raw_json, raw_text, err = "", "", ""
    models = []
    try:
        proc = subprocess.run([AGY_BIN, "models", "--output-format", "json"], capture_output=True, text=True, timeout=15, env=_agy_env())
        if proc.returncode == 0 and proc.stdout.strip():
            raw_json = proc.stdout
            models = _parse_models_json(proc.stdout)
    except Exception as e:
        err = str(e)

    if not models:
        try:
            proc = subprocess.run([AGY_BIN, "models"], capture_output=True, text=True, timeout=15, env=_agy_env())
            if proc.stdout.strip():
                raw_text = proc.stdout
                models = _parse_models_tsv(proc.stdout)
            err = err or proc.stderr
        except Exception as e:
            err = err or str(e)

    if not models:
        snapshot = _static_fallback_snapshot(
            err or "`agy models` 응답을 파싱하지 못해 내장 카탈로그를 사용합니다.", raw_json, raw_text,
        )
        _CACHE.update(data=snapshot, ts=now)
        return snapshot

    default_model = DEFAULT_MODEL_SLUG if any(m["slug"] == DEFAULT_MODEL_SLUG for m in models) else models[0]["slug"]
    snapshot = {
        "available": True,
        "models": models,
        "family_labels": FAMILY_LABELS,
        "default_model": default_model,
        "reason": None,
        "raw_json": raw_json[:4000],
        "raw_text": raw_text[:4000],
        "source": "live",
    }
    _CACHE.update(data=snapshot, ts=now)
    return snapshot


def get_valid_variant_slugs() -> set:
    """Every real, agy-invocable --model value (the resolved variant slugs, not the group ids)."""
    out = set()
    for m in get_live_model_catalog().get("models", []):
        out.update((m.get("variant_slugs") or {}).values())
    return out
