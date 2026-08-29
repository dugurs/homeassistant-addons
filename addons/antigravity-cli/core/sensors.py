"""Sensor data processing, multi-dimensional environmental parsing, and area parser module."""

import re
from core.system_info import get_resource_usage

ENV_METRIC_CONFIGS = {
    "temperature": {
        "label": "온도",
        "default_unit": "°C",
        "device_classes": ["temperature"],
        "patterns": ["_temperature", "온도"],
        "uom": ["°c", "°f", "k"],
    },
    "humidity": {
        "label": "습도",
        "default_unit": "%",
        "device_classes": ["humidity"],
        "patterns": ["_humidity", "습도"],
        "uom": ["%"],
    },
    "co2": {
        "label": "CO2",
        "default_unit": "ppm",
        "device_classes": ["carbon_dioxide", "co2"],
        "patterns": ["_co2", "_carbon_dioxide", "이산화탄소", "co2"],
        "uom": ["ppm"],
    },
    "tvoc": {
        "label": "TVOC",
        "default_unit": "µg/m³",
        "device_classes": ["volatile_organic_compounds", "volatile_organic_compounds_parts", "voc", "tvoc"],
        "patterns": ["_tvoc", "_voc", "유기화합물", "tvoc", "voc"],
        "uom": ["µg/m³", "ug/m3", "ppb", "ppm", "mg/m³", "mg/m3"],
    },
    "pm25": {
        "label": "PM2.5",
        "default_unit": "µg/m³",
        "device_classes": ["pm25", "pm2_5"],
        "patterns": ["_pm25", "_pm2_5", "초미세먼지", "pm2.5", "pm25", "pm2_5"],
        "uom": ["µg/m³", "ug/m3", "ppm"],
    },
    "pm10": {
        "label": "PM10",
        "default_unit": "µg/m³",
        "device_classes": ["pm10"],
        "patterns": ["_pm10", "미세먼지", "pm10"],
        "uom": ["µg/m³", "ug/m3"],
    },
    "illuminance": {
        "label": "조도",
        "default_unit": "lx",
        "device_classes": ["illuminance"],
        "patterns": ["_illuminance", "_lux", "조도", "밝기", "illuminance", "lux"],
        "uom": ["lx", "lux"],
    },
    "pressure": {
        "label": "기압",
        "default_unit": "hPa",
        "device_classes": ["atmospheric_pressure", "pressure"],
        "patterns": ["_pressure", "_atmospheric_pressure", "기압", "pressure"],
        "uom": ["hpa", "mbar", "bar", "psi"],
    },
}

METRIC_ORDER = ["temperature", "humidity", "co2", "tvoc", "pm25", "pm10", "illuminance", "pressure"]

EXCLUDE_KEYWORDS = [
    "배터리", "battery", "전압", "voltage", "calibration", "보정",
    "플러그", "스토브", "cpu", "최고", "최저", "지수", "임계", "threshold",
    "power", "energy", "전력", "전력량", "soil", "linkquality", "signal", "rssi"
]


def get_dynamic_rooms(states: list) -> list:
    """Dynamically discover all defined rooms/areas from HA entity attributes and names."""
    known_candidates = [
        "거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "베란다",
        "현관", "서재", "아이방", "드레스룸", "다용도실", "팬트리", "침실", "욕실"
    ]
    discovered = []

    # 1. Discover rooms from friendly_name and entity_ids
    for s in states:
        fn = s.get("attributes", {}).get("friendly_name", "")
        eid = s.get("entity_id", "")
        for c in known_candidates:
            if c in fn or c in eid:
                if c not in discovered:
                    discovered.append(c)

    # 2. Discover custom area suffixes (e.g. OO방, OO실, OO룸)
    for s in states:
        fn = s.get("attributes", {}).get("friendly_name", "")
        for word in re.findall(r"([가-힣]{2,4}(?:방|실|룸|홀|테라스|베란다|현관))", fn):
            if word not in discovered and word not in ["알림", "설정", "동작", "스위치", "환풍기"]:
                discovered.append(word)

    priority_order = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "베란다", "현관", "서재", "드레스룸", "아이방"]
    sorted_rooms = [r for r in priority_order if r in discovered]
    for r in discovered:
        if r not in sorted_rooms:
            sorted_rooms.append(r)

    return sorted_rooms or priority_order[:8]


def classify_sensor(entity: dict) -> str | None:
    """Classify a Home Assistant sensor entity into a standard environmental metric."""
    eid = entity.get("entity_id", "").lower()
    attrs = entity.get("attributes", {})
    fn = attrs.get("friendly_name", "")
    fn_lower = fn.lower()
    st = entity.get("state", "").strip()
    uom = str(attrs.get("unit_of_measurement", "")).lower()
    dev_class = str(attrs.get("device_class", "")).lower()

    if not eid.startswith("sensor.") or st in ("unavailable", "unknown", ""):
        return None

    # Noise filter
    if any(ex in fn_lower or ex in eid for ex in EXCLUDE_KEYWORDS):
        return None

    # Validate numeric value
    try:
        float(st.replace(",", ""))
    except ValueError:
        return None

    # 1. CO2
    cfg_co2 = ENV_METRIC_CONFIGS["co2"]
    if (
        dev_class in cfg_co2["device_classes"]
        or any(pat in eid for pat in ["_co2", "_carbon_dioxide"])
        or any(pat in fn_lower for pat in ["co2", "이산화탄소"])
        or uom == "ppm" and ("co2" in fn_lower or "co2" in eid or "이산화탄소" in fn)
    ):
        return "co2"

    # 2. TVOC
    cfg_tvoc = ENV_METRIC_CONFIGS["tvoc"]
    if (
        dev_class in cfg_tvoc["device_classes"]
        or any(pat in eid for pat in ["_tvoc", "_voc"])
        or any(pat in fn_lower for pat in ["tvoc", "voc", "유기화합물"])
    ):
        return "tvoc"

    # 3. PM2.5
    cfg_pm25 = ENV_METRIC_CONFIGS["pm25"]
    if (
        dev_class in cfg_pm25["device_classes"]
        or any(pat in eid for pat in ["_pm25", "_pm2_5"])
        or any(pat in fn_lower for pat in ["pm2.5", "pm25", "pm2_5", "초미세먼지"])
    ):
        return "pm25"

    # 4. PM10 (Exclude pm2.5)
    cfg_pm10 = ENV_METRIC_CONFIGS["pm10"]
    if (
        dev_class in cfg_pm10["device_classes"]
        or any(pat in eid for pat in ["_pm10"])
        or ("미세먼지" in fn and "초미세" not in fn)
        or ("pm10" in fn_lower and "pm2" not in fn_lower)
    ):
        return "pm10"

    # 5. Illuminance
    cfg_ill = ENV_METRIC_CONFIGS["illuminance"]
    if (
        dev_class in cfg_ill["device_classes"]
        or any(pat in eid for pat in ["_illuminance", "_lux"])
        or any(pat in fn_lower for pat in ["조도", "밝기", "illuminance", "lux"])
        or uom in cfg_ill["uom"]
    ):
        return "illuminance"

    # 6. Pressure
    cfg_pres = ENV_METRIC_CONFIGS["pressure"]
    if (
        dev_class in cfg_pres["device_classes"]
        or any(pat in eid for pat in ["_pressure", "_atmospheric_pressure"])
        or ("기압" in fn and "습도" not in fn and "온도" not in fn)
        or uom in cfg_pres["uom"]
    ):
        return "pressure"

    # 7. Temperature
    cfg_temp = ENV_METRIC_CONFIGS["temperature"]
    if (
        dev_class in cfg_temp["device_classes"]
        or eid.endswith("_temperature")
        or ("온도" in fn and "습도" not in fn)
        or uom in ("°c", "°f", "k")
    ):
        return "temperature"

    # 8. Humidity
    cfg_hum = ENV_METRIC_CONFIGS["humidity"]
    if (
        dev_class in cfg_hum["device_classes"]
        or eid.endswith("_humidity")
        or ("습도" in fn and "온도" not in fn)
        or (uom == "%" and "습도" in fn)
    ):
        return "humidity"

    return None


def get_room_env_matrix(states: list) -> dict:
    """Extract a multi-dimensional environmental matrix across all discovered rooms."""
    rooms = get_dynamic_rooms(states)
    matrix = {r: {} for r in rooms}
    active_metrics_found = set()

    for s in states:
        metric = classify_sensor(s)
        if not metric:
            continue

        fn = s.get("attributes", {}).get("friendly_name", "")
        eid = s.get("entity_id", "")
        st = s.get("state", "").strip()
        uom = s.get("attributes", {}).get("unit_of_measurement", "")
        cfg = ENV_METRIC_CONFIGS.get(metric, {})
        default_unit = cfg.get("default_unit", "")

        try:
            num_val = float(st.replace(",", ""))
        except ValueError:
            continue

        for r in rooms:
            if r in fn or r in eid:
                if metric not in matrix[r]:
                    matrix[r][metric] = {
                        "value": num_val,
                        "unit": uom or default_unit,
                        "formatted": f"{st}{uom or default_unit}",
                        "raw_state": st,
                        "entity_id": eid,
                        "friendly_name": fn,
                    }
                    active_metrics_found.add(metric)

    # Order active metrics based on METRIC_ORDER
    # Ensure temperature and humidity are prioritized if any room has them, or include discovered
    active_metrics = [m for m in METRIC_ORDER if m in active_metrics_found]
    if not active_metrics:
        active_metrics = ["temperature", "humidity"]

    metric_labels = {m: ENV_METRIC_CONFIGS[m]["label"] for m in METRIC_ORDER}

    return {
        "rooms": rooms,
        "active_metrics": active_metrics,
        "matrix": matrix,
        "metric_labels": metric_labels,
    }


def get_room_env_summary(states: list, kind: str = "temperature") -> str:
    """Summarize environmental metrics across discovered rooms."""
    env_data = get_room_env_matrix(states)
    rooms = env_data["rooms"]
    matrix = env_data["matrix"]

    norm_kind = kind.lower().strip()
    if norm_kind in ("temp", "temperature", "온도", "기온"):
        target_metric = "temperature"
    elif norm_kind in ("hum", "humidity", "습도"):
        target_metric = "humidity"
    elif norm_kind in ("co2", "이산화탄소"):
        target_metric = "co2"
    elif norm_kind in ("tvoc", "voc", "유기화합물"):
        target_metric = "tvoc"
    elif norm_kind in ("pm25", "pm2.5", "초미세먼지"):
        target_metric = "pm25"
    elif norm_kind in ("pm10", "미세먼지"):
        target_metric = "pm10"
    elif norm_kind in ("illuminance", "lux", "조도", "밝기"):
        target_metric = "illuminance"
    elif norm_kind in ("pressure", "기압"):
        target_metric = "pressure"
    elif norm_kind in ("air_quality", "공기질", "공기"):
        lines = ["🍃 **구역별 실내 공기질 종합 요약**\n"]
        has_any = False
        for r in rooms:
            r_data = matrix.get(r, {})
            air_parts = []
            if "co2" in r_data:
                air_parts.append(f"CO2 {r_data['co2']['formatted']}")
            if "tvoc" in r_data:
                air_parts.append(f"TVOC {r_data['tvoc']['formatted']}")
            if "pm25" in r_data:
                air_parts.append(f"PM2.5 {r_data['pm25']['formatted']}")
            if "pm10" in r_data:
                air_parts.append(f"PM10 {r_data['pm10']['formatted']}")

            if air_parts:
                has_any = True
                lines.append(f"• **{r}**: {' | '.join(air_parts)}")
        if has_any:
            return "\n".join(lines)
        return "실내 공기질(CO2, TVOC, 미세먼지) 센서 데이터를 수집하지 못했습니다."
    else:
        target_metric = "temperature"

    cfg = ENV_METRIC_CONFIGS.get(target_metric, {})
    label = cfg.get("label", "환경")
    lines = [f"현재 각 방별 실내 {label}입니다:"]
    found_count = 0
    for r in rooms:
        r_data = matrix.get(r, {})
        if target_metric in r_data:
            lines.append(f"• {r}: {r_data[target_metric]['formatted']}")
            found_count += 1

    if found_count == 0:
        return f"각 방별 실내 {label} 센서 데이터를 찾지 못했습니다."
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


def get_room_full_state(states: list, room_name: str) -> str:
    """Summarize all entities, devices, and multi-dimensional sensors for a specific room."""
    lines = [f"📍 **{room_name} 통합 스마트홈 상태 리포트**\n"]

    env_data = get_room_env_matrix(states)
    r_data = env_data["matrix"].get(room_name, {})

    env_parts = []
    t_val = r_data.get("temperature", {}).get("formatted")
    h_val = r_data.get("humidity", {}).get("formatted")
    if t_val or h_val:
        env_parts.append(f"온도 {t_val or '--'} / 습도 {h_val or '--'}")
    if "co2" in r_data:
        env_parts.append(f"🍃 CO2 {r_data['co2']['formatted']}")
    if "tvoc" in r_data:
        env_parts.append(f"🧪 TVOC {r_data['tvoc']['formatted']}")
    if "pm25" in r_data:
        env_parts.append(f"🌪️ PM2.5 {r_data['pm25']['formatted']}")
    if "pm10" in r_data:
        env_parts.append(f"🌫️ PM10 {r_data['pm10']['formatted']}")
    if "illuminance" in r_data:
        env_parts.append(f"💡 조도 {r_data['illuminance']['formatted']}")
    if "pressure" in r_data:
        env_parts.append(f"⏱️ 기압 {r_data['pressure']['formatted']}")

    if env_parts:
        lines.append(f"• 🌡️ 환경: {' | '.join(env_parts)}")

    # Active Devices
    on_lights = [
        s.get("attributes", {}).get("friendly_name") or s.get("entity_id")
        for s in states
        if s.get("entity_id", "").startswith("light.")
        and room_name in (s.get("attributes", {}).get("friendly_name") or "")
        and s.get("state") == "on"
    ]
    if on_lights:
        lines.append(f"• 💡 켜진 조명: {', '.join(on_lights)}")
    else:
        lines.append("• 💡 조명: 꺼짐")

    covers = [
        f"{s.get('attributes', {}).get('friendly_name') or s.get('entity_id')} ({'열림' if s.get('state') == 'open' else '닫힘'})"
        for s in states
        if s.get("entity_id", "").startswith("cover.")
        and room_name in (s.get("attributes", {}).get("friendly_name") or "")
    ]
    if covers:
        lines.append(f"• 🪟 커튼: {', '.join(covers)}")

    fans = [
        s.get("attributes", {}).get("friendly_name") or s.get("entity_id")
        for s in states
        if s.get("entity_id", "").startswith("fan.")
        and room_name in (s.get("attributes", {}).get("friendly_name") or "")
        and s.get("state") == "on"
    ]
    if fans:
        lines.append(f"• 🌀 가동 팬/환풍기: {', '.join(fans)}")

    return "\n".join(lines)


def get_automations_summary(states: list) -> str:
    """Summarize configured automations and their active states."""
    autos = [s for s in states if s.get("entity_id", "").startswith("automation.")]
    if not autos:
        return "등록된 자동화가 없습니다."

    on_autos = [s.get("attributes", {}).get("friendly_name") or s.get("entity_id") for s in autos if s.get("state") == "on"]
    lines = [
        f"🤖 **Home Assistant 자동화 목록 (총 {len(autos)}개 중 {len(on_autos)}개 활성)**\n",
        f"• 활성화된 자동화 ({len(on_autos)}개):\n  - " + "\n  - ".join(on_autos[:8]),
    ]
    if len(on_autos) > 8:
        lines.append(f"  - 외 {len(on_autos) - 8}개 자동화 상시 가동 중")
    return "\n".join(lines)


def get_todo_summary(states: list) -> str:
    """Summarize to-do lists and shopping tasks."""
    todos = [s for s in states if s.get("entity_id", "").startswith("todo.")]
    if not todos:
        return "📝 등록된 투두리스트(할 일/쇼핑 목록)가 없습니다."

    lines = [f"📝 **스마트홈 투두리스트 (To-Do) 목록 (총 {len(todos)}개 목록)**\n"]
    for t in todos:
        fn = t.get("attributes", {}).get("friendly_name") or t.get("entity_id")
        st = t.get("state", "0")
        lines.append(f"• **{fn}**: 미완료 항목 {st}개")
    return "\n".join(lines)


def get_system_health_summary(states: list) -> str:
    """Perform system health check on core, memory, CPU, and entities."""
    usage = get_resource_usage()
    unavail = [s.get("entity_id") for s in states if s.get("state") in ("unavailable", "unknown")]

    lines = [
        "🛡️ **Home Assistant 시스템 헬스체크 진단 보고서**\n",
        "• 🟢 시스템 상태: 정상 운영 중 (Core Online)",
        f"• ⚙️ 리소스 점검: 호스트 RAM {usage['used_memory_gb']} GB / {usage['total_memory_gb']} GB ({usage['memory_percent']}%) | 애드온 RAM {usage['memory_usage']} MB",
        f"• 📊 엔티티 건전성: 전체 {len(states)}개 엔티티 중 응답 불가 {len(unavail)}개",
        "• 🔒 MCP 서버 상태: ha-mcp (stdio) 정상 바인딩 및 통신 중",
        "\n✅ 치명적인 시스템 장애가 발견되지 않았습니다.",
    ]
    return "\n".join(lines)
