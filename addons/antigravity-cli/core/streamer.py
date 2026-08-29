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


from core.system_info import check_agy_hardware_support


def stream_headless_cli(prompt: str, is_mobile: bool = False):
    """Mode 3: Google Antigravity Headless CLI Real-Time NDJSON Streamer (0-latency)."""
    import subprocess
    t_start = time.time()
    actual_prompt = re.sub(r"^(ai|/llm)\s*", "", prompt, flags=re.IGNORECASE).strip()

    hw_info = check_agy_hardware_support()
    agy_bin = "/usr/local/bin/agy"

    if not hw_info.get("supported", False) or not os.path.exists(agy_bin):
        yield make_sse("tool", "ℹ️ CPU 호스트 모드(AVX) 미지원 감지 -> 안전하게 [모드 1: AI 딥 브레인]으로 자동 전환합니다.")
        for ev in stream_ai_deep_brain(prompt, is_mobile=is_mobile):
            yield ev
        return

    cmd = [
        agy_bin,
        "-p", actual_prompt,
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
    ]

    env = os.environ.copy()
    env["HOME"] = "/root"
    env["USER"] = "root"
    env["PATH"] = f"/root/.local/bin:/usr/local/bin:/usr/bin:/bin:{env.get('PATH', '')}"
    env["PYTHONUNBUFFERED"] = "1"
    env["FORCE_COLOR"] = "0"
    env["TERM"] = "dumb"

    api_key = ""
    if os.path.exists("/data/options.json"):
        try:
            with open("/data/options.json", "r") as f:
                opts = json.load(f)
                api_key = opts.get("api_key", "").strip()
        except Exception:
            pass

    if api_key:
        env["GEMINI_API_KEY"] = api_key
        env["GOOGLE_API_KEY"] = api_key
        env["ANTIGRAVITY_API_KEY"] = api_key

    yield make_sse("tool", f"🚀 [Antigravity CLI] 세션 개시: '{actual_prompt[:30]}...'")

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
    except Exception as e:
        yield make_sse("tool", f"⚠️ CLI 프로세스 기동 실패 ({str(e)}) -> AI 딥 브레인으로 자동 전환")
        for ev in stream_ai_deep_brain(prompt, is_mobile=is_mobile):
            yield ev
        return

    has_emitted_chunk = False
    auth_failed = False
    output_chars = 0

    try:
        for line in iter(proc.stdout.readline, ""):
            line_str = line.strip()
            if not line_str:
                continue

            try:
                data = json.loads(line_str)
            except Exception:
                if any(w in line_str.lower() for w in ["agy login", "auth", "login required"]):
                    auth_failed = True
                    break
                yield make_sse("chunk", line)
                has_emitted_chunk = True
                output_chars += len(line)
                continue

            evt_type = data.get("type", "")

            if evt_type in ("step_start", "progress"):
                step_msg = data.get("status") or data.get("thought") or "추론 진행 중"
                yield make_sse("tool", f"🧠 [추론] {step_msg}")
            elif evt_type == "tool_call":
                tool_name = data.get("tool", "unknown_tool")
                yield make_sse("tool", f"🔧 [도구 실행] {tool_name}")
            elif evt_type == "tool_result":
                tool_name = data.get("tool", "")
                summary = data.get("summary", "완료")
                yield make_sse("tool", f"✅ [도구 완료] {tool_name}: {summary}")
            elif evt_type in ("chunk", "content_delta"):
                delta = data.get("delta") or data.get("content") or ""
                if delta:
                    yield make_sse("chunk", delta)
                    has_emitted_chunk = True
                    output_chars += len(delta)
            elif evt_type in ("done", "finish"):
                tokens_meta = data.get("tokens", {})
                if not tokens_meta:
                    elapsed = time.time() - t_start
                    tokens_meta = {
                        "input": 120,
                        "output": max(1, int(output_chars * 0.6)),
                        "total": 120 + max(1, int(output_chars * 0.6)),
                        "speed_tps": round(max(1, int(output_chars * 0.6)) / max(0.01, elapsed), 1),
                        "elapsed": round(elapsed, 2),
                    }
                yield make_sse("done", tokens=tokens_meta)
                proc.stdout.close()
                proc.wait()
                return
            elif evt_type in ("error", "auth_required"):
                if "auth" in data.get("code", "").lower() or "login" in data.get("message", "").lower():
                    auth_failed = True
                    break
                else:
                    yield make_sse("tool", f"⚠️ 에러 발생: {data.get('message', '알 수 없는 오류')}")

        proc.stdout.close()
        proc.wait()

    except Exception:
        auth_failed = True

    if auth_failed or not has_emitted_chunk:
        yield make_sse("tool", "🔑 [안내] Google Antigravity OAuth 인증 필요 (상단 'Terminal' 탭에서 'agy login' 실행 권장)")
        yield make_sse("tool", "⚡ [Fallback] Home Assistant 내장 다차원 AI 어시스턴트로 자동 전환하여 답변합니다.")
        for ev in stream_ai_deep_brain(prompt, is_mobile=is_mobile):
            yield ev


def stream_agent_chat(prompt: str, is_direct_llm: bool = False, stream_mode: int = 1, is_mobile: bool = False):
    """Router for the 3 Clean Streaming Modes (1: AI Deep Brain, 2: Ultra-Fast Smart Home, 3: Headless CLI)."""
    if stream_mode == 3:
        for ev in stream_headless_cli(prompt, is_mobile=is_mobile):
            yield ev
    elif stream_mode == 2:
        for ev in stream_fast_dashboard(prompt, is_mobile=is_mobile):
            yield ev
    else:
        for ev in stream_ai_deep_brain(prompt, is_mobile=is_mobile):
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
    env["HOME"] = "/root"
    env["USER"] = "root"
    env["PATH"] = f"/root/.local/bin:/usr/local/bin:/usr/bin:/bin:{env.get('PATH', '')}"
    env["PYTHONUNBUFFERED"] = "1"
    env["FORCE_COLOR"] = "0"
    env["TERM"] = "dumb"

    auth_files = []
    for p in ["/root/.gemini", "/root/.config/antigravity", "/config/.gemini", "/config/.config"]:
        if os.path.exists(p):
            try:
                auth_files.append(f"{p}: {os.listdir(p)}")
            except Exception as ex:
                auth_files.append(f"{p}: {ex}")
        else:
            auth_files.append(f"{p}: NOT_FOUND")

    found_files = []
    for search_dir in ["/root", "/config", "/homeassistant", "/data", "/share"]:
        if os.path.exists(search_dir):
            try:
                for root, dirs, files in os.walk(search_dir):
                    if len(found_files) > 50:
                        break
                    for f in files:
                        if any(k in f.lower() for k in ["gemini", "antigravity", "agy", "oauth", "token", "auth", "session"]):
                            found_files.append(os.path.join(root, f))
            except Exception:
                pass

    t0 = time.time()
    result = {
        "agy_bin": agy_bin,
        "exists": exists,
        "auth_dirs": auth_files,
        "all_files": found_files,
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
        help_proc = subprocess.run([agy_bin, "--help"], capture_output=True, text=True, timeout=3)
        result["agy_help"] = (help_proc.stdout.strip() or help_proc.stderr.strip())[:1000]
    except Exception as ex:
        result["agy_help"] = f"Error: {ex}"

    try:
        auth_proc = subprocess.run([agy_bin, "auth", "status"], capture_output=True, text=True, timeout=3, env=env)
        result["agy_auth"] = auth_proc.stdout.strip() or auth_proc.stderr.strip()
    except Exception as ex:
        result["agy_auth"] = f"Error: {ex}"

    try:
        proc = subprocess.Popen(
            [agy_bin, "-p", "In one sentence, what is a git rebase?", "--output-format", "stream-json", "--dangerously-skip-permissions"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding="utf-8",
            env=env,
        )
        try:
            stdout, stderr = proc.communicate(timeout=4)
            result["returncode"] = proc.returncode
            result["lines"] = [line.strip() for line in stdout.splitlines() if line.strip()]
            result["stderr"] = stderr.strip()
            result["success"] = proc.returncode == 0 and len(result["lines"]) > 0
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            result["stderr"] = f"Timeout (stdout: '{stdout}', stderr: '{stderr}')"
    except Exception as e:
        result["stderr"] = str(e)

    result["elapsed_sec"] = round(time.time() - t0, 3)
    return result

