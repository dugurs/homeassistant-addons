"""Home Assistant REST API Client and Direct Device Controller."""

import json
import re
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


def _strip_device_type_suffix(name: str, suffixes: tuple) -> str:
    """Strip a trailing device-type word (e.g. '조명', '커튼') from a friendly
    name so it doesn't get repeated when that same word is appended in the
    response sentence (avoids '거실 조명 조명을 켰습니다' style duplication)."""
    for suf in suffixes:
        if name.endswith(suf) and name != suf:
            return name[: -len(suf)].rstrip()
    return name


def _has_batchim(text: str) -> bool:
    """Whether the last character of text is a Korean syllable with a batchim
    (final consonant) -- decides which allomorph of a particle (을/를, 이/가...)
    to use so dynamically-inserted device/room names read grammatically."""
    if not text:
        return False
    code = ord(text[-1])
    if 0xAC00 <= code <= 0xD7A3:
        return (code - 0xAC00) % 28 != 0
    return False


def _particle(text: str, with_batchim: str, without_batchim: str) -> str:
    return with_batchim if _has_batchim(text) else without_batchim


def _has_whole_house_keyword(prompt: str, clean: str) -> bool:
    """Detect an explicit whole-house control keyword.

    A control command only ever targets every device in a domain when the
    user says so explicitly -- there is no silent "couldn't find the room,
    so act on everything" fallback. That silent fallback was the root cause
    of a mistyped or unspecified room turning into a whole-house action.
    """
    if any(k in clean for k in ["전체", "모두", "다같이", "싹다", "집전체", "총출동"]):
        return True
    # Bare "다" (e.g. "불 다 꺼줘") only counts as its own standalone token, not
    # as part of a longer word ("다음", "다양한"): Hangul syllables are single
    # characters with no delimiter between them, so a neighboring Hangul
    # character means it's part of a longer word, not the word "다" itself.
    return bool(re.search(r"(?<![가-힣])다(?![가-힣])", prompt))


def resolve_control_scope(
    prompt: str,
    clean: str,
    rooms: list,
    matched_room,
    candidates: list,
    device_label: str,
):
    """Decide which entities a control command should act on.

    Returns (targets, error_message). A non-empty error_message means the
    command was unrecognized or ambiguous and nothing should be touched --
    the caller should return that message as-is instead of calling any
    service. This is the single choke point every control branch goes
    through, so "act on everything because the room wasn't recognized"
    can't happen silently anywhere.
    """
    if not candidates:
        return [], f"제어할 수 있는 {device_label}{_particle(device_label, '을', '를')} 찾지 못했습니다."

    if matched_room:
        targets = [
            c for c in candidates
            if matched_room in (c.get("attributes", {}).get("friendly_name") or c.get("entity_id"))
        ]
        if not targets:
            return [], f"{matched_room}에는 제어할 수 있는 {device_label}{_particle(device_label, '이', '가')} 없습니다."
        return targets, ""

    if _has_whole_house_keyword(prompt, clean):
        return candidates, ""

    relevant_rooms = [
        r for r in rooms
        if any(r in (c.get("attributes", {}).get("friendly_name") or c.get("entity_id")) for c in candidates)
    ]
    if relevant_rooms:
        return [], (
            f"어느 방의 {device_label}{_particle(device_label, '을', '를')} 말씀하시는 걸까요? "
            f"({', '.join(relevant_rooms)} 중 하나로 다시 말씀해 주세요.)"
        )
    return [], f"제어할 수 있는 {device_label}{_particle(device_label, '을', '를')} 찾지 못했습니다."


SWITCH_EXCLUDE_KEYWORDS = [
    "차일드", "Child", "락", "Lock", "Alarm", "알람", "Led", "LED", "Indicator",
    "표시등", "Reboot", "재부팅", "Microphone", "마이크", "Mute", "Countdown",
    "카운트다운", "Timer", "타이머",
]

# Deliberately a curated allowlist, not blanket "switch." domain access: that
# domain also holds config/diagnostic switches (child lock, mic mute, reboot,
# indicator LEDs) that must never be toggled by a loose keyword match.
# "냉장고" is intentionally NOT included -- an accidental fridge power-off is
# exactly the kind of mistake this whole feature exists to prevent.
APPLIANCE_SWITCH_KEYWORDS = ["보일러", "히터", "온열기", "전기스토브", "콘센트", "플러그"]


def execute_device_control_intent(prompt: str, states: list) -> str:
    """Execute direct device control (lights, fans, covers, switches, climate, media)."""
    from core.sensors import get_dynamic_rooms, match_room

    clean = prompt.replace(" ", "")
    lower_clean = clean.lower()

    is_on = any(k in clean for k in ["켜", "틀어", "시작", "올려", "가동"])
    is_off = any(k in clean for k in ["꺼", "정지", "내려", "종료", "중지"])
    is_open = any(k in clean for k in ["열어", "open"])
    is_close = any(k in clean for k in ["닫아", "close"])

    rooms = get_dynamic_rooms(states)
    matched_room = match_room(rooms, clean)

    # 1. Curtains / Covers
    if any(w in clean for w in ["커튼", "블라인드", "창문"]):
        service = "open_cover" if is_open else ("close_cover" if is_close else None)
        if service:
            candidates = [s for s in states if s.get("entity_id", "").startswith("cover.")]
            targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, "커튼")
            if err:
                return err
            for c in targets:
                ha_call_service_api("cover", service, {"entity_id": c.get("entity_id")})
            act_str = "열었습니다" if is_open else "닫았습니다"
            names = [
                _strip_device_type_suffix(c.get("attributes", {}).get("friendly_name") or c.get("entity_id"), ("커튼", "블라인드"))
                for c in targets
            ]
            return f"🪟 {', '.join(names)} 커튼을 {act_str}."

    # 2. Fans / Ventilators
    if any(w in clean for w in ["팬", "선풍기", "환풍기", "실링팬"]):
        service = "turn_on" if is_on else ("turn_off" if is_off else None)
        if service:
            candidates = [s for s in states if s.get("entity_id", "").startswith("fan.")]
            targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, "선풍기/환풍기")
            if err:
                return err
            for f in targets:
                ha_call_service_api("fan", service, {"entity_id": f.get("entity_id")})
            act_str = "켰습니다" if is_on else "껐습니다"
            names = [f.get("attributes", {}).get("friendly_name") or f.get("entity_id") for f in targets]
            return f"🌀 {', '.join(names)} 가동을 {act_str}."

    # 3. Lights (NOTE: "스위치" intentionally not a trigger here -- it's too
    # generic and now genuinely ambiguous with the curated appliance-switch
    # branch below; a bare "스위치 꺼줘" should ask for clarification, not
    # silently mean "light".)
    if any(w in clean for w in ["불", "조명", "전등", "등"]):
        service = "turn_on" if is_on else ("turn_off" if is_off else None)
        if service:
            candidates = [
                s for s in states
                if s.get("entity_id", "").startswith("light.") and "all" not in s.get("entity_id", "").lower()
            ]
            targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, "조명")
            if err:
                return err
            for l in targets:
                ha_call_service_api("light", service, {"entity_id": l.get("entity_id")})
            act_str = "켰습니다" if is_on else "껐습니다"
            names = [
                _strip_device_type_suffix(l.get("attributes", {}).get("friendly_name") or l.get("entity_id"), ("조명", "전등"))
                for l in targets
            ]
            return f"💡 {', '.join(names)} 조명을 {act_str}."

    # 4. Humidifiers / Dehumidifiers -- prefer the dedicated humidifier.* entity
    # (correct HA service semantics); fall back to a curated switch relay only
    # if no such entity exists for this appliance.
    if any(w in clean for w in ["가습기", "제습기"]):
        keyword = "가습기" if "가습기" in clean else "제습기"
        service = "turn_on" if is_on else ("turn_off" if is_off else None)
        if service:
            domain = "humidifier"
            candidates = [
                s for s in states
                if s.get("entity_id", "").startswith("humidifier.")
                and keyword in (s.get("attributes", {}).get("friendly_name") or "")
            ]
            if not candidates:
                domain = "switch"
                candidates = [
                    s for s in states
                    if s.get("entity_id", "").startswith("switch.")
                    and keyword in (s.get("attributes", {}).get("friendly_name") or "")
                    and not any(x in (s.get("attributes", {}).get("friendly_name") or "") for x in SWITCH_EXCLUDE_KEYWORDS)
                ]
            targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, keyword)
            if err:
                return err
            for t in targets:
                ha_call_service_api(domain, service, {"entity_id": t.get("entity_id")})
            act_str = "켰습니다" if is_on else "껐습니다"
            names = [t.get("attributes", {}).get("friendly_name") or t.get("entity_id") for t in targets]
            icon = "💧" if keyword == "가습기" else "🌬️"
            obj_p = _particle(names[-1], "을", "를") if names else "를"
            return f"{icon} {', '.join(names)}{obj_p} {act_str}."

    # 5. Curated appliance switches (boiler, heater, outlet/plug)
    matched_appliance = next((k for k in APPLIANCE_SWITCH_KEYWORDS if k in clean), None)
    if matched_appliance:
        service = "turn_on" if is_on else ("turn_off" if is_off else None)
        if service:
            candidates = [
                s for s in states
                if s.get("entity_id", "").startswith("switch.")
                and matched_appliance in (s.get("attributes", {}).get("friendly_name") or "")
                and not any(x in (s.get("attributes", {}).get("friendly_name") or "") for x in SWITCH_EXCLUDE_KEYWORDS)
            ]
            targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, matched_appliance)
            if err:
                return err
            for t in targets:
                ha_call_service_api("switch", service, {"entity_id": t.get("entity_id")})
            act_str = "켰습니다" if is_on else "껐습니다"
            names = [t.get("attributes", {}).get("friendly_name") or t.get("entity_id") for t in targets]
            obj_p = _particle(names[-1], "을", "를") if names else "를"
            return f"🔌 {', '.join(names)}{obj_p} {act_str}."

    # 6. Climate (air conditioner / heater) -- on/off only for now.
    # "환풍기" is deliberately excluded here: it's already handled by the fan
    # branch above even for climate-domain bathroom ventilators, so this stays
    # scoped to actual air conditioning/heating only.
    if any(w in clean for w in ["에어컨", "냉방", "난방"]):
        service = "turn_on" if is_on else ("turn_off" if is_off else None)
        if service:
            candidates = [s for s in states if s.get("entity_id", "").startswith("climate.")]
            targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, "에어컨")
            if err:
                return err
            for t in targets:
                ha_call_service_api("climate", service, {"entity_id": t.get("entity_id")})
            act_str = "켰습니다" if is_on else "껐습니다"
            names = [
                _strip_device_type_suffix(t.get("attributes", {}).get("friendly_name") or t.get("entity_id"), ("에어컨",))
                for t in targets
            ]
            return f"❄️ {', '.join(names)} 에어컨을 {act_str}."

    # 7. Media player (TV / speaker) -- on/off only. TV prefers an existing
    # user-authored IR script (this house already has reliable "리모콘 TV 전원
    # ON/OFF" scripts) over a generic media_player call, since IR-controlled
    # TVs are unreliable to power on/off via a plain media_player service.
    media_trigger = None
    filter_terms = []
    if "티비" in clean or "tv" in lower_clean:
        media_trigger = "TV"
        filter_terms = ["tv"]
    elif "스피커" in clean:
        media_trigger = "스피커"
        filter_terms = ["스피커", "speaker"]

    if media_trigger:
        service = "turn_on" if is_on else ("turn_off" if is_off else None)
        if service:
            if media_trigger == "TV":
                action_words = ["on", "켜기"] if is_on else ["off", "끄기"]
                script_match = next(
                    (
                        s for s in states
                        if s.get("entity_id", "").startswith("script.")
                        and "tv" in (s.get("attributes", {}).get("friendly_name") or "").lower()
                        and any(a in (s.get("attributes", {}).get("friendly_name") or "").lower() for a in action_words)
                    ),
                    None,
                )
                if script_match:
                    ha_call_service_api("script", "turn_on", {"entity_id": script_match.get("entity_id")})
                    name = script_match.get("attributes", {}).get("friendly_name") or script_match.get("entity_id")
                    return f"📺 '{name}' 스크립트를 실행했습니다."

            candidates = [
                s for s in states
                if s.get("entity_id", "").startswith("media_player.")
                and any(t in (s.get("attributes", {}).get("friendly_name") or "").lower() for t in filter_terms)
            ]
            targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, media_trigger)
            if err:
                return err
            for t in targets:
                ha_call_service_api("media_player", service, {"entity_id": t.get("entity_id")})
            act_str = "켰습니다" if is_on else "껐습니다"
            names = [t.get("attributes", {}).get("friendly_name") or t.get("entity_id") for t in targets]
            obj_p = _particle(names[-1], "을", "를") if names else "를"
            return f"📺 {', '.join(names)}{obj_p} {act_str}."

    return ""


def toggle_automation_intent(prompt: str, states: list) -> str:
    """Turn a named automation on/off by partial name match."""
    clean = prompt.replace(" ", "")
    if not any(k in clean for k in ["자동화", "오토메이션"]):
        return ""
    is_on = any(k in clean for k in ["켜", "틀어", "시작", "활성화", "켜줘"])
    is_off = any(k in clean for k in ["꺼", "정지", "종료", "중지", "비활성화", "꺼줘"])
    service = "turn_on" if is_on else ("turn_off" if is_off else None)
    if not service:
        return ""

    autos = [s for s in states if s.get("entity_id", "").startswith("automation.")]
    name_no_space = re.sub(r"(자동화|오토메이션|켜줘|꺼줘|켜|꺼|시작|정지|종료|중지|활성화|비활성화)", "", clean)

    matches = [
        s for s in autos
        if name_no_space and name_no_space in (s.get("attributes", {}).get("friendly_name") or "").replace(" ", "")
    ]

    if len(matches) == 1:
        target = matches[0]
        ha_call_service_api("automation", service, {"entity_id": target.get("entity_id")})
        name = target.get("attributes", {}).get("friendly_name") or target.get("entity_id")
        act_str = "켰습니다" if is_on else "껐습니다"
        return f"🤖 자동화 '{name}'{_particle(name, '을', '를')} {act_str}."

    if len(matches) > 1:
        names = [s.get("attributes", {}).get("friendly_name") or s.get("entity_id") for s in matches[:8]]
        return f"어느 자동화를 말씀하시는 걸까요? ({', '.join(names)} 중 하나로 다시 말씀해 주세요.)"

    return f"'{name_no_space}' 이름을 포함한 자동화를 찾지 못했습니다."


def run_script_or_scene_intent(prompt: str, states: list) -> str:
    """Run a script or scene by partial name match."""
    clean = prompt.replace(" ", "")
    if not any(k in clean for k in ["실행", "돌려", "작동시켜", "재생해"]):
        return ""

    name_no_space = re.sub(r"(스크립트|씬|scene|실행해줘|실행해|실행|돌려줘|돌려|작동시켜줘|작동시켜|재생해줘|재생해)", "", clean, flags=re.IGNORECASE)
    if not name_no_space:
        return ""

    candidates = [
        s for s in states
        if (s.get("entity_id", "").startswith("script.") or s.get("entity_id", "").startswith("scene."))
        and name_no_space in (s.get("attributes", {}).get("friendly_name") or "").replace(" ", "")
    ]

    if len(candidates) == 1:
        target = candidates[0]
        domain = target.get("entity_id", "").split(".")[0]
        ha_call_service_api(domain, "turn_on", {"entity_id": target.get("entity_id")})
        name = target.get("attributes", {}).get("friendly_name") or target.get("entity_id")
        kind = "스크립트" if domain == "script" else "씬"
        return f"▶️ {kind} '{name}'{_particle(name, '을', '를')} 실행했습니다."

    if len(candidates) > 1:
        names = [s.get("attributes", {}).get("friendly_name") or s.get("entity_id") for s in candidates[:8]]
        return f"어느 것을 실행할까요? ({', '.join(names)} 중 하나로 다시 말씀해 주세요.)"

    return ""
