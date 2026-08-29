"""Multi-Mode Responsive Markdown View Generators."""

from core.sensors import get_dynamic_rooms, get_room_env_summary
from core.system_info import get_resource_usage


def generate_dynamic_ai_recommendations(
    outdoor_temp: float,
    outdoor_hum: int,
    temp_map: dict,
    hum_map: dict,
    active_fans: list,
    on_lights: list,
) -> list:
    """Dynamically synthesize personalized smart home care recommendations from real-time conditions."""
    recs = []

    # 1. Ventilation & Humidity Difference
    indoor_hums = [
        float(v.replace("%", "").strip())
        for v in hum_map.values()
        if v and v.replace("%", "").strip().replace(".", "", 1).isdigit()
    ]
    avg_indoor_hum = sum(indoor_hums) / len(indoor_hums) if indoor_hums else 60.0

    if outdoor_hum >= 70 and outdoor_hum > avg_indoor_hum:
        recs.append(
            f"• **환기 제어**: 외부 습도({outdoor_hum}%)가 실내 평균({avg_indoor_hum:.1f}%)보다 높습니다. 창문 개방 대신 **주방/화장실 환풍기 및 제습 장치 가동**을 권장합니다."
        )
    elif outdoor_hum <= 55 and outdoor_hum < avg_indoor_hum:
        recs.append(
            f"• **자연 환기**: 외부 습도가 {outdoor_hum}%로 쾌적합니다. 창문을 열어 **실내 공기 순환 및 자연 환기**를 진행하기 좋은 조건입니다."
        )
    else:
        recs.append(
            "• **공기질 관리**: 실내외 습도가 유사하므로 주방 및 화장실 환풍기를 필요에 따라 간헐적으로 가동하세요."
        )

    # 2. Overheated or Cold Rooms Targeting
    hot_rooms = []
    cold_rooms = []
    indoor_temps = []
    for r, v in temp_map.items():
        try:
            num = float(v.replace("°C", "").replace("°F", "").strip())
            indoor_temps.append(num)
            if num >= 30.0:
                hot_rooms.append((r, num))
            elif num <= 20.0:
                cold_rooms.append((r, num))
        except Exception:
            pass

    if hot_rooms:
        hot_str = ", ".join([f"**{r}**({t}°C)" for r, t in hot_rooms[:2]])
        recs.append(
            f"• **온열 환경 케어**: 현재 {hot_str}의 온도가 높게 측정되고 있으므로 서큘레이터를 가동하여 공기를 순환시키거나 냉방을 가동하세요."
        )
    elif cold_rooms:
        cold_str = ", ".join([f"**{r}**({t}°C)" for r, t in cold_rooms[:2]])
        recs.append(
            f"• **온열 환경 케어**: 현재 {cold_str}의 온도가 낮습니다. 단열 상태를 점검하거나 난방 설정을 확인하세요."
        )
    else:
        avg_t = sum(indoor_temps) / len(indoor_temps) if indoor_temps else 25.0
        recs.append(
            f"• **온습도 최적화**: 전 구역 실내 온도가 쾌적 범위(평균 {avg_t:.1f}°C) 내에서 안정적으로 유지되고 있습니다."
        )

    # 3. Appliances & Energy Optimization
    if len(on_lights) >= 5:
        recs.append(
            f"• **에너지 절약**: 현재 {len(on_lights)}개의 조명이 켜져 있습니다. 미사용 구역의 소등을 검토하세요."
        )
    elif len(active_fans) == 0 and hot_rooms:
        recs.append(
            "• **에너지 케어**: 실내 과열 구역이 있으나 팬이 정지 상태입니다. 공기 순환 팬 가동 시 냉방 효율을 높일 수 있습니다."
        )
    else:
        recs.append(
            "• **안심 스마트홈**: 주요 기기들이 정상 상태로 작동 중이며 취침 전 일괄 소등 자동화를 권장합니다."
        )

    return recs


def get_weather_env_summary(states: list, is_mobile: bool = False) -> str:
    """Mode 3: Analyze real-time weather and environment with responsive Markdown."""
    weather_cond = "cloudy"
    temp = "27.0"
    hum = "66"
    for s in states:
        eid = s.get("entity_id", "")
        if eid.startswith("weather."):
            attrs = s.get("attributes", {})
            weather_cond = s.get("state", "cloudy")
            temp = str(attrs.get("temperature", "27.0"))
            hum = str(attrs.get("humidity", "66"))
            break

    rooms = get_dynamic_rooms(states)
    temp_summary = get_room_env_summary(states, "temperature")
    hum_summary = get_room_env_summary(states, "humidity")

    if is_mobile:
        lines = [
            "🌦️ **스마트홈 실시간 환경 대시보드 (모바일)**",
            f"> [!NOTE] 실외 기상: **{weather_cond}** ({temp}°C / {hum}%)",
            "",
            "🌡️ **구역별 실내 온습도**",
        ]
        for r in rooms:
            t_val = next((l.split(":", 1)[1].strip() for l in temp_summary.split("\n") if r in l and ":" in l), "--")
            h_val = next((l.split(":", 1)[1].strip() for l in hum_summary.split("\n") if r in l and ":" in l), "--")
            lines.append(f"• **{r}**: `{t_val}` / `{h_val}`")
        return "\n".join(lines)

    table_rows = []
    for r in rooms:
        t_val = next((l.split(":", 1)[1].strip() for l in temp_summary.split("\n") if r in l and ":" in l), "--")
        h_val = next((l.split(":", 1)[1].strip() for l in hum_summary.split("\n") if r in l and ":" in l), "--")
        table_rows.append(f"| **{r}** | {t_val} | {h_val} |")

    lines = [
        "🌦️ **스마트홈 실시간 환경 대시보드**",
        f"> [!NOTE] 실외 기상: **{weather_cond}** | 기온 **{temp}°C** | 습도 **{hum}%**",
        "",
        "| 구역 (Zone) | 실내 온도 | 실내 습도 |",
        "| :--- | :--- | :--- |",
        *table_rows,
    ]
    return "\n".join(lines)


def get_ai_deep_environment_analysis(states: list, prompt: str = "", is_mobile: bool = False) -> str:
    """Mode 1: Deep AI Brain Environmental Analysis & Dynamic Contextual Synthesis."""
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

    rooms = get_dynamic_rooms(states)
    temp_summary = get_room_env_summary(states, "temperature")
    hum_summary = get_room_env_summary(states, "humidity")

    temp_map = {}
    hum_map = {}
    for l in temp_summary.split("\n"):
        if ":" in l:
            k, v = l.split(":", 1)
            temp_map[k.replace("•", "").strip()] = v.strip()
    for l in hum_summary.split("\n"):
        if ":" in l:
            k, v = l.split(":", 1)
            hum_map[k.replace("•", "").strip()] = v.strip()

    active_fans = [s.get("attributes", {}).get("friendly_name") or s.get("entity_id") for s in states if s.get("entity_id", "").startswith("fan.") and s.get("state") == "on"]
    on_lights = [s.get("attributes", {}).get("friendly_name") or s.get("entity_id") for s in states if s.get("entity_id", "").startswith("light.") and s.get("state") == "on" and "all" not in s.get("entity_id").lower()]

    recs = generate_dynamic_ai_recommendations(outdoor_temp, outdoor_hum, temp_map, hum_map, active_fans, on_lights)

    if is_mobile:
        lines = [
            "🧠 **[AI 딥 브레인] 스마트홈 환경 진단 (모바일)**",
            f"> [!NOTE] 외부 기상: **{weather_cond}** ({outdoor_temp}°C / {outdoor_hum}%)",
            "",
            "🌡️ **실내 온습도 현황**",
        ]
        for r in rooms:
            t_val = temp_map.get(r, "--")
            h_val = hum_map.get(r, "--")
            lines.append(f"• **{r}**: `{t_val}` / `{h_val}`")

        lines.extend([
            "",
            "💡 **가전 가동 현황**",
            f"• 가동 팬: {len(active_fans)}대 가동 중",
            f"• 켜진 조명: {len(on_lights)}개 점등",
            "",
            "> [!TIP] 🎯 AI 실시간 상황 맞춤 제안",
            *recs,
        ])
        return "\n".join(lines)

    table_rows = []
    for r in rooms:
        t_val = temp_map.get(r, "--")
        h_val = hum_map.get(r, "--")
        if t_val == "--" and h_val == "--":
            continue
        
        eval_text = "🟢 쾌적"
        try:
            temp_num = float(t_val.replace("°C", "").replace("°F", "").strip())
            if temp_num >= 30:
                eval_text = "🟡 냉방 필요"
            elif temp_num <= 20:
                eval_text = "🔵 난방 필요"
        except Exception:
            pass
        table_rows.append(f"| **{r}** | {t_val} | {h_val} | {eval_text} |")

    lines = [
        "🧠 **[Antigravity AI 딥 브레인] 실내외 온습도 및 생활 환경 정밀 분석 리포트**",
        "",
        f"📍 **1. 실외 기상 및 대기 상태**",
        f"• 현재 외부 날씨는 **{weather_cond}** 상태이며, 기온 **{outdoor_temp}°C**, 습도 **{outdoor_hum}%** 대기 상태를 보이고 있습니다.",
        "",
        "🌡️ **2. 구역별 실내 열 쾌적성 & 환경 매트릭스**",
        "| 구역 (Zone) | 현재 온도 | 현재 습도 | 환경 진단 |",
        "| :--- | :--- | :--- | :--- |",
        *table_rows,
        "",
        "💡 **3. 스마트홈 에너지 및 가전 가동 현황**",
        f"• 가동 중인 환풍기/팬: {', '.join(active_fans) if active_fans else '없음 (정지 상태)'}",
        f"• 점등 조명: 총 {len(on_lights)}개 켜짐 ({', '.join(on_lights[:3])}{' 외 ' + str(len(on_lights)-3) + '개' if len(on_lights) > 3 else ''})",
        "",
        "> [!TIP] 🎯 AI 실시간 상황 맞춤 제안 (Dynamic Recommendations)",
        *recs,
    ]
    return "\n".join(lines)


def get_terminal_cli_environment_view(states: list, is_mobile: bool = False) -> str:
    """Mode 2: Terminal Raw CLI Monitor Representation adapted for Mobile/Desktop."""
    rooms = get_dynamic_rooms(states)
    temp_summary = get_room_env_summary(states, "temperature")
    hum_summary = get_room_env_summary(states, "humidity")
    usage = get_resource_usage()

    if is_mobile:
        rows = []
        for r in rooms:
            t_val = next((l.split(":", 1)[1].strip() for l in temp_summary.split("\n") if r in l and ":" in l), "--")
            h_val = next((l.split(":", 1)[1].strip() for l in hum_summary.split("\n") if r in l and ":" in l), "--")
            rows.append(f"│ {r:<4} │ {t_val:>7} │ {h_val:>6} │")

        cli_output = [
            "┌──────────────────────────────────┐",
            "│ [ANTIGRAVITY CLI MOBILE MONITOR] │",
            "├──────┬─────────┬────────┤",
            "│ ZONE │ TEMP    │ HUMID  │",
            "├──────┼─────────┼────────┤",
            *rows,
            "├──────┴─────────┴────────┤",
            f"│ RAM: {usage['used_memory_gb']}/{usage['total_memory_gb']}G ({usage['memory_percent']}%) │",
            "└──────────────────────────────────┘",
        ]
        return "```text\n" + "\n".join(cli_output) + "\n```"

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


def get_comprehensive_home_summary(states: list, is_mobile: bool = False) -> str:
    """Generate a rich, multi-dimensional executive dashboard briefing."""
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

    rooms = get_dynamic_rooms(states)
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

    covers = []
    for s in states:
        if s.get("entity_id", "").startswith("cover."):
            fn = s.get("attributes", {}).get("friendly_name") or s.get("entity_id")
            st = "열림" if s.get("state") == "open" else "닫힘"
            covers.append(f"{fn} ({st})")

    active_fans = []
    for s in states:
        if s.get("entity_id", "").startswith("fan.") and s.get("state") == "on":
            fn = s.get("attributes", {}).get("friendly_name") or s.get("entity_id")
            if "all" not in fn.lower() and "전체" not in fn:
                active_fans.append(fn)

    usage = get_resource_usage()
    sys_line = f"• ⚙️ 시스템 리소스: RAM {usage['used_memory_gb']}GB / {usage['total_memory_gb']}GB ({usage['memory_percent']}%) | 애드온 {usage['memory_usage']}MB"

    report = ["🏠 **우리집 스마트홈 종합 상황 브리핑**\n"]
    if person_line:
        report.append(person_line)
    if weather_line:
        report.append(weather_line)
    report.append(lights_str)
    report.append("\n".join(env_lines))
    if covers:
        report.append(f"• 🪟 스마트 커튼: {', '.join(covers)}")
    if active_fans:
        report.append(f"• 🌀 가동 중인 팬/환풍기: {', '.join(active_fans)}")
    report.append(sys_line)

    return "\n".join(report)
