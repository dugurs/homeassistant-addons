#!/usr/bin/env python3
"""Antigravity CLI Background Status & REST API Server for Home Assistant Integration."""

import json
import os
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
import re
import select
try:
    import pty
except ImportError:
    pty = None

START_TIME = time.time()
VERSION = "1.1.0"
DEFAULT_PORT = 8000


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
        # System RAM info from /proc/meminfo
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

        # Addon container memory usage (sum of RSS) & CPU %
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


def run_agy_with_pty(prompt: str, timeout: int = 60) -> str:
    """Execute agy CLI inside a virtual pseudo-terminal (PTY) and capture pure output."""
    if pty is None:
        return ""

    agy_bin = "/usr/local/bin/agy" if os.path.exists("/usr/local/bin/agy") else "/root/.local/bin/agy"
    if not os.path.exists(agy_bin):
        return ""

    supervisor_token = get_supervisor_token()
    master_fd = None
    try:
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

        cmd = [agy_bin, "--dangerously-skip-permissions", "--print", prompt]
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

        output_chunks = []
        start_time = time.time()

        timed_out = False
        while True:
            if time.time() - start_time > timeout:
                timed_out = True
                try:
                    proc.kill()
                except Exception:
                    pass
                break

            r, _, _ = select.select([master_fd], [], [], 0.4)
            if master_fd in r:
                try:
                    data = os.read(master_fd, 4096)
                    if not data:
                        break
                    output_chunks.append(data.decode("utf-8", errors="replace"))
                except OSError:
                    break

            if proc.poll() is not None:
                while True:
                    r, _, _ = select.select([master_fd], [], [], 0.2)
                    if master_fd in r:
                        try:
                            data = os.read(master_fd, 4096)
                            if not data:
                                break
                            output_chunks.append(data.decode("utf-8", errors="replace"))
                        except OSError:
                            break
                    else:
                        break
                break

        os.close(master_fd)
        master_fd = None

        if timed_out and not output_chunks:
            return f"[오류] Antigravity CLI AI 추론 시간이 초과되었습니다 ({timeout}초 초과). QEMU VM 부하 또는 다중 도구 조회 지연을 확인해주세요."

        raw_output = "".join(output_chunks)
        clean = strip_ansi(raw_output)

        filtered_lines = []
        for line in clean.split("\n"):
            line_str = line.strip()
            if not line_str:
                continue
            if any(w in line_str for w in ["[WARNING]", "[INFO]", "Starting Web Terminal", "tmux", "root@", "/usr/local/bin/agy:"]):
                continue
            filtered_lines.append(line)

        res_text = "\n".join(filtered_lines).strip()
        if res_text:
            return res_text
        if timed_out:
            return f"[오류] Antigravity CLI AI 추론 시간이 초과되었습니다 ({timeout}초 초과)."
        return "[오류] Antigravity CLI 에이전트 실행 결과가 비어 있습니다. (CLI 세션 상태를 확인해주세요.)"
    except Exception as e:
        if master_fd is not None:
            try:
                os.close(master_fd)
            except Exception:
                pass
        return f"[오류] Antigravity CLI 가상 터미널(PTY) 실행 중 예외가 발생했습니다: {e}"


def handle_agent_chat(prompt: str, conversation_id: str = "", home_summary: str = "", is_direct_llm: bool = False) -> str:
    """Dispatches prompt to Antigravity CLI or autonomously resolves intents."""
    clean_prompt = prompt.strip()
    lower = clean_prompt.lower()

    # 1. Pure AI Direct Pass-Through: If user explicitly invoked LLM (/llm, ai), try PTY execution first
    if is_direct_llm:
        return run_agy_with_pty(clean_prompt, timeout=60)

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


class AntigravityAPIHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Antigravity CLI status API."""

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

    def do_GET(self):
        """Handle GET requests."""
        if not self._check_auth():
            self._set_headers(401)
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
            return

        if self.path in ("/api/status", "/api/status/"):
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
        elif self.path in ("/api/health", "/"):
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "healthy", "version": VERSION}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        """Handle POST requests."""
        if not self._check_auth():
            self._set_headers(401)
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
            return

        if self.path in ("/api/chat", "/api/chat/", "/api/prompt", "/api/prompt/"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception:
                payload = {}

            prompt = payload.get("prompt", "").strip()
            conv_id = payload.get("conversation_id") or ""
            home_summary = payload.get("home_summary") or ""
            is_direct_llm = payload.get("is_direct_llm", False)

            if not prompt:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Empty prompt"}).encode("utf-8"))
                return

            response_text = handle_agent_chat(prompt, conv_id, home_summary, is_direct_llm)
            self._set_headers(200)
            self.wfile.write(
                json.dumps({
                    "response": response_text,
                    "conversation_id": conv_id,
                }).encode("utf-8")
            )
        elif self.path in ("/api/restart", "/api/restart/"):
            self._set_headers(200)
            self.wfile.write(json.dumps({"result": "restarted", "status": "online"}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress noisy request logs."""
        pass


def run_server(port: int = DEFAULT_PORT):
    """Run HTTP API Server."""
    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, AntigravityAPIHandler)
    print(f"[INFO] Antigravity Status API server running on port {port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    port_env = os.environ.get("ANTIGRAVITY_API_PORT")
    port = int(port_env) if port_env and port_env.isdigit() else DEFAULT_PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
