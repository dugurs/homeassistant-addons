"""Real-Time SSE Streaming Engine supporting Mode 1 (AI Deep Brain) and Mode 2 (Ultra-Fast Smart Home)."""

import json
import os
import re
import sys
import time

from core.ha_engine import (
    get_ai_deep_environment_analysis,
    get_ha_states,
    get_weather_env_summary,
    handle_agent_chat,
)


def estimate_tokens(text: str) -> int:
    """Calculate realistic token count for multilingual / Korean + English markdown."""
    if not text:
        return 0
    korean_chars = len(re.findall(r"[\uac00-\ud7a3]", text))
    other_chars = len(text) - korean_chars
    return max(1, int(korean_chars * 0.8 + other_chars * 0.3))


def make_sse(event_type: str, content: str = "", tokens: dict = None) -> str:
    """Format SSE payload."""
    payload = {"type": event_type}
    if content:
        payload["content"] = content
    if tokens:
        payload["tokens"] = tokens
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def stream_ai_deep_brain(prompt: str, is_mobile: bool = False):
    """Mode 1: AI Deep Brain Multi-Dimensional Environmental Analysis & Living Advice Streamer."""
    t_start = time.time()
    actual_prompt = re.sub(r"^(ai|/llm)\s*", "", prompt, flags=re.IGNORECASE).strip()
    input_tokens = estimate_tokens(actual_prompt) + 120  # prompt + system context

    yield make_sse("tool", f"🧠 [모드 1: AI 딥 브레인] 환경 분석 세션 초기화: '{actual_prompt}'")
    time.sleep(0.04)
    yield make_sse("tool", "🔍 [1단계] Home Assistant 다차원 환경 센서(CO2, TVOC, PM2.5, 조도) 수집")
    time.sleep(0.05)
    yield make_sse("tool", "📊 [2단계] 실내외 온습도 및 공기질 쾌적성 밸런스 추론 & AI 맞춤 조언 합성")
    time.sleep(0.05)

    states = get_ha_states()
    lower = actual_prompt.lower()
    if states and any(w in lower for w in ["날씨", "환경", "온도", "습도", "기상", "기온", "공기", "co2", "미세먼지"]):
        full_text = get_ai_deep_environment_analysis(states, actual_prompt, is_mobile=is_mobile)
    else:
        full_text = handle_agent_chat(actual_prompt, "", "", False, is_mobile=is_mobile)

    yield make_sse("text", full_text)

    elapsed = time.time() - t_start
    output_tokens = estimate_tokens(full_text)
    total_tokens = input_tokens + output_tokens
    speed_tps = round(output_tokens / max(0.01, elapsed), 1)

    tokens_meta = {
        "input": input_tokens,
        "output": output_tokens,
        "total": total_tokens,
        "speed_tps": speed_tps,
        "elapsed": round(elapsed, 3),
    }
    yield make_sse("done", tokens=tokens_meta)


def stream_fast_dashboard(prompt: str, is_mobile: bool = False):
    """Mode 2: Ultra-Fast Smart Home Native Dispatcher (0.05s) + Step-by-Step Tool Visibility."""
    t_start = time.time()
    actual_prompt = re.sub(r"^(ai|/llm)\s*", "", prompt, flags=re.IGNORECASE).strip()
    input_tokens = estimate_tokens(actual_prompt) + 40

    yield make_sse("tool", "⚡ [모드 2: 초고속 스마트홈] 실시간 기기 및 엔티티 상태 고속 탐색")
    time.sleep(0.03)

    full_text = handle_agent_chat(actual_prompt, "", "", False, is_mobile=is_mobile)
    yield make_sse("text", full_text)

    elapsed = time.time() - t_start
    output_tokens = estimate_tokens(full_text)
    total_tokens = input_tokens + output_tokens
    speed_tps = round(output_tokens / max(0.01, elapsed), 1)

    tokens_meta = {
        "input": input_tokens,
        "output": output_tokens,
        "total": total_tokens,
        "speed_tps": speed_tps,
        "elapsed": round(elapsed, 3),
    }
    yield make_sse("done", tokens=tokens_meta)


def stream_agent_chat(prompt: str, is_direct_llm: bool = False, stream_mode: int = 1, is_mobile: bool = False):
    """Router for the 2 Clean Streaming Modes (1: AI Deep Brain, 2: Ultra-Fast Smart Home)."""
    if stream_mode == 1:
        for ev in stream_ai_deep_brain(prompt, is_mobile=is_mobile):
            yield ev
    else:
        for ev in stream_fast_dashboard(prompt, is_mobile=is_mobile):
            yield ev


def test_headless_cli_execution(prompt: str = "In one sentence, what is a git rebase?") -> dict:
    """Execute test run of agy headless CLI with stream-json format and return full diagnostic report."""
    import shutil
    import subprocess

    agy_bin = shutil.which("agy") or "/usr/local/bin/agy"
    exists = os.path.exists(agy_bin)

    cmd = [
        agy_bin,
        "-p", prompt,
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
    ]

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["FORCE_COLOR"] = "0"
    env["TERM"] = "dumb"

    t0 = time.time()
    result = {
        "agy_bin": agy_bin,
        "exists": exists,
        "cmd": cmd,
        "lines": [],
        "stderr": "",
        "returncode": None,
        "elapsed_sec": None,
        "success": False,
    }

    if not exists:
        result["stderr"] = f"Binary not found at {agy_bin}"
        return result

    try:
        ver_proc = subprocess.run([agy_bin, "--version"], capture_output=True, text=True, timeout=3)
        result["agy_version"] = ver_proc.stdout.strip() or ver_proc.stderr.strip()
    except Exception as ex:
        result["agy_version"] = f"Error: {ex}"

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding="utf-8",
            env=env,
        )
        try:
            stdout, stderr = proc.communicate(timeout=5)
            result["returncode"] = proc.returncode
            result["lines"] = [line.strip() for line in stdout.splitlines() if line.strip()]
            result["stderr"] = stderr.strip()
            result["success"] = proc.returncode == 0 and len(result["lines"]) > 0
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            result["stderr"] = f"Timeout (stdout: {stdout.strip()[:200]}, stderr: {stderr.strip()[:200]})"
    except Exception as e:
        result["stderr"] = str(e)

    result["elapsed_sec"] = round(time.time() - t0, 3)
    return result

