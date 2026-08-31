"""Session and Transcript Manager for Antigravity Add-on.
Provides unified, decoupled session storage matching Antigravity Mode 3 transcript.jsonl specification.
Allows Modes 1, 2, and 3 to share a single conversation context seamlessly.

Mode 3 (Antigravity CLI / agy) writes its own transcript under
``.system_generated/logs/chunks/transcript_full/00000000.jsonl`` — this module
never writes there, only reads it. Modes 1/2 have no such external writer, so
this module owns a separate file, ``.system_generated/logs/transcript.jsonl``,
for their synthetic session log. Both files share the same step schema
(step_index/type/thinking/tool_calls/content), so listing/history code reads
whichever one exists for a given conversation_id.
"""

import datetime
import json
import os
import re
import threading
import uuid


def get_brain_base_dir() -> str:
    """Resolve the brain base directory across different runtime environments."""
    for p in ["/root/.gemini/antigravity-cli/brain", "/config/.gemini/antigravity-cli/brain"]:
        if os.path.exists(os.path.dirname(p)):
            return p
    home = os.path.expanduser("~")
    return os.path.join(home, ".gemini", "antigravity-cli", "brain")


def generate_conversation_id() -> str:
    """Generate a standard UUID v4 conversation ID."""
    return str(uuid.uuid4())


def get_session_transcript_path(conversation_id: str) -> str:
    """Path to the Modes-1/2 synthetic transcript.jsonl for a conversation.

    Mode 3 does not write here — see get_mode3_transcript_path().
    """
    base = get_brain_base_dir()
    return os.path.join(base, conversation_id, ".system_generated", "logs", "transcript.jsonl")


def get_mode3_transcript_path(conversation_id: str) -> str:
    """Path to agy's own live transcript for a Mode 3 conversation (read-only)."""
    base = get_brain_base_dir()
    return os.path.join(
        base, conversation_id, ".system_generated", "logs", "chunks", "transcript_full", "00000000.jsonl"
    )


def get_readable_transcript_path(conversation_id: str) -> str | None:
    """Return whichever transcript file actually exists for this conversation.

    Prefers agy's native Mode 3 transcript (more complete: raw thinking/tool
    steps as agy recorded them) and falls back to the Modes-1/2 synthetic log.
    Returns None if the conversation has no transcript yet.
    """
    mode3_path = get_mode3_transcript_path(conversation_id)
    if os.path.exists(mode3_path):
        return mode3_path
    modes12_path = get_session_transcript_path(conversation_id)
    if os.path.exists(modes12_path):
        return modes12_path
    return None


def session_exists(conversation_id: str) -> bool:
    """Whether a conversation has any recorded transcript (Mode 3 or 1/2)."""
    return get_readable_transcript_path(conversation_id) is not None


def get_current_iso_time() -> str:
    """Return ISO 8601 formatted timestamp with timezone."""
    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    return now.isoformat()


def _write_line_to_transcript(file_path: str, data: dict):
    """Internal helper to safely create directories and append a JSON line."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[SessionManager Error] Failed to write transcript: {e}")


def get_next_step_index(file_path: str) -> int:
    """Count existing steps to assign monotonically increasing step_index."""
    if not os.path.exists(file_path):
        return 1
    count = 0
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in f:
                count += 1
    except Exception:
        pass
    return count + 1


def format_cli_user_input(prompt: str) -> str:
    """Format user prompt in Google Antigravity CLI's standard metadata envelope."""
    now_iso = get_current_iso_time()
    return (
        f"<USER_REQUEST>\n{prompt.strip()}\n</USER_REQUEST>\n"
        f"<ADDITIONAL_METADATA>\nThe current local time is: {now_iso}.\n</ADDITIONAL_METADATA>"
    )


_UNICODE_ESCAPE_RE = re.compile(r"\\u([0-9a-fA-F]{4})")


def decode_unicode_text(text: str) -> str:
    """Decode literal '\\uXXXX' escape sequences embedded in already-decoded text.

    Only the matched escape substrings are replaced (via a targeted regex), so
    genuine UTF-8 text elsewhere in the string is left untouched. The previous
    implementation did `text.encode("utf-8").decode("unicode_escape")` on the
    *whole* string, which also mangled real (non-escaped) UTF-8 characters —
    e.g. Korean text already in the string would come out corrupted.
    """
    if not text:
        return ""
    try:
        text = _UNICODE_ESCAPE_RE.sub(lambda m: chr(int(m.group(1), 16)), text)
    except Exception:
        pass
    return text.strip()


def clean_user_prompt(text: str) -> str:
    """Extract pure user question and strip system XML envelopes/metadata."""
    if not text:
        return ""
    m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", text, flags=re.DOTALL | re.IGNORECASE)
    if m and m.group(1).strip():
        text = m.group(1).strip()
    else:
        text = re.sub(r"<[A-Z_]+>.*?</[A-Z_]+>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    return decode_unicode_text(text)


def record_user_input(conversation_id: str, prompt: str) -> int:
    """Record user's input step (USER_INPUT) formatted in standard CLI envelope."""
    if not conversation_id or not prompt:
        return 0
    fpath = get_session_transcript_path(conversation_id)
    step_idx = get_next_step_index(fpath)
    entry = {
        "step_index": step_idx,
        "type": "USER_INPUT",
        "source": "USER_EXPLICIT",
        "content": format_cli_user_input(prompt),
        "created_at": get_current_iso_time(),
    }
    _write_line_to_transcript(fpath, entry)
    return step_idx


def record_thinking_and_tools(
    conversation_id: str,
    thinking: str = "",
    tool_calls: list = None,
) -> int:
    """Record model's internal thinking process and executed tool calls."""
    if not conversation_id or (not thinking and not tool_calls):
        return 0
    fpath = get_session_transcript_path(conversation_id)
    step_idx = get_next_step_index(fpath)
    entry = {
        "step_index": step_idx,
        "type": "PLANNER_RESPONSE",
        "source": "MODEL",
        "status": "DONE",
        "created_at": get_current_iso_time(),
    }
    if thinking:
        entry["thinking"] = thinking
    if tool_calls:
        entry["tool_calls"] = tool_calls

    _write_line_to_transcript(fpath, entry)
    return step_idx


def record_model_response(
    conversation_id: str,
    content: str,
) -> int:
    """Record model's final response text."""
    if not conversation_id or not content:
        return 0
    fpath = get_session_transcript_path(conversation_id)
    step_idx = get_next_step_index(fpath)
    entry = {
        "step_index": step_idx,
        "type": "PLANNER_RESPONSE",
        "source": "MODEL",
        "status": "DONE",
        "content": content,
        "created_at": get_current_iso_time(),
    }
    _write_line_to_transcript(fpath, entry)
    return step_idx


_TRANSCRIPT_LOCK = threading.Lock()


def append_session_interaction(
    conversation_id: str,
    prompt: str,
    thinking: str = "",
    tool_calls: list = None,
    response_text: str = "",
):
    """Synchronously record a full interaction cycle with sequential step ordering."""
    if not conversation_id:
        return
    with _TRANSCRIPT_LOCK:
        record_user_input(conversation_id, prompt)
        if thinking or tool_calls:
            record_thinking_and_tools(conversation_id, thinking, tool_calls)
        if response_text:
            record_model_response(conversation_id, response_text)


def append_session_interaction_async(
    conversation_id: str,
    prompt: str,
    thinking: str = "",
    tool_calls: list = None,
    response_text: str = "",
):
    """Non-blocking asynchronous helper to record a complete interaction cycle."""
    if not conversation_id:
        return

    def _worker():
        append_session_interaction(
            conversation_id,
            prompt,
            thinking,
            tool_calls,
            response_text,
        )

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def get_session_history(conversation_id: str) -> list:
    """Parse and return full chronological history of a session (Mode 3 or 1/2)."""
    fpath = get_readable_transcript_path(conversation_id)
    if not fpath:
        return []
    history = []
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                l = line.strip()
                if l:
                    try:
                        item = json.loads(l)
                        if item.get("type") == "USER_INPUT" and "content" in item:
                            item["content"] = clean_user_prompt(item["content"])
                        elif "content" in item and isinstance(item["content"], str):
                            item["content"] = decode_unicode_text(item["content"])
                        if "thinking" in item and isinstance(item["thinking"], str):
                            item["thinking"] = decode_unicode_text(item["thinking"])
                        history.append(item)
                    except Exception:
                        pass
    except Exception as e:
        print(f"[SessionManager Error] Failed to read session history: {e}")
    return history


def list_all_sessions(limit: int = 50) -> list:
    """List all available conversation sessions sorted by recent activity."""
    base = get_brain_base_dir()
    if not os.path.exists(base):
        return []
    sessions = []
    try:
        entries = os.listdir(base)
        for cid in entries:
            cdir = os.path.join(base, cid)
            if not os.path.isdir(cdir):
                continue
            tpath = get_readable_transcript_path(cid)
            mtime = os.path.getmtime(cdir)
            first_prompt = ""
            last_message = ""
            turn_count = 0
            if tpath:
                mtime = max(mtime, os.path.getmtime(tpath))
                try:
                    with open(tpath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = [line.strip() for line in f if line.strip()]
                        turn_count = len(lines)
                        for l in lines:
                            item = json.loads(l)
                            if not first_prompt and item.get("type") == "USER_INPUT":
                                first_prompt = clean_user_prompt(item.get("content", ""))
                            if item.get("content"):
                                last_message = decode_unicode_text(str(item.get("content", "")))
                except Exception:
                    pass

            clean_title = first_prompt[:50] if first_prompt else f"Session {cid[:8]}"
            sessions.append({
                "conversation_id": cid,
                "title": clean_title,
                "turns": turn_count,
                "last_message": last_message[:80],
                "updated_at": datetime.datetime.fromtimestamp(mtime).isoformat(),
                "timestamp": mtime,
            })
    except Exception as e:
        print(f"[SessionManager Error] Failed to list sessions: {e}")

    sessions.sort(key=lambda s: s["timestamp"], reverse=True)
    return sessions[:limit]


def record_mode2_interaction(
    conversation_id: str,
    prompt: str,
    response_text: str,
    target_entities: list = None,
    service_called: str = "",
):
    """Record Mode 2 (Ultra-Fast Smart Home) interaction with HA service tool calls."""
    if not conversation_id:
        return

    thinking = f"초고속 스마트홈 엔진: 사용자 의도 분석 및 기기 제어/상태 조회 ('{prompt}')"
    tool_calls = []
    if target_entities and service_called:
        domain = service_called.split(".")[0] if "." in service_called else "homeassistant"
        service = service_called.split(".")[1] if "." in service_called else service_called
        for eid in target_entities:
            tool_calls.append({
                "name": "call_mcp_tool",
                "args": {
                    "ServerName": "home-assistant",
                    "ToolName": "ha_call_service",
                    "Arguments": {
                        "domain": domain,
                        "service": service,
                        "service_data": {"entity_id": eid},
                    },
                },
                "toolSummary": f"{service.replace('_', ' ').capitalize()} device",
                "toolAction": f"Calling {service_called} on {eid}",
            })
    elif "상태" in prompt or "온도" in prompt or "습도" in prompt or "공기" in prompt:
        tool_calls.append({
            "name": "call_mcp_tool",
            "args": {
                "ServerName": "home-assistant",
                "ToolName": "ha_get_state",
                "Arguments": {"query": prompt},
            },
            "toolSummary": "Get HA states",
            "toolAction": "Querying current entity states",
        })

    append_session_interaction_async(
        conversation_id=conversation_id,
        prompt=prompt,
        thinking=thinking,
        tool_calls=tool_calls if tool_calls else None,
        response_text=response_text,
    )


def record_mode1_interaction(
    conversation_id: str,
    prompt: str,
    response_text: str,
    sensor_count: int = 0,
):
    """Record Mode 1 (AI Deep Brain) interaction with sensor collection and analysis steps."""
    if not conversation_id:
        return

    thinking = f"AI 딥 브레인: 다차원 환경 센서({sensor_count}개) 수집 및 실내외 온습도/공기질 쾌적성 밸런스 추론"
    tool_calls = [
        {
            "name": "call_mcp_tool",
            "args": {
                "ServerName": "home-assistant",
                "ToolName": "ha_get_state",
                "Arguments": {"category": "environment_sensors"},
            },
            "toolSummary": "Fetch sensor matrix",
            "toolAction": f"Collected {sensor_count} environmental sensors (CO2, TVOC, PM2.5, Temp, Hum)",
        }
    ]

    append_session_interaction_async(
        conversation_id=conversation_id,
        prompt=prompt,
        thinking=thinking,
        tool_calls=tool_calls,
        response_text=response_text,
    )
