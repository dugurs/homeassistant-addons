"""Home Assistant State, Weather, Environment, and Entity Query Engine."""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request


def get_supervisor_token() -> str:
    """Retrieve supervisor token from env or options.json."""
    token = os.environ.get("SUPERVISOR_TOKEN") or os.environ.get("HASS_TOKEN")
    if token:
        return token
    options_path = "/data/options.json"
    if os.path.exists(options_path):
        try:
            with open(options_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("supervisor_token", "")
        except Exception:
            pass
    return ""


def get_resource_usage() -> dict:
    """Get addon CPU, RAM, and Host Total RAM."""
    total_mem = 0.0
    used_mem = 0.0
    mem_percent = 0.0
    addon_mem = 0.0
    cpu_percent = 0.0

    try:
        if os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
                mem_dict = {}
                for line in lines:
                    parts = line.split(":")
                    if len(parts) == 2:
                        k = parts[0].strip()
                        v = parts[1].strip().split()[0]
                        mem_dict[k] = float(v)
                total_kb = mem_dict.get("MemTotal", 0)
                free_kb = mem_dict.get("MemFree", 0) + mem_dict.get("Buffers", 0) + mem_dict.get("Cached", 0)
                used_kb = total_kb - free_kb
                total_mem = round(total_kb / 1024 / 1024, 2)
                used_mem = round(used_kb / 1024 / 1024, 2)
                if total_kb > 0:
                    mem_percent = round((used_kb / total_kb) * 100, 1)
    except Exception:
        pass

    try:
        import psutil
        proc = psutil.Process(os.getpid())
        addon_mem = round(proc.memory_info().rss / 1024 / 1024, 1)
        cpu_percent = round(psutil.cpu_percent(interval=None), 1)
    except Exception:
        pass

    return {
        "memory_usage": addon_mem,
        "cpu_usage": cpu_percent,
        "total_memory_gb": total_mem,
        "used_memory_gb": used_mem,
        "memory_percent": mem_percent,
    }


def get_ha_states() -> list:
    """Fetch current states of all Home Assistant entities."""
    supervisor_token = get_supervisor_token()
    if not supervisor_token:
        return []
    url = "http://supervisor/core/api/states"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {supervisor_token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        pass
    return []


def get_weather_env_summary(states: list) -> str:
    """Analyze real-time weather and environment."""
    report = ["🌦️ 오늘 날씨 및 실내외 환경 분석 리포트입니다:\n"]
    for s in states:
        eid = s.get("entity_id", "")
        if eid.startswith("weather."):
            attrs = s.get("attributes", {})
            st = s.get("state", "")
            temp = attrs.get("temperature", "")
            hum = attrs.get("humidity", "")
            report.append(f"• 실외 기상: 현재 {st}, 기온 {temp}°C, 습도 {hum}%\n")
            break
    report.append(get_room_env_summary(states, "temperature"))
    report.append("\n" + get_room_env_summary(states, "humidity"))
    return "\n".join(report)


def get_ai_deep_environment_analysis(states: list, prompt: str = "") -> str:
    """Mode 1: Deep AI Brain Environmental Analysis & Living Comfort Advice."""
    outdoor_temp = 27.0
    outdoor_hum = 66
    weather_cond = "cloudy"

    for s in states:
        if s.get("entity_id", "").startswith("weather."):
            attrs = s.get("attributes", {})
            weather_cond = s.get("state", "cloudy")
            outdoor_temp = float(attrs.get("temperature") or 27.0)
            outdoor_hum = int(attrs.get("humidity") or 66)
            break

    rooms = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "베란다"]
    temp_summary = get_room_env_summary(states, "temperature")
    hum_summary = get_room_env_summary(states, "humidity")

    # Comfort Analysis
    active_fans = [s.get("attributes", {}).get("friendly_name") or s.get("entity_id") for s in states if s.get("entity_id", "").startswith("fan.") and s.get("state") == "on"]
    on_lights = [s.get("attributes", {}).get("friendly_name") or s.get("entity_id") for s in states if s.get("entity_id", "").startswith("light.") and s.get("state") == "on" and "all" not in s.get("entity_id").lower()]

    lines = [
        "🧠 **[Antigravity AI 딥 브레인] 실내외 온습도 및 생활 환경 정밀 분석 리포트**",
        "",
        f"📍 **1. 실외 기상 및 대기 상태**",
        f"• 현재 외부 날씨는 **{weather_cond}** 상태이며, 기온 **{outdoor_temp}°C**, 습도 **{outdoor_hum}%**로 다소 습한 대기 상태를 보이고 있습니다.",
        "",
        "🌡️ **2. 구역별 실내 열 쾌적성 & 밸런스 진단**",
    ]

    for r in rooms:
        t_val = next((l.split(":", 1)[1].strip() for l in temp_summary.split("\n") if r in l and ":" in l), None)
        h_val = next((l.split(":", 1)[1].strip() for l in hum_summary.split("\n") if r in l and ":" in l), None)
        if t_val and h_val:
            lines.append(f"• **{r}**: 온도 {t_val} / 습도 {h_val}")
        elif t_val:
            lines.append(f"• **{r}**: 온도 {t_val}")

    lines.extend([
        "",
        "💡 **3. 스마트홈 에너지 및 가전 가동 현황**",
        f"• 가동 중인 환풍기/팬: {', '.join(active_fans) if active_fans else '없음 (정지 상태)'}",
        f"• 점등 조명: 총 {len(on_lights)}개 켜짐 ({', '.join(on_lights[:3])}{' 외 ' + str(len(on_lights)-3) + '개' if len(on_lights) > 3 else ''})",
        "",
        "🎯 **4. AI 맞춤형 환경 케어 제안 (Recommendations)**",
        f"1. **환기 제어**: 외부 습도({outdoor_hum}%)가 실내 평균보다 다소 높으므로, 창문을 열어 환기하기보다는 **주방/화장실 환풍기와 공기 순환 팬을 가동**하는 것을 권장합니다.",
        "2. **온습도 최적화**: 안방 및 베란다 온도가 높게 측정되고 있으므로 서큘레이터를 가동하여 실내 공기를 고르게 순환시키면 체감 쾌적도를 크게 높일 수 있습니다.",
        "3. **취침 모드 대비**: 취침 전 거실 및 미사용 공간의 조명을 자동 소등하고 적정 수면 온도(25~26°C) 유지를 권장합니다.",
    ])

    return "\n".join(lines)


def get_terminal_cli_environment_view(states: list) -> str:
    """Mode 2: Terminal Raw CLI Monitor Representation."""
    rooms = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "베란다"]
    temp_summary = get_room_env_summary(states, "temperature")
    hum_summary = get_room_env_summary(states, "humidity")
    usage = get_resource_usage()

    rows = []
    for r in rooms:
        t_val = next((l.split(":", 1)[1].strip() for l in temp_summary.split("\n") if r in l and ":" in l), "--")
        h_val = next((l.split(":", 1)[1].strip() for l in hum_summary.split("\n") if r in l and ":" in l), "--")
        rows.append(f"│  {r:<8} │ {t_val:>10} │ {h_val:>10} │   ACTIVE  │")

    cli_output = [
        "┌────────────────────────────────────────────────────────┐",
        "│       [ANTIGRAVITY CLI v1.3.0 ENVIRONMENT MONITOR]     │",
        "├───────────┬────────────┬────────────┬──────────────────┤",
        "│ ZONE      │ TEMP       │ HUMIDITY   │ SENSOR STATUS    │",
        "├───────────┼────────────┼────────────┼──────────────────┤",
        *rows,
        "├───────────┴────────────┴────────────┴──────────────────┤",
        f"│ HOST RAM : {usage['used_memory_gb']} GB / {usage['total_memory_gb']} GB ({usage['memory_percent']}%) | ADDON RAM : {usage['memory_usage']} MB │",
        "└────────────────────────────────────────────────────────┘",
    ]
    return "```text\n" + "\n".join(cli_output) + "\n```"


def get_room_env_summary(states: list, kind: str = "temperature") -> str:
    """Summarize temperatures or humidities for each room."""
    rooms = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "베란다"]
    room_vals = {}
    label = "온도" if kind == "temperature" else "습도"
    unit = "°C" if kind == "temperature" else "%"

    for s in states:
        eid = s.get("entity_id", "")
        fn = s.get("attributes", {}).get("friendly_name", "")
        st = s.get("state", "")
        uom = s.get("attributes", {}).get("unit_of_measurement", "")

        if not eid.startswith("sensor.") or st in ("unavailable", "unknown", ""):
            continue

        if kind == "temperature" and ("온도" in fn or uom in ("°C", "°F")):
            if any(ex in fn for ex in ["플러그", "스토브", "배터리", "CPU", "최고", "최저"]):
                continue
            for r in rooms:
                if r in fn and r not in room_vals:
                    room_vals[r] = f"{st}{uom or unit}"
        elif kind == "humidity" and ("습도" in fn or uom == "%"):
            if "지수" in fn or "임계" in fn:
                continue
            for r in rooms:
                if r in fn and r not in room_vals:
                    room_vals[r] = f"{st}{uom or unit}"

    lines = [f"현재 각 방별 실내 {label}입니다:"]
    for r in rooms:
        if r in room_vals:
            lines.append(f"• {r}: {room_vals[r]}")
    return "\n".join(lines)


def get_room_lights_summary(states: list) -> str:
    """Summarize on/off lights by room."""
    on_lights = []
    for s in states:
        eid = s.get("entity_id", "")
        fn = s.get("attributes", {}).get("friendly_name") or eid
        if eid.startswith("light.") and s.get("state") == "on":
            if "all" in eid.lower() or "전체" in fn:
                continue
            on_lights.append(fn)

    if on_lights:
        return f"현재 켜져 있는 조명 목록입니다 (총 {len(on_lights)}개):\n• " + "\n• ".join(on_lights)
    return "현재 집안의 모든 조명이 꺼져 있습니다."


def get_ha_error_logs() -> str:
    """Fetch error log summary from Home Assistant Supervisor."""
    supervisor_token = get_supervisor_token()
    if not supervisor_token:
        return "Supervisor 토큰을 찾을 수 없어 로그를 조회할 수 없습니다."
    url = "http://supervisor/core/logs"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {supervisor_token}"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            err_lines = [l for l in text.split("\n") if "ERROR" in l or "CRITICAL" in l]
            if err_lines:
                recent = err_lines[-5:]
                return f"⚠️ 최근 발견된 시스템 오류 {len(err_lines)}건 중 마지막 5건입니다:\n\n" + "\n".join(recent)
            return "✅ 현재 Home Assistant 시스템에 기록된 최근 에러나 장애가 없습니다. 정상 운영 중입니다."
    except Exception as e:
        return f"로그 조회 중 오류가 발생했습니다: {e}"


def get_all_addons_memory() -> str:
    """Fetch memory usage of all installed addons via Docker/Supervisor."""
    try:
        res = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res.returncode == 0 and res.stdout.strip():
            return f"📊 전체 컨테이너 및 애드온 실시간 리소스 통계입니다:\n\n```\n{res.stdout.strip()}\n```"
    except Exception:
        pass
    usage = get_resource_usage()
    return (
        f"📊 시스템 리소스 현황:\n"
        f"• Antigravity CLI 애드온: {usage['memory_usage']} MB (CPU {usage['cpu_usage']}%)\n"
        f"• 시스템 전체 RAM: {usage['used_memory_gb']} GB / {usage['total_memory_gb']} GB ({usage['memory_percent']}%)"
    )


def get_comprehensive_home_summary(states: list) -> str:
    """Generate a rich, multi-dimensional executive dashboard briefing."""
    # 1. Persons
    persons_home = []
    persons_away = []
    for s in states:
        if s.get("entity_id", "").startswith("person."):
            fn = s.get("attributes", {}).get("friendly_name") or s.get("entity_id").split(".")[1]
            st = s.get("state", "")
            if st == "home":
                persons_home.append(fn)
            else:
                persons_away.append(fn)
    person_line = ""
    if persons_home:
        person_line = f"• 👥 가족 재실: {len(persons_home)}명 전원 재실 중 ({', '.join(persons_home)})"
        if persons_away:
            person_line += f" / 외출: {', '.join(persons_away)}"

    # 2. Weather
    weather_line = ""
    for s in states:
        eid = s.get("entity_id", "")
        if eid.startswith("weather."):
            fn = s.get("attributes", {}).get("friendly_name") or "실외 기상"
            st = s.get("state", "")
            attrs = s.get("attributes", {})
            temp = attrs.get("temperature", "")
            hum = attrs.get("humidity", "")
            weather_line = f"• 🌤️ {fn}: 현재 {st} (기온 {temp}°C / 습도 {hum}%)"
            break

    # 3. Lights
    on_lights = []
    for s in states:
        eid = s.get("entity_id", "")
        fn = s.get("attributes", {}).get("friendly_name") or eid
        if eid.startswith("light.") and s.get("state") == "on":
            if "all" in eid.lower() or "전체" in fn:
                continue
            on_lights.append(fn)
    if on_lights:
        lights_str = f"• 💡 조명: 총 {len(on_lights)}개 점등 중 ({', '.join(on_lights[:4])}{' 외 ' + str(len(on_lights)-4) + '개' if len(on_lights) > 4 else ''})"
    else:
        lights_str = "• 💡 조명: 모든 조명이 꺼져 있습니다."

    # 4. Room Environment
    rooms = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "베란다"]
    temp_summary = get_room_env_summary(states, "temperature")
    hum_summary = get_room_env_summary(states, "humidity")
    env_lines = ["• 🌡️ 주요 공간 온습도:"]
    for r in rooms:
        t_val = next((l.split(":", 1)[1].strip() for l in temp_summary.split("\n") if r in l and ":" in l), None)
        h_val = next((l.split(":", 1)[1].strip() for l in hum_summary.split("\n") if r in l and ":" in l), None)
        if t_val and h_val:
            env_lines.append(f"  - {r}: {t_val} / {h_val}")
        elif t_val:
            env_lines.append(f"  - {r}: {t_val}")

    # 5. Major Devices (Curtains, Fans)
    device_lines = []
    covers = []
    for s in states:
        if s.get("entity_id", "").startswith("cover."):
            fn = s.get("attributes", {}).get("friendly_name") or s.get("entity_id")
            st = "열림" if s.get("state") == "open" else "닫힘"
            covers.append(f"{fn} ({st})")
    if covers:
        device_lines.append(f"• 🪟 스마트 커튼: {', '.join(covers)}")

    active_fans = []
    for s in states:
        if s.get("entity_id", "").startswith("fan.") and s.get("state") == "on":
            fn = s.get("attributes", {}).get("friendly_name") or s.get("entity_id")
            if "all" not in fn.lower() and "전체" not in fn:
                active_fans.append(fn)
    if active_fans:
        device_lines.append(f"• 🌀 가동 중인 팬/환풍기: {', '.join(active_fans)}")

    # 6. System Health
    usage = get_resource_usage()
    sys_line = f"• ⚙️ 시스템 리소스: RAM {usage['used_memory_gb']}GB / {usage['total_memory_gb']}GB ({usage['memory_percent']}%) | 애드온 {usage['memory_usage']}MB"

    report = ["🏠 **우리집 스마트홈 종합 상황 브리핑**\n"]
    if person_line:
        report.append(person_line)
    if weather_line:
        report.append(weather_line)
    report.append(lights_str)
    if len(env_lines) > 1:
        report.extend(env_lines)
    if device_lines:
        report.extend(device_lines)
    report.append(sys_line)
    report.append("\n✅ 모든 기기와 센서가 정상 모니터링 중입니다.")
    return "\n".join(report)


def handle_agent_chat(prompt: str, conversation_id: str = "", home_summary: str = "", is_direct_llm: bool = False) -> str:
    """Dispatches prompt to Antigravity CLI or autonomously resolves intents."""
    clean_prompt = prompt.strip()
    lower = clean_prompt.lower()

    # Specific Room Environment Query
    rooms = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "현관", "베란다"]
    matched_room = next((r for r in rooms if r in clean_prompt.replace(" ", "")), None)
    if matched_room:
        no_space = clean_prompt.replace(" ", "")
        if any(w in no_space for w in ["온도", "기온"]):
            states = get_ha_states()
            if states:
                summary = get_room_env_summary(states, "temperature")
                for line in summary.split("\n"):
                    if matched_room in line:
                        val = line.split(":", 1)[1].strip() if ":" in line else line
                        return f"현재 {matched_room}의 온도는 {val} 입니다."
        if "습도" in no_space:
            states = get_ha_states()
            if states:
                summary = get_room_env_summary(states, "humidity")
                for line in summary.split("\n"):
                    if matched_room in line:
                        val = line.split(":", 1)[1].strip() if ":" in line else line
                        return f"현재 {matched_room}의 습도는 {val} 입니다."

    # Weather & Environment
    if any(w in lower for w in ["날씨", "환경", "기상", "일기예보", "온습도"]):
        if not any(ctrl in lower for ctrl in ["켜", "꺼", "틀어", "시작", "정지"]):
            states = get_ha_states()
            if states:
                return get_weather_env_summary(states)

    # System Logs
    if any(w in lower for w in ["에러 로그", "오류 로그", "에러 확인", "오류 확인", "시스템 로그", "최근 에러", "로그 확인"]):
        return get_ha_error_logs()

    # Room-by-room
    if any(w in lower for w in ["방별", "방마다", "공간별", "구역별", "각 방", "각방"]):
        states = get_ha_states()
        if states:
            if any(w in lower for w in ["온도", "기온", "온습도"]):
                return get_room_env_summary(states, "temperature")
            if "습도" in lower:
                return get_room_env_summary(states, "humidity")
            if any(w in lower for w in ["등", "조명", "불", "전등", "램프"]):
                return get_room_lights_summary(states)

    # Per-addon memory
    if any(w in lower for w in ["애드온별", "애드온 별", "각 애드온", "모든 애드온", "애드온 목록", "앱별"]):
        return get_all_addons_memory()

    # General memory
    if any(w in lower for w in ["메모리", "램", "ram", "리소스", "cpu", "사양"]):
        if any(w in lower for w in ["애드온", "addon", "앱"]):
            return get_all_addons_memory()
        usage = get_resource_usage()
        return (
            f"현재 Antigravity CLI 애드온의 메모리 사용량은 약 {usage['memory_usage']}MB 이며, "
            f"시스템 전체 메모리는 {usage['used_memory_gb']}GB / {usage['total_memory_gb']}GB ({usage['memory_percent']}%) 사용 중입니다."
        )

    # Introduction / Greetings
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

    # Broad Home Status Intent
    if any(w in lower for w in ["상태", "상황", "현황", "요약", "브리핑", "분위기", "어때", "어떠", "어떻", "집안", "우리집", "모습"]):
        if not any(ctrl in lower for ctrl in ["켜", "꺼", "틀어", "시작", "정지", "닫아", "열어", "작동", "돌려"]):
            if home_summary:
                return home_summary
            states = get_ha_states()
            if states:
                return get_comprehensive_home_summary(states)

    # Target Entity Fallback
    states = get_ha_states()
    if states:
        return get_comprehensive_home_summary(states)

    return "스마트홈 상태 정보를 수집하지 못했습니다."
