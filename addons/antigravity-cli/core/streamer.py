"""Real-Time SSE Streaming Engine supporting Mode 1 (AI Deep Brain) and Mode 2 (Ultra-Fast Smart Home)."""

import json
import os
import re
import shlex
import signal
import sys
import threading
import time
import uuid
from datetime import datetime

from core.ha_engine import (
    get_ai_deep_environment_analysis,
    get_ha_states,
    get_weather_env_summary,
    handle_agent_chat,
)
from core.session_manager import (
    build_rewind_context_preamble,
    clear_rewound,
    generate_conversation_id,
    is_agy_native_session,
    is_rewound,
    link_conversation_continuation,
    record_mode1_interaction,
    record_mode2_interaction,
    session_exists,
)


def estimate_tokens(text: str) -> int:
    """Calculate realistic token count for multilingual / Korean + English markdown."""
    if not text:
        return 0
    korean_chars = len(re.findall(r"[\uac00-\ud7a3]", text))
    other_chars = len(text) - korean_chars
    return max(1, int(korean_chars * 0.8 + other_chars * 0.3))


def _agy_str(v):
    """Unwrap agy's double-JSON-encoded tool-call arg values.

    Content-bearing args (CodeContent, TargetContent, AbsolutePath,
    CommandLine, toolSummary, ...) arrive as a JSON string literal *inside*
    the already-parsed outer value -- e.g. parsing the transcript line once
    leaves args["CodeContent"] == '"hello world\\n"' (quote characters and
    all), and it takes a second json.loads() to get the real `hello world`
    text. Scalar-looking args (Overwrite, StartLine, ...) aren't wrapped
    this way (confirmed against a real write_to_file/replace_file_content
    transcript) and pass through unchanged.
    """
    if isinstance(v, str) and len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        try:
            return json.loads(v)
        except Exception:
            pass
    return v


def _diff_log_lines(old_text: str, new_text: str) -> str:
    """Render a '- old' / '+ new' block diff for a live-log line.

    write_to_file/replace_file_content already scope old/new content to
    the exact changed range, so a real line-matching diff algorithm isn't
    needed here -- just show what was removed then what was added.
    """
    lines = []
    if old_text:
        lines.extend(f"- {l}" for l in old_text.splitlines())
    if new_text:
        lines.extend(f"+ {l}" for l in new_text.splitlines())
    return "\n".join(lines)


def _diff_stat(old_text: str, new_text: str) -> str:
    """'+N -M' added/removed line counts for a reasoning-step badge."""
    added = len(new_text.splitlines()) if new_text else 0
    removed = len(old_text.splitlines()) if old_text else 0
    return f"+{added} -{removed}"


def _parse_iso(ts):
    """Parse agy's 'YYYY-MM-DDTHH:MM:SSZ' created_at into a datetime, or None."""
    if not ts or not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


_DETAIL_CAP = 6000  # matches build_rewind_context_preamble()'s existing convention


def _cap_detail(text: str) -> str:
    if text and len(text) > _DETAIL_CAP:
        return text[:_DETAIL_CAP] + "\n...(생략)"
    return text or ""


# When a call_mcp_tool result is too big to inline, agy's GENERIC follow-up
# is just this one-line pointer -- the real payload sits in a per-step
# output.txt agy then reads back itself (a separate view_file tool_calls
# step immediately after, whose own GENERIC result is a numbered-line dump
# with a "File Path:/Total Lines:/..." header agy prints around it). Rather
# than show that plumbing as its own confusing "확인 output.txt" row, read
# the file directly (see tail_transcript's suppress_file_path) and fold its
# real content into the original MCP Tool card as its Tool Output.
_SAVED_TO_FILE_RE = re.compile(r"saved to:\s*(file://\S+)")


def _read_saved_output_file(file_uri: str) -> str:
    """Reads back a step's output.txt referenced by a "saved to: file://..."
    pointer. Tries the literal path first, then swaps /root/<->/config/ (the
    same ambiguity tail_transcript's candidate_paths already accounts for --
    the addon and the agy process don't always agree on which prefix the
    shared .gemini directory is mounted at).
    """
    path = file_uri[len("file://"):] if file_uri.startswith("file://") else file_uri
    candidates = [path]
    if path.startswith("/root/"):
        candidates.append("/config/" + path[len("/root/"):])
    elif path.startswith("/config/"):
        candidates.append("/root/" + path[len("/config/"):])
    for p in candidates:
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            continue
    return ""


def _result_stat(tname: str, content: str) -> str:
    """Best-effort short summary badge for a tool's GENERIC follow-up result."""
    if tname == "find_by_name":
        m = re.search(r"Found (\d+) results?", content or "")
        if m:
            return f"{m.group(1)}개 결과"
    elif tname == "grep_search":
        m = re.search(r"Found (\d+) (?:matches|results?)", content or "", re.IGNORECASE)
        if m:
            return f"{m.group(1)}개 결과"
    elif tname == "run_command":
        lines = (content or "").strip().splitlines()
        if lines:
            return f"{len(lines)}줄 출력"
    return ""


def _classify_tool_call(tname: str, args: dict, desc: str) -> dict:
    """Build the display shape for one tool_call -- shared by the live SSE
    reasoning_step pipeline and (mirrored in core/ui/scripts.py) the
    restored-history renderer. `needs_result` marks tools whose args alone
    don't carry their outcome, so tail_transcript() holds the step open one
    more line waiting for a GENERIC follow-up step to fill in stat/detail
    (see the buffering loop below) -- write_to_file/replace_file_content
    already carry full old/new content in args, so they're never buffered.
    """
    if tname == "call_mcp_tool":
        # Args go in a separate "Tool arguments" JSON block on expand (see
        # args_json / toolIoDetailHTML() in core/ui/scripts.py) rather than
        # crammed into the summary line -- matches Antigravity's own
        # "MCP Tool: server / tool" + expandable arguments/output UI.
        tcalled = _agy_str(args.get("ToolName", "mcp"))
        tcalled_display = tcalled.replace("/", " / ") if isinstance(tcalled, str) and "/" in tcalled else tcalled
        targs = args.get("Arguments", {})
        if isinstance(targs, str):
            # agy sometimes logs Arguments as a JSON-encoded string (the same
            # shape MCP wire args take) rather than an already-nested dict --
            # without this, a real tool call with actual parameters (e.g.
            # ha_search's domain_filter) silently lost its whole "Tool
            # arguments" block (only Tool Output ever showed).
            try:
                targs = json.loads(targs)
            except Exception:
                targs = {}
        args_json = json.dumps(targs, ensure_ascii=False, indent=2) if isinstance(targs, dict) and targs else ""
        return {
            "group": "ha", "verb": "MCP Tool:", "target": tcalled_display,
            "stat": "", "detail": "", "args_json": args_json, "needs_result": True,
        }
    if tname == "view_file":
        fpath = _agy_str(args.get("AbsolutePath", ""))
        fname = os.path.basename(fpath) if fpath else "file"
        return {"group": "explore", "explore_kind": "file", "verb": "확인", "target": fname + (f" ({desc})" if desc else ""), "stat": "", "detail": "", "needs_result": True}
    if tname == "run_command":
        cmd_str = _agy_str(args.get("CommandLine", ""))
        return {"group": "command", "verb": "명령어", "target": cmd_str, "stat": "", "detail": "", "needs_result": True}
    if tname == "search_web":
        q = _agy_str(args.get("query", ""))
        return {"group": "web", "verb": "웹 검색", "target": q, "stat": "", "detail": "", "needs_result": True}
    if tname == "find_by_name":
        pattern = _agy_str(args.get("Pattern", ""))
        return {"group": "explore", "explore_kind": "search", "verb": "파일명 검색", "target": pattern, "stat": "", "detail": "", "needs_result": True}
    if tname == "grep_search":
        query = _agy_str(args.get("Query", "")) or desc
        return {"group": "explore", "explore_kind": "search", "verb": "검색", "target": query, "stat": "", "detail": "", "needs_result": True}
    if tname == "replace_file_content":
        fpath = _agy_str(args.get("TargetFile", ""))
        fname = os.path.basename(fpath) if fpath else "file"
        old_c = _agy_str(args.get("TargetContent", "")) or ""
        new_c = _agy_str(args.get("ReplacementContent", "")) or ""
        instr = _agy_str(args.get("Instruction", "")) or desc
        return {
            "group": "edit", "verb": "수정", "target": fname + (f" ({instr})" if instr else ""),
            "stat": _diff_stat(old_c, new_c), "detail": _diff_log_lines(old_c, new_c), "needs_result": False,
        }
    if tname == "write_to_file":
        fpath = _agy_str(args.get("TargetFile", ""))
        fname = os.path.basename(fpath) if fpath else "file"
        new_c = _agy_str(args.get("CodeContent", "")) or ""
        overwrite = _agy_str(args.get("Overwrite", "false")) == "true"
        added = len(new_c.splitlines()) if new_c else 0
        # Overwriting an existing file's prior line count isn't in these args
        # (see _agy_str's docstring -- write_to_file only ever carries the
        # new content), so the stat only claims what's actually known: lines
        # added. A genuine diff needs old content, which replace_file_content
        # supplies and this tool doesn't.
        stat = f"+{added}" if not overwrite else f"+{added} (덮어씀)"
        return {
            "group": "edit", "verb": "덮어쓰기" if overwrite else "생성", "target": fname + (f" ({desc})" if desc else ""),
            "stat": stat, "detail": _diff_log_lines("", new_c), "needs_result": False,
        }
    return {"group": "other", "verb": "도구 실행", "target": f"{tname} {desc}".strip(), "stat": "", "detail": "", "needs_result": True}


def make_sse(event_type: str, content: str = "", tokens: dict = None, data: dict = None) -> str:
    """Format SSE payload."""
    payload = {"type": event_type}
    if content:
        payload["content"] = content
    if tokens:
        payload["tokens"] = tokens
    if data is not None:
        payload["data"] = data
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# Mode 3 stop/cancel registry -- maps a per-request stream_id (minted at the
# start of stream_headless_cli, before agy's own conversation_id is even
# known) to the running `script`/agy process group and a stop flag. Lets
# POST /api/chat/stop (antigravity_api.py) reach across HTTP request threads
# and kill an in-flight generation without agy having to cooperate.
_RUNNING_STREAMS_LOCK = threading.Lock()
_RUNNING_STREAMS = {}  # stream_id -> (subprocess.Popen, threading.Event)


def stop_stream(stream_id: str) -> bool:
    """Kill the process group backing an in-flight Mode 3 stream, if any."""
    with _RUNNING_STREAMS_LOCK:
        entry = _RUNNING_STREAMS.get(stream_id)
    if not entry:
        return False
    proc, stop_event = entry
    stop_event.set()
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    return True


def stream_ai_deep_brain(prompt: str, is_mobile: bool = False, conversation_id: str = ""):
    """Mode 1: AI Deep Brain Multi-Dimensional Environmental Analysis & Living Advice Streamer."""
    t_start = time.time()
    actual_prompt = re.sub(r"^(ai|/llm)\s*", "", prompt, flags=re.IGNORECASE).strip()
    input_tokens = estimate_tokens(actual_prompt) + 120  # prompt + system context

    if not conversation_id:
        conversation_id = generate_conversation_id()
    yield make_sse("session_init", conversation_id)

    states = get_ha_states()
    sensor_cnt = len(states) if states else 0
    lower = actual_prompt.lower()
    # Also route general "how's the house" queries here, not just explicit
    # weather/env words -- otherwise a prompt like "우리집 종합 상황 알려줘"
    # matches none of the weather words, falls through to the same
    # handle_agent_chat() Mode 2 already calls, and 복합모드 ends up returning
    # the exact same text as 고속모드 for the single most common status query.
    if states and any(
        w in lower
        for w in [
            "날씨", "환경", "온도", "습도", "기상", "기온", "공기", "co2", "미세먼지",
            "상태", "상황", "현황", "요약", "브리핑", "종합", "분위기", "집안", "우리집", "어때",
        ]
    ):
        full_text = get_ai_deep_environment_analysis(states, actual_prompt, is_mobile=is_mobile)
    else:
        full_text = handle_agent_chat(actual_prompt, conversation_id, "", False, is_mobile=is_mobile)

    # Same synthetic MCP Tool card as Mode 2's stream_fast_dashboard (see its
    # comment) -- no real MCP round-trip here either (get_ha_states() above
    # is a direct HA REST call), but showing the query/sensor-count args and
    # the synthesized result through the identical "MCP Tool: ha_get_state"
    # card keeps 복합모드's live view consistent with 고속모드's.
    yield make_sse("reasoning_step", data={
        "group": "ha",
        "verb": "MCP Tool:",
        "target": "ha_get_state",
        "stat": "",
        "args_json": json.dumps({"query": actual_prompt, "category": "environment_sensors"}, ensure_ascii=False, indent=2),
        "detail": json.dumps({"result": full_text, "sensor_count": sensor_cnt}, ensure_ascii=False, indent=2),
    })

    yield make_sse("text", full_text)

    if conversation_id:
        record_mode1_interaction(conversation_id, actual_prompt, full_text, sensor_cnt)

    elapsed = time.time() - t_start
    output_tokens = estimate_tokens(full_text)
    total_tokens = input_tokens + output_tokens
    speed_tps = round(output_tokens / max(0.01, elapsed), 1)

    tokens_meta = {
        "input": input_tokens,
        "output": output_tokens,
        "total": total_tokens,
        "speed_tps": speed_tps,
        "elapsed": round(elapsed, 3),
    }
    yield make_sse("done", tokens=tokens_meta)


def stream_fast_dashboard(prompt: str, is_mobile: bool = False, conversation_id: str = ""):
    """Mode 2: Ultra-Fast Smart Home Native Dispatcher (0.05s) + Step-by-Step Tool Visibility."""
    t_start = time.time()
    actual_prompt = re.sub(r"^(ai|/llm)\s*", "", prompt, flags=re.IGNORECASE).strip()
    input_tokens = estimate_tokens(actual_prompt) + 40

    if not conversation_id:
        conversation_id = generate_conversation_id()
    yield make_sse("session_init", conversation_id)

    full_text = handle_agent_chat(actual_prompt, conversation_id, "", False, is_mobile=is_mobile)

    # Fast mode has no real MCP round-trip (handle_agent_chat resolves the
    # answer with local heuristics against already-cached HA state), but the
    # reasoning-timeline card is still worth showing so a user can see what
    # was asked and what came back -- same "MCP Tool: name" + expandable
    # Tool arguments/Output shape _classify_tool_call() builds for a real
    # call_mcp_tool step (core/ui/scripts.py's toolIoDetailHTML renders both
    # the same way regardless of source).
    yield make_sse("reasoning_step", data={
        "group": "ha",
        "verb": "MCP Tool:",
        "target": "ha_get_state",
        "stat": "",
        "args_json": json.dumps({"query": actual_prompt}, ensure_ascii=False, indent=2),
        "detail": json.dumps({"result": full_text}, ensure_ascii=False, indent=2),
    })

    yield make_sse("text", full_text)

    if conversation_id:
        record_mode2_interaction(conversation_id, actual_prompt, full_text)

    elapsed = time.time() - t_start
    output_tokens = estimate_tokens(full_text)
    total_tokens = input_tokens + output_tokens
    speed_tps = round(output_tokens / max(0.01, elapsed), 1)

    tokens_meta = {
        "input": input_tokens,
        "output": output_tokens,
        "total": total_tokens,
        "speed_tps": speed_tps,
        "elapsed": round(elapsed, 3),
    }
    yield make_sse("done", tokens=tokens_meta)


from core.system_info import check_agy_hardware_support


def stream_headless_cli(
    prompt: str,
    is_mobile: bool = False,
    conversation_id: str = "",
    model: str = "",
    agent: str = "",
):
    """Mode 3: Google Antigravity Headless CLI Real-Time NDJSON Streamer (0-latency).

    `model` must be one of agy's actual, directly-invocable slugs (e.g.
    "gemini-3.7-flash-high") -- there is no separate --effort flag. Effort is
    baked into the slug itself; the picker resolves (base model, effort) to
    the right variant slug client-side before this is ever called. See
    core/model_discovery.py for how that mapping is discovered live.

    `agent` must be the id (directory name) of a custom agent discovered by
    core.agent_discovery -- see that module for why this is read off disk
    instead of via `agy agents` (no structured output support).
    """
    import subprocess
    t_start = time.time()
    actual_prompt = re.sub(r"^(ai|/llm)\s*", "", prompt, flags=re.IGNORECASE).strip()

    # Validate against agy's own live model discovery (queried and cached in
    # core.model_discovery) rather than a hardcoded list -- new models ship
    # and the lineup varies by account, so a static catalog can't be trusted
    # as the source of truth for what's actually valid.
    from core.model_discovery import get_valid_variant_slugs

    model = model if model in get_valid_variant_slugs() else ""

    from core.agent_discovery import get_valid_agent_ids

    agent = agent if agent in get_valid_agent_ids() else ""

    hw_info = check_agy_hardware_support()
    agy_bin = "/usr/local/bin/agy"

    if not hw_info.get("supported", False) or not os.path.exists(agy_bin):
        yield make_sse("tool", "ℹ️ CPU 호스트 모드(AVX) 미지원 감지 -> 안전하게 [모드 2: 복합 모드]로 자동 전환합니다.")
        for ev in stream_ai_deep_brain(prompt, is_mobile=is_mobile, conversation_id=conversation_id):
            yield ev
        return

    # Require agy's own first-turn marker, not just "a transcript.jsonl exists" --
    # Modes 1/2 write that file themselves via record_mode1_interaction /
    # record_mode2_interaction, for an id agy has never seen. Handing such an
    # id to --conversation would hit the exact failure this function's
    # docstring warns about (docs/COMMUNICATION_SPEC.md constraint #6), so a
    # Modes-1/2-only conversation switching to Mode 3 is treated as new here
    # (see the `cid != conversation_id` hand-off handling in read_stdout()
    # below, which links the two ids together once agy assigns its own).
    # A rewind (see core/session_manager.py rewind_session()/mark_rewound())
    # truncated this conversation's *displayed* transcript, but agy's own
    # internal memory of the discarded turns can't actually be erased --
    # there is no --rewind flag. Resuming with --conversation here would
    # silently un-rewind everything from agy's point of view. So a rewound
    # conversation is forced through the same "no --conversation, agy mints
    # a fresh id, we link it as a continuation" path already used for the
    # Modes-1/2 -> Mode-3 hand-off below (see the `evt == "init"` handling in
    # read_stdout()), and the retained history is replayed into the prompt
    # itself (build_rewind_context_preamble()) so the fresh id isn't
    # starting from zero context.
    was_rewound = bool(conversation_id) and is_rewound(conversation_id)
    resume_this_session = (
        bool(conversation_id)
        and session_exists(conversation_id)
        and is_agy_native_session(conversation_id)
        and not was_rewound
    )
    if resume_this_session:
        # We already know the id (echoed back from a previous session_init for
        # this same conversation) — announce it again immediately. For a new
        # conversation we don't know agy's id yet; that's announced once agy's
        # own "init" event reports it (see read_stdout() below).
        yield make_sse("session_init", conversation_id)
    # Kept separate from actual_prompt (which gets the rewind context
    # preamble prepended below) so the status line still shows the user's own
    # new message rather than the replayed context that precedes it.
    display_prompt = actual_prompt
    if was_rewound:
        actual_prompt = build_rewind_context_preamble(conversation_id) + actual_prompt

    env = os.environ.copy()
    env["HOME"] = "/root"
    env["USER"] = "root"
    env["PATH"] = f"/root/.local/bin:/usr/local/bin:/usr/bin:/bin:{env.get('PATH', '')}"
    env["PYTHONUNBUFFERED"] = "1"
    env["FORCE_COLOR"] = "0"
    env["TERM"] = "dumb"

    api_key = ""
    print_timeout = "5m"
    enable_sandbox = False
    if os.path.exists("/data/options.json"):
        try:
            with open("/data/options.json", "r") as f:
                opts = json.load(f)
                api_key = opts.get("api_key", "").strip()
                print_timeout = str(opts.get("print_timeout") or "5m").strip()
                enable_sandbox = bool(opts.get("enable_sandbox", False))
        except Exception:
            pass

    if api_key:
        env["GEMINI_API_KEY"] = api_key
        env["GOOGLE_API_KEY"] = api_key
        env["ANTIGRAVITY_API_KEY"] = api_key

    resume_desc = " (대화 이어가기)" if resume_this_session else (" (되돌리기 이후 새 대화로 이어감)" if was_rewound else "")
    yield make_sse("tool", f"🚀 [Antigravity CLI] 세션 개시{resume_desc}: '{display_prompt[:30]}...'")

    # Use 'script -q -c' to run agy in a pseudo-TTY.
    # This forces the Go runtime to flush output line-by-line instead of buffering.
    # Without this, agy buffers 4KB before writing anything to a pipe.
    # `--conversation <id>` is the documented flag for resuming a specific
    # prior conversation by id (per `agy --help`); there is no `--resume` flag.
    resume_arg = f" --conversation {conversation_id}" if resume_this_session else ""
    model_arg = f" --model {model}" if model else ""
    agent_arg = f" --agent {agent}" if agent else ""
    # Go duration format only (e.g. "5m", "90s", "1h30m") -- print_timeout is
    # addon-config-supplied but still gets embedded into a shell -c string
    # below, so anything not matching this shape is dropped in favor of
    # agy's own built-in default rather than passed through unsanitized.
    timeout_arg = f" --print-timeout {print_timeout}" if re.fullmatch(r"[0-9]+(h|m|s)([0-9]+(m|s))?", print_timeout) else ""
    sandbox_arg = " --sandbox" if enable_sandbox else ""
    # shlex.quote(), not json.dumps() -- this string is re-parsed by a POSIX
    # shell (`script -c` runs it via `/bin/sh -c`), which has no idea what
    # JSON escaping is. json.dumps("안녕\n하세요") produces
    # "안녕\n하세요" -- inside shell double quotes neither
    # \uXXXX nor \n is a recognized escape, so agy received those as *literal*
    # backslash-u.../backslash-n text instead of Korean characters/a real
    # newline (confirmed live: multi-line attachment captions showed a bare
    # "\n" in the answer). shlex.quote() single-quotes the whole string, which
    # passes UTF-8 bytes and embedded newlines through completely unchanged.
    script_cmd = (
        f"{agy_bin} -p {shlex.quote(actual_prompt)}"
        f"{resume_arg}"
        f"{model_arg}"
        f"{agent_arg}"
        f" --output-format stream-json"
        f" --dangerously-skip-permissions"
        f"{timeout_arg}"
        f"{sandbox_arg}"
    )
    cmd = ["script", "-q", "-e", "-c", script_cmd, "/dev/null"]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            encoding="utf-8",
            env=env,
            start_new_session=True,  # own process group -- lets stop_stream() kill script + its agy child together
        )
    except Exception as e:
        yield make_sse("tool", f"⚠️ CLI 프로세스 기동 실패 ({str(e)}) -> AI 딥 브레인으로 자동 전환")
        for ev in stream_ai_deep_brain(prompt, is_mobile=is_mobile, conversation_id=conversation_id):
            yield ev
        return

    # Register this process so a concurrent POST /api/chat/stop (a different
    # HTTP request thread) can find and kill it. stream_id is announced to the
    # client immediately -- unlike conversation_id, it doesn't depend on agy
    # having assigned anything yet, so a stop is possible from the very first
    # moment of a brand-new conversation.
    stream_id = uuid.uuid4().hex
    stop_event = threading.Event()
    with _RUNNING_STREAMS_LOCK:
        _RUNNING_STREAMS[stream_id] = (proc, stop_event)
    yield make_sse("stream_id", stream_id)

    import queue

    event_queue = queue.Queue()
    done_event = threading.Event()
    seen_step_indices = set()
    has_emitted_chunk = False
    auth_failed = False
    output_chars = 0
    full_text_parts = []

    def tail_transcript(conv_id):
        """Monitor conversation transcript on disk in real time and emit thoughts/tool actions."""
        # transcript.jsonl is the canonical, cumulative log (grows across every
        # --conversation-resumed turn); the chunks/transcript_full snapshot only ever holds
        # the conversation's first turn, so it's tried last as a fallback for
        # the brief window before transcript.jsonl exists on a new session.
        candidate_paths = [
            f"/root/.gemini/antigravity-cli/brain/{conv_id}/.system_generated/logs/transcript.jsonl",
            f"/config/.gemini/antigravity-cli/brain/{conv_id}/.system_generated/logs/transcript.jsonl",
            f"/root/.gemini/antigravity-cli/brain/{conv_id}/.system_generated/logs/chunks/transcript_full/00000000.jsonl",
            f"/config/.gemini/antigravity-cli/brain/{conv_id}/.system_generated/logs/chunks/transcript_full/00000000.jsonl",
        ]
        
        # No fixed retry cap here on purpose -- a previous version gave up
        # after ~6.4s (80 * 0.08s), but agy's own README documents a cold
        # ha-mcp/uvx startup taking 10-20s on its own, well past that budget.
        # When the cap was hit first, this thread returned silently with zero
        # reasoning_step events for the whole turn: the final answer still
        # streamed through fine (a separate code path), just with no
        # reasoning log ever shown for that turn -- reproducing exactly when
        # agy/MCP happened to be slow to start, not on any pattern a user
        # could pin down. Instead, keep looking for as long as the agy
        # process itself is still running (done_event, set in read_stdout()'s
        # finally block when the process exits) -- there's no reason to give
        # up while the turn that would eventually write this file is still
        # in flight.
        file_obj = None
        while not done_event.is_set():
            for cp in candidate_paths:
                if os.path.exists(cp):
                    try:
                        file_obj = open(cp, "r", encoding="utf-8", errors="ignore")
                        break
                    except Exception:
                        pass
            if file_obj:
                break
            time.sleep(0.08)

        if not file_obj:
            return

        if resume_this_session:
            # This transcript already has prior turns on disk (we're resuming).
            # Seek past them so only genuinely new steps are treated as "live" —
            # otherwise every step from earlier turns replays as if it just
            # happened, flooding the live log with stale history.
            file_obj.seek(0, os.SEEK_END)

        # A tool step whose outcome isn't in its own args (see
        # _classify_tool_call's needs_result) is held here for one more line
        # instead of being emitted right away -- agy logs a plain GENERIC step
        # with the tool's actual output *right after* the call (confirmed live
        # for find_by_name/run_command/search_web: "Found N results", command
        # stdout, a search summary), and folding that in beats showing an
        # empty "검색했음" row with no way to see what it found.
        pending_tool = None
        prev_created_at = None  # previous step's created_at, for "Nsec" badges
        suppress_file_path = None  # set by the "saved to" branch below -- see _read_saved_output_file

        def flush_pending():
            nonlocal pending_tool
            if pending_tool is not None:
                event_queue.put(("reasoning_step", pending_tool))
                pending_tool = None

        try:
            while not done_event.is_set():
                line = file_obj.readline()
                if not line:
                    time.sleep(0.08)
                    continue
                try:
                    step_data = json.loads(line.strip())
                    s_idx = step_data.get("step_index")
                    if s_idx in seen_step_indices:
                        continue
                    seen_step_indices.add(s_idx)

                    stype = step_data.get("type", "")
                    created = _parse_iso(step_data.get("created_at"))
                    duration_sec = None
                    if created and prev_created_at:
                        duration_sec = max(0, round((created - prev_created_at).total_seconds()))
                    if created:
                        prev_created_at = created

                    tcs = step_data.get("tool_calls", [])
                    thinking = (step_data.get("thinking") or "").strip()
                    content = step_data.get("content", "")

                    if stype == "GENERIC" and content and not tcs and pending_tool is not None:
                        saved_to = _SAVED_TO_FILE_RE.search(content)
                        if saved_to and pending_tool.get("tname") == "call_mcp_tool":
                            file_content = _read_saved_output_file(saved_to.group(1))
                            pending_tool["detail"] = _cap_detail(file_content) if file_content else _cap_detail(content)
                            if not pending_tool["stat"]:
                                pending_tool["stat"] = _result_stat(pending_tool["tname"], pending_tool["detail"])
                            flush_pending()
                            if file_content:
                                # agy is about to auto-issue a view_file call to
                                # read this same file back for itself -- we
                                # already inlined its content above, so that
                                # call (and its own numbered-dump result) is
                                # pure plumbing now; drop it instead of showing
                                # a second, confusing "확인 output.txt" row.
                                suppress_file_path = saved_to.group(1)[len("file://"):]
                            continue
                        pending_tool["detail"] = _cap_detail(content)
                        if not pending_tool["stat"]:
                            pending_tool["stat"] = _result_stat(pending_tool["tname"], content)
                        flush_pending()
                        continue

                    # This step isn't the buffered tool's result (or nothing was
                    # buffered) -- whatever was waiting doesn't get a result now.
                    flush_pending()

                    # 1. Thinking / Reasoning step
                    if thinking:
                        # No length cap -- the reasoning-log box scrolls
                        # horizontally instead of wrapping (see .term-body in
                        # core/ui/styles.py), so truncating here only threw
                        # content away for no display reason.
                        clean_think = thinking.replace("\n\n", " · ").replace("\n", " ")
                        event_queue.put(("reasoning_step", {
                            "kind": "thinking", "step_index": s_idx,
                            "text": clean_think, "duration_sec": duration_sec,
                        }))

                    # 2. Tool Calls
                    for tc in tcs:
                        tname = tc.get("name", "tool")
                        args = tc.get("args") or {}
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                pass
                        if not isinstance(args, dict):
                            args = {}

                        if suppress_file_path and tname == "view_file":
                            fpath = _agy_str(args.get("AbsolutePath", ""))
                            fpath = fpath[len("file://"):] if fpath.startswith("file://") else fpath
                            if fpath == suppress_file_path or os.path.basename(fpath) == os.path.basename(suppress_file_path):
                                suppress_file_path = None
                                continue  # its GENERIC result falls through as a no-op (no pending_tool set for it)

                        summary = _agy_str(tc.get("toolSummary") or args.get("toolSummary") or "") or ""
                        action = _agy_str(tc.get("toolAction") or args.get("toolAction") or "") or ""
                        desc = summary or action or ""

                        step = {"kind": "tool", "step_index": s_idx, "tname": tname, "duration_sec": duration_sec}
                        step.update(_classify_tool_call(tname, args, desc))

                        if step.pop("needs_result", False):
                            # Only the last call in a multi-call step can plausibly
                            # be answered by the very next line -- flush any earlier
                            # one in this same step as-is first.
                            flush_pending()
                            pending_tool = step
                        else:
                            event_queue.put(("reasoning_step", step))

                    # 3. Model Response (Final output)
                    if content and stype == "PLANNER_RESPONSE" and not tcs:
                        event_queue.put(("content", content))

                    # suppress_file_path only ever describes THE step right
                    # after a "saved to" pointer -- if it wasn't consumed by a
                    # matching view_file call above, drop it so it can't later
                    # misfire against some unrelated step's own output.txt
                    # (steps reuse that same basename under different dirs).
                    suppress_file_path = None

                except Exception:
                    pass
        finally:
            flush_pending()
            try:
                file_obj.close()
            except Exception:
                pass

    def read_stdout():
        nonlocal auth_failed, output_chars
        try:
            for line in iter(proc.stdout.readline, ""):
                l = line.rstrip("\r\n").strip()
                if not l:
                    continue
                try:
                    data = json.loads(l)
                except Exception:
                    lower = l.lower()
                    if any(w in lower for w in ["login required", "please run", "agy login", "oauth", "unauthorized", "unauthenticated"]):
                        auth_failed = True
                        break
                    continue

                evt = data.get("event", data.get("type", ""))

                if evt == "init":
                    tools = data.get("init", {}).get("tools", [])
                    cid = data.get("conversation_id", "")
                    if cid and conversation_id and cid != conversation_id:
                        # Modes 1/2 -> Mode 3 hand-off: we came in with an id
                        # of our own (already carrying Modes-1/2 history) but
                        # withheld --conversation since agy never issued it
                        # (see is_agy_native_session() above), so agy minted
                        # its own, different id. Link the two so session
                        # listing/history reads present one merged
                        # conversation regardless of which id is opened.
                        link_conversation_continuation(conversation_id, cid)
                        # If this hand-off was caused by a rewind rather than
                        # a Modes-1/2-only conversation's first Mode 3 turn,
                        # the fresh id agy just minted is now the live one --
                        # clear the marker so the *next* turn is free to
                        # resume normally with --conversation again.
                        clear_rewound(conversation_id)
                    if cid and not resume_this_session:
                        # New conversation: agy just assigned its own id (we
                        # never sent --conversation, so it can't be echoing
                        # one back to us). This is the id future turns must
                        # pass as conversation_id to actually resume with agy.
                        event_queue.put(("session_init", cid))
                    event_queue.put(("live_log", f"🚀 [세션 시작] Antigravity CLI v2.0 ({len(tools)}개 도구 로드됨)"))
                    if cid:
                        t_tail = threading.Thread(target=tail_transcript, args=(cid,), daemon=True)
                        t_tail.start()

                elif evt == "step_update":
                    delta = data.get("step_update", {}).get("text_delta", "")
                    if delta:
                        event_queue.put(("chunk", delta))

                elif evt == "result":
                    res = data.get("result", {})
                    event_queue.put(("result", res))
                    break

                elif evt in ("content_block_delta", "text_delta"):
                    delta = data.get("delta", {}).get("text", "") or data.get("text", "")
                    if delta:
                        event_queue.put(("chunk", delta))

                elif evt == "error":
                    msg = data.get("error", {}).get("message", "") or data.get("message", "")
                    if any(w in msg.lower() for w in ["auth", "login", "oauth", "unauthorized"]):
                        auth_failed = True
                        break
                    event_queue.put(("live_log", f"⚠️ [오류] {msg}"))
        finally:
            done_event.set()
            try:
                proc.stdout.close()
                proc.wait()
            except Exception:
                pass

    t_proc = threading.Thread(target=read_stdout, daemon=True)
    t_proc.start()

    try:
        # Stream out events as they arrive in real time
        while True:
            try:
                ev_type, ev_data = event_queue.get(timeout=0.08)
                if ev_type == "session_init":
                    yield make_sse("session_init", ev_data)
                elif ev_type == "live_log":
                    yield make_sse("live_log", ev_data)
                elif ev_type == "reasoning_step":
                    yield make_sse("reasoning_step", data=ev_data)
                elif ev_type == "chunk":
                    full_text_parts.append(ev_data)
                    output_chars += len(ev_data)
                    has_emitted_chunk = True
                    yield make_sse("chunk", ev_data)
                elif ev_type == "content":
                    # Check if content was already streamed. Must compare
                    # against the *joined* text, not each chunk individually
                    # (any(... in p for p in full_text_parts)) -- a chunked
                    # answer accumulates as many small pieces, so the first 40
                    # chars of a later duplicate rarely fall entirely inside
                    # any single piece, and the false negative meant the whole
                    # answer got appended a second time (confirmed live: full
                    # responses were duplicated in the chat bubble).
                    already_streamed = ev_data[:40] in "".join(full_text_parts) if full_text_parts else False
                    if not already_streamed:
                        full_text_parts.append(ev_data)
                        output_chars += len(ev_data)
                        has_emitted_chunk = True
                        yield make_sse("chunk", ev_data)
                elif ev_type == "result":
                    # Documented terminal statuses: SUCCESS, ERROR, CANCELED,
                    # INTERRUPTED, INVALID, WAITING, RUNNING. Anything but SUCCESS
                    # (or a missing status, for older/other agy builds) means no
                    # real answer is coming — surface it instead of completing
                    # silently with a blank bubble.
                    status = ev_data.get("status")
                    if status and status != "SUCCESS" and not has_emitted_chunk:
                        err_msg = ev_data.get("error") or f"작업이 정상적으로 완료되지 않았습니다 (status: {status})."
                        yield make_sse("live_log", f"⚠️ [Antigravity CLI 오류] {err_msg}")
                        yield make_sse("chunk", f"> ⚠️ **[Antigravity CLI 오류]**\n\n{err_msg}\n")
                        full_text_parts.append(err_msg)
                        has_emitted_chunk = True

                    resp_text = ev_data.get("response", "")
                    # Same joined-text comparison as the "content" branch
                    # above -- this is the specific case that was actually
                    # duplicating full answers live (the terminal "result"
                    # event's `response` re-sends the whole answer that
                    # already streamed in as many small "chunk"/step_update
                    # deltas beforehand).
                    already_streamed = resp_text[:40] in "".join(full_text_parts) if full_text_parts else False
                    if resp_text and not already_streamed:
                        full_text_parts.append(resp_text)
                        output_chars += len(resp_text)
                        has_emitted_chunk = True
                        yield make_sse("chunk", resp_text)

                    usage = ev_data.get("usage", {})
                    duration = ev_data.get("duration_seconds", 0)
                    elapsed = duration or (time.time() - t_start)
                    in_tok = usage.get("input_tokens", 120)
                    out_tok = usage.get("output_tokens", max(1, int(output_chars * 0.4)))
                    think_tok = usage.get("thinking_tokens", 0)
                    total_tok = usage.get("total_tokens", in_tok + out_tok)

                    tokens_meta = {
                        "input": in_tok,
                        "output": out_tok,
                        "thinking": think_tok,
                        "total": total_tok,
                        "speed_tps": round(out_tok / max(0.01, elapsed), 1),
                        "elapsed": round(elapsed, 2),
                    }
                    yield make_sse("done", tokens=tokens_meta)
                    return
            except queue.Empty:
                if done_event.is_set() and event_queue.empty():
                    break

        if stop_event.is_set():
            # User-initiated stop (POST /api/chat/stop, see stop_stream() above)
            # -- report whatever was generated so far and end here. This check
            # must come before the fallback branches below: falling through to
            # those would silently substitute a Mode 2 answer for a generation
            # the user just cancelled.
            yield make_sse("live_log", "⏹️ 사용자에 의해 중지되었습니다.")
            elapsed = time.time() - t_start
            tokens_meta = {
                "input": 120,
                "output": max(1, int(output_chars * 0.4)),
                "thinking": 0,
                "total": 120 + max(1, int(output_chars * 0.4)),
                "speed_tps": round(max(1, int(output_chars * 0.4)) / max(0.01, elapsed), 1),
                "elapsed": round(elapsed, 2),
            }
            yield make_sse("done", tokens=tokens_meta)
            return

        if has_emitted_chunk:
            elapsed = time.time() - t_start
            tokens_meta = {
                "input": 120,
                "output": max(1, int(output_chars * 0.4)),
                "thinking": 0,
                "total": 120 + max(1, int(output_chars * 0.4)),
                "speed_tps": round(max(1, int(output_chars * 0.4)) / max(0.01, elapsed), 1),
                "elapsed": round(elapsed, 2),
            }
            yield make_sse("done", tokens=tokens_meta)
            return

        if auth_failed:
            yield make_sse("live_log", "🔑 [인증 필요] Terminal 탭에서 agy 실행 후 로그인하세요.")
            yield make_sse("chunk", "> 🔑 **[인증 필요]** Terminal 탭에서 `agy` 실행 후 Google 계정으로 1회 로그인하세요.\n\n")
            for ev in stream_ai_deep_brain(prompt, is_mobile=is_mobile, conversation_id=conversation_id):
                yield ev
        else:
            for ev in stream_ai_deep_brain(prompt, is_mobile=is_mobile, conversation_id=conversation_id):
                yield ev
    finally:
        with _RUNNING_STREAMS_LOCK:
            _RUNNING_STREAMS.pop(stream_id, None)


def stream_agent_chat(
    prompt: str,
    is_direct_llm: bool = False,
    stream_mode: int = 1,
    is_mobile: bool = False,
    conversation_id: str = "",
    model: str = "",
    agent: str = "",
):
    """Router for the 3 Clean Streaming Modes with unified session management.

    conversation_id assignment differs by mode: Modes 1/2 have no external
    process with its own identity, so an id is generated up front (see
    stream_ai_deep_brain / stream_fast_dashboard). Mode 3 delegates to `agy`,
    which assigns its own conversation id — pre-generating one here and
    telling agy to --conversation it would target an id agy has never seen,
    so resume silently no-ops and a *second*, disconnected id gets created.
    stream_headless_cli() handles id assignment itself for that reason.

    model/agent only apply to Mode 3 (agy) -- Modes 1/2 never invoke agy.

    Numbering matches the recovered reference UI's own AVAILABLE_MODES ids
    (1 = fast dashboard, 2 = deep brain, 3 = CLI) -- not the historical
    internal order of the two functions below.
    """
    if stream_mode == 3:
        for ev in stream_headless_cli(prompt, is_mobile=is_mobile, conversation_id=conversation_id, model=model, agent=agent):
            yield ev
    elif stream_mode == 1:
        for ev in stream_fast_dashboard(prompt, is_mobile=is_mobile, conversation_id=conversation_id):
            yield ev
    else:
        for ev in stream_ai_deep_brain(prompt, is_mobile=is_mobile, conversation_id=conversation_id):
            yield ev


def test_headless_cli_execution(prompt: str = "In one sentence, what is a git rebase?") -> dict:
    """Execute test run of agy headless CLI with stream-json format and return full diagnostic report."""
    import shutil
    import subprocess

    agy_bin = shutil.which("agy") or "/usr/local/bin/agy"
    exists = os.path.exists(agy_bin)

    cmd = [
        agy_bin,
        "-p", prompt,
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
    ]

    env = os.environ.copy()
    env["HOME"] = "/root"
    env["USER"] = "root"
    env["PATH"] = f"/root/.local/bin:/usr/local/bin:/usr/bin:/bin:{env.get('PATH', '')}"
    env["PYTHONUNBUFFERED"] = "1"
    env["FORCE_COLOR"] = "0"
    env["TERM"] = "dumb"

    auth_files = []
    for p in ["/root/.gemini", "/root/.config/antigravity", "/config/.gemini", "/config/.config"]:
        if os.path.exists(p):
            try:
                auth_files.append(f"{p}: {os.listdir(p)}")
            except Exception as ex:
                auth_files.append(f"{p}: {ex}")
        else:
            auth_files.append(f"{p}: NOT_FOUND")

    found_files = []
    for search_dir in ["/root", "/config", "/homeassistant", "/data", "/share"]:
        if os.path.exists(search_dir):
            try:
                for root, dirs, files in os.walk(search_dir):
                    if len(found_files) > 50:
                        break
                    for f in files:
                        if any(k in f.lower() for k in ["gemini", "antigravity", "agy", "oauth", "token", "auth", "session"]):
                            found_files.append(os.path.join(root, f))
            except Exception:
                pass

    t0 = time.time()
    result = {
        "agy_bin": agy_bin,
        "exists": exists,
        "auth_dirs": auth_files,
        "all_files": found_files,
        "cmd": cmd,
        "lines": [],
        "stderr": "",
        "returncode": None,
        "elapsed_sec": None,
        "success": False,
    }

    if not exists:
        result["stderr"] = f"Binary not found at {agy_bin}"
        return result

    try:
        ver_proc = subprocess.run([agy_bin, "--version"], capture_output=True, text=True, timeout=3)
        result["agy_version"] = ver_proc.stdout.strip() or ver_proc.stderr.strip()
    except Exception as ex:
        result["agy_version"] = f"Error: {ex}"

    try:
        help_proc = subprocess.run([agy_bin, "--help"], capture_output=True, text=True, timeout=3)
        result["agy_help"] = (help_proc.stdout.strip() or help_proc.stderr.strip())[:6000]
    except Exception as ex:
        result["agy_help"] = f"Error: {ex}"

    try:
        auth_proc = subprocess.run([agy_bin, "auth", "status"], capture_output=True, text=True, timeout=3, env=env)
        result["agy_auth"] = auth_proc.stdout.strip() or auth_proc.stderr.strip()
    except Exception as ex:
        result["agy_auth"] = f"Error: {ex}"

    flag_tests = []
    test_commands = [
        ("echo prompt", ["bash", "-c", "echo 'Say hi in 3 words' | /usr/local/bin/agy --output-format stream-json --dangerously-skip-permissions"]),
        ("print flag", ["/usr/local/bin/agy", "-p", "Say hi in 3 words"]),
        ("stream-json flag", ["/usr/local/bin/agy", "-p", "Say hi in 3 words", "--output-format", "stream-json"]),
        ("disable slash", ["/usr/local/bin/agy", "-p", "Say hi in 3 words", "--output-format", "stream-json", "--disable-slash-commands"]),
    ]

    for label, c in test_commands:
        t_c = time.time()
        try:
            p = subprocess.Popen(
                c,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            try:
                stdout, stderr = p.communicate(input="Say hi in 3 words\n", timeout=2)
                flag_tests.append({
                    "label": label,
                    "ret": p.returncode,
                    "stdout": stdout[:200],
                    "stderr": stderr[:200],
                    "time": round(time.time() - t_c, 2)
                })
            except subprocess.TimeoutExpired:
                p.kill()
                stdout, stderr = p.communicate()
                flag_tests.append({
                    "label": label,
                    "timeout": True,
                    "stdout": stdout[:200],
                    "stderr": stderr[:200],
                    "time": round(time.time() - t_c, 2)
                })
        except Exception as e:
            flag_tests.append({"label": label, "err": str(e)})

    result["flag_tests"] = flag_tests

    # Production-faithful full run: same 'script -q -e -c' pseudo-tty wrapper as
    # stream_headless_cli, but with a generous timeout so we capture the real
    # terminal 'result' event's raw JSON schema (diagnostic only).
    prod_prompt = "In one sentence, what is a git rebase?"
    script_cmd = (
        f"{agy_bin} -p {shlex.quote(prod_prompt)}"
        f" --output-format stream-json"
        f" --dangerously-skip-permissions"
    )
    prod_cmd = ["script", "-q", "-e", "-c", script_cmd, "/dev/null"]
    prod_result = {"cmd": prod_cmd, "lines": [], "elapsed_sec": None}
    t_p = time.time()
    try:
        pp = subprocess.Popen(
            prod_cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            encoding="utf-8",
            env=env,
        )
        collected = []
        deadline = time.time() + 45
        while time.time() < deadline:
            line = pp.stdout.readline()
            if not line:
                if pp.poll() is not None:
                    break
                continue
            l = line.rstrip("\r\n").strip()
            if not l:
                continue
            collected.append(l)
            try:
                d = json.loads(l)
                if d.get("event", d.get("type", "")) == "result":
                    break
            except Exception:
                pass
        try:
            pp.kill()
        except Exception:
            pass
        prod_result["lines"] = collected[-30:]
        prod_result["line_count"] = len(collected)
    except Exception as e:
        prod_result["err"] = str(e)
    prod_result["elapsed_sec"] = round(time.time() - t_p, 2)
    result["production_faithful_run"] = prod_result

    return result

