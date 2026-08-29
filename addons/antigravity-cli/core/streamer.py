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

    # Use 'script -q -c' to run agy in a pseudo-TTY.
    # This forces the Go runtime to flush output line-by-line instead of buffering.
    # Without this, agy buffers 4KB before writing anything to a pipe.
    script_cmd = (
        f"{agy_bin} -p {json.dumps(actual_prompt)}"
        f" --output-format stream-json"
        f" --dangerously-skip-permissions"
    )
    cmd = ["script", "-q", "-e", "-c", script_cmd, "/dev/null"]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
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
    full_text_parts = []

    try:
        for line in iter(proc.stdout.readline, ""):
            # script -q sometimes adds carriage returns; strip control chars
            line_str = line.rstrip("\r\n").strip()
            if not line_str:
                continue

            # Try to parse as JSON
            try:
                data = json.loads(line_str)
            except Exception:
                # Not JSON - check for auth error messages in plain text
                lower = line_str.lower()
                if any(w in lower for w in ["login required", "please run", "agy login", "oauth", "unauthorized", "unauthenticated"]):
                    auth_failed = True
                    break
                # Some other plain text - ignore (script adds noise)
                continue

            # Official Google Antigravity CLI stream-json event schema
            evt = data.get("event", data.get("type", ""))

            # 1. Session Initialization Event
            if evt == "init":
                tools = data.get("init", {}).get("tools", [])
                yield make_sse("tool", f"🚀 [CLI 세션 시작] 사용 가능 도구 {len(tools)}개 로드됨")

            # 2. Step Update Event (Text tokens, Tool execution, Thinking)
            elif evt == "step_update":
                step = data.get("step_update", {})
                step_type = step.get("step_type", "")
                state = step.get("state", "")

                # 2-1. Real-time text token delta
                delta = step.get("text_delta") or ""
                if delta:
                    full_text_parts.append(delta)
                    output_chars += len(delta)
                    has_emitted_chunk = True
                    yield make_sse("chunk", delta)

                # 2-2. Thinking / Reasoning step
                thinking = step.get("thinking") or step.get("thought") or ""
                if thinking:
                    yield make_sse("tool", f"💭 [추론] {thinking[:80]}...")

                # 2-3. Tool Call step
                tool_call = step.get("tool_call") or step.get("tool") or {}
                if tool_call:
                    if isinstance(tool_call, dict):
                        tname = tool_call.get("name") or tool_call.get("tool", "unknown")
                        tinput = str(tool_call.get("input") or tool_call.get("args") or "")[:80]
                        yield make_sse("tool", f"🔧 [도구 실행] {tname}{f': {tinput}' if tinput else ''}")
                    else:
                        yield make_sse("tool", f"🔧 [도구 실행] {tool_call}")

                # 2-4. Tool Result step
                if step_type == "tool_result" or "tool_result" in step:
                    tname = step.get("tool_name", "")
                    yield make_sse("tool", f"✅ [도구 완료] {tname}")

            # 3. Final Execution Result Event
            elif evt == "result":
                res = data.get("result", {})
                status = res.get("status", "")
                response_text = res.get("response", "")
                usage = res.get("usage", {})
                duration = res.get("duration_seconds", 0)

                # Fallback: if no streaming chunks arrived but response exists
                if not has_emitted_chunk and response_text:
                    full_text_parts.append(response_text)
                    output_chars += len(response_text)
                    has_emitted_chunk = True
                    yield make_sse("chunk", response_text)

                elapsed = duration or (time.time() - t_start)
                in_tok = usage.get("input_tokens", 120)
                out_tok = usage.get("output_tokens", max(1, int(output_chars * 0.4)))
                think_tok = usage.get("thinking_tokens", 0)
                total_tok = usage.get("total_tokens", in_tok + out_tok)

                tokens_meta = {
                    "input": in_tok,
                    "output": out_tok,
                    "thinking": think_tok,
                    "total": total_tok,
                    "speed_tps": round(out_tok / max(0.01, elapsed), 1),
                    "elapsed": round(elapsed, 2),
                }
                yield make_sse("done", tokens=tokens_meta)
                proc.stdout.close()
                proc.wait()
                return

            # 4. Standard Anthropic/OpenAI compatibility fallbacks
            elif evt in ("content_block_start", "content_block_delta", "text_delta"):
                delta = (
                    data.get("delta", {}).get("text", "")
                    or data.get("text", "")
                    or data.get("content", "")
                    or ""
                )
                if delta:
                    full_text_parts.append(delta)
                    output_chars += len(delta)
                    has_emitted_chunk = True
                    yield make_sse("chunk", delta)

            elif evt == "message_stop":
                elapsed = time.time() - t_start
                tokens_meta = {
                    "input": data.get("message", {}).get("usage", {}).get("input_tokens", 120),
                    "output": data.get("message", {}).get("usage", {}).get("output_tokens", max(1, int(output_chars * 0.4))),
                    "total": 0,
                    "speed_tps": 0,
                    "elapsed": round(elapsed, 2),
                }
                tokens_meta["total"] = tokens_meta["input"] + tokens_meta["output"]
                tokens_meta["speed_tps"] = round(tokens_meta["output"] / max(0.01, elapsed), 1)
                yield make_sse("done", tokens=tokens_meta)
                proc.stdout.close()
                proc.wait()
                return

            # 5. Error Event
            elif evt in ("error",):
                msg = data.get("error", {}).get("message", "") or data.get("message", "")
                if any(w in msg.lower() for w in ["auth", "login", "oauth", "unauthorized"]):
                    auth_failed = True
                    break
                yield make_sse("tool", f"⚠️ [오류] {msg}")

        proc.stdout.close()
        proc.wait()

    except Exception as ex:
        yield make_sse("tool", f"⚠️ [스트림 파싱 예외] {type(ex).__name__}: {str(ex)[:150]}")
        auth_failed = False  # do not falsely trigger auth fallback for general exceptions

    if has_emitted_chunk:
        # Completed normally
        return

    if auth_failed:
        yield make_sse("tool", "🔑 [인증 필요] Terminal 탭에서 'agy' 실행 후 Google 계정으로 1회 로그인하세요.")
        yield make_sse("tool", "⚡ [자동 전환] Home Assistant 내장 AI 어시스턴트로 답변합니다.")
        for ev in stream_ai_deep_brain(prompt, is_mobile=is_mobile):
            yield ev
    else:
        # No chunks emitted, but not auth failure - try deep brain fallback gracefully
        yield make_sse("tool", "⚡ [응답 생성] Home Assistant 통합 AI 엔진으로 즉시 답변합니다.")
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

    flag_tests = []
    test_commands = [
        ("echo prompt", ["bash", "-c", "echo 'Say hi in 3 words' | /usr/local/bin/agy --output-format stream-json --dangerously-skip-permissions"]),
        ("print flag", ["/usr/local/bin/agy", "-p", "Say hi in 3 words"]),
        ("stream-json flag", ["/usr/local/bin/agy", "-p", "Say hi in 3 words", "--output-format", "stream-json"]),
        ("disable slash", ["/usr/local/bin/agy", "-p", "Say hi in 3 words", "--output-format", "stream-json", "--disable-slash-commands"]),
    ]

    for label, c in test_commands:
        t_c = time.time()
        try:
            p = subprocess.Popen(
                c,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            try:
                stdout, stderr = p.communicate(input="Say hi in 3 words\n", timeout=2)
                flag_tests.append({
                    "label": label,
                    "ret": p.returncode,
                    "stdout": stdout[:200],
                    "stderr": stderr[:200],
                    "time": round(time.time() - t_c, 2)
                })
            except subprocess.TimeoutExpired:
                p.kill()
                stdout, stderr = p.communicate()
                flag_tests.append({
                    "label": label,
                    "timeout": True,
                    "stdout": stdout[:200],
                    "stderr": stderr[:200],
                    "time": round(time.time() - t_c, 2)
                })
        except Exception as e:
            flag_tests.append({"label": label, "err": str(e)})

    result["flag_tests"] = flag_tests
    return result

