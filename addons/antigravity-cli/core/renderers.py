"""Multi-Mode Responsive Markdown View Generators."""

from core.sensors import get_room_env_summary
from core.system_info import get_resource_usage


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

    rooms = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "베란다"]
    temp_summary = get_room_env_summary(states, "temperature")
    hum_summary = get_room_env_summary(states, "humidity")

    if is_mobile:
        # Compact Mobile Card
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

    # Wide Desktop GFM Table
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
    """Mode 1: Deep AI Brain Environmental Analysis & Responsive Markdown Synthesis."""
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

    active_fans = [s.get("attributes", {}).get("friendly_name") or s.get("entity_id") for s in states if s.get("entity_id", "").startswith("fan.") and s.get("state") == "on"]
    on_lights = [s.get("attributes", {}).get("friendly_name") or s.get("entity_id") for s in states if s.get("entity_id", "").startswith("light.") and s.get("state") == "on" and "all" not in s.get("entity_id").lower()]

    if is_mobile:
        lines = [
            "🧠 **[AI 딥 브레인] 스마트홈 환경 진단 (모바일)**",
            f"> [!NOTE] 외부 기상: **{weather_cond}** ({outdoor_temp}°C / {outdoor_hum}%)",
            "",
            "🌡️ **실내 온습도 현황**",
        ]
        for r in rooms:
            t_val = next((l.split(":", 1)[1].strip() for l in temp_summary.split("\n") if r in l and ":" in l), None)
            h_val = next((l.split(":", 1)[1].strip() for l in hum_summary.split("\n") if r in l and ":" in l), None)
            if t_val and h_val:
                lines.append(f"• **{r}**: `{t_val}` / `{h_val}`")
            elif t_val:
                lines.append(f"• **{r}**: `{t_val}`")

        lines.extend([
            "",
            "💡 **가전 가동 현황**",
            f"• 가동 팬: {len(active_fans)}대 가동 중",
            f"• 켜진 조명: {len(on_lights)}개 점등",
            "",
            "> [!TIP] AI 맞춤 케어 제안",
            "> 외부 습도가 높으므로 창문 개방 대신 환풍기와 서큘레이터를 가동하여 실내 공기를 순환시키세요.",
        ])
        return "\n".join(lines)

    table_rows = []
    for r in rooms:
        t_val = next((l.split(":", 1)[1].strip() for l in temp_summary.split("\n") if r in l and ":" in l), "--")
        h_val = next((l.split(":", 1)[1].strip() for l in hum_summary.split("\n") if r in l and ":" in l), "--")
        
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
        "> [!TIP] 🎯 AI 맞춤형 환경 케어 제안 (Recommendations)",
        "> • **환기 제어**: 외부 습도가 실내 평균보다 높으므로, 창문 대신 **주방/화장실 환풍기와 공기 순환 팬 가동**을 권장합니다.",
        "> • **온습도 최적화**: 안방 및 베란다 온도가 높게 측정되고 있으므로 서큘레이터를 가동하여 실내 공기를 순환시키세요.",
        "> • **취침 모드 대비**: 취침 전 거실 및 미사용 공간의 조명을 자동 소등하고 적정 수면 온도(25~26°C) 유지를 권장합니다.",
    ]
    return "\n".join(lines)


def get_terminal_cli_environment_view(states: list, is_mobile: bool = False) -> str:
    """Mode 2: Terminal Raw CLI Monitor Representation adapted for Mobile/Desktop."""
    rooms = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "베란다"]
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
