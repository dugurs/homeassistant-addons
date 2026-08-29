"""Real-Time SSE Streaming Engine supporting Modes 1, 2, and 3."""

import json
import os
import re
import select
import subprocess
import sys
import time

try:
    import pty
except ImportError:
    pty = None

from core.ha_engine import get_supervisor_token, handle_agent_chat


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
    """Mode 1: Tail transcript.jsonl in real-time to stream thoughts, tool calls, and chunks without blocking."""
    actual_prompt = re.sub(r"^(ai|/llm)\s*", "", prompt, flags=re.IGNORECASE).strip()
    yield make_sse("tool", f"📜 [모드 1: Transcript 추적] AI 작업 세션 초기화: '{actual_prompt}'")

    agy_bin = "/usr/local/bin/agy" if os.path.exists("/usr/local/bin/agy") else "/root/.local/bin/agy"
    if not os.path.exists(agy_bin):
        yield make_sse("text", "[오류] agy 바이너리를 찾을 수 없습니다.")
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

    brain_roots = [
        "/root/.gemini/antigravity/brain",
        "/config/.gemini/antigravity/brain",
        os.path.expanduser("~/.gemini/antigravity/brain"),
    ]

    cmd = [agy_bin, "--dangerously-skip-permissions", "--print", actual_prompt]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd="/config" if os.path.exists("/config") else "/root",
        )
    except Exception as e:
        yield make_sse("text", f"[오류] agy 프로세스 시작 실패: {e}")
        yield make_sse("done")
        return

    yield make_sse("tool", "AI 딥 브레인 연산 시작 및 실시간 트랜스크립트 로그 모니터링 중...")

    transcript_file = None
    file_pos = 0
    start_time = time.time()
    timeout = 180
    streamed_any_chunk = False

    while time.time() - start_time < timeout:
        if not transcript_file:
            for br in brain_roots:
                if os.path.exists(br):
                    try:
                        all_sub = [os.path.join(br, d) for d in os.listdir(br)]
                        all_sub.sort(key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)
                        for d in all_sub:
                            cand = os.path.join(d, ".system_generated", "logs", "transcript.jsonl")
                            if os.path.exists(cand) and (os.path.getmtime(cand) >= start_time - 5):
                                transcript_file = cand
                                break
                    except Exception:
                        pass
                if transcript_file:
                    break

        if transcript_file and os.path.exists(transcript_file):
            try:
                with open(transcript_file, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(file_pos)
                    new_lines = f.readlines()
                    file_pos = f.tell()
                    for line in new_lines:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            item = json.loads(line)
                            itype = item.get("type")
                            if itype == "PLANNER_RESPONSE":
                                if "thinking" in item and item["thinking"]:
                                    t_snippet = item["thinking"].strip().replace("\n", " ")
                                    yield make_sse("tool", f"💭 AI 사고 과정: {t_snippet[:100]}...")
                                if "tool_calls" in item and item["tool_calls"]:
                                    for tc in item["tool_calls"]:
                                        name = tc.get("name", "tool")
                                        args = json.dumps(tc.get("args", {}), ensure_ascii=False)
                                        yield make_sse("tool", f"🔧 도구 호출: {name}({args[:60]})")
                                if "content" in item and item["content"]:
                                    yield make_sse("chunk", item["content"])
                                    streamed_any_chunk = True
                            elif itype == "TOOL_RESPONSE":
                                c_len = len(item.get("content", ""))
                                yield make_sse("tool", f"📥 도구 결과 수신 완료 ({c_len}자)")
                        except Exception:
                            pass
            except Exception:
                pass

        if proc.poll() is not None:
            break

        time.sleep(0.3)

    # Process final stdout
    if not streamed_any_chunk:
        stdout_data, _ = proc.communicate()
        out_str = strip_ansi(stdout_data.decode("utf-8", errors="replace").strip())
        if out_str:
            yield make_sse("text", out_str)

    yield make_sse("done")


def stream_pty_interactive(prompt: str):
    """Mode 2: Virtual PTY Terminal Interactive Stream with ANSI parsing."""
    actual_prompt = re.sub(r"^(ai|/llm)\s*", "", prompt, flags=re.IGNORECASE).strip()
    yield make_sse("tool", f"🖥️ [모드 2: PTY 터미널 스트림] 가상 터미널 세션 생성: '{actual_prompt}'")

    if pty is None:
        yield make_sse("text", "[오류] PTY 가상 터미널 모듈을 사용할 수 없습니다.")
        yield make_sse("done")
        return

    agy_bin = "/usr/local/bin/agy" if os.path.exists("/usr/local/bin/agy") else "/root/.local/bin/agy"
    if not os.path.exists(agy_bin):
        yield make_sse("text", "[오류] agy 바이너리를 찾을 수 없습니다.")
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
    timeout = 180

    try:
        while True:
            if time.time() - start_time > timeout:
                try:
                    proc.kill()
                except Exception:
                    pass
                yield make_sse("chunk", f"\n[오류] AI 추론 시간이 초과되었습니다 ({timeout}초 초과).")
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
    finally:
        try:
            os.close(master_fd)
        except Exception:
            pass

    yield make_sse("done")


def stream_hybrid_fast(prompt: str):
    """Mode 3: Ultra-Fast Smart Home Native Dispatcher (0.05s) + LLM Auto-Fallback."""
    actual_prompt = re.sub(r"^(ai|/llm)\s*", "", prompt, flags=re.IGNORECASE).strip()
    lower = actual_prompt.lower()

    smart_home_keywords = [
        "상태", "상황", "현황", "요약", "브리핑", "날씨", "환경", "기상",
        "온도", "습도", "조명", "에러", "로그", "켜", "꺼", "틀어", "시작", "정지",
        "열어", "닫아", "거실", "안방", "작은방", "주방", "화장실", "세탁실", "옷방", "메모리", "램"
    ]

    if any(w in lower for w in smart_home_keywords):
        yield make_sse("tool", "⚡ [모드 3: 하이브리드 고속] 스마트홈 실시간 엔티티 고속 수집 중...")
        full_text = handle_agent_chat(actual_prompt, "", "", False)
        yield make_sse("text", full_text)
        yield make_sse("done")
        return

    # Fallback to Transcript Tail for deep reasoning
    for ev in stream_transcript_tail(prompt):
        yield ev


def stream_agent_chat(prompt: str, is_direct_llm: bool = False, stream_mode: int = 3):
    """Router for the 3 Streaming Modes."""
    if stream_mode == 1:
        for ev in stream_transcript_tail(prompt):
            yield ev
    elif stream_mode == 2:
        for ev in stream_pty_interactive(prompt):
            yield ev
    else:  # Default Mode 3: Hybrid Fast
        for ev in stream_hybrid_fast(prompt):
            yield ev
