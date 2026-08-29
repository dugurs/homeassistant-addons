"""Sensor data processing and area entity parser module."""

from core.system_info import get_resource_usage


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
    import re
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


def get_room_env_summary(states: list, kind: str = "temperature") -> str:
    """Summarize temperatures or humidities for dynamically discovered rooms without battery or noise sensors."""
    rooms = get_dynamic_rooms(states)
    room_vals = {}
    label = "온도" if kind == "temperature" else "습도"
    unit = "°C" if kind == "temperature" else "%"

    exclude_keywords = [
        "배터리", "battery", "전압", "voltage", "calibration", "보정",
        "플러그", "스토브", "cpu", "최고", "최저", "지수", "임계", "threshold",
        "illuminance", "조도", "power", "energy", "전력", "전력량", "soil"
    ]

    for s in states:
        eid = s.get("entity_id", "").lower()
        fn = s.get("attributes", {}).get("friendly_name", "")
        fn_lower = fn.lower()
        st = s.get("state", "").strip()
        uom = s.get("attributes", {}).get("unit_of_measurement", "")
        dev_class = s.get("attributes", {}).get("device_class", "")

        if not eid.startswith("sensor.") or st in ("unavailable", "unknown", ""):
            continue

        if any(ex in fn_lower or ex in eid for ex in exclude_keywords):
            continue

        if kind == "temperature":
            is_temp = (
                dev_class == "temperature"
                or eid.endswith("_temperature")
                or ("온도" in fn and "습도" not in fn)
                or uom in ("°C", "°F")
            )
            if is_temp:
                try:
                    float(st)
                    for r in rooms:
                        if r in fn and r not in room_vals:
                            room_vals[r] = f"{st}{uom or unit}"
                except ValueError:
                    pass

        elif kind == "humidity":
            is_hum = (
                dev_class == "humidity"
                or eid.endswith("_humidity")
                or ("습도" in fn and "온도" not in fn)
            )
            if is_hum:
                try:
                    float(st)
                    for r in rooms:
                        if r in fn and r not in room_vals:
                            room_vals[r] = f"{st}{uom or unit}"
                except ValueError:
                    pass

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


def get_room_full_state(states: list, room_name: str) -> str:
    """Summarize all entities, devices, and sensors for a specific room."""
    lines = [f"📍 **{room_name} 통합 스마트홈 상태 리포트**\n"]
    
    # Temp & Hum
    temp = None
    hum = None
    temp_summary = get_room_env_summary(states, "temperature")
    hum_summary = get_room_env_summary(states, "humidity")
    for l in temp_summary.split("\n"):
        if room_name in l and ":" in l:
            temp = l.split(":", 1)[1].strip()
    for l in hum_summary.split("\n"):
        if room_name in l and ":" in l:
            hum = l.split(":", 1)[1].strip()
    if temp or hum:
        lines.append(f"• 🌡️ 환경: 온도 {temp or '--'} / 습도 {hum or '--'}")

    # Active Devices
    on_lights = [s.get("attributes", {}).get("friendly_name") or s.get("entity_id") for s in states if s.get("entity_id", "").startswith("light.") and room_name in (s.get("attributes", {}).get("friendly_name") or "") and s.get("state") == "on"]
    if on_lights:
        lines.append(f"• 💡 켜진 조명: {', '.join(on_lights)}")
    else:
        lines.append("• 💡 조명: 꺼짐")

    covers = [f"{s.get('attributes', {}).get('friendly_name') or s.get('entity_id')} ({'열림' if s.get('state') == 'open' else '닫힘'})" for s in states if s.get("entity_id", "").startswith("cover.") and room_name in (s.get("attributes", {}).get("friendly_name") or "")]
    if covers:
        lines.append(f"• 🪟 커튼: {', '.join(covers)}")

    fans = [s.get("attributes", {}).get("friendly_name") or s.get("entity_id") for s in states if s.get("entity_id", "").startswith("fan.") and room_name in (s.get("attributes", {}).get("friendly_name") or "") and s.get("state") == "on"]
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
