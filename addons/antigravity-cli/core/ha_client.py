"""Home Assistant REST API Client and Direct Device Controller."""

import json
import urllib.request
from core.system_info import get_supervisor_token


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


def ha_call_service_api(domain: str, service: str, service_data: dict = None) -> bool:
    """Execute Home Assistant service call via REST API."""
    supervisor_token = get_supervisor_token()
    if not supervisor_token:
        return False
    url = f"http://supervisor/core/api/services/{domain}/{service}"
    payload = json.dumps(service_data or {}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {supervisor_token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status in (200, 201)
    except Exception:
        return False


def execute_device_control_intent(prompt: str, states: list) -> str:
    """Execute direct device control (lights, fans, covers, switches)."""
    clean = prompt.replace(" ", "")

    is_on = any(k in clean for k in ["켜", "틀어", "시작", "올려", "가동"])
    is_off = any(k in clean for k in ["꺼", "정지", "내려", "종료", "중지"])
    is_open = any(k in clean for k in ["열어", "open"])
    is_close = any(k in clean for k in ["닫아", "close"])

    rooms = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "현관", "베란다"]
    matched_room = next((r for r in rooms if r in clean), None)

    # 1. Curtains / Covers
    if any(w in clean for w in ["커튼", "블라인드", "창문"]):
        target_covers = [s for s in states if s.get("entity_id", "").startswith("cover.")]
        if matched_room:
            target_covers = [s for s in target_covers if matched_room in (s.get("attributes", {}).get("friendly_name") or s.get("entity_id"))]
        if target_covers:
            service = "open_cover" if is_open else ("close_cover" if is_close else None)
            if service:
                for c in target_covers:
                    ha_call_service_api("cover", service, {"entity_id": c.get("entity_id")})
                act_str = "열었습니다" if is_open else "닫았습니다"
                names = [c.get("attributes", {}).get("friendly_name") or c.get("entity_id") for c in target_covers]
                return f"🪟 {', '.join(names)} 커튼을 성공적으로 {act_str}."

    # 2. Fans / Ventilators
    if any(w in clean for w in ["팬", "선풍기", "환풍기", "실링팬"]):
        target_fans = [s for s in states if s.get("entity_id", "").startswith("fan.")]
        if matched_room:
            target_fans = [s for s in target_fans if matched_room in (s.get("attributes", {}).get("friendly_name") or s.get("entity_id"))]
        if target_fans:
            service = "turn_on" if is_on else ("turn_off" if is_off else None)
            if service:
                for f in target_fans:
                    ha_call_service_api("fan", service, {"entity_id": f.get("entity_id")})
                act_str = "켰습니다" if is_on else "껐습니다"
                names = [f.get("attributes", {}).get("friendly_name") or f.get("entity_id") for f in target_fans]
                return f"🌀 {', '.join(names)} 가동을 성공적으로 {act_str}."

    # 3. Lights
    if any(w in clean for w in ["불", "조명", "전등", "등", "스위치"]):
        target_lights = [s for s in states if s.get("entity_id", "").startswith("light.") and "all" not in s.get("entity_id").lower()]
        if matched_room:
            target_lights = [s for s in target_lights if matched_room in (s.get("attributes", {}).get("friendly_name") or s.get("entity_id"))]
        if target_lights:
            service = "turn_on" if is_on else ("turn_off" if is_off else None)
            if service:
                for l in target_lights:
                    ha_call_service_api("light", service, {"entity_id": l.get("entity_id")})
                act_str = "켰습니다" if is_on else "껐습니다"
                names = [l.get("attributes", {}).get("friendly_name") or l.get("entity_id") for l in target_lights]
                return f"💡 {', '.join(names)} 조명을 성공적으로 {act_str}."

    return ""
