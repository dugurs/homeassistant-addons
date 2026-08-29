"""Multi-Mode Responsive Markdown View Generators with Multi-Dimensional Sensor Support."""

from core.sensors import get_dynamic_rooms, get_room_env_matrix, get_room_env_summary
from core.system_info import get_resource_usage


def evaluate_room_env_health(room_data: dict) -> str:
    """Diagnose comprehensive environmental health for a single room."""
    if not room_data:
        return "⚪ 데이터 없음"

    # 1. Critical Air Quality (CO2, TVOC, PM2.5)
    co2_val = room_data.get("co2", {}).get("value")
    if co2_val is not None:
        if co2_val >= 1500:
            return "🔴 즉시 환기 요망(CO2)"
        elif co2_val >= 1000:
            return "🟡 환기 필요(CO2)"

    tvoc_val = room_data.get("tvoc", {}).get("value")
    tvoc_unit = room_data.get("tvoc", {}).get("unit", "").lower()
    if tvoc_val is not None:
        if "ppb" in tvoc_unit:
            if tvoc_val >= 220:
                return "🔴 유해가스 경고(VOC)"
            elif tvoc_val >= 80:
                return "🟡 공기질 주의(VOC)"
        else:
            if tvoc_val >= 660:
                return "🔴 유해가스 경고(VOC)"
            elif tvoc_val >= 250:
                return "🟡 공기질 주의(VOC)"

    pm25_val = room_data.get("pm25", {}).get("value")
    if pm25_val is not None:
        if pm25_val >= 75:
            return "🔴 초미세먼지 경고"
        elif pm25_val >= 35:
            return "🟠 공기질 주의(PM2.5)"

    # 2. Thermal Comfort (Temperature, Humidity)
    temp_val = room_data.get("temperature", {}).get("value")
    if temp_val is not None:
        if temp_val >= 30.0:
            return "🟡 냉방 필요"
        elif temp_val <= 18.0:
            return "🔵 난방 필요"

    hum_val = room_data.get("humidity", {}).get("value")
    if hum_val is not None:
        if hum_val >= 68.0:
            return "🟡 다습(제습 권장)"
        elif hum_val <= 35.0:
            return "🟡 건조(가습 권장)"

    return "🟢 쾌적"


def generate_dynamic_ai_recommendations(
    outdoor_temp: float,
    outdoor_hum: int,
    temp_map: dict,
    hum_map: dict,
    active_fans: list,
    on_lights: list,
    env_matrix: dict = None,
    outdoor_pm25: float = None,
) -> list:
    """Dynamically synthesize personalized smart home care recommendations from real-time conditions."""
    recs = []
    matrix = env_matrix.get("matrix", {}) if env_matrix else {}

    # --- 1. CO2 Air Quality & Ventilation Intelligence ---
    co2_findings = []
    for r, r_data in matrix.items():
        if "co2" in r_data:
            co2_findings.append((r, r_data["co2"]["value"]))

    if co2_findings:
        co2_findings.sort(key=lambda x: x[1], reverse=True)
        max_room, max_co2 = co2_findings[0]
        if max_co2 >= 1500:
            recs.append(
                f"• 🚨 **실내 이산화탄소 경고**: 현재 **{max_room}**({max_co2:.0f} ppm)의 CO2 농도가 매우 높습니다. 두통 및 집중력 저하가 발생할 수 있으므로 **즉시 창문을 열고 환풍기/전열교환기를 최대 풍량으로 가동**하세요."
            )
        elif max_co2 >= 1000:
            recs.append(
                f"• ⚠️ **공기 환기 권장**: **{max_room}**의 CO2 농도가 {max_co2:.0f} ppm으로 높아지고 있습니다. 10~15분간 자연 환기를 진행하거나 환기 장치를 켜는 것을 권장합니다."
            )
        elif max_co2 < 800:
            recs.append(
                f"• 🍃 **청정 실내 공기**: 실내 CO2 농도(최고 {max_co2:.0f} ppm)가 쾌적 수준으로 유지되어 학습 및 휴식에 적합합니다."
            )

    # --- 2. TVOC Hazardous Gas & VOC Recommendations ---
    tvoc_findings = []
    for r, r_data in matrix.items():
        if "tvoc" in r_data:
            tvoc_findings.append((r, r_data["tvoc"]["value"], r_data["tvoc"].get("unit", "µg/m³")))

    if tvoc_findings:
        tvoc_findings.sort(key=lambda x: x[1], reverse=True)
        t_room, t_val, t_unit = tvoc_findings[0]
        is_ppb = "ppb" in t_unit.lower()
        if (is_ppb and t_val >= 220) or (not is_ppb and t_val >= 660):
            recs.append(
                f"• ⚠️ **휘발성 유기화합물(TVOC) 주의**: **{t_room}**의 TVOC 농도({t_val:.0f} {t_unit})가 기준치를 초과했습니다. 조리 연기나 화학제품 사용 여부를 확인하고 **주방 후드 및 환풍기를 가동**하세요."
            )
        elif (is_ppb and t_val >= 80) or (not is_ppb and t_val >= 250):
            recs.append(
                f"• 🟡 **실내 유기화합물(TVOC) 관리**: **{t_room}**의 TVOC 수치({t_val:.0f} {t_unit})가 다소 상승 중입니다. 환풍기 가동 또는 맞바람 환기를 권장합니다."
            )

    # --- 3. Particulate Matter (PM2.5) & Outdoor Quality Fusion ---
    pm25_findings = []
    for r, r_data in matrix.items():
        if "pm25" in r_data:
            pm25_findings.append((r, r_data["pm25"]["value"]))

    if pm25_findings:
        pm25_findings.sort(key=lambda x: x[1], reverse=True)
        p_room, p_val = pm25_findings[0]
        if p_val >= 75:
            recs.append(
                f"• 🚨 **초미세먼지(PM2.5) 경고**: **{p_room}**의 초미세먼지 농도({p_val:.0f} µg/m³)가 매우 나쁩니다. 창문을 닫고 **공기청정기를 터보 모드**로 즉시 가동하세요."
            )
        elif p_val >= 35:
            if outdoor_pm25 is not None and outdoor_pm25 >= 36:
                recs.append(
                    f"• 🛑 **미세먼지 내부 순환**: 실외 미세먼지 유입 위험이 있으므로 창문을 닫고, **공기청정기 내부 순환 모드**를 가동하세요."
                )
            else:
                recs.append(
                    f"• 🌪️ **실내 미세먼지 배출**: **{p_room}**의 초미세먼지({p_val:.0f} µg/m³)가 다소 높습니다. 외부 공기가 양호하므로 창문을 열어 **맞바람 환기 및 공기청정기 가동**을 권장합니다."
                )

    # --- 4. Humidity & Thermal Balance ---
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
    elif outdoor_hum <= 55 and outdoor_hum < avg_indoor_hum and not co2_findings:
        recs.append(
            f"• **자연 환기**: 외부 습도가 {outdoor_hum}%로 쾌적합니다. 창문을 열어 **실내 공기 순환 및 자연 환기**를 진행하기 좋은 조건입니다."
        )

    # --- 5. Overheated or Cold Rooms Targeting ---
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
    elif not co2_findings and not tvoc_findings and not pm25_findings:
        avg_t = sum(indoor_temps) / len(indoor_temps) if indoor_temps else 25.0
        recs.append(
            f"• **온습도 최적화**: 전 구역 실내 온도가 쾌적 범위(평균 {avg_t:.1f}°C) 내에서 안정적으로 유지되고 있습니다."
        )

    # --- 6. Appliances & Energy Optimization ---
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
    """Mode 3: Analyze real-time weather and multi-dimensional environment with responsive dynamic Markdown."""
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

    env_data = get_room_env_matrix(states)
    rooms = env_data["rooms"]
    active_metrics = env_data["active_metrics"]
    matrix = env_data["matrix"]
    metric_labels = env_data["metric_labels"]

    if is_mobile:
        lines = [
            "🌦️ **스마트홈 실시간 환경 대시보드 (모바일)**",
            f"> [!NOTE] 실외 기상: **{weather_cond}** ({temp}°C / {hum}%)",
            "",
            "🌡️ **구역별 실내 다차원 환경 지표**",
        ]
        for r in rooms:
            r_data = matrix.get(r, {})
            metric_strs = []
            for m in active_metrics:
                if m in r_data:
                    metric_strs.append(f"{metric_labels[m]} `{r_data[m]['formatted']}`")
            if metric_strs:
                lines.append(f"• **{r}**: {' | '.join(metric_strs)}")
            else:
                lines.append(f"• **{r}**: `--`")
        return "\n".join(lines)

    # Desktop Table with Dynamic Columns
    header_cols = ["구역 (Zone)"] + [metric_labels[m] for m in active_metrics]
    sep_cols = [":---"] + [":---" for _ in active_metrics]
    header_line = "| " + " | ".join(header_cols) + " |"
    sep_line = "| " + " | ".join(sep_cols) + " |"

    table_rows = []
    for r in rooms:
        r_data = matrix.get(r, {})
        row_vals = [f"**{r}**"]
        for m in active_metrics:
            val_str = r_data.get(m, {}).get("formatted", "--")
            row_vals.append(val_str)
        table_rows.append("| " + " | ".join(row_vals) + " |")

    lines = [
        "🌦️ **스마트홈 실시간 환경 대시보드**",
        f"> [!NOTE] 실외 기상: **{weather_cond}** | 기온 **{temp}°C** | 습도 **{hum}%**",
        "",
        header_line,
        sep_line,
        *table_rows,
    ]
    return "\n".join(lines)


def get_ai_deep_environment_analysis(states: list, prompt: str = "", is_mobile: bool = False) -> str:
    """Mode 1: Deep AI Brain Environmental Analysis & Dynamic Contextual Synthesis."""
    outdoor_temp = 27.0
    outdoor_hum = 66
    outdoor_pm25 = None
    weather_cond = "cloudy"

    for s in states:
        if s.get("entity_id", "").startswith("weather."):
            attrs = s.get("attributes", {})
            weather_cond = s.get("state", "cloudy")
            outdoor_temp = float(attrs.get("temperature") or 27.0)
            outdoor_hum = int(attrs.get("humidity") or 66)
            if "pm25" in attrs:
                try:
                    outdoor_pm25 = float(attrs["pm25"])
                except Exception:
                    pass
            break

    env_data = get_room_env_matrix(states)
    rooms = env_data["rooms"]
    matrix = env_data["matrix"]
    metric_labels = env_data["metric_labels"]

    # Only include primary indoor comfort metrics in the main table (exclude illuminance & PMs from table)
    table_metrics = [m for m in ["temperature", "humidity", "co2", "tvoc"] if m in env_data["active_metrics"]]
    if not table_metrics:
        table_metrics = ["temperature", "humidity"]

    temp_map = {r: matrix.get(r, {}).get("temperature", {}).get("formatted", "--") for r in rooms}
    hum_map = {r: matrix.get(r, {}).get("humidity", {}).get("formatted", "--") for r in rooms}

    active_fans = [
        s.get("attributes", {}).get("friendly_name") or s.get("entity_id")
        for s in states
        if s.get("entity_id", "").startswith("fan.") and s.get("state") == "on"
    ]
    on_lights = [
        s.get("attributes", {}).get("friendly_name") or s.get("entity_id")
        for s in states
        if s.get("entity_id", "").startswith("light.") and s.get("state") == "on" and "all" not in s.get("entity_id", "").lower()
    ]

    recs = generate_dynamic_ai_recommendations(
        outdoor_temp,
        outdoor_hum,
        temp_map,
        hum_map,
        active_fans,
        on_lights,
        env_matrix=env_data,
        outdoor_pm25=outdoor_pm25,
    )

    # Extract clean PM2.5 & PM10 sentence
    pm_parts = []
    for r in rooms:
        r_data = matrix.get(r, {})
        pm25 = r_data.get("pm25", {}).get("formatted")
        pm10 = r_data.get("pm10", {}).get("formatted")
        if pm25 and pm10:
            pm_parts.append(f"**{r}** 초미세먼지(PM2.5) **{pm25}** / 미세먼지(PM10) **{pm10}**")
        elif pm25:
            pm_parts.append(f"**{r}** 초미세먼지(PM2.5) **{pm25}**")

    if outdoor_pm25 is not None:
        pm_line = f"- 실외 초미세먼지: **{outdoor_pm25} µg/m³**" + (f" | 실내: {', '.join(pm_parts)}" if pm_parts else "")
    elif pm_parts:
        pm_line = f"- 실내 공기질: {', '.join(pm_parts)}"
    else:
        pm_line = "- 실내외 미세먼지 수치가 쾌적한 청정 상태를 유지하고 있습니다."

    if is_mobile:
        lines = [
            "🧠 **[AI 딥 브레인] 스마트홈 환경 진단 (모바일)**",
            f"> [!NOTE] 외부 기상: **{weather_cond}** ({outdoor_temp}°C / {outdoor_hum}%)",
            "",
            "🍃 **실내외 미세먼지 및 공기 청정도**",
            pm_line,
            "",
            "🌡️ **실내 온습도 & CO2 현황**",
        ]
        for r in rooms:
            r_data = matrix.get(r, {})
            metric_strs = []
            for m in table_metrics:
                if m in r_data:
                    metric_strs.append(f"{metric_labels[m]} `{r_data[m]['formatted']}`")
            health = evaluate_room_env_health(r_data)
            metrics_joined = " | ".join(metric_strs) if metric_strs else "--"
            lines.append(f"• **{r}**: {metrics_joined} → **{health}**")

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

    # Desktop Table: Slim, focused on Temperature, Humidity, CO2 (No Illuminance or PM columns)
    header_cols = ["구역 (Zone)"] + [f"현재 {metric_labels[m]}" for m in table_metrics] + ["종합 환경 진단"]
    sep_cols = [":---"] + [":---" for _ in table_metrics] + [":---"]
    header_line = "| " + " | ".join(header_cols) + " |"
    sep_line = "| " + " | ".join(sep_cols) + " |"

    table_rows = []
    for r in rooms:
        r_data = matrix.get(r, {})
        if not r_data:
            continue
        row_vals = [f"**{r}**"]
        for m in table_metrics:
            val_str = r_data.get(m, {}).get("formatted", "--")
            row_vals.append(val_str)
        health = evaluate_room_env_health(r_data)
        row_vals.append(health)
        table_rows.append("| " + " | ".join(row_vals) + " |")

    lines = [
        "🧠 **[Antigravity AI 딥 브레인] 실내외 환경 및 공기질 정밀 분석 리포트**",
        "",
        "📍 **1. 실외 기상 및 대기 상태**",
        f"- 현재 외부 날씨는 **{weather_cond}** 상태이며, 기온 **{outdoor_temp}°C**, 습도 **{outdoor_hum}%** 입니다.",
        "",
        "🍃 **2. 실내외 미세먼지 및 공기 청정도**",
        pm_line,
        "",
        "🌡️ **3. 구역별 실내 열 쾌적성 & CO2 매트릭스**",
        header_line,
        sep_line,
        *table_rows,
        "",
        "💡 **4. 스마트홈 에너지 및 가전 가동 현황**",
        f"- 가동 중인 환풍기/팬: {', '.join(active_fans) if active_fans else '없음 (정지 상태)'}",
        f"- 점등 조명: 총 {len(on_lights)}개 켜짐 ({', '.join(on_lights[:3])}{' 외 ' + str(len(on_lights)-3) + '개' if len(on_lights) > 3 else ''})",
        "",
        "> [!TIP] 🎯 AI 실시간 상황 맞춤 제안 (Dynamic Recommendations)",
        *recs,
    ]
    return "\n".join(lines)





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
        person_line = f"- 👥 **가족 재실**: {len(persons_home)}명 전원 재실 중 ({', '.join(persons_home)})"
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
            weather_line = f"- 🌤️ **{fn}**: 현재 **{st}** (기온 {temp}°C / 습도 {hum}%)"
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
        lights_str = f"- 💡 **조명**: 총 {len(on_lights)}개 점등 중 ({', '.join(on_lights[:4])}{' 외 ' + str(len(on_lights)-4) + '개' if len(on_lights) > 4 else ''})"
    else:
        lights_str = "- 💡 **조명**: 모든 조명이 꺼져 있습니다."

    env_data = get_room_env_matrix(states)
    rooms = env_data["rooms"]
    matrix = env_data["matrix"]
    env_lines = ["- 🌡️ **주요 공간 다차원 환경**:"]
    for r in rooms:
        r_data = matrix.get(r, {})
        t_val = r_data.get("temperature", {}).get("formatted")
        h_val = r_data.get("humidity", {}).get("formatted")
        parts = []
        if t_val and h_val:
            parts.append(f"{t_val} / {h_val}")
        elif t_val:
            parts.append(t_val)

        if "co2" in r_data:
            parts.append(f"CO2 {r_data['co2']['formatted']}")
        if "pm25" in r_data:
            parts.append(f"PM2.5 {r_data['pm25']['formatted']}")

        if parts:
            env_lines.append(f"  - **{r}**: {' | '.join(parts)}")

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
    sys_line = f"- ⚙️ **시스템 리소스**: RAM {usage['used_memory_gb']}GB / {usage['total_memory_gb']}GB ({usage['memory_percent']}%) | 애드온 {usage['memory_usage']}MB"

    report = ["🏠 **우리집 스마트홈 종합 상황 브리핑**\n"]
    if person_line:
        report.append(person_line)
    if weather_line:
        report.append(weather_line)
    report.append(lights_str)
    report.extend(env_lines)
    if covers:
        report.append(f"- 🪟 **스마트 커튼**: {', '.join(covers)}")
    if active_fans:
        report.append(f"- 🌀 **가동 중인 팬/환풍기**: {', '.join(active_fans)}")
    report.append(sys_line)

    return "\n".join(report)
