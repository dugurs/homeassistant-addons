"""Home Assistant REST API Client and Direct Device Controller."""

import itertools
import json
import re
import threading
import time
import urllib.request
from core.system_info import get_supervisor_token

# When a delayed command ("안방 등 10분 뒤에 꺼줘") is being resolved, the
# resolution logic runs completely unchanged (same domain branches, same
# resolve_control_scope calls) but the actual HA service calls it would make
# must be captured instead of fired immediately -- see
# _schedule_delayed_control() below. Thread-local so concurrent requests
# (each request thread resolving its own command) can never cross-contaminate
# each other's captured call list.
_deferred_call_sink = threading.local()

# Which entities the most recent execute_device_control_intent() call on
# this thread actually resolved successfully -- used by
# get_last_action_entities() so core/streamer.py can attach a device
# control card (see build_device_cards()) to the response for exactly the
# entities THIS turn touched, and none when nothing was actually controlled
# (a status/weather question, an unresolved ambiguous command, a delayed
# command not yet fired, or a pending confirmation not yet answered --
# resolve_control_scope() only calls _remember() on a genuine success, so
# this sink only ever fills in that case). Thread-local for the same reason
# as _deferred_call_sink above.
_card_entity_sink = threading.local()

# Same arm/drain lifecycle as _card_entity_sink above, but for the "OO에
# 음악 틀어줘" playlist-pick-list card (see _h_media() and
# core/music_assistant.py) instead of a normal executed-control card --
# nothing is actually played yet at the point this is armed, only offered
# as choices, so it's kept entirely separate from "entities this turn
# actually controlled".
_playlist_card_sink = threading.local()

# Registry of currently pending delayed-control timers (see
# _schedule_delayed_control() below), keyed by an opaque incrementing id --
# lets get_scheduled_controls_answer() report "몇 개 예약돼 있어?"/"예약 목록
# 보여줘" without needing to reach into threading.Timer internals. Entries
# are removed once their timer actually fires.
_scheduled_lock = threading.Lock()
_scheduled_controls: dict = {}
_scheduled_id_counter = itertools.count(1)


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


def ha_call_service_api(domain: str, service: str, service_data: dict = None, timeout: int = 3) -> bool:
    """Execute Home Assistant service call via REST API.

    Captured instead of fired for real when a delayed command is currently
    being resolved on this thread (see _deferred_call_sink / _schedule_
    delayed_control()) -- transparent to every caller, none of which need to
    know whether they're running immediately or being scheduled.

    `timeout` defaults to 3s, plenty for the instant light/fan/switch calls
    every other caller makes. antigravity_api.py's /api/device/control
    passes a longer one for music_assistant.play_media specifically --
    confirmed live that HA's REST call for it doesn't return until the
    actual Cast handshake finishes (several seconds), so 3s reliably timed
    out and reported failure even though playback then started anyway a
    moment later. That's the card's own single-click request, entirely
    separate from the natural-language "0.05s" dispatch path, so a longer
    wait there costs nothing on the hot path.
    """
    sink = getattr(_deferred_call_sink, "calls", None)
    if sink is not None:
        sink.append((domain, service, service_data or {}))
        return True

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
        with urllib.request.urlopen(req, timeout=timeout) as resp:
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


_GENERIC_DEVICE_WORDS = {"등", "불", "조명", "전등"}


def _remainder_after_room(friendly_name: str, room: str) -> str:
    """Friendly name with the room name and all whitespace stripped, e.g.
    "안방 스탠드 등" + "안방" -> "스탠드등". This is what's left to tell
    same-type devices within one room apart."""
    return friendly_name.replace(room, "", 1).replace(" ", "").strip()


def _narrow_multi_device_targets(clean: str, matched_room: str, room_targets: list):
    """When a room has more than one device of the same type, figure out
    which single one (if any) the prompt actually singles out.

    Returns a one-item list when the prompt clearly names a specific device
    -- either an explicit qualifier like "스탠드"/"화장대", or, when no
    qualifier at all is given, the one device whose name is just the bare
    generic word (e.g. "안방 등" among "안방 스탠드 등"/"안방 화장대 등").
    Returns None when it can't confidently narrow to one -- the caller
    should ask instead of guessing. This is what stops "안방 등 켜" from
    turning on every light in the bedroom just because they all contain
    "등" somewhere in their name (previously each candidate only had to
    contain the room name, with no per-device narrowing at all).
    """
    remainders = [
        (c, _remainder_after_room(c.get("attributes", {}).get("friendly_name") or c.get("entity_id"), matched_room))
        for c in room_targets
    ]

    specific = [(c, r) for c, r in remainders if r and r not in _GENERIC_DEVICE_WORDS and r in clean]
    if len(specific) == 1:
        return [specific[0][0]]
    if len(specific) > 1:
        return None

    # No explicit qualifier in the prompt -- fall back to the candidate with
    # the shortest (bare) remainder, but only if that's unambiguous (e.g. two
    # equally-generic "등1"/"등2" style names should still ask).
    remainders.sort(key=lambda cr: len(cr[1]))
    if len(remainders) >= 2 and len(remainders[0][1]) < len(remainders[1][1]):
        return [remainders[0][0]]
    return None


def resolve_control_scope(
    prompt: str,
    clean: str,
    rooms: list,
    matched_room,
    candidates: list,
    device_label: str,
    conversation_id: str = "",
    domain: str = "",
    service: str = "",
    extra_data: dict = None,
):
    """Decide which entities a control command should act on.

    Returns (targets, error_message). A non-empty error_message means the
    command was unrecognized or ambiguous and nothing should be touched --
    the caller should return that message as-is instead of calling any
    service. This is the single choke point every control branch goes
    through, so "act on everything because the room wasn't recognized"
    can't happen silently anywhere.

    Every successful (non-error) resolution is also remembered via
    set_last_control_targets() when conversation_id is given, so a later bare
    follow-up with no device word at all ("닫아" on its own) can reuse these
    same entities -- see the fallback at the end of
    execute_device_control_intent().

    `domain`/`service`/`extra_data` (the exact HA service call this
    resolution is for) are only used for the hidden-entity confirmation gate
    below -- every other code path here is unaffected by them.
    """
    def _remember(targets: list) -> list:
        if conversation_id and targets:
            from core.session_manager import set_last_control_targets
            set_last_control_targets(conversation_id, [t.get("entity_id") for t in targets if t.get("entity_id")])
        card_sink = getattr(_card_entity_sink, "entities", None)
        if card_sink is not None and targets:
            card_sink.extend(t.get("entity_id") for t in targets if t.get("entity_id"))
        return targets

    def _split_hidden(targets: list):
        """(visible_targets, hidden_singleton_or_None). If any visible
        candidate exists, hidden ones are just dropped -- see the module
        docstring incident: a hidden "거실 플러그" outlet must never join a
        room-wide sweep just because it happens to share the room name.
        When EVERY candidate is hidden and there's exactly one, it's
        returned separately so the caller can ask for confirmation instead
        of silently acting on something the user deliberately hid. Multiple
        all-hidden candidates fall through unfiltered -- rare, and the
        existing multi-candidate disambiguation below still applies safely.
        """
        from core.ha_registry import get_hidden_entity_ids
        hidden_ids = get_hidden_entity_ids()
        if not hidden_ids:
            return targets, None
        visible = [t for t in targets if t.get("entity_id") not in hidden_ids]
        if visible:
            return visible, None
        if len(targets) == 1:
            return [], targets[0]
        return targets, None

    def _confirm_hidden(entity: dict):
        name = entity.get("attributes", {}).get("friendly_name") or entity.get("entity_id")
        if domain and service and conversation_id:
            from core.session_manager import set_pending_confirmation
            target = {"domain": domain, "service": service, "entity_id": entity.get("entity_id")}
            if extra_data:
                target.update(extra_data)
            set_pending_confirmation(conversation_id, {"targets": [target], "names": [name]})
        return [], (
            f"'{name}'{_particle(name, '은', '는')} 숨김 처리된 기기입니다. 그래도 제어할까요? "
            f"계속하시려면 \"응\"이라고 답해주세요."
        )

    def _resolve_within_room(room: str, cands: list):
        """Shared "we know which room, now narrow within it" logic -- used
        both when the room was named explicitly in this turn and when it
        was recovered from get_last_room_context() below. Remembers `room`
        as the conversation's last-mentioned room either way (shared with
        the metric-follow-up memory used for "습도는?" style questions --
        see set_last_room_context()'s other caller in core/ha_engine.py --
        so "안방 선풍기 꺼" then "습도는?" now correctly means 안방's humidity
        too, not just the other way around).
        """
        if conversation_id:
            from core.session_manager import set_last_room_context
            set_last_room_context(conversation_id, room)
        targets = [
            c for c in cands
            if room in (c.get("attributes", {}).get("friendly_name") or c.get("entity_id"))
        ]
        if not targets:
            return [], f"{room}에는 제어할 수 있는 {device_label}{_particle(device_label, '이', '가')} 없습니다."
        targets, hidden_singleton = _split_hidden(targets)
        if hidden_singleton:
            return _confirm_hidden(hidden_singleton)
        if not targets:
            return [], f"{room}에는 제어할 수 있는 {device_label}{_particle(device_label, '이', '가')} 없습니다."
        if len(targets) > 1 and not _has_whole_house_keyword(prompt, clean):
            narrowed = _narrow_multi_device_targets(clean, room, targets)
            if narrowed is not None:
                return _remember(narrowed), ""
            names = [c.get("attributes", {}).get("friendly_name") or c.get("entity_id") for c in targets]
            return [], (
                f"{room}에 {device_label}{_particle(device_label, '이', '가')} 여러 개 있습니다. "
                f"어느 것을 말씀하시는 걸까요? ({', '.join(names)} 중 하나로, 또는 '전체'/'다'라고 말씀해 주세요.)"
            )
        return _remember(targets), ""

    if not candidates:
        return [], f"제어할 수 있는 {device_label}{_particle(device_label, '을', '를')} 찾지 못했습니다."

    if matched_room:
        return _resolve_within_room(matched_room, candidates)

    if _has_whole_house_keyword(prompt, clean):
        targets, hidden_singleton = _split_hidden(candidates)
        if hidden_singleton:
            return _confirm_hidden(hidden_singleton)
        return _remember(targets), ""

    visible_candidates, hidden_singleton = _split_hidden(candidates)
    if hidden_singleton:
        return _confirm_hidden(hidden_singleton)

    relevant_rooms = [
        r for r in rooms
        if any(r in (c.get("attributes", {}).get("friendly_name") or c.get("entity_id")) for c in visible_candidates)
    ]
    if relevant_rooms:
        # No room named this turn, but the same device type exists in
        # several rooms -- before asking, check whether the conversation's
        # last-mentioned room (see _resolve_within_room() above and
        # core/ha_engine.py's metric-follow-up use of the same memory) is
        # one of them. E.g. "안방 선풍기 꺼" then, with no room repeated,
        # "책상등 꺼" -- 안방 is still the last-mentioned room, and 안방 IS
        # one of the rooms with a 책상등, so it resolves there directly
        # instead of asking "어느 방?" for a room the user already implied.
        if conversation_id:
            from core.session_manager import get_last_room_context
            remembered_room = get_last_room_context(conversation_id)
            if remembered_room and remembered_room in relevant_rooms:
                return _resolve_within_room(remembered_room, visible_candidates)
        return [], (
            f"어느 방의 {device_label}{_particle(device_label, '을', '를')} 말씀하시는 걸까요? "
            f"({', '.join(relevant_rooms)} 중 하나로 다시 말씀해 주세요.)"
        )
    return [], f"제어할 수 있는 {device_label}{_particle(device_label, '을', '를')} 찾지 못했습니다."


# Used to filter both switch.* AND light.* candidates: some devices (mi
# fans, IR blasters, heaters, ...) expose a companion diagnostic/status LED
# as its own light.* entity (e.g. "안방 전기스토브1S Indicator Light",
# "작은방 선풍기 Indicator Light") which shares the room name in its friendly
# name -- without this filter a room-wide light command ("불 다 꺼") would
# also flip that unrelated status LED.
DIAGNOSTIC_EXCLUDE_KEYWORDS = [
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

# Device control card (see build_device_cards()) toggle/slider interactions
# hit /api/device/control directly, bypassing the natural-language pipeline
# entirely -- there's no room-matching or hidden/dangerous-device gate to
# reuse there, since the card only ever exists for an entity that already
# passed those on its way to being controlled once by the actual command.
# This allowlist is the only thing standing between that endpoint and "call
# any HA service with any data on any entity_id" if the frontend ever sends
# something unexpected (a bug, a stale/tampered card, ...).
ALLOWED_CARD_SERVICES = {
    "light": {"turn_on", "turn_off"},
    "fan": {"turn_on", "turn_off", "set_percentage"},
    "switch": {"turn_on", "turn_off"},
    "cover": {"open_cover", "close_cover", "set_cover_position"},
    "climate": {"turn_on", "turn_off", "set_temperature", "set_hvac_mode", "set_fan_mode"},
    "media_player": {
        "turn_on", "turn_off", "volume_set",
        # Now-playing widget controls (see build_device_cards()'s
        # media_title-gated block and renderOneDeviceCard() in
        # core/ui/scripts.py).
        "media_play", "media_pause", "media_next_track", "media_previous_track", "media_seek",
    },
    # Only play_media -- this is what the playlist-pick-list card's click
    # handler calls (see _h_media()/core/music_assistant.py); no reason to
    # allow the frontend to hit any other music_assistant.* service.
    "music_assistant": {"play_media"},
}

# "중지"/"정지"/"멈춰" are already generic power-off synonyms (see is_off's
# keyword list in _execute_single_control_clause()), but for a media_player
# specifically they mean "pause the current track" (media_pause), not
# "power the device off" (turn_off) -- confirmed live that media_pause on
# the room's speaker correctly pauses Music Assistant's queue too, no
# separate entity needed. "재생"("play") isn't in the generic is_on list at
# all (it's not a natural way to say "turn on" a light), so it needs its
# own resume-specific check to make "재생해줘" resume media_play after a
# pause -- see _h_media() and the "bare follow-up fallback" below, which
# both consult these two lists to decide when to use media_pause/media_play
# instead of turn_off/turn_on for a media_player target specifically.
_MEDIA_PAUSE_WORDS = ["중지", "정지", "멈춰", "일시정지"]
_MEDIA_RESUME_WORDS = ["재생"]

_STATE_QUERY_PATTERNS = [
    "켜져있", "꺼져있", "켜있", "꺼있", "켜진", "꺼진", "켜졌", "꺼졌",
    "닫혀있", "닫힌", "닫혔", "열려있", "열린", "열렸",
    "작동중", "작동하고있", "가동중", "가동하고있", "돌아가고있", "돌고있",
    # "안방 등 목록"/"조명 뭐있어"/"선풍기 보여줘" -- not asking about ON/OFF
    # state specifically, but the same "list every matching device instead
    # of guessing/acting on one" behavior in get_device_status_answer() is
    # exactly what these want too, so they route through the same gate.
    "목록", "리스트", "뭐있어", "뭐가있어", "보여줘",
]
_COMMAND_MARKERS = ["줘", "줄래", "주세요", "주실래요", "주실수", "게해줘", "게해", "라"]


def is_status_query(prompt: str, clean: str) -> bool:
    """True when the prompt is ASKING about current device state ("켜져있어?" --
    is it on?) rather than COMMANDING a change ("켜줘" -- turn it on).

    Both share the same "켜"/"꺼" substring, so a plain keyword-in-string check
    can never tell them apart -- this is the single choke point every control
    function (device/automation) must check FIRST. A status question that
    slips past this and reaches an on/off branch will actually flip the
    device: this is exactly what happened when "안방 스탠드 등 켜져있어?" (is
    the bedroom stand lamp on?) turned every bedroom light on.
    """
    if any(p in clean for p in _STATE_QUERY_PATTERNS):
        return True
    if prompt.rstrip().endswith("?") and not any(m in clean for m in _COMMAND_MARKERS):
        return True
    return False


_DOMAIN_STATUS_TRIGGERS = [
    (("등", "조명", "불", "전등", "라이트", "램프"), "light.", "조명"),
    (("커튼", "블라인드"), "cover.", "커튼"),
    (("선풍기", "환풍기", "팬", "실링팬"), "fan.", "선풍기/환풍기"),
    (("에어컨",), "climate.", "에어컨"),
    (("가습기",), "humidifier.", "가습기"),
    (("제습기",), "humidifier.", "제습기"),
    (("tv", "티비"), "media_player.", "TV"),
    (("스피커",), "media_player.", "스피커"),
]


def get_device_status_answer(prompt: str, states: list) -> str:
    """Answer an on/off (or open/closed) status question by listing each
    matching device's individual current state.

    Deliberately does not try to guess which single device within a room the
    user meant (e.g. "스탠드" among several bedroom lights) -- listing every
    match with its own state answers the question directly and safely,
    without the ambiguity risk of picking one entity to act on.
    """
    from core.sensors import get_dynamic_rooms, match_room

    clean = prompt.replace(" ", "")
    lower_clean = clean.lower()

    matched = None
    for words, domain_prefix, label in _DOMAIN_STATUS_TRIGGERS:
        haystack = lower_clean if domain_prefix == "media_player." else clean
        if any(w in haystack for w in words):
            matched = (domain_prefix, label)
            break
    if not matched:
        return ""
    domain_prefix, label = matched

    rooms = get_dynamic_rooms(states)
    room = match_room(rooms, clean)

    candidates = [s for s in states if s.get("entity_id", "").startswith(domain_prefix)]
    if domain_prefix == "light.":
        candidates = [
            c for c in candidates
            if "all" not in c.get("entity_id", "").lower()
            and not any(x in (c.get("attributes", {}).get("friendly_name") or "") for x in DIAGNOSTIC_EXCLUDE_KEYWORDS)
        ]
    if room:
        candidates = [
            c for c in candidates
            if room in (c.get("attributes", {}).get("friendly_name") or c.get("entity_id"))
        ]

    if not candidates:
        where = f"{room}에는 " if room else ""
        return f"{where}확인할 수 있는 {label}{_particle(label, '이', '가')} 없습니다."

    on_label, off_label = ("열림", "닫힘") if domain_prefix == "cover." else ("켜짐", "꺼짐")
    lines = []
    for c in candidates:
        fn = c.get("attributes", {}).get("friendly_name") or c.get("entity_id")
        st = c.get("state")
        if domain_prefix == "climate.":
            is_active = st not in ("off", "unavailable", "unknown", None)
        elif domain_prefix == "cover.":
            is_active = st == "open"
        else:
            is_active = st == "on"
        lines.append(f"- {fn}: {on_label if is_active else off_label}")

    header = f"{room + ' ' if room else ''}{label} 상태"
    return f"🔎 **{header}**\n" + "\n".join(lines)


_PERCENT_RE = re.compile(r"(\d{1,3})\s*(?:%|퍼센트|프로)")


def _service_for_action(domain: str, is_on: bool, is_off: bool, is_open: bool, is_close: bool) -> str | None:
    """Map a domain + this turn's detected verb to the right HA service name.
    cover.* uses open_cover/close_cover; every other domain used here
    (light/fan/switch/humidifier/climate/media_player) uses turn_on/turn_off.
    Returns None when the verb doesn't apply to this domain (e.g. "닫아" for
    a light) -- caller must treat that as "doesn't apply", not as off/closed.
    """
    if domain == "cover":
        if is_open:
            return "open_cover"
        if is_close:
            return "close_cover"
        return None
    if is_on:
        return "turn_on"
    if is_off:
        return "turn_off"
    return None


def _execute_single_control_clause(prompt: str, states: list, conversation_id: str = "", forced_room=None) -> str:
    """Execute direct device control (lights, fans, covers, switches, climate, media)
    for ONE clause -- i.e. a command naming one or more device types that all
    share the same action (e.g. "안방 등하고 선풍기 켜", "안방 등 선풍기 켜").

    `forced_room` lets a compound command's later clauses (see
    execute_device_control_intent()) inherit the room named earlier in the
    same sentence when the clause itself doesn't repeat it (e.g. "안방 등
    끄고 선풍기 끄고" -- the fan clause has no room of its own).
    """
    from core.sensors import get_dynamic_rooms, match_room

    clean = prompt.replace(" ", "")
    if is_status_query(prompt, clean):
        return ""
    lower_clean = clean.lower()

    # Each list carries both the "-아/어" command form (켜/꺼/열어/닫아/틀어/
    # 올려/내려) AND the "-고" clause-connector form used by a compound
    # command's non-final clauses (켜고/끄고/열고/닫고/틀고/올리고/내리고) --
    # Korean's 으-irregular conjugation means these aren't always substrings
    # of each other (틀다's stem "틀" vs contracted "틀어"; 끄다's stem "끄"
    # vs contracted "꺼"; 올리다's stem "올리" vs contracted "올려"; 내리다's
    # stem "내리" vs contracted "내려"), so without both forms a clause like
    # "선풍기 끄고" (see _split_compound_clauses()) silently matched no verb
    # at all and the whole clause was dropped.
    is_on = any(k in clean for k in ["켜", "틀어", "틀고", "시작", "올려", "올리고", "가동"])
    is_off = any(k in clean for k in ["꺼", "끄고", "정지", "내려", "내리고", "종료", "중지"])
    is_open = any(k in clean for k in ["열어", "열고", "open"])
    is_close = any(k in clean for k in ["닫아", "닫고", "close"])
    # See _MEDIA_PAUSE_WORDS/_MEDIA_RESUME_WORDS above -- media_player-only
    # override of is_off/is_on so "정지"/"재생" pause/resume playback
    # instead of power-cycling the speaker.
    wants_media_pause = any(k in clean for k in _MEDIA_PAUSE_WORDS)
    wants_media_resume = any(k in clean for k in _MEDIA_RESUME_WORDS)

    rooms = get_dynamic_rooms(states)
    matched_room = forced_room or match_room(rooms, clean)

    # Each handler below owns one device type and returns None when that
    # type isn't named at all (or is named with no actionable verb) --
    # exactly like the branch used to just fall through to the next one.
    # Running every handler instead of returning from the first hit lets one
    # clause name several device types under one shared verb, e.g. "안방
    # 등하고 선풍기 켜" / "안방 등 선풍기 켜" -- previously whichever handler's
    # keyword happened to come first below (fans, checked before lights)
    # returned immediately and the light was never touched at all.

    def _h_curtain():
        # 1. Curtains / Covers
        if any(w in clean for w in ["커튼", "블라인드", "창문"]):
            service = "open_cover" if is_open else ("close_cover" if is_close else None)
            if service:
                candidates = [s for s in states if s.get("entity_id", "").startswith("cover.")]
                targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, "커튼", conversation_id, domain="cover", service=service)
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
        return None

    def _h_fan():
        # 2. Fans / Ventilators
        if any(w in clean for w in ["팬", "선풍기", "환풍기", "실링팬"]):
            percent_match = _PERCENT_RE.search(clean)
            if percent_match:
                percentage = max(0, min(100, int(percent_match.group(1))))
                candidates = [s for s in states if s.get("entity_id", "").startswith("fan.")]
                targets, err = resolve_control_scope(
                    prompt, clean, rooms, matched_room, candidates, "선풍기/환풍기", conversation_id,
                    domain="fan", service="set_percentage", extra_data={"percentage": percentage},
                )
                if err:
                    return err
                for f in targets:
                    ha_call_service_api("fan", "set_percentage", {"entity_id": f.get("entity_id"), "percentage": percentage})
                names = [f.get("attributes", {}).get("friendly_name") or f.get("entity_id") for f in targets]
                return f"🌀 {', '.join(names)} 풍량을 {percentage}%로 설정했습니다."

            service = "turn_on" if is_on else ("turn_off" if is_off else None)
            if service:
                fan_candidates = [s for s in states if s.get("entity_id", "").startswith("fan.")]
                # Some bathroom ventilator/dryer combo units (e.g. "안방 화장실
                # 환풍기 Climate", a himpel-style device) are modeled as HA's
                # climate domain instead of fan -- entirely missed by the
                # fan.-only search above, which is exactly why "안방 화장실
                # 환풍기 켜" reported "제어할 수 있는 선풍기/환풍기가 없습니다"
                # despite the device existing. Identified by having "fan_only"
                # among its hvac_modes (marks it as usable purely as a fan,
                # as opposed to an actual heater/AC) -- controlled via
                # set_hvac_mode(fan_only/off) below, not fan.turn_on/off, since
                # a plain climate.turn_on could restore some other hvac_mode
                # (heat/dry/cool) rather than pure ventilation.
                climate_fan_candidates = [
                    s for s in states
                    if s.get("entity_id", "").startswith("climate.")
                    and "fan_only" in (s.get("attributes", {}).get("hvac_modes") or [])
                    and any(w in (s.get("attributes", {}).get("friendly_name") or "") for w in ["팬", "선풍기", "환풍기", "실링팬"])
                ]
                candidates = fan_candidates + climate_fan_candidates
                targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, "선풍기/환풍기", conversation_id, domain="fan", service=service)
                if err:
                    return err
                for f in targets:
                    if f.get("entity_id", "").startswith("climate."):
                        ha_call_service_api("climate", "set_hvac_mode", {"entity_id": f.get("entity_id"), "hvac_mode": "fan_only" if is_on else "off"})
                    else:
                        ha_call_service_api("fan", service, {"entity_id": f.get("entity_id")})
                act_str = "켰습니다" if is_on else "껐습니다"
                names = [
                    _strip_device_type_suffix(f.get("attributes", {}).get("friendly_name") or f.get("entity_id"), ("Climate",))
                    for f in targets
                ]
                return f"🌀 {', '.join(names)} 가동을 {act_str}."
        return None

    def _h_light():
        # 3. Lights (NOTE: "스위치" intentionally not a trigger here -- it's too
        # generic and now genuinely ambiguous with the curated appliance-switch
        # branch below; a bare "스위치 꺼줘" should ask for clarification, not
        # silently mean "light".)
        #
        # "라이트"/"램프" cover real fixture names that don't contain "등"/"조명"/
        # "전등" at all (e.g. "안방 다운라이트", "안방 스텐드 램프", "작은방
        # 스트립라이트") -- without them this branch never triggered for those
        # entities, execute_device_control_intent() returned "" as if no light
        # command was recognized at all, and the prompt fell all the way through
        # handle_agent_chat() to the unrelated "Fallback" comprehensive home
        # summary (core/ha_engine.py) instead of turning anything on/off.
        if any(w in clean for w in ["불", "조명", "전등", "등", "라이트", "램프"]):
            percent_match = _PERCENT_RE.search(clean)
            if percent_match:
                # Brightness percentage, not on/off -- same "no 켜/꺼 verb, so the
                # command never got recognized at all" gap fixed for fan speed
                # (see beta.87 CHANGELOG entry); light.turn_on with brightness_pct
                # both sets the level AND turns the light on, which matches what
                # "안방 책상 등 50%" actually means. Clamped to 1-100: 0% brightness
                # isn't a sensible "on" state, and a light integration's own
                # handling of 0 is inconsistent (some turn off, some reject it).
                percentage = max(1, min(100, int(percent_match.group(1))))
                candidates = [
                    s for s in states
                    if s.get("entity_id", "").startswith("light.")
                    and "all" not in s.get("entity_id", "").lower()
                    and not any(x in (s.get("attributes", {}).get("friendly_name") or "") for x in DIAGNOSTIC_EXCLUDE_KEYWORDS)
                ]
                targets, err = resolve_control_scope(
                    prompt, clean, rooms, matched_room, candidates, "조명", conversation_id,
                    domain="light", service="turn_on", extra_data={"brightness_pct": percentage},
                )
                if err:
                    return err
                for l in targets:
                    ha_call_service_api("light", "turn_on", {"entity_id": l.get("entity_id"), "brightness_pct": percentage})
                names = [
                    _strip_device_type_suffix(l.get("attributes", {}).get("friendly_name") or l.get("entity_id"), ("조명", "전등"))
                    for l in targets
                ]
                return f"💡 {', '.join(names)} 밝기를 {percentage}%로 설정했습니다."

            service = "turn_on" if is_on else ("turn_off" if is_off else None)
            if service:
                candidates = [
                    s for s in states
                    if s.get("entity_id", "").startswith("light.")
                    and "all" not in s.get("entity_id", "").lower()
                    and not any(x in (s.get("attributes", {}).get("friendly_name") or "") for x in DIAGNOSTIC_EXCLUDE_KEYWORDS)
                ]
                targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, "조명", conversation_id, domain="light", service=service)
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
        return None

    def _h_humidifier():
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
                        and not any(x in (s.get("attributes", {}).get("friendly_name") or "") for x in DIAGNOSTIC_EXCLUDE_KEYWORDS)
                    ]
                targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, keyword, conversation_id, domain=domain, service=service)
                if err:
                    return err
                for t in targets:
                    ha_call_service_api(domain, service, {"entity_id": t.get("entity_id")})
                act_str = "켰습니다" if is_on else "껐습니다"
                names = [t.get("attributes", {}).get("friendly_name") or t.get("entity_id") for t in targets]
                icon = "💧" if keyword == "가습기" else "🌬️"
                obj_p = _particle(names[-1], "을", "를") if names else "를"
                return f"{icon} {', '.join(names)}{obj_p} {act_str}."
        return None

    def _h_appliance():
        # 5. Curated appliance switches (boiler, heater, outlet/plug)
        matched_appliance = next((k for k in APPLIANCE_SWITCH_KEYWORDS if k in clean), None)
        if matched_appliance:
            service = "turn_on" if is_on else ("turn_off" if is_off else None)
            if service:
                candidates = [
                    s for s in states
                    if s.get("entity_id", "").startswith("switch.")
                    and matched_appliance in (s.get("attributes", {}).get("friendly_name") or "")
                    and not any(x in (s.get("attributes", {}).get("friendly_name") or "") for x in DIAGNOSTIC_EXCLUDE_KEYWORDS)
                ]
                targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, matched_appliance, conversation_id, domain="switch", service=service)
                if err:
                    return err

                # Turning OFF one of these curated appliances (보일러/히터/
                # 전기스토브/콘센트/플러그) can have real consequences (pipes
                # freezing, food spoiling, ...) if it wasn't actually intended --
                # unlike a light/fan/curtain, don't execute immediately. Warn and
                # require an explicit yes on the next turn (see
                # handle_agent_chat()'s pending-confirmation check in
                # core/ha_engine.py). Turning ON is never gated -- there's no
                # "accidentally turned something on" safety concern here.
                if service == "turn_off" and conversation_id:
                    from core.session_manager import set_pending_confirmation
                    names = [t.get("attributes", {}).get("friendly_name") or t.get("entity_id") for t in targets]
                    set_pending_confirmation(conversation_id, {
                        "targets": [{"domain": "switch", "service": "turn_off", "entity_id": t.get("entity_id")} for t in targets],
                        "names": names,
                    })
                    return (
                        f"⚠️ {', '.join(names)}{_particle(names[-1], '을', '를') if names else '를'} 정말 끄시겠어요? "
                        f"끄면 불편이 생길 수 있는 기기입니다. 계속하시려면 \"응\"이라고 답해주세요."
                    )

                for t in targets:
                    ha_call_service_api("switch", service, {"entity_id": t.get("entity_id")})
                act_str = "켰습니다" if is_on else "껐습니다"
                names = [t.get("attributes", {}).get("friendly_name") or t.get("entity_id") for t in targets]
                obj_p = _particle(names[-1], "을", "를") if names else "를"
                return f"🔌 {', '.join(names)}{obj_p} {act_str}."
        return None

    def _h_climate():
        # 6. Climate (air conditioner / heater) -- on/off only for now.
        # "환풍기" is deliberately excluded here: it's already handled by the fan
        # branch above even for climate-domain bathroom ventilators, so this stays
        # scoped to actual air conditioning/heating only.
        if any(w in clean for w in ["에어컨", "냉방", "난방"]):
            service = "turn_on" if is_on else ("turn_off" if is_off else None)
            if service:
                candidates = [s for s in states if s.get("entity_id", "").startswith("climate.")]
                targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, "에어컨", conversation_id, domain="climate", service=service)
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
        return None

    def _h_media():
        # 7. Media player (TV / speaker) -- on/off only. TV prefers an existing
        # user-authored IR script (this house already has reliable "리모콘 TV 전원
        # ON/OFF" scripts) over a generic media_player call, since IR-controlled
        # TVs are unreliable to power on/off via a plain media_player service.
        media_trigger = None
        filter_terms = []
        # "음악"/"노래"/"플레이리스트" alone (no room-less "스피커" word at
        # all, e.g. "안방에 음악 틀어줘") used to match no keyword here at
        # all and fall through to the generic "확인하지 못했습니다" fallback.
        # Routed to the same 스피커 resolution as an explicit "스피커"
        # mention -- see wants_playlist_picker below for what actually
        # differs once a target speaker is resolved.
        wants_playlist_picker = any(w in clean for w in ["음악", "노래", "플레이리스트"])
        if "티비" in clean or "tv" in lower_clean:
            media_trigger = "TV"
            filter_terms = ["tv"]
        elif "스피커" in clean or wants_playlist_picker:
            media_trigger = "스피커"
            filter_terms = ["스피커", "speaker"]

        if media_trigger:
            # Pause/resume only makes sense for a speaker's actual playback
            # (TV power stays on the existing IR-script on/off path below --
            # "정지"/"재생" don't map to anything meaningful for an IR TV).
            if media_trigger == "스피커" and wants_media_pause:
                service = "media_pause"
            elif media_trigger == "스피커" and wants_media_resume:
                service = "media_play"
            else:
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
                targets, err = resolve_control_scope(prompt, clean, rooms, matched_room, candidates, media_trigger, conversation_id, domain="media_player", service=service)
                if err:
                    return err

                # "음악 틀어줘" names no specific song/playlist -- if this
                # resolved to exactly one speaker AND that speaker is
                # actually Music-Assistant-managed AND it actually has a
                # playlist library to offer, show a pick list instead of
                # guessing what to play (see core/music_assistant.py and
                # core/ui/scripts.py's setPlaylistCard()). Any of those
                # three not holding (ambiguous/whole-house target, a
                # non-MA speaker, or MA installed but genuinely empty
                # library) falls straight through to the plain power-on
                # below exactly as before this feature existed.
                if service == "turn_on" and wants_playlist_picker and len(targets) == 1:
                    import core.ha_registry as ha_registry
                    import core.music_assistant as music_assistant

                    target = targets[0]
                    eid = target.get("entity_id")
                    ma_entity_id = ha_registry.find_music_assistant_sibling(eid)
                    if ma_entity_id:
                        playlists = music_assistant.get_recent_playlists()
                        if playlists:
                            name = target.get("attributes", {}).get("friendly_name") or eid
                            ha_call_service_api("media_player", "turn_on", {"entity_id": eid})

                            # Every player Music Assistant actually knows
                            # about (see get_all_music_assistant_players()'s
                            # docstring on why MA's own players, not native
                            # HA entities, are the right list here) -- lets
                            # the card offer a speaker picker so the user
                            # isn't stuck with whichever one the room name
                            # happened to resolve to. Cross-referenced
                            # against `states` (already fetched this turn)
                            # for a human-readable name; the resolved
                            # ma_entity_id is sorted first so it's
                            # preselected.
                            by_id = {s.get("entity_id"): s for s in states}
                            players = []
                            for p in ha_registry.get_all_music_assistant_players():
                                peid = p.get("entity_id")
                                pstate = by_id.get(peid)
                                pname = (pstate.get("attributes", {}).get("friendly_name") if pstate else None) or peid
                                players.append({"entity_id": peid, "name": pname})
                            players.sort(key=lambda p: (p["entity_id"] != ma_entity_id, p["name"]))

                            _playlist_card_sink.card = {
                                "entity_id": ma_entity_id,
                                "entity_name": name,
                                "playlists": playlists,
                                "players": players,
                            }
                            return f"🎵 {name}에서 재생할 플레이리스트를 선택해 주세요."

                for t in targets:
                    ha_call_service_api("media_player", service, {"entity_id": t.get("entity_id")})
                act_str = {
                    "turn_on": "켰습니다", "turn_off": "껐습니다",
                    "media_pause": "일시정지했습니다", "media_play": "재생했습니다",
                }[service]
                names = [t.get("attributes", {}).get("friendly_name") or t.get("entity_id") for t in targets]
                obj_p = _particle(names[-1], "을", "를") if names else "를"
                return f"📺 {', '.join(names)}{obj_p} {act_str}."
        return None

    messages = [
        msg for msg in (
            _h_curtain(), _h_fan(), _h_light(), _h_humidifier(),
            _h_appliance(), _h_climate(), _h_media(),
        )
        if msg
    ]
    if messages:
        return "\n".join(messages)

    # Bare follow-up fallback: none of the handlers above matched ANY
    # device-type keyword (otherwise one would already have returned a
    # message), but this turn still carries an on/off/open/close verb and a
    # prior turn in this conversation successfully resolved a control
    # target. E.g. "안방 커튼 열어" followed next turn by just "닫아" -- with
    # no device word at all, "닫아" alone used to fall through every handler
    # and hit ha_engine.py's "확인하지 못했습니다" clarifying question even
    # though the obvious intent is "close the same curtain". Reuse those
    # remembered entities instead.
    # "재생" alone never sets is_on (it's not a natural way to say "turn on"
    # a light, so it's deliberately excluded from that generic list -- see
    # _MEDIA_RESUME_WORDS above), so it needs to be included in this gate
    # directly or a bare "재생해줘" following "안방에 음악 틀어줘" would never
    # even reach here.
    if conversation_id and (is_on or is_off or is_open or is_close or wants_media_pause or wants_media_resume):
        from core.session_manager import get_last_control_targets, set_last_control_targets

        last_ids = get_last_control_targets(conversation_id)
        if last_ids:
            by_id = {s.get("entity_id"): s for s in states}
            applied = []
            applied_service = None
            for eid in last_ids:
                s = by_id.get(eid)
                if not s:
                    continue
                domain = eid.split(".", 1)[0]
                # media_player-only pause/resume override -- see
                # _MEDIA_PAUSE_WORDS/_MEDIA_RESUME_WORDS above; every other
                # domain (light/fan/cover/...) is unaffected by these words
                # beyond "정지"/"중지" already being generic is_off synonyms.
                if domain == "media_player" and wants_media_pause:
                    service = "media_pause"
                elif domain == "media_player" and wants_media_resume:
                    service = "media_play"
                else:
                    service = _service_for_action(domain, is_on, is_off, is_open, is_close)
                if not service:
                    continue
                ha_call_service_api(domain, service, {"entity_id": eid})
                applied.append(s)
                applied_service = service
            if applied:
                set_last_control_targets(conversation_id, [s.get("entity_id") for s in applied])
                card_sink = getattr(_card_entity_sink, "entities", None)
                if card_sink is not None:
                    card_sink.extend(s.get("entity_id") for s in applied if s.get("entity_id"))
                names = [s.get("attributes", {}).get("friendly_name") or s.get("entity_id") for s in applied]
                act_str = {
                    "open_cover": "열었습니다", "close_cover": "닫았습니다",
                    "turn_on": "켰습니다", "turn_off": "껐습니다",
                    "media_pause": "일시정지했습니다", "media_play": "재생했습니다",
                }[applied_service]
                return f"↩️ (이어서) {', '.join(names)}{_particle(names[-1], '을', '를')} {act_str}."

    return ""


# Splits a compound command like "안방 등 켜고 커튼 닫아" into ["안방 등 켜고",
# "커튼 닫아"] so each clause can be resolved independently -- without this,
# _execute_single_control_clause() computes is_on/is_off/is_open/is_close
# ONCE for the whole sentence, which breaks the moment two different device
# types in one sentence need opposite actions from the SAME verb vocabulary
# (e.g. "선풍기 켜고 에어컨 꺼" -- is_on and is_off would both be true for the
# whole sentence, so a naive per-branch check would turn the AC on too,
# since is_on is checked before is_off in every branch).
_CLAUSE_CONNECTOR_RE = re.compile(
    r"(켜고|끄고|닫고|열고|틀고|올리고|내리고|시작하고|정지하고|종료하고|중지하고|돌리고|실행하고|재생하고)"
)


def _split_compound_clauses(prompt: str) -> list:
    """Split on "-고"-chained control verbs; returns [prompt] unchanged (a
    single-item list) when no connector is found, so an ordinary single
    command is completely unaffected."""
    parts = _CLAUSE_CONNECTOR_RE.split(prompt)
    if len(parts) == 1:
        return [prompt]
    clauses = []
    buf = ""
    for i, part in enumerate(parts):
        if i % 2 == 0:
            buf += part
        else:
            buf += part
            if buf.strip():
                clauses.append(buf.strip())
            buf = ""
    if buf.strip():
        clauses.append(buf.strip())
    return [c for c in clauses if c.strip()]


def _run_control_clauses(prompt: str, states: list, conversation_id: str = "") -> str:
    """Resolve and execute a (possibly compound) control command -- shared by
    the immediate path and the delayed path (_schedule_delayed_control()),
    so a delay expression doesn't need its own copy of the compound-clause
    logic. A later clause that names no room of its own inherits the room
    from the most recent EARLIER clause that did (e.g. "안방 등 모두 끄고
    선풍기 끄고 커튼 닫아" -- only the first clause says "안방", but all
    three should act on the bedroom).
    """
    from core.sensors import get_dynamic_rooms, match_room

    clauses = _split_compound_clauses(prompt)
    if len(clauses) == 1:
        return _execute_single_control_clause(prompt, states, conversation_id)

    rooms = get_dynamic_rooms(states)
    carried_room = None
    messages = []
    for clause in clauses:
        clause_room = match_room(rooms, clause.replace(" ", ""))
        result = _execute_single_control_clause(
            clause, states, conversation_id, forced_room=clause_room or carried_room
        )
        if result:
            messages.append(result)
        if clause_room:
            carried_room = clause_room

    return "\n".join(messages)


# "N분/초/시간 뒤/후(에)" or "N분/초/시간 있다가/있으면/있다" -- covers the
# phrasing variants named in the request ("10분 뒤에(후에, 있다)").
_DELAY_RE = re.compile(r"(\d+)\s*(초|분|시간)\s*(?:뒤|후|있다가|있으면|있다)\s*(?:에)?")
_DELAY_UNIT_SECONDS = {"초": 1, "분": 60, "시간": 3600}


def _extract_delay(prompt: str):
    """Pull a relative-delay expression out of the prompt.

    Returns (delay_seconds, prompt_with_delay_phrase_removed) when found,
    else (None, prompt) unchanged -- so a plain command without any delay
    wording is completely unaffected downstream.
    """
    m = _DELAY_RE.search(prompt)
    if not m:
        return None, prompt
    seconds = int(m.group(1)) * _DELAY_UNIT_SECONDS[m.group(2)]
    stripped = (prompt[: m.start()] + prompt[m.end():]).strip()
    return seconds, stripped


def _format_delay(seconds: int) -> str:
    if seconds % 3600 == 0:
        return f"{seconds // 3600}시간"
    if seconds % 60 == 0:
        return f"{seconds // 60}분"
    return f"{seconds}초"


def _label_for_call(domain: str, service: str, data: dict, tense: str = "future") -> str:
    """Fully-conjugated clause for one (domain, service, data) call, for a
    scheduling/confirmation message -- e.g. "끄겠습니다"/"껐습니다" (device
    name takes the 을/를 object particle before this) or "풍량을 50%로
    설정하겠습니다"/"설정했습니다" (already carries its own object, a compound
    noun with the device name needs no particle between them).
    `tense`: "future" (예약 실행 전 안내, see _schedule_delayed_control) or
    "past" (확인 후 실제로 실행됐음을 알릴 때, see core/ha_engine.py's pending-
    confirmation executor).
    """
    verb = "설정했습니다" if tense == "past" else "설정하겠습니다"
    if service == "set_percentage":
        return f"풍량을 {data.get('percentage')}%로 {verb}"
    if service == "turn_on" and "brightness_pct" in data:
        return f"밝기를 {data.get('brightness_pct')}%로 {verb}"
    if tense == "past":
        return {
            "turn_on": "켰습니다", "turn_off": "껐습니다",
            "open_cover": "열었습니다", "close_cover": "닫았습니다",
        }.get(service, "실행했습니다")
    return {
        "turn_on": "켜겠습니다", "turn_off": "끄겠습니다",
        "open_cover": "열겠습니다", "close_cover": "닫겠습니다",
    }.get(service, "실행하겠습니다")


def describe_calls(captured: list, states: list, tense: str = "future") -> str:
    """"안방 등을 끄겠습니다, 안방 커튼을 닫겠습니다" (or past-tense "껐습니다"
    once actually executed) style summary of a set of (domain, service,
    data) calls, built from their own entity_id/service/data --
    domain-agnostic, so it reads the same whether it's one device or several.
    Used by both the delayed-command confirmation (_schedule_delayed_
    control) and the pending dangerous/hidden-device confirmation executor
    (core/ha_engine.py) so the two message styles never drift apart."""
    by_id = {s.get("entity_id"): s for s in states}
    parts = []
    for domain, service, data in captured:
        eid = data.get("entity_id", "")
        s = by_id.get(eid)
        name = (s.get("attributes", {}).get("friendly_name") or eid) if s else eid
        label = _label_for_call(domain, service, data, tense=tense)
        if label.startswith(("풍량을", "밝기를")):
            parts.append(f"{name} {label}")
        else:
            parts.append(f"{name}{_particle(name, '을', '를')} {label}")
    return ", ".join(parts)


def _schedule_delayed_control(stripped_prompt: str, states: list, conversation_id: str, delay_seconds: int) -> str:
    """Resolve `stripped_prompt` exactly like an immediate command (same
    room/device matching, same clarifying-question safety net), but capture
    the HA service calls it would make instead of firing them, then replay
    them for real after `delay_seconds` via a background timer.

    If resolution produced no actual service calls (e.g. a clarifying
    question because the room/device was ambiguous), that message is
    returned as-is and nothing is scheduled -- a delay on top of an
    unresolved command would just be confusing.
    """
    _deferred_call_sink.calls = []
    try:
        message = _run_control_clauses(stripped_prompt, states, conversation_id)
    finally:
        captured = _deferred_call_sink.calls
        _deferred_call_sink.calls = None

    if not captured:
        return message

    entry_id = next(_scheduled_id_counter)
    description = describe_calls(captured, states)

    def _fire():
        for domain, service, data in captured:
            ha_call_service_api(domain, service, data)
        with _scheduled_lock:
            _scheduled_controls.pop(entry_id, None)

    timer = threading.Timer(delay_seconds, _fire)
    timer.daemon = True
    with _scheduled_lock:
        _scheduled_controls[entry_id] = {
            "fire_at": time.time() + delay_seconds,
            "description": description,
        }
    timer.start()

    return f"⏰ {_format_delay(delay_seconds)} 후에 {description}"


def get_scheduled_controls() -> list:
    """Snapshot of currently pending delayed-control timers, soonest first.

    Best-effort remaining time: computed from each entry's fire_at at read
    time rather than the original delay, so it stays accurate no matter how
    long ago the command was scheduled.
    """
    now = time.time()
    with _scheduled_lock:
        entries = list(_scheduled_controls.values())
    entries.sort(key=lambda e: e["fire_at"])
    return [
        {"remaining_seconds": max(0, int(e["fire_at"] - now)), "description": e["description"]}
        for e in entries
    ]


_SCHEDULE_QUERY_WORDS = ("목록", "리스트", "몇개", "몇 개", "개수", "뭐있", "뭐 있", "보여줘", "알려줘", "확인")


def is_scheduled_controls_query(prompt: str, clean: str) -> bool:
    """True for a question about currently pending delayed commands ("예약
    실행 목록 보여줘", "예약 몇 개야?") -- checked before the control-verb
    dispatch in core/ha_engine.py because such a question can contain "실행",
    which that branch would otherwise treat as a bare, unrecognized command.
    """
    if "예약" not in clean:
        return False
    if any(w.replace(" ", "") in clean for w in _SCHEDULE_QUERY_WORDS):
        return True
    return prompt.rstrip().endswith("?")


def _format_remaining(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}초"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}분 {sec}초" if sec else f"{minutes}분"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}시간 {minutes}분" if minutes else f"{hours}시간"


def get_scheduled_controls_answer() -> str:
    """"예약 실행 목록/개수" answer -- count plus each entry's remaining time
    and what it will do, soonest first."""
    entries = get_scheduled_controls()
    if not entries:
        return "⏰ 현재 예약된 실행이 없습니다."
    lines = [f"- {_format_remaining(e['remaining_seconds'])} 후: {e['description']}" for e in entries]
    return f"⏰ **예약된 실행 {len(entries)}건**\n" + "\n".join(lines)


def get_last_action_entities() -> list:
    """Entity ids the most recent execute_device_control_intent() call on
    this thread actually resolved and controlled for real.

    Drains (not just reads) the sink -- meant to be called exactly once per
    turn, immediately after handle_agent_chat() returns (see
    core/streamer.py's stream_fast_dashboard()). That drain is what keeps a
    later turn that never calls execute_device_control_intent at all (a
    status question routed through get_device_status_answer(), a weather
    question, ...) from leaking a stale entity list from several turns back
    -- it reads whatever this turn actually left behind, then resets to
    empty for the next one.

    Correctly empty for a delayed command not yet fired or a pending
    dangerous/hidden-device confirmation not yet answered: _remember() only
    appends here when it's already been explicitly armed with an empty list
    by execute_device_control_intent's immediate path below, which a
    delayed command's capture-only resolution never does.
    """
    entities = list(getattr(_card_entity_sink, "entities", None) or [])
    _card_entity_sink.entities = None
    return entities


def get_last_playlist_card() -> dict | None:
    """Drains and returns the playlist-pick-list card armed by this thread's
    most recent execute_device_control_intent() call, or None when this
    turn's command didn't offer one (see _playlist_card_sink's docstring
    above and _h_media() below). Same one-shot drain contract as
    get_last_action_entities() -- call exactly once per turn, right after
    handle_agent_chat() returns."""
    card = getattr(_playlist_card_sink, "card", None)
    _playlist_card_sink.card = None
    return card


def build_device_cards(entity_ids: list, states: list) -> list:
    """Shape the already-fetched HA state for each entity_id into a plain
    JSON "device card" descriptor for the chat UI's interactive control
    widget (see core/ui/scripts.py's setDeviceCard()). Domain-specific
    fields are only included when actually present on the entity -- the
    frontend uses their presence/absence to decide which sliders to draw
    (e.g. no color_temp_kelvin key at all means "don't show a color-temp
    slider for this light"), so this never invents a default/placeholder
    value the entity doesn't actually report.

    No new HA network calls: `states` is the same REST states list already
    fetched once per turn for command resolution -- every attribute here
    was already sitting in memory, just never read before now (see the
    2026-09-05 architecture note: only friendly_name was ever pulled out).
    """
    by_id = {s.get("entity_id"): s for s in states}
    cards = []
    for eid in entity_ids:
        s = by_id.get(eid)
        if not s:
            continue
        domain = eid.split(".", 1)[0]
        attrs = s.get("attributes", {})
        name = attrs.get("friendly_name") or eid
        card = {"entity_id": eid, "domain": domain, "name": name, "state": s.get("state")}

        if domain == "light":
            # HA Core computes/reports rgb_color (and hs_color/xy_color) as
            # a convenience conversion of the CURRENT color even for a light
            # whose supported_color_modes is color_temp-only -- e.g. "안방
            # 책상 등" (color_temp only) still reports a non-null rgb_color
            # approximating its current warm/cool white. Presence of the
            # attribute is NOT evidence the light can be SET to an arbitrary
            # color; supported_color_modes is the only reliable signal for
            # what a card should actually offer to control.
            supported_modes = set(attrs.get("supported_color_modes") or [])
            supports_brightness = bool(supported_modes - {"onoff"})
            supports_color_temp = "color_temp" in supported_modes
            supports_rgb = bool(supported_modes & {"rgb", "rgb_white", "rgbw", "rgbww", "hs", "xy"})

            if supports_brightness and attrs.get("brightness") is not None:
                card["brightness_pct"] = round(attrs["brightness"] / 255 * 100)
            if supports_color_temp and attrs.get("color_temp_kelvin") is not None:
                card["color_temp_kelvin"] = attrs["color_temp_kelvin"]
                card["min_color_temp_kelvin"] = attrs.get("min_color_temp_kelvin", 2000)
                card["max_color_temp_kelvin"] = attrs.get("max_color_temp_kelvin", 6500)
            if supports_rgb and attrs.get("rgb_color") is not None:
                card["rgb_color"] = attrs["rgb_color"]
        elif domain == "fan":
            if attrs.get("percentage") is not None:
                card["percentage"] = attrs["percentage"]
            if attrs.get("preset_modes"):
                card["preset_mode"] = attrs.get("preset_mode")
                card["preset_modes"] = attrs["preset_modes"]
        elif domain == "climate":
            if attrs.get("current_temperature") is not None:
                card["current_temperature"] = attrs["current_temperature"]
            if attrs.get("temperature") is not None:
                card["target_temperature"] = attrs["temperature"]
                card["min_temp"] = attrs.get("min_temp", 16)
                card["max_temp"] = attrs.get("max_temp", 30)
            if attrs.get("hvac_modes"):
                # No separate "current hvac_mode" field needed -- a climate
                # entity's own `state` IS its hvac_mode in HA (confirmed
                # live: "안방 화장실 환풍기" reports state="fan_only" while
                # running as a fan) -- the card's existing top-level `state`
                # is what the frontend's mode selector marks as current.
                card["hvac_modes"] = attrs["hvac_modes"]
            if attrs.get("fan_modes"):
                card["fan_mode"] = attrs.get("fan_mode")
                card["fan_modes"] = attrs["fan_modes"]
        elif domain == "cover":
            if attrs.get("current_position") is not None:
                card["current_position"] = attrs["current_position"]
        elif domain == "media_player":
            if attrs.get("volume_level") is not None:
                card["volume_pct"] = round(attrs["volume_level"] * 100)
            # "Now playing" widget (title/artist/cover/progress/prev-next/
            # play-pause) -- only meaningful once something is actually
            # loaded, so gated on media_title being present (idle/off
            # players simply don't get this block; see renderOneDeviceCard()
            # in core/ui/scripts.py). `entity_picture` (an absolute URL) is
            # used rather than `entity_picture_local` (a path relative to
            # HA's OWN origin, e.g. "/api/media_player_proxy/...") -- this
            # chat UI is served from the add-on's own origin, not HA core's,
            # so a relative entity_picture_local would resolve against the
            # wrong host and 404.
            if attrs.get("media_title"):
                card["media_title"] = attrs["media_title"]
                if attrs.get("media_artist"):
                    card["media_artist"] = attrs["media_artist"]
                if attrs.get("entity_picture"):
                    card["media_image"] = attrs["entity_picture"]
                duration = attrs.get("media_duration")
                position = attrs.get("media_position")
                if duration is None or position is None:
                    # A native Cast-integration entity generically mirrors
                    # media_title/artist/position of whatever's casting to
                    # it, but NOT media_duration -- confirmed live (Music
                    # Assistant playing through it: media_title/position
                    # present, media_duration simply absent from that
                    # entity's attributes). The Music-Assistant-owned
                    # sibling (see ha_registry.find_music_assistant_sibling())
                    # is the one that actually knows the track length, so
                    # pull whichever of the two is missing from there when
                    # one exists -- this is what makes the progress bar
                    # show up at all for an MA-managed speaker's own card.
                    import core.ha_registry as ha_registry
                    sibling_id = ha_registry.find_music_assistant_sibling(eid)
                    sibling = by_id.get(sibling_id) if sibling_id else None
                    if sibling:
                        s_attrs = sibling.get("attributes", {})
                        if duration is None:
                            duration = s_attrs.get("media_duration")
                        if position is None:
                            position = s_attrs.get("media_position")
                if duration is not None and position is not None:
                    card["media_duration"] = duration
                    card["media_position"] = position

        cards.append(card)
    return cards


def execute_device_control_intent(prompt: str, states: list, conversation_id: str = "") -> str:
    """Execute direct device control, including a compound command that
    chains multiple device types/actions in one sentence (see
    _split_compound_clauses()) and a delayed command ("안방 등 10분 뒤에
    꺼줘", see _extract_delay()/_schedule_delayed_control()).
    """
    clean = prompt.replace(" ", "")
    if is_status_query(prompt, clean):
        return ""

    delay_seconds, stripped_prompt = _extract_delay(prompt)
    if delay_seconds is not None:
        # Deliberately do NOT arm _card_entity_sink here -- nothing is
        # actually executed yet (see get_last_action_entities() docstring),
        # so _remember() must see it as inactive (None) during this
        # capture-only resolution.
        return _schedule_delayed_control(stripped_prompt, states, conversation_id, delay_seconds)

    _card_entity_sink.entities = []
    _playlist_card_sink.card = None
    return _run_control_clauses(prompt, states, conversation_id)


def toggle_automation_intent(prompt: str, states: list) -> str:
    """Turn a named automation on/off by partial name match."""
    clean = prompt.replace(" ", "")
    if is_status_query(prompt, clean):
        return ""
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
    if is_status_query(prompt, clean):
        return ""
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
