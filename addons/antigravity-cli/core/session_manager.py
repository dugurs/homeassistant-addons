"""Session and Transcript Manager for Antigravity Add-on.
Provides unified, decoupled session storage matching Antigravity Mode 3 transcript.jsonl specification.
Allows Modes 1, 2, and 3 to share a single conversation context seamlessly.

``.system_generated/logs/transcript.jsonl`` is the one canonical, cumulative
log for a conversation, appended to across every turn regardless of mode —
Modes 1/2 write here directly (see record_mode1_interaction /
record_mode2_interaction), and Mode 3 (`agy`) writes here natively on its own
whenever it runs for this conversation_id (including across --resume calls).

``.system_generated/logs/chunks/transcript_full/00000000.jsonl`` is a
*separate*, agy-internal snapshot that only reflects the conversation's first
turn — verified empirically it does not grow across --resume calls, so it
must never be treated as the source of truth for history/listing. It is kept
here only as a last-resort fallback for old conversation directories that
happen to have it but not the canonical file.
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
    """Path to the canonical, cumulative transcript.jsonl for a conversation.

    Written to directly by Modes 1/2 (this module) and natively by Mode 3
    (`agy`) — see the module docstring.
    """
    base = get_brain_base_dir()
    return os.path.join(base, conversation_id, ".system_generated", "logs", "transcript.jsonl")


def get_mode3_first_turn_snapshot_path(conversation_id: str) -> str:
    """Path to agy's first-turn-only chunk snapshot (fallback read source only).

    Does not grow across --resume calls — never use this as the primary
    source for a conversation's history/listing.
    """
    base = get_brain_base_dir()
    return os.path.join(
        base, conversation_id, ".system_generated", "logs", "chunks", "transcript_full", "00000000.jsonl"
    )


def get_readable_transcript_path(conversation_id: str) -> str | None:
    """Return the transcript file to read for this conversation.

    Prefers the canonical, cumulative transcript.jsonl. Falls back to agy's
    first-turn snapshot only for old conversation directories that predate
    it (or the rare case where agy hasn't flushed the canonical file yet but
    has produced the first-turn snapshot). Returns None if neither exists.
    """
    canonical_path = get_session_transcript_path(conversation_id)
    if os.path.exists(canonical_path):
        return canonical_path
    fallback_path = get_mode3_first_turn_snapshot_path(conversation_id)
    if os.path.exists(fallback_path):
        return fallback_path
    return None


def session_exists(conversation_id: str) -> bool:
    """Whether a conversation has any recorded transcript (Mode 3 or 1/2)."""
    return get_readable_transcript_path(conversation_id) is not None


def is_agy_native_session(conversation_id: str) -> bool:
    """Whether agy itself has ever run a turn under this exact conversation_id.

    True only once agy's own first-turn snapshot exists on disk -- the one
    reliable signal that agy, not just our own record_mode1_interaction /
    record_mode2_interaction, has adopted this id. A Modes-1/2-only
    conversation (client-generated uuid, agy never invoked) returns False,
    which matters for stream_headless_cli(): agy has no record of a
    Modes-1/2-only id, so it must never be handed to it via --conversation
    (see docs/COMMUNICATION_SPEC.md constraint #6).
    """
    return os.path.exists(get_mode3_first_turn_snapshot_path(conversation_id))


def _continuation_marker_paths(conversation_id: str) -> tuple[str, str]:
    """(continued_as path, continued_from path) for a conversation's logs dir."""
    base = os.path.join(get_brain_base_dir(), conversation_id, ".system_generated", "logs")
    return os.path.join(base, "continued_as.txt"), os.path.join(base, "continued_from.txt")


def link_conversation_continuation(old_conversation_id: str, new_conversation_id: str):
    """Record that old_conversation_id's chat continued under new_conversation_id.

    Written when a Modes-1/2-only conversation hands off to Mode 3 and agy
    assigns its own, different id (see stream_headless_cli()). Only touches
    our own marker files -- never agy's own directory contents -- so it can't
    interfere with agy's resume/tailing logic.
    """
    if not old_conversation_id or not new_conversation_id or old_conversation_id == new_conversation_id:
        return
    old_as, _ = _continuation_marker_paths(old_conversation_id)
    _, new_from = _continuation_marker_paths(new_conversation_id)
    try:
        os.makedirs(os.path.dirname(old_as), exist_ok=True)
        with open(old_as, "w", encoding="utf-8") as f:
            f.write(new_conversation_id)
        os.makedirs(os.path.dirname(new_from), exist_ok=True)
        with open(new_from, "w", encoding="utf-8") as f:
            f.write(old_conversation_id)
    except Exception as e:
        print(f"[SessionManager Error] Failed to write continuation marker: {e}")


def get_continuation_target(conversation_id: str) -> str | None:
    """The id this conversation continued into (via a later mode hand-off), if any."""
    as_path, _ = _continuation_marker_paths(conversation_id)
    try:
        if os.path.exists(as_path):
            with open(as_path, "r", encoding="utf-8") as f:
                target = f.read().strip()
                return target or None
    except Exception:
        pass
    return None


def get_continuation_source(conversation_id: str) -> str | None:
    """The id this conversation continued from (via an earlier mode hand-off), if any."""
    _, from_path = _continuation_marker_paths(conversation_id)
    try:
        if os.path.exists(from_path):
            with open(from_path, "r", encoding="utf-8") as f:
                source = f.read().strip()
                return source or None
    except Exception:
        pass
    return None


def get_continuation_chain(conversation_id: str) -> list:
    """Full chain of conversation_ids this conversation belongs to, oldest first.

    Walks backward via continued_from to the root, then forward via
    continued_as to the tail, so the result is identical regardless of which
    id in the chain is passed in. Guards against a corrupt/cyclic marker
    producing an infinite loop.
    """
    if not conversation_id:
        return []

    root = conversation_id
    seen = {root}
    while True:
        prev = get_continuation_source(root)
        if not prev or prev in seen:
            break
        root = prev
        seen.add(root)

    chain = [root]
    seen = {root}
    cursor = root
    while True:
        nxt = get_continuation_target(cursor)
        if not nxt or nxt in seen:
            break
        chain.append(nxt)
        seen.add(nxt)
        cursor = nxt
    return chain


def _delete_single_conversation_dir(conversation_id: str) -> bool:
    """Remove one conversation's brain folder. Path-safety-checked (see delete_session)."""
    if not conversation_id or "/" in conversation_id or "\\" in conversation_id or ".." in conversation_id:
        return False
    cdir = os.path.join(get_brain_base_dir(), conversation_id)
    if not os.path.isdir(cdir):
        return False
    import shutil
    try:
        shutil.rmtree(cdir)
        return True
    except Exception:
        return False


def delete_session(conversation_id: str) -> bool:
    """Permanently remove a conversation's brain folder (all transcripts/logs).

    Deletes every id in its mode-hand-off continuation chain (see
    get_continuation_chain()), not just the one passed in -- otherwise a
    superseded Modes-1/2-only folder from before a Mode 3 hand-off would
    never be reachable from the (now hidden) session list, yet would linger
    on disk forever.

    Path-safety-checked: rejects anything that isn't a bare id (no path
    separators or traversal), since conversation_id ultimately comes from
    client-supplied JSON and is joined directly into a filesystem path.
    """
    if not conversation_id or "/" in conversation_id or "\\" in conversation_id or ".." in conversation_id:
        return False
    chain = get_continuation_chain(conversation_id) or [conversation_id]
    deleted_any = False
    for cid in chain:
        if _delete_single_conversation_dir(cid):
            deleted_any = True
    return deleted_any


def _custom_title_path(conversation_id: str) -> str:
    """Path to a conversation's user-set custom title marker (see set_session_title)."""
    return os.path.join(get_brain_base_dir(), conversation_id, ".system_generated", "logs", "custom_title.txt")


def set_session_title(conversation_id: str, title: str) -> bool:
    """Persist a user-chosen title for a conversation, overriding the auto-generated one.

    Path-safety-checked like delete_session(), since conversation_id comes
    from client-supplied JSON and is joined directly into a filesystem path.
    """
    if not conversation_id or "/" in conversation_id or "\\" in conversation_id or ".." in conversation_id:
        return False
    title = (title or "").strip()[:80]
    if not title:
        return False
    cdir = os.path.join(get_brain_base_dir(), conversation_id)
    if not os.path.isdir(cdir):
        return False
    path = _custom_title_path(conversation_id)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(title)
        return True
    except Exception:
        return False


def get_custom_title(conversation_id: str) -> str | None:
    """User-set title for a conversation, if any (see set_session_title)."""
    path = _custom_title_path(conversation_id)
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                title = f.read().strip()
                return title or None
    except Exception:
        pass
    return None


def _rewound_marker_path(conversation_id: str) -> str:
    """Path to a conversation's "was rewound, next Mode 3 turn needs a fresh agy id" marker."""
    return os.path.join(get_brain_base_dir(), conversation_id, ".system_generated", "logs", "rewound.marker")


def mark_rewound(conversation_id: str):
    """Flag that this conversation was just rewound (see rewind_session()).

    Read by core/streamer.py's resume-decision logic: agy has no --rewind
    flag and can't actually be made to forget the turns rewind_session()
    discarded from the *displayed* transcript, so the next Mode 3 turn must
    start a brand-new agy id instead of resuming the old one with
    --conversation (which would silently un-rewind everything from agy's own
    point of view). Cleared once that fresh id is established -- see
    clear_rewound().
    """
    path = _rewound_marker_path(conversation_id)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(get_current_iso_time())
    except Exception as e:
        print(f"[SessionManager Error] Failed to write rewound marker: {e}")


def is_rewound(conversation_id: str) -> bool:
    """Whether this conversation is waiting on a fresh agy id after a rewind (see mark_rewound())."""
    return os.path.exists(_rewound_marker_path(conversation_id))


def clear_rewound(conversation_id: str):
    """Clear the rewound marker once a fresh agy id has taken over (see mark_rewound())."""
    path = _rewound_marker_path(conversation_id)
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def rewind_session(conversation_id: str, step_index: int) -> bool:
    """Truncate a conversation's canonical transcript to discard the
    USER_INPUT step at `step_index` and everything after it -- i.e. roll the
    conversation back to right before that message was sent, so the user can
    send a different one from that point. (Not "keep the clicked message but
    drop its answer": that would leave a dangling, unanswered question sitting
    in the middle of the retained history.) Also flags the conversation as
    rewound (see mark_rewound()) so the next Mode 3 turn starts fresh instead
    of silently resuming with all the "rewound-away" content still live in
    agy's own memory.

    Path-safety-checked like delete_session()/set_session_title() --
    conversation_id comes from client-supplied JSON and is joined directly
    into a filesystem path.

    Only rewinds within conversation_id's own transcript file -- not an
    earlier segment of its continuation chain (see get_continuation_chain).
    The frontend enforces this by only offering the rewind action on turns
    whose source_cid (see get_session_history()) matches the conversation
    actually open.

    Reads/writes whichever file get_readable_transcript_path() would read
    (canonical transcript.jsonl if present, else agy's legacy first-turn
    snapshot) -- NOT unconditionally get_session_transcript_path()'s
    canonical path. A conversation created before this addon's canonical
    transcript.jsonl convention (or one agy hasn't flushed it for yet) only
    has the legacy snapshot; truncating a canonical path that doesn't exist
    for it silently no-ops (os.path.exists() check fails) instead of
    rewinding what's actually displayed. Rewriting the legacy snapshot here
    is safe despite its own docstring warning ("must never be treated as the
    source of truth for history/listing", i.e. don't read it back for
    aggregation when a canonical file also exists) -- that warning is about
    *listing*, not about mutating it, and a rewind always forces the next
    Mode 3 turn onto a brand-new agy id (see mark_rewound() above), so agy
    never reads this file back either.

    Locates the physical line to cut at by matching each line's own
    `step_index` JSON field rather than assuming line position N holds
    step_index N -- true for our own writer (get_next_step_index() always
    assigns len(existing lines)+1) but not a documented guarantee for agy's
    own native transcript writer, which is what actually produces this file
    for a Mode 3 conversation.
    """
    if not conversation_id or "/" in conversation_id or "\\" in conversation_id or ".." in conversation_id:
        return False
    if not isinstance(step_index, int) or step_index < 1:
        return False
    fpath = get_readable_transcript_path(conversation_id)
    if not fpath:
        return False
    with _TRANSCRIPT_LOCK:
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            return False
        cutoff = None
        for i, line in enumerate(lines):
            l = line.strip()
            if not l:
                continue
            try:
                item = json.loads(l)
            except Exception:
                continue
            if item.get("step_index") == step_index:
                cutoff = i
                break
        if cutoff is None:
            return False  # no line carries this step_index -- nothing to rewind to
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                f.writelines(lines[:cutoff])
        except Exception:
            return False
    mark_rewound(conversation_id)
    return True


def build_rewind_context_preamble(conversation_id: str, max_chars: int = 6000) -> str:
    """Compact question/answer replay of a rewound conversation's retained
    turns, meant to be prepended to the next Mode 3 prompt.

    A rewind forces that next turn onto a brand-new agy id (see
    is_rewound()/mark_rewound()) since agy has no --rewind flag and its own
    internal memory of the discarded turns can't actually be erased -- so a
    fresh agy conversation otherwise has *zero* awareness of what the user
    chose to keep. This reconstructs just the retained question/answer text
    (skipping raw tool-call/thinking noise) so the fresh id starts with real
    context instead of none. Length-capped like the other best-effort text
    blobs in this addon (crash logs, /usage raw_text) since a long kept
    history would otherwise blow up prompt size.
    """
    history = get_session_history(conversation_id)
    lines = []
    for item in history:
        if item.get("type") == "USER_INPUT":
            q = clean_user_prompt(item.get("content", ""))
            if q:
                lines.append(f"User: {q}")
        else:
            content = item.get("content")
            if isinstance(content, str) and content.strip():
                lines.append(f"Assistant: {content.strip()}")
    if not lines:
        return ""
    replay = "\n".join(lines)
    if len(replay) > max_chars:
        replay = "...(생략)...\n" + replay[-max_chars:]
    return (
        "<PRIOR_CONVERSATION_CONTEXT>\n"
        "다음은 사용자가 이어가길 원하는 이전 대화 내용입니다. 이 맥락을 참고해서 답변하세요.\n\n"
        f"{replay}\n"
        "</PRIOR_CONVERSATION_CONTEXT>\n\n"
    )


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


def _parse_transcript_file(fpath: str) -> list:
    """Parse one transcript.jsonl file into a list of cleaned history items."""
    items = []
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
                        items.append(item)
                    except Exception:
                        pass
    except Exception as e:
        print(f"[SessionManager Error] Failed to read transcript {fpath}: {e}")
    return items


def get_session_history(conversation_id: str) -> list:
    """Parse and return full chronological history of a session (Mode 3 or 1/2).

    Follows the conversation's continuation chain (get_continuation_chain())
    so a conversation that hopped ids mid-chat -- Modes 1/2 handing off to
    Mode 3, which agy resumes under its own, different id (see
    stream_headless_cli() / link_conversation_continuation()) -- returns one
    merged, chronologically-ordered timeline no matter which id in the chain
    is queried.
    """
    chain = get_continuation_chain(conversation_id) or [conversation_id]
    history = []
    for cid in chain:
        fpath = get_readable_transcript_path(cid)
        if fpath:
            items = _parse_transcript_file(fpath)
            # Tag each item with the physical conversation_id/file it actually
            # lives in -- distinct from `conversation_id` (the id this whole
            # merged view was requested under, i.e. the chain's terminal id).
            # rewind_session() can only truncate one physical file at a time,
            # so the UI needs this to tell "this message is in the file we
            # can actually rewind" (source_cid == the terminal id) apart from
            # an earlier, already-superseded chain segment (see rewind_session()
            # docstring) -- without it, a step_index from an old segment's
            # file could be misapplied to truncate the wrong file.
            for item in items:
                item["source_cid"] = cid
            history.extend(items)
    return history


def list_all_sessions(limit: int = 50) -> list:
    """List all available conversation sessions sorted by recent activity.

    A conversation that hopped ids mid-chat (Modes 1/2 -> Mode 3 hand-off,
    see link_conversation_continuation()) is shown as exactly one card, keyed
    by the chain's terminal (newest) id, with title/turns/last_message/
    timestamp computed across the FULL chain -- otherwise the same logical
    conversation would show up as two disconnected, partial cards. An id
    that has since continued elsewhere (get_continuation_target() returns
    something) is skipped here; it's only reachable as part of its chain.
    """
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
            if get_continuation_target(cid):
                continue  # superseded by a later id in its chain; not its own card

            chain = get_continuation_chain(cid) or [cid]
            mtime = 0.0
            first_prompt = ""
            last_message = ""
            turn_count = 0
            for chain_cid in chain:
                chain_dir = os.path.join(base, chain_cid)
                if os.path.isdir(chain_dir):
                    mtime = max(mtime, os.path.getmtime(chain_dir))
                tpath = get_readable_transcript_path(chain_cid)
                if not tpath:
                    continue
                mtime = max(mtime, os.path.getmtime(tpath))
                try:
                    with open(tpath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = [line.strip() for line in f if line.strip()]
                        turn_count += len(lines)
                        for l in lines:
                            item = json.loads(l)
                            if not first_prompt and item.get("type") == "USER_INPUT":
                                first_prompt = clean_user_prompt(item.get("content", ""))
                            if item.get("content"):
                                last_message = decode_unicode_text(str(item.get("content", "")))
                except Exception:
                    pass

            if mtime == 0.0:
                mtime = os.path.getmtime(cdir)
            clean_title = get_custom_title(cid) or (first_prompt[:50] if first_prompt else f"Session {cid[:8]}")
            updated_dt = datetime.datetime.fromtimestamp(mtime)
            sessions.append({
                "conversation_id": cid,
                "title": clean_title,
                "turns": turn_count,
                "last_message": last_message[:80],
                "updated_at": updated_dt.isoformat(),
                # Pre-formatted server-side (MM/DD HH:MM, 24h) so the UI
                # doesn't depend on the browser's locale/AM-PM formatting.
                "date_str": updated_dt.strftime("%m/%d %H:%M"),
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
