"""Real-Time SSE Streaming Engine supporting Modes 1, 2, and 3."""

import json
import os
import queue
import re
import select
import subprocess
import sys
import threading
import time

try:
    import pty
except ImportError:
    pty = None

from core.ha_engine import (
    get_ai_deep_environment_analysis,
    get_ha_states,
    get_resource_usage,
    get_supervisor_token,
    get_terminal_cli_environment_view,
    get_weather_env_summary,
    handle_agent_chat,
)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from terminal text."""
    ansi_escape = re.compile(r"(?:\x1B[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def make_sse(event_type: str, content: str = "") -> str:
    """Format SSE payload."""
    payload = {"type": event_type}
    if content:
        payload["content"] = content
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def stream_transcript_tail(prompt: str):
    """Mode 1: Deep AI Brain Environmental Analysis & Living Advice Streamer."""
    actual_prompt = re.sub(r"^(ai|/llm)\s*", "", prompt, flags=re.IGNORECASE).strip()
    yield make_sse("tool", f"📜 [모드 1: AI 딥 브레인 분석] 세션 초기화: '{actual_prompt}'")
    time.sleep(0.05)

    smart_home_keywords = [
        "상태", "상황", "현황", "요약", "브리핑", "날씨", "환경", "기상",
        "온도", "습도", "조명", "에러", "로그", "켜", "꺼", "틀어", "시작", "정지",
        "열어", "닫아", "거실", "안방", "작은방", "주방", "화장실", "세탁실", "옷방", "메모리", "램", "안녕"
    ]
    lower = actual_prompt.lower()

    if any(w in lower for w in smart_home_keywords):
        yield make_sse("tool", "🔍 [1단계] Home Assistant 엔티티 상태 실시간 탐색 및 MCP 데이터 수집")
        time.sleep(0.08)
        yield make_sse("tool", "🧠 [2단계] Gemini 딥 브레인 연산: 실내외 환경 쾌적성 & 밸런스 추론")
        time.sleep(0.08)
        yield make_sse("tool", "📊 [3단계] 맞춤형 스마트홈 케어 제안 및 심층 분석 리포트 합성")
        time.sleep(0.08)

        states = get_ha_states()
        if states and any(w in lower for w in ["날씨", "환경", "온도", "습도", "기상", "기온"]):
            full_text = get_ai_deep_environment_analysis(states, actual_prompt)
        else:
            full_text = handle_agent_chat(actual_prompt, "", "", False)

        yield make_sse("text", full_text)
        yield make_sse("done")
        return

    # For general CLI commands or deep reasoning, launch agy
    agy_bin = "/usr/local/bin/agy" if os.path.exists("/usr/local/bin/agy") else "/root/.local/bin/agy"
    if not os.path.exists(agy_bin):
        yield make_sse("tool", "💡 [스마트홈 대체 모드] Home Assistant 지능형 엔진으로 처리합니다.")
        full_text = handle_agent_chat(actual_prompt, "", "", False)
        yield make_sse("text", full_text)
        yield make_sse("done")
        return

    supervisor_token = get_supervisor_token()
    env = {
        **os.environ,
        "HOME": "/root",
        "TERM": "xterm-256color",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "LANGUAGE": "C.UTF-8",
        "PYTHONIOENCODING": "utf-8",
        "HASS_SERVER": "http://supervisor/core",
        "HASS_TOKEN": supervisor_token,
        "SUPERVISOR_TOKEN": supervisor_token,
        "UV_CACHE_DIR": "/config/.uv_cache",
        "PATH": f"/root/.local/bin:/usr/local/bin:{os.environ.get('PATH', '')}:/usr/bin:/bin",
    }

    cmd = [agy_bin, "--dangerously-skip-permissions", "--print", actual_prompt]
    yield make_sse("tool", "🧠 [1단계] Antigravity CLI 딥 브레인 엔진 호출 중...")
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd="/config" if os.path.exists("/config") else "/root",
        )
    except Exception as e:
        yield make_sse("text", f"[오류] agy 프로세스 시작 실패: {e}")
        yield make_sse("done")
        return

    out_queue = queue.Queue()

    def reader_thread(pipe, q):
        try:
            for line in iter(pipe.readline, b""):
                if line:
                    q.put(line.decode("utf-8", errors="replace"))
        except Exception:
            pass
        finally:
            pipe.close()

    t = threading.Thread(target=reader_thread, args=(proc.stdout, out_queue), daemon=True)
    t.start()

    start_time = time.time()
    timeout = 30
    streamed_any_chunk = False

    while time.time() - start_time < timeout:
        while not out_queue.empty():
            try:
                line_data = out_queue.get_nowait()
                clean = strip_ansi(line_data).strip()
                if clean:
                    if clean.startswith("● ") or clean.startswith("▸ ") or clean.startswith("Initiating") or clean.startswith("Discovering"):
                        yield make_sse("tool", clean)
                    else:
                        yield make_sse("chunk", clean + "\n")
                        streamed_any_chunk = True
            except queue.Empty:
                break

        if proc.poll() is not None and out_queue.empty():
            break

        time.sleep(0.1)

    if not streamed_any_chunk:
        yield make_sse("tool", "💡 [스마트홈 대체 모드] 실시간 데이터로 응답을 생성합니다.")
        full_text = handle_agent_chat(actual_prompt, "", "", False)
        yield make_sse("text", full_text)

    yield make_sse("done")


def stream_pty_interactive(prompt: str):
    """Mode 2: Virtual PTY Terminal Interactive Stream with ANSI parsing."""
    actual_prompt = re.sub(r"^(ai|/llm)\s*", "", prompt, flags=re.IGNORECASE).strip()
    yield make_sse("tool", f"🖥️ [모드 2: PTY 터미널 스트림] 가상 터미널 세션 생성: '{actual_prompt}'")
    time.sleep(0.05)

    smart_home_keywords = [
        "상태", "상황", "현황", "요약", "브리핑", "날씨", "환경", "기상",
        "온도", "습도", "조명", "에러", "로그", "켜", "꺼", "틀어", "시작", "정지",
        "열어", "닫아", "거실", "안방", "작은방", "주방", "화장실", "세탁실", "옷방", "메모리", "램", "안녕"
    ]
    lower = actual_prompt.lower()

    if any(w in lower for w in smart_home_keywords):
        yield make_sse("tool", "🖥️ [가상 터미널] Home Assistant 엔티티 상태 스트림 수신...")
        time.sleep(0.08)
        yield make_sse("tool", "📊 [터미널 렌더링] 디바이스 상태 및 센서 데이터 CLI 테이블 포맷팅")
        time.sleep(0.08)
        states = get_ha_states()
        if states and any(w in lower for w in ["날씨", "환경", "온도", "습도", "기상", "기온"]):
            full_text = get_terminal_cli_environment_view(states)
        else:
            full_text = handle_agent_chat(actual_prompt, "", "", False)
        yield make_sse("text", full_text)
        yield make_sse("done")
        return

    if pty is None:
        yield make_sse("text", "[오류] PTY 가상 터미널 모듈을 사용할 수 없습니다.")
        yield make_sse("done")
        return

    agy_bin = "/usr/local/bin/agy" if os.path.exists("/usr/local/bin/agy") else "/root/.local/bin/agy"
    if not os.path.exists(agy_bin):
        yield make_sse("tool", "💡 [스마트홈 대체 모드] Home Assistant 지능형 엔진으로 처리합니다.")
        full_text = handle_agent_chat(actual_prompt, "", "", False)
        yield make_sse("text", full_text)
        yield make_sse("done")
        return

    supervisor_token = get_supervisor_token()
    master_fd, slave_fd = pty.openpty()
    env = {
        **os.environ,
        "HOME": "/root",
        "TERM": "xterm-256color",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "LANGUAGE": "C.UTF-8",
        "PYTHONIOENCODING": "utf-8",
        "HASS_SERVER": "http://supervisor/core",
        "HASS_TOKEN": supervisor_token,
        "SUPERVISOR_TOKEN": supervisor_token,
        "UV_CACHE_DIR": "/config/.uv_cache",
        "PATH": f"/root/.local/bin:/usr/local/bin:{os.environ.get('PATH', '')}:/usr/bin:/bin",
    }

    cmd = [agy_bin, "--dangerously-skip-permissions", "--print", actual_prompt]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
            env=env,
            cwd="/config" if os.path.exists("/config") else "/root",
        )
    except Exception as e:
        os.close(slave_fd)
        os.close(master_fd)
        yield make_sse("text", f"[오류] PTY 프로세스 시작 실패: {e}")
        yield make_sse("done")
        return

    os.close(slave_fd)
    buffer = ""
    start_time = time.time()
    timeout = 30
    streamed_any = False

    try:
        while True:
            if time.time() - start_time > timeout:
                try:
                    proc.kill()
                except Exception:
                    pass
                break

            r, _, _ = select.select([master_fd], [], [], 0.2)
            if master_fd in r:
                try:
                    data = os.read(master_fd, 4096)
                    if not data:
                        break
                    chunk_str = data.decode("utf-8", errors="replace")
                    buffer += chunk_str

                    if "\n" in buffer:
                        lines = buffer.split("\n")
                        buffer = lines[-1]
                        for line in lines[:-1]:
                            clean = strip_ansi(line).strip()
                            if not clean or any(w in clean for w in ["[WARNING]", "[INFO]", "Starting Web Terminal", "tmux", "root@", "/usr/local/bin/agy:"]):
                                continue
                            if clean.startswith("● ") or clean.startswith("▸ ") or clean.startswith("Initiating") or clean.startswith("Discovering"):
                                yield make_sse("tool", clean)
                            else:
                                yield make_sse("chunk", clean + "\n")
                                streamed_any = True
                except OSError:
                    break

            if proc.poll() is not None:
                while True:
                    r, _, _ = select.select([master_fd], [], [], 0.1)
                    if master_fd in r:
                        try:
                            data = os.read(master_fd, 4096)
                            if not data:
                                break
                            buffer += data.decode("utf-8", errors="replace")
                        except OSError:
                            break
                    else:
                        break
                break

        if buffer:
            for line in buffer.split("\n"):
                clean = strip_ansi(line).strip()
                if clean and not any(w in clean for w in ["[WARNING]", "[INFO]", "Starting Web Terminal", "tmux", "root@", "/usr/local/bin/agy:"]):
                    if clean.startswith("● ") or clean.startswith("▸ "):
                        yield make_sse("tool", clean)
                    else:
                        yield make_sse("chunk", clean + "\n")
                        streamed_any = True
    finally:
        try:
            os.close(master_fd)
        except Exception:
            pass

    if not streamed_any:
        full_text = handle_agent_chat(actual_prompt, "", "", False)
        yield make_sse("text", full_text)

    yield make_sse("done")


def stream_hybrid_fast(prompt: str):
    """Mode 3: Ultra-Fast Smart Home Native Dispatcher (0.05s) + Step-by-Step Tool Visibility."""
    actual_prompt = re.sub(r"^(ai|/llm)\s*", "", prompt, flags=re.IGNORECASE).strip()
    yield make_sse("tool", "⚡ [모드 3: 하이브리드 고속] 스마트홈 실시간 엔티티 고속 수집 중...")
    time.sleep(0.04)
    yield make_sse("tool", "📊 [2단계] 주요 공간 센서 및 기기 데이터 실시간 분석")
    time.sleep(0.04)

    full_text = handle_agent_chat(actual_prompt, "", "", False)
    yield make_sse("text", full_text)
    yield make_sse("done")


def stream_agent_chat(prompt: str, is_direct_llm: bool = False, stream_mode: int = 3):
    """Router for the 3 Streaming Modes."""
    if stream_mode == 1:
        for ev in stream_transcript_tail(prompt):
            yield ev
    elif stream_mode == 2:
        for ev in stream_pty_interactive(prompt):
            yield ev
    else:
        for ev in stream_hybrid_fast(prompt):
            yield ev
