"""Self-implemented `/codesearch` -- agy has no headless code-search command
(the interactive `/codesearch` is a TUI-only tool), so this is a plain
recursive grep over the workspace instead of an agy call. Triggered from the
composer as a client-side slash command (see sendMessage() in
core/ui/scripts.py), bypassing the SSE chat pipeline entirely.
"""

import os

_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".gemini"}
_MAX_FILE_BYTES = 2_000_000  # skip anything bigger -- almost certainly not source
_MAX_FILES_SCANNED = 5000    # hard ceiling so a huge workspace can't hang the request
_MAX_LINE_LEN = 300          # truncate absurdly long lines (minified files, etc.)


def _workspace_root() -> str:
    for p in ["/homeassistant", "/config"]:
        if os.path.isdir(p):
            return p
    return os.path.expanduser("~")


def _is_probably_binary(chunk: bytes) -> bool:
    return b"\x00" in chunk


def search_workspace(query: str, max_results: int = 30) -> dict:
    """Recursively grep the workspace for `query` (plain substring, case-insensitive).

    Returns {"root": ..., "matches": [{"file", "line", "text"}], "truncated": bool,
    "files_scanned": int}. `file` is relative to the workspace root.
    """
    query = (query or "").strip()
    root = _workspace_root()
    matches = []
    files_scanned = 0
    truncated = False

    if not query:
        return {"root": root, "matches": [], "truncated": False, "files_scanned": 0}

    needle = query.lower()

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for filename in filenames:
            if len(matches) >= max_results:
                truncated = True
                break
            if files_scanned >= _MAX_FILES_SCANNED:
                truncated = True
                break
            full_path = os.path.join(dirpath, filename)
            try:
                if os.path.getsize(full_path) > _MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            files_scanned += 1
            try:
                with open(full_path, "rb") as f:
                    head = f.read(4096)
                    if _is_probably_binary(head):
                        continue
                    f.seek(0)
                    content = f.read().decode("utf-8", errors="ignore")
            except Exception:
                continue

            rel_path = os.path.relpath(full_path, root)
            for line_no, line in enumerate(content.splitlines(), start=1):
                if needle in line.lower():
                    text = line.strip()
                    if len(text) > _MAX_LINE_LEN:
                        text = text[:_MAX_LINE_LEN] + "..."
                    matches.append({"file": rel_path, "line": line_no, "text": text})
                    if len(matches) >= max_results:
                        break
        if truncated:
            break

    return {"root": root, "matches": matches, "truncated": truncated, "files_scanned": files_scanned}
