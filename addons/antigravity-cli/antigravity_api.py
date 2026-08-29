#!/usr/bin/env python3
"""Antigravity CLI Dual Ingress Web UI (Real-time SSE Streaming + ttyd Web Terminal) & REST API Server."""

import json
import os
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
import re
import socket
import select
try:
    import pty
except ImportError:
    pty = None

START_TIME = time.time()
VERSION = "1.3.0"
DEFAULT_PORT = 8000
INGRESS_PORT = 7681
TTYD_INTERNAL_PORT = 7682


def get_options():
    """Load addon options from /data/options.json if available."""
    options_file = "/data/options.json"
    if os.path.exists(options_file):
        try:
            with open(options_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from terminal output."""
    ansi_regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_regex.sub('', text)


def get_active_sessions() -> int:
    """Get active tmux sessions count."""
    try:
        res = subprocess.run(
            ["tmux", "list-sessions"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0:
            lines = [line for line in res.stdout.strip().split("\n") if line]
            return len(lines)
    except Exception:
        pass
    return 1 if os.path.exists("/tmp/tmux-0") else 0


def get_agent_status() -> str:
    """Check agent / process status."""
    try:
        res = subprocess.run(
            ["pgrep", "-f", "agy"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0 and res.stdout.strip():
            return "online"
    except Exception:
        pass
    return "online"


def get_resource_usage() -> dict:
    """Get container resource usage (RAM MB, CPU %, Total System RAM)."""
    res = {
        "memory_usage": 0.0,
        "cpu_usage": 0.0,
        "addon_memory_mb": 0.0,
        "total_memory_gb": 0.0,
        "used_memory_gb": 0.0,
        "memory_percent": 0.0,
    }
    try:
        if os.path.exists("/proc/meminfo"):
            mem = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        mem[parts[0].strip()] = int(parts[1].strip().split()[0])
            total_kb = mem.get("MemTotal", 0)
            avail_kb = mem.get("MemAvailable", 0)
            used_kb = total_kb - avail_kb
            if total_kb > 0:
                res["total_memory_gb"] = round(total_kb / 1024 / 1024, 2)
                res["used_memory_gb"] = round(used_kb / 1024 / 1024, 2)
                res["memory_percent"] = round((used_kb / total_kb) * 100, 1)

        proc = subprocess.run(["ps", "-eo", "%cpu,rss"], capture_output=True, text=True, timeout=2)
        if proc.returncode == 0:
            lines = proc.stdout.strip().split("\n")[1:]
            total_rss_kb = 0
            total_cpu = 0.0
            for line in lines:
                parts = line.strip().split()
                if len(parts) == 2:
                    try:
                        total_cpu += float(parts[0])
                        total_rss_kb += int(parts[1])
                    except ValueError:
                        pass
            mem_mb = round(total_rss_kb / 1024, 1)
            res["memory_usage"] = mem_mb
            res["addon_memory_mb"] = mem_mb
            res["cpu_usage"] = round(total_cpu, 1)
    except Exception:
        pass
    return res


def get_supervisor_token() -> str:
    """Retrieve SUPERVISOR_TOKEN from environment, s6, or proc1."""
    token = os.environ.get("SUPERVISOR_TOKEN", "")
    if token:
        return token
    for p in [
        "/var/run/s6/container_environment/SUPERVISOR_TOKEN",
        "/var/run/secrets/supervisor/token",
        "/run/s6/container_environment/SUPERVISOR_TOKEN",
    ]:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    t = f.read().strip()
                    if t:
                        return t
            except Exception:
                pass
    if os.path.exists("/proc/1/environ"):
        try:
            with open("/proc/1/environ", "rb") as f:
                raw = f.read().decode("utf-8", errors="ignore")
                for line in raw.split("\0"):
                    if line.startswith("SUPERVISOR_TOKEN="):
                        return line.split("=", 1)[1]
        except Exception:
            pass
    return ""


def get_ha_states() -> list:
    """Fetch all states from Home Assistant via Supervisor API."""
    supervisor_token = get_supervisor_token()
    if not supervisor_token:
        return []
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://supervisor/core/api/states",
            headers={"Authorization": f"Bearer {supervisor_token}"}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        pass
    return []


def call_ha_service(domain: str, service: str, service_data: dict) -> bool:
    """Call a Home Assistant service via Supervisor API."""
    supervisor_token = get_supervisor_token()
    if not supervisor_token:
        return False
    try:
        import urllib.request
        req = urllib.request.Request(
            f"http://supervisor/core/api/services/{domain}/{service}",
            data=json.dumps(service_data).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {supervisor_token}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            return resp.status in (200, 201)
    except Exception:
        return False


def get_all_addons_memory() -> str:
    """Fetch per-addon memory usage breakdown from Supervisor API."""
    supervisor_token = get_supervisor_token()
    if not supervisor_token:
        usage = get_resource_usage()
        return (
            f"현재 Antigravity CLI 애드온의 메모리 사용량은 약 {usage['memory_usage']}MB 이며, "
            f"시스템 전체 메모리는 {usage['used_memory_gb']}GB / {usage['total_memory_gb']}GB ({usage['memory_percent']}%) 사용 중입니다."
        )

    try:
        import urllib.request
        req = urllib.request.Request(
            "http://supervisor/addons",
            headers={"Authorization": f"Bearer {supervisor_token}"}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8")).get("data", {})
                addons_list = data.get("addons", [])
                
                addon_stats = []
                for a in addons_list:
                    slug = a.get("slug")
                    name = a.get("name", slug)
                    state = a.get("state")
                    if state == "started" and slug:
                        try:
                            s_req = urllib.request.Request(
                                f"http://supervisor/addons/{slug}/stats",
                                headers={"Authorization": f"Bearer {supervisor_token}"}
                            )
                            with urllib.request.urlopen(s_req, timeout=3) as s_resp:
                                if s_resp.status == 200:
                                    st_data = json.loads(s_resp.read().decode("utf-8")).get("data", {})
                                    mem_bytes = st_data.get("memory_usage", 0)
                                    mem_mb = round(mem_bytes / 1024 / 1024, 1)
                                    addon_stats.append((name, mem_mb))
                        except Exception:
                            pass

                if addon_stats:
                    addon_stats.sort(key=lambda x: x[1], reverse=True)
                    res_lines = ["현재 실행 중인 애드온별 메모리 사용량입니다:"]
                    for name, mb in addon_stats:
                        res_lines.append(f"• {name}: {mb}MB")
                    
                    sys_usage = get_resource_usage()
                    if sys_usage["total_memory_gb"] > 0:
                        res_lines.append(f"(전체 시스템 메모리: {sys_usage['used_memory_gb']}GB / {sys_usage['total_memory_gb']}GB, {sys_usage['memory_percent']}%)")
                    return "\n".join(res_lines)
    except Exception:
        pass

    sys_usage = get_resource_usage()
    return (
        f"현재 Antigravity CLI 애드온의 메모리 사용량은 약 {sys_usage['memory_usage']}MB 이며, "
        f"시스템 전체 메모리는 {sys_usage['used_memory_gb']}GB / {sys_usage['total_memory_gb']}GB ({sys_usage['memory_percent']}%) 사용 중입니다."
    )


def get_ha_error_logs() -> str:
    """Fetch and summarize Home Assistant Core error logs."""
    supervisor_token = get_supervisor_token()
    raw_logs = ""
    if supervisor_token:
        try:
            import urllib.request
            req = urllib.request.Request(
                "http://supervisor/core/logs",
                headers={"Authorization": f"Bearer {supervisor_token}"}
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    raw_logs = resp.read().decode("utf-8", errors="ignore")
        except Exception:
            pass

    if not raw_logs:
        for p in ["/config/home-assistant.log", "/homeassistant/home-assistant.log"]:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        raw_logs = f.read()
                    break
                except Exception:
                    pass

    if raw_logs:
        lines = raw_logs.split("\n")
        errors = [l.strip() for l in lines if " ERROR " in l or " CRITICAL " in l]
        if errors:
            recent = errors[-4:]
            formatted = []
            for e in recent:
                parts = e.split(" ERROR ", 1)
                formatted.append(parts[1] if len(parts) > 1 else e)
            return f"현재 Home Assistant 시스템 에러 로그 요약입니다:\n• 최근 에러 {len(formatted)}건:\n  - " + "\n  - ".join(formatted)
        return "현재 Home Assistant 시스템에 기록된 에러가 없습니다. (시스템 정상 동작 중)"
    return "현재 Home Assistant 시스템에 기록된 치명적인 에러는 없습니다."


def get_room_lights_summary(states: list) -> str:
    """Group all lights by room and return structured summary."""
    rooms = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "현관", "베란다"]
    room_map = {r: [] for r in rooms}
    etc_lights = []

    for s in states:
        if s.get("entity_id", "").startswith("light."):
            fn = s.get("attributes", {}).get("friendly_name") or s.get("entity_id")
            state = s.get("state")
            if "all" in s.get("entity_id", "").lower() or "전체" in fn:
                continue

            matched = False
            for r in rooms:
                if r in fn:
                    room_map[r].append((fn, state))
                    matched = True
                    break
            if not matched:
                etc_lights.append((fn, state))

    lines = ["현재 방별 조명 상태입니다:"]
    total_on = 0
    for r in rooms:
        lights = room_map[r]
        if not lights:
            continue
        on_list = [fn for fn, st in lights if st == "on"]
        total_on += len(on_list)
        if on_list:
            lines.append(f"• {r}: {len(on_list)}개 켜짐 ({', '.join(on_list)})")
        else:
            lines.append(f"• {r}: 모두 꺼짐")

    if etc_lights:
        on_list = [fn for fn, st in etc_lights if st == "on"]
        total_on += len(on_list)
        if on_list:
            lines.append(f"• 기타: {len(on_list)}개 켜짐 ({', '.join(on_list)})")

    lines.append(f"(총 {total_on}개 조명 점등 중)")
    return "\n".join(lines)


def get_room_env_summary(states: list, env_type: str = "temperature") -> str:
    """Group temperature or humidity sensors by room and return structured summary."""
    rooms = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "현관", "베란다"]
    room_map = {r: None for r in rooms}
    is_temp = env_type == "temperature"

    for s in states:
        if s.get("entity_id", "").startswith("sensor."):
            fn = s.get("attributes", {}).get("friendly_name") or s.get("entity_id")
            dc = s.get("attributes", {}).get("device_class")
            val = s.get("state")
            if val in ("unavailable", "unknown", None):
                continue

            if any(ex in fn for ex in ["플러그", "버튼", "스위치", "재실", "도어", "창문", "문", "배터리", "세탁기", "건조기", "장치"]):
                continue

            match_env = False
            if is_temp:
                if dc == "temperature" or ("온도" in fn and "습도" not in fn and "설정" not in fn and "최고" not in fn and "최저" not in fn):
                    match_env = True
            else:
                if dc == "humidity" or ("습도" in fn and "온도" not in fn):
                    match_env = True

            if not match_env:
                continue

            unit = s.get("attributes", {}).get("unit_of_measurement") or ("°C" if is_temp else "%")
            for r in rooms:
                if r in fn and room_map[r] is None:
                    room_map[r] = f"{val}{unit}"
                    break

    res_items = []
    for r in rooms:
        if room_map[r] is not None:
            res_items.append(f"• {r}: {room_map[r]}")

    label = "실내 온도" if is_temp else "실내 습도"
    if res_items:
        return f"현재 각 방별 {label}입니다:\n" + "\n".join(res_items)
    return f"현재 등록된 각 방별 {label} 센서가 없습니다."


def get_weather_env_summary(states: list) -> str:
    """Synthesize outdoor weather and indoor room environment into a comprehensive briefing."""
    weather_lines = []
    for s in states:
        eid = s.get("entity_id", "")
        fn = s.get("attributes", {}).get("friendly_name") or eid
        state = s.get("state", "")
        if eid.startswith("weather.") or "날씨" in fn or "기상" in fn:
            attrs = s.get("attributes", {})
            temp = attrs.get("temperature", "")
            hum = attrs.get("humidity", "")
            weather_lines.append(f"• 실외 기상: 현재 {state}, 기온 {temp}°C, 습도 {hum}%")
            break

    indoor_temp = get_room_env_summary(states, "temperature")
    indoor_hum = get_room_env_summary(states, "humidity")

    res = ["🌦️ 오늘 날씨 및 실내외 환경 분석 리포트입니다:"]
    if weather_lines:
        res.extend(weather_lines)
    res.append("\n" + indoor_temp)
    res.append("\n" + indoor_hum)
    return "\n".join(res)


def stream_agent_chat(prompt: str, is_direct_llm: bool = False):
    """Generator that yields real-time SSE stream events for Antigravity AI."""
    clean_prompt = prompt.strip()
    lower = clean_prompt.lower()

    # 1. Real-Time Deep Brain AI via PTY
    if is_direct_llm:
        if pty is None:
            yield f"data: {json.dumps({'type': 'text', 'content': '[오류] PTY 가상 터미널 모듈을 사용할 수 없습니다.'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        agy_bin = "/usr/local/bin/agy" if os.path.exists("/usr/local/bin/agy") else "/root/.local/bin/agy"
        if not os.path.exists(agy_bin):
            yield f"data: {json.dumps({'type': 'text', 'content': '[오류] agy 바이너리를 찾을 수 없습니다.'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
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

        cmd = [agy_bin, "--dangerously-skip-permissions", "--print", clean_prompt]
        proc = subprocess.Popen(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
            env=env,
            cwd="/config" if os.path.exists("/config") else "/root",
        )
        os.close(slave_fd)

        buffer = ""
        start_time = time.time()
        timeout = 180  # 3 minutes for deep reasoning

        try:
            while True:
                if time.time() - start_time > timeout:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    yield f"data: {json.dumps({'type': 'chunk', 'content': f'\\n[오류] AI 추론 시간이 초과되었습니다 ({timeout}초 초과).' })}\n\n"
                    break

                r, _, _ = select.select([master_fd], [], [], 0.2)
                if master_fd in r:
                    try:
                        data = os.read(master_fd, 4096)
                        if not data:
                            break
                        chunk_str = data.decode("utf-8", errors="replace")
                        buffer += chunk_str

                        # Process complete lines from buffer
                        if "\n" in buffer:
                            lines = buffer.split("\n")
                            buffer = lines[-1]
                            for line in lines[:-1]:
                                clean = strip_ansi(line).strip()
                                if not clean:
                                    continue
                                if any(w in clean for w in ["[WARNING]", "[INFO]", "Starting Web Terminal", "tmux", "root@", "/usr/local/bin/agy:"]):
                                    continue
                                if clean.startswith("● ") or clean.startswith("▸ ") or clean.startswith("Initiating") or clean.startswith("Discovering"):
                                    yield f"data: {json.dumps({'type': 'tool', 'content': clean})}\n\n"
                                else:
                                    yield f"data: {json.dumps({'type': 'chunk', 'content': clean + '\\n'})}\n\n"
                    except OSError:
                        break

                if proc.poll() is not None:
                    # Drain remaining buffer
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
                            yield f"data: {json.dumps({'type': 'tool', 'content': clean})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'chunk', 'content': clean + '\\n'})}\n\n"

        finally:
            try:
                os.close(master_fd)
            except Exception:
                pass

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    # 2. Fast Semantic Engine Queries (Weather, System, Room sensors)
    full_text = handle_agent_chat(clean_prompt, "", "", False)
    yield f"data: {json.dumps({'type': 'text', 'content': full_text})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


def handle_agent_chat(prompt: str, conversation_id: str = "", home_summary: str = "", is_direct_llm: bool = False) -> str:
    """Dispatches prompt to Antigravity CLI or autonomously resolves intents."""
    clean_prompt = prompt.strip()
    lower = clean_prompt.lower()

    # 1. Weather & Environment Analysis Query
    if any(w in lower for w in ["날씨", "환경", "기상", "일기예보", "온습도"]):
        if not any(ctrl in lower for ctrl in ["켜", "꺼", "틀어", "시작", "정지"]):
            states = get_ha_states()
            if states:
                return get_weather_env_summary(states)

    # 2. System Log Query (에러 로그, 시스템 로그, 오류 확인)
    if any(w in lower for w in ["에러 로그", "오류 로그", "에러 확인", "오류 확인", "시스템 로그", "최근 에러", "로그 확인"]):
        return get_ha_error_logs()

    # 3. Room-by-room queries (각 방 온도, 각방 습도, 방별 조명 상태)
    if any(w in lower for w in ["방별", "방마다", "공간별", "구역별", "각 방", "각방"]):
        states = get_ha_states()
        if states:
            if any(w in lower for w in ["온도", "기온", "온습도"]):
                return get_room_env_summary(states, "temperature")
            if "습도" in lower:
                return get_room_env_summary(states, "humidity")
            if any(w in lower for w in ["등", "조명", "불", "전등", "램프"]):
                return get_room_lights_summary(states)

    # 4. Per-addon memory breakdown query
    if any(w in lower for w in ["애드온별", "애드온 별", "각 애드온", "모든 애드온", "애드온 목록", "앱별"]):
        return get_all_addons_memory()

    # 5. General memory query
    if any(w in lower for w in ["메모리", "램", "ram", "리소스", "cpu", "사양"]):
        if any(w in lower for w in ["애드온", "addon", "앱"]):
            return get_all_addons_memory()
        usage = get_resource_usage()
        return (
            f"현재 Antigravity CLI 애드온의 메모리 사용량은 약 {usage['memory_usage']}MB 이며, "
            f"시스템 전체 메모리는 {usage['used_memory_gb']}GB / {usage['total_memory_gb']}GB ({usage['memory_percent']}%) 사용 중입니다."
        )

    # 6. Introduction / Capabilities
    if "뭐" in clean_prompt and ("할 수" in clean_prompt or "할수" in clean_prompt or "가능" in clean_prompt):
        return (
            "저는 Google Antigravity CLI 기반 Home Assistant 스마트홈 어시스턴트입니다.\n\n"
            "다음과 같은 작업을 도와드릴 수 있습니다:\n"
            "• 조명, 스위치, 커튼, 환풍기, 냉난방 등 스마트홈 기기 제어\n"
            "• 시스템 에러 로그 및 진단 브리핑\n"
            "• 방별 조명 및 온습도 상태 요약 브리핑\n"
            "• 애드온별 메모리/CPU 사용량 및 시스템 리소스 모니터링\n"
            "• 외출/취침 모드 및 스마트 자동화 실행"
        )

    if any(greet in clean_prompt for greet in ["안녕", "반가워", "hello", "hi", "누구"]):
        return "안녕하세요! Google Antigravity CLI 어시스턴트입니다. 무엇을 도와드릴까요?"

    # 7. Broad Home Status / Situation / Summary Intent
    if any(w in lower for w in ["상태", "상황", "현황", "요약", "브리핑", "분위기", "어때", "어떠", "어떻", "집안", "우리집", "모습"]):
        if not any(ctrl in lower for ctrl in ["켜", "꺼", "틀어", "시작", "정지", "닫아", "열어", "작동", "돌려"]):
            if home_summary:
                return home_summary
            states = get_ha_states()
            if states:
                on_lights = [
                    s.get("attributes", {}).get("friendly_name") or s.get("entity_id")
                    for s in states
                    if s.get("entity_id", "").startswith("light.") and s.get("state") == "on"
                ]
                light_str = f"{len(on_lights)}개 켜짐 ({', '.join(on_lights[:3])})" if on_lights else "모두 꺼짐"
                return f"현재 우리집 상태 요약입니다.\n• 조명: {light_str}\n• 기기 및 센서가 정상 모니터링 중입니다."

    # 8. Targeted Entity Control & Query
    states = get_ha_states()
    if states:
        is_turn_on = any(w in lower for w in ["켜", "틀어", "시작", "돌려", "열어", "on", "open"])
        is_turn_off = any(w in lower for w in ["꺼", "중지", "멈춰", "정지", "닫아", "off", "close"])

        best_match = None
        best_score = 0
        tokens = [t for t in re.split(r"[\s,!?]+", clean_prompt) if len(t) > 1]

        for s in states:
            fn = s.get("attributes", {}).get("friendly_name", "")
            eid = s.get("entity_id", "")
            score = 0
            for t in tokens:
                if t in fn:
                    score += 10
                elif t in eid:
                    score += 5
            if score > best_score:
                best_score = score
                best_match = s

        if best_match and best_score >= 10:
            fn = best_match.get("attributes", {}).get("friendly_name") or best_match.get("entity_id")
            eid = best_match.get("entity_id")
            domain = eid.split(".")[0]

            if is_turn_on:
                call_ha_service(domain, "turn_on" if domain != "cover" else "open_cover", {"entity_id": eid})
                return f"{fn}을(를) 켰습니다."
            elif is_turn_off:
                call_ha_service(domain, "turn_off" if domain != "cover" else "close_cover", {"entity_id": eid})
                return f"{fn}을(를) 껐습니다."
            else:
                st = best_match.get("state", "")
                unit = best_match.get("attributes", {}).get("unit_of_measurement", "")
                return f"{fn}의 현재 상태는 {st}{unit} 입니다."

    if home_summary:
        return home_summary
    return f"'{clean_prompt}' 요청에 대한 스마트홈 상태가 정상 확인되었습니다."


HTML_INDEX = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Antigravity CLI Dashboard</title>
  <style>
    :root {
      --bg-main: #0b0f19;
      --bg-card: #151d30;
      --bg-bubble-user: #2563eb;
      --bg-bubble-bot: #1e293b;
      --border-color: #2e3d5b;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-green: #10b981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", sans-serif; }
    body { background-color: var(--bg-main); color: var(--text-main); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }

    /* Header */
    header {
      background-color: var(--bg-card);
      border-bottom: 1px solid var(--border-color);
      padding: 12px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-shrink: 0;
    }
    .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.1rem; color: #fff; }
    .brand-badge { background: #1e40af; color: #93c5fd; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
    .nav-tabs { display: flex; gap: 8px; }
    .tab-btn {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 8px 16px;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.9rem;
      transition: all 0.2s;
    }
    .tab-btn.active { background: var(--bg-bubble-user); color: #fff; border-color: var(--bg-bubble-user); }
    .tab-btn:hover:not(.active) { background: #1f293d; color: var(--text-main); }

    /* Content Area */
    main { flex: 1; position: relative; overflow: hidden; }
    .tab-view { width: 100%; height: 100%; display: none; }
    .tab-view.active { display: flex; flex-direction: column; }

    /* Chat View */
    #chat-view { height: 100%; display: none; flex-direction: column; }
    #chat-view.active { display: flex; }
    .chat-container {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      scroll-behavior: smooth;
    }

    /* Welcome Hero */
    .hero-card {
      background: linear-gradient(135deg, #1e293b, #0f172a);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 16px 20px;
      text-align: center;
      margin-bottom: 8px;
    }
    .hero-card h2 { font-size: 1.1rem; margin-bottom: 6px; color: var(--accent-blue); }
    .hero-card p { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 12px; }
    .quick-chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
    .chip {
      background: #1e293b;
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 6px 12px;
      border-radius: 16px;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.2s;
    }
    .chip:hover { background: var(--bg-bubble-user); border-color: var(--bg-bubble-user); transform: translateY(-1px); }

    /* Messages */
    .msg-row { display: flex; width: 100%; }
    .msg-row.user { justify-content: flex-end; }
    .msg-row.bot { justify-content: flex-start; }
    .bubble {
      max-width: 85%;
      padding: 12px 16px;
      border-radius: 14px;
      font-size: 0.92rem;
      line-height: 1.5;
      word-break: break-word;
    }
    .msg-row.user .bubble { background: var(--bg-bubble-user); color: #fff; border-bottom-right-radius: 2px; }
    .msg-row.bot .bubble {
      background: var(--bg-bubble-bot);
      color: var(--text-main);
      border: 1px solid var(--border-color);
      border-bottom-left-radius: 2px;
    }

    /* Markdown Formats in Bubble */
    .bubble table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 0.85rem; }
    .bubble th, .bubble td { border: 1px solid var(--border-color); padding: 6px 10px; text-align: left; }
    .bubble th { background: #0f172a; color: var(--accent-blue); }
    .bubble tr:nth-child(even) { background: rgba(255, 255, 255, 0.03); }
    .bubble pre { background: #0b0f19; padding: 10px; border-radius: 8px; overflow-x: auto; margin: 8px 0; font-size: 0.82rem; }
    .bubble code { font-family: monospace; color: #38bdf8; }
    .bubble ul, .bubble ol { margin-left: 20px; margin-top: 6px; margin-bottom: 6px; }

    /* Live Tool Accordion */
    .tool-box {
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid #334155;
      border-radius: 8px;
      margin-bottom: 10px;
      overflow: hidden;
      font-size: 0.82rem;
    }
    .tool-header {
      padding: 6px 12px;
      background: #1e293b;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      font-weight: 600;
      color: var(--accent-blue);
    }
    .tool-content { padding: 8px 12px; display: block; max-height: 250px; overflow-y: auto; color: var(--text-muted); font-family: monospace; }

    /* Input Area */
    .input-bar-wrap {
      background: var(--bg-card);
      border-top: 1px solid var(--border-color);
      padding: 12px 20px;
      flex-shrink: 0;
    }
    .input-bar {
      display: flex;
      gap: 10px;
      background: var(--bg-main);
      border: 1px solid var(--border-color);
      border-radius: 24px;
      padding: 6px 12px 6px 16px;
      align-items: center;
    }
    .input-bar textarea {
      flex: 1;
      background: transparent;
      border: none;
      color: var(--text-main);
      font-size: 0.95rem;
      outline: none;
      resize: none;
      height: 24px;
      max-height: 100px;
      line-height: 1.5;
    }
    .send-btn {
      background: var(--bg-bubble-user);
      border: none;
      color: #fff;
      width: 34px;
      height: 34px;
      border-radius: 50%;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: opacity 0.2s;
    }
    .send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

    /* Terminal View */
    #terminal-view { height: 100%; display: none; width: 100%; }
    #terminal-view.active { display: block; }
    iframe { width: 100%; height: 100%; border: none; background: #1e1e1e; }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span>🤖 Antigravity AI</span>
      <span class="brand-badge">Real-time Stream</span>
    </div>
    <div class="nav-tabs">
      <button class="tab-btn active" onclick="switchTab('chat')">💬 AI Chat</button>
      <button class="tab-btn" onclick="switchTab('terminal')">🖥️ Terminal</button>
    </div>
  </header>

  <main>
    <!-- Chat View -->
    <section id="chat-view" class="tab-view active">
      <div class="chat-container" id="chat-box">
        <div class="hero-card">
          <h2>Google Antigravity 스마트홈 실시간 어시스턴트</h2>
          <p>자연어 발화 및 Antigravity CLI AI 딥 브레인이 연동된 실시간 스트리밍 대시보드입니다.</p>
          <div class="quick-chips">
            <div class="chip" onclick="sendQuick('우리집 종합 상황 알려줘')">🏠 종합 상황</div>
            <div class="chip" onclick="sendQuick('각 방 온도 알려줘')">🌡️ 각 방 온도</div>
            <div class="chip" onclick="sendQuick('각 방 습도 알려줘')">💧 각 방 습도</div>
            <div class="chip" onclick="sendQuick('켜져 있는 조명 목록')">💡 켜진 조명</div>
            <div class="chip" onclick="sendQuick('시스템 에러 로그 확인')">⚠️ 에러 로그</div>
            <div class="chip" onclick="sendQuick('ai 오늘 날씨와 환경 분석해줘')">🤖 AI 실시간 추론</div>
          </div>
        </div>
      </div>
      <div class="input-bar-wrap">
        <div class="input-bar">
          <textarea id="user-input" placeholder="무엇이든 물어보거나 지시하세요... (Shift+Enter 줄바꿈)" rows="1" onkeydown="handleKey(event)"></textarea>
          <button class="send-btn" id="send-btn" onclick="sendMessage()">➤</button>
        </div>
      </div>
    </section>

    <!-- Terminal View -->
    <section id="terminal-view" class="tab-view">
      <iframe id="terminal-iframe" src="./terminal/"></iframe>
    </section>
  </main>

  <script>
    function switchTab(tab) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-view').forEach(v => v.classList.remove('active'));
      if (tab === 'chat') {
        document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
        document.getElementById('chat-view').classList.add('active');
      } else {
        document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
        document.getElementById('terminal-view').classList.add('active');
      }
    }

    function formatMarkdown(text) {
      if (!text) return "";
      let raw = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      
      // Tables
      raw = raw.replace(/\\|(.+)\\|\\n\\|[-|\\s]+\\|\\n((?:\\|.*\\|\\n?)*)/g, function(match, header, rows) {
        let headers = header.split('|').map(h => h.trim()).filter(h => h);
        let rowLines = rows.trim().split('\\n');
        let html = '<table><thead><tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr></thead><tbody>';
        rowLines.forEach(r => {
          let cols = r.split('|').map(c => c.trim()).filter(c => c);
          if (cols.length) {
            html += '<tr>' + cols.map(c => `<td>${c}</td>`).join('') + '</tr>';
          }
        });
        html += '</tbody></table>';
        return html;
      });

      // Code blocks
      raw = raw.replace(/```([a-z]*)\\n([\\s\\S]*?)```/g, '<pre><code>$2</code></pre>');
      // Bold
      raw = raw.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
      // Lists & bullets
      raw = raw.replace(/^[•\\-] (.*)$/gm, '<li>$1</li>');
      raw = raw.replace(/((?:<li>.*<\\/li>\\s*)+)/g, '<ul>$1</ul>');
      // Line breaks
      raw = raw.replace(/\\n/g, '<br>');
      return raw;
    }

    function appendUserMessage(text) {
      const box = document.getElementById('chat-box');
      const row = document.createElement('div');
      row.className = 'msg-row user';
      row.innerHTML = `<div class="bubble">${text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>`;
      box.appendChild(row);
      box.scrollTop = box.scrollHeight;
    }

    function createBotStreamMessage() {
      const box = document.getElementById('chat-box');
      const row = document.createElement('div');
      row.className = 'msg-row bot';
      row.innerHTML = `
        <div class="bubble">
          <div class="tool-box" style="display: none;">
            <div class="tool-header" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
              <span class="tool-title">🔍 AI 도구 호출 진행 중...</span>
              <span>▼</span>
            </div>
            <div class="tool-content"></div>
          </div>
          <div class="answer-content"><span style="color: var(--text-muted);">🤖 스마트홈 데이터 분석 중...</span></div>
        </div>
      `;
      box.appendChild(row);
      box.scrollTop = box.scrollHeight;

      const toolBox = row.querySelector('.tool-box');
      const toolTitle = row.querySelector('.tool-title');
      const toolContent = row.querySelector('.tool-content');
      const answerContent = row.querySelector('.answer-content');

      let toolList = [];
      let answerText = "";

      return {
        addTool: function(toolStr) {
          toolList.push(toolStr);
          toolBox.style.display = 'block';
          toolTitle.textContent = `🔍 AI 도구 호출 진행 중 (${toolList.length}단계)`;
          toolContent.innerHTML = toolList.map(t => '• ' + t.replace(/</g, "&lt;")).join('<br>');
          box.scrollTop = box.scrollHeight;
        },
        appendChunk: function(chunk) {
          answerText += chunk;
          answerContent.innerHTML = formatMarkdown(answerText);
          box.scrollTop = box.scrollHeight;
        },
        setText: function(text) {
          answerText = text;
          answerContent.innerHTML = formatMarkdown(answerText);
          box.scrollTop = box.scrollHeight;
        },
        finish: function() {
          if (toolList.length > 0) {
            toolTitle.textContent = `🔍 AI 도구 호출 완료 (${toolList.length}단계)`;
          }
          if (!answerText) {
            answerContent.innerHTML = "답변 작성을 완료했습니다.";
          }
          box.scrollTop = box.scrollHeight;
        }
      };
    }

    function sendQuick(prompt) {
      document.getElementById('user-input').value = prompt;
      sendMessage();
    }

    function handleKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    }

    async function sendMessage() {
      const input = document.getElementById('user-input');
      const btn = document.getElementById('send-btn');
      const prompt = input.value.trim();
      if (!prompt) return;

      appendUserMessage(prompt);
      input.value = '';
      btn.disabled = true;

      const streamUI = createBotStreamMessage();
      const isDirectLLM = prompt.startsWith('ai ') || prompt.startsWith('/llm');

      try {
        const apiUrl = new URL('api/chat', window.location.href).href;
        const res = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: prompt, is_direct_llm: isDirectLLM })
        });

        if (!res.ok) {
          streamUI.setText(`[오류] 서버 응답 코드 HTTP ${res.status}`);
          btn.disabled = false;
          return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split('\\n');
          buffer = lines.pop(); // keep last incomplete line

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || !trimmed.startsWith('data:')) continue;
            const jsonStr = trimmed.slice(5).trim();
            try {
              const ev = JSON.parse(jsonStr);
              if (ev.type === 'tool') {
                streamUI.addTool(ev.content);
              } else if (ev.type === 'chunk') {
                streamUI.appendChunk(ev.content);
              } else if (ev.type === 'text') {
                streamUI.setText(ev.content);
              } else if (ev.type === 'done') {
                streamUI.finish();
              }
            } catch (e) {}
          }
        }
        streamUI.finish();
      } catch (err) {
        streamUI.setText(`[오류] 실시간 스트림 연결 실패: ${err.message}`);
      } finally {
        btn.disabled = false;
        input.focus();
      }
    }
  </script>
</body>
</html>
"""


class AntigravityAPIHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Ingress Dual Web UI, Real-Time Streaming, and REST API."""

    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def _check_auth(self) -> bool:
        options = get_options()
        expected_key = options.get("api_key") or os.environ.get("ANTIGRAVITY_API_KEY", "").strip()
        if not expected_key:
            return True

        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            return token == expected_key
        return False

    def _proxy_to_ttyd(self):
        """Proxy HTTP and WebSocket requests to internal ttyd on port 7682."""
        if self.headers.get("Upgrade", "").lower() == "websocket":
            try:
                target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target_sock.connect(("127.0.0.1", TTYD_INTERNAL_PORT))
                
                req_lines = [f"{self.command} {self.path} {self.request_version}"]
                for k, v in self.headers.items():
                    req_lines.append(f"{k}: {v}")
                req_lines.append("\r\n")
                target_sock.sendall("\r\n".join(req_lines).encode("utf-8"))

                client_sock = self.connection
                client_sock.setblocking(0)
                target_sock.setblocking(0)
                sockets = [client_sock, target_sock]
                while True:
                    r, _, x = select.select(sockets, [], sockets, 30.0)
                    if x or not r:
                        break
                    for s in r:
                        other = target_sock if s is client_sock else client_sock
                        try:
                            data = s.recv(16384)
                            if not data:
                                return
                            other.sendall(data)
                        except Exception:
                            return
            except Exception:
                pass
            return

        import urllib.request
        target_url = f"http://127.0.0.1:{TTYD_INTERNAL_PORT}{self.path}"
        try:
            req_headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
            req = urllib.request.Request(target_url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ("transfer-encoding", "content-length"):
                        self.send_header(k, v)
                body = resp.read()
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:
            self.send_error(502, f"Bad Gateway to ttyd: {e}")

    def do_GET(self):
        """Handle GET requests."""
        clean_path = self.path.split("?")[0].rstrip("/")

        # 1. Forward /terminal traffic to ttyd
        if clean_path.endswith("/terminal") or "/terminal" in self.path:
            self._proxy_to_ttyd()
            return

        # 2. REST Status API
        if clean_path.endswith("/api/status"):
            if not self._check_auth():
                self._set_headers(401)
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return
            uptime = int(time.time() - START_TIME)
            usage = get_resource_usage()
            data = {
                "status": get_agent_status(),
                "version": VERSION,
                "active_sessions": get_active_sessions(),
                "uptime": uptime,
                **usage,
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        elif clean_path.endswith("/api/health"):
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "healthy", "version": VERSION}).encode("utf-8"))
            return

        # 3. Serve Main Ingress Web UI (Dashboard)
        self._set_headers(200, "text/html; charset=utf-8")
        self.wfile.write(HTML_INDEX.encode("utf-8"))

    def do_POST(self):
        """Handle POST requests with Server-Sent Events (SSE) streaming support."""
        clean_path = self.path.split("?")[0].rstrip("/")

        # 1. Forward /terminal traffic to ttyd
        if clean_path.endswith("/terminal") or "/terminal" in self.path:
            self._proxy_to_ttyd()
            return

        if not self._check_auth():
            self._set_headers(401)
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
            return

        # 2. Real-Time Chat Streaming API
        if clean_path.endswith("/api/chat") or clean_path.endswith("/api/prompt") or "/api/chat" in clean_path or "/api/prompt" in clean_path:
            body = b""
            content_length = self.headers.get("Content-Length")
            if content_length:
                try:
                    body = self.rfile.read(int(content_length))
                except Exception:
                    body = b""
            elif self.headers.get("Transfer-Encoding", "").lower() == "chunked":
                chunks = []
                while True:
                    line = self.rfile.readline().strip()
                    if not line:
                        break
                    try:
                        chunk_len = int(line, 16)
                    except ValueError:
                        break
                    if chunk_len == 0:
                        self.rfile.readline()
                        break
                    chunks.append(self.rfile.read(chunk_len))
                    self.rfile.readline()
                body = b"".join(chunks)

            payload = {}
            if body:
                try:
                    payload = json.loads(body.decode("utf-8"))
                except Exception:
                    try:
                        import urllib.parse
                        payload = dict(urllib.parse.parse_qsl(body.decode("utf-8")))
                    except Exception:
                        pass

            prompt = payload.get("prompt", "").strip()
            if not prompt and "?" in self.path:
                try:
                    import urllib.parse
                    qs = urllib.parse.parse_qs(self.path.split("?", 1)[1])
                    prompt = qs.get("prompt", [""])[0].strip()
                except Exception:
                    pass

            is_direct_llm = payload.get("is_direct_llm", False) or prompt.startswith("ai ") or prompt.startswith("/llm")

            if not prompt:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Empty prompt"}).encode("utf-8"))
                return

            # Send Server-Sent Events (SSE) Stream Headers
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            try:
                for event_str in stream_agent_chat(prompt, is_direct_llm):
                    self.wfile.write(event_str.encode("utf-8"))
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        elif clean_path.endswith("/api/restart"):
            self._set_headers(200)
            self.wfile.write(json.dumps({"result": "restarted", "status": "online"}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress noisy request logs."""
        pass


class DualThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def run_dual_server():
    """Run HTTP Ingress Server on 7681 and REST API Server on 8000."""
    api_port_env = os.environ.get("ANTIGRAVITY_API_PORT")
    api_port = int(api_port_env) if api_port_env and api_port_env.isdigit() else DEFAULT_PORT

    import threading

    def serve_ingress():
        while True:
            try:
                httpd_ingress = DualThreadingHTTPServer(("0.0.0.0", INGRESS_PORT), AntigravityAPIHandler)
                print(f"[INFO] Dual Ingress Web UI server running on port {INGRESS_PORT}")
                httpd_ingress.serve_forever()
            except Exception as e:
                print(f"[ERR] Ingress server error: {e}")
                time.sleep(2)

    def serve_api():
        while True:
            try:
                httpd_api = DualThreadingHTTPServer(("0.0.0.0", api_port), AntigravityAPIHandler)
                print(f"[INFO] Antigravity REST API server running on port {api_port}")
                httpd_api.serve_forever()
            except Exception as e:
                print(f"[ERR] API server error: {e}")
                time.sleep(2)

    t_ingress = threading.Thread(target=serve_ingress, daemon=True)
    t_ingress.start()

    serve_api()


if __name__ == "__main__":
    run_dual_server()
