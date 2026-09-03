"""File attachment storage for Mode 3 (CLI 추론 모드) chat uploads.

Verified live (2026-09) that agy's own built-in `view_file` tool genuinely
reads and visually understands image files referenced by absolute path in a
headless `-p` prompt -- no special protocol needed, no direct multimodal API
bypass required. So the whole feature is just: save the uploaded bytes
somewhere agy's container filesystem can see, hand back the absolute path,
and let the chat prompt reference it. Modes 1/2 never invoke agy, so this
storage (and the picker wiring in core/streamer.py's caller) is Mode-3-only.
"""

import base64
import os
import re
import sys
import uuid

from core.session_manager import get_brain_base_dir

MAX_FILE_BYTES = 15 * 1024 * 1024  # 15MB per file
MAX_FILES_PER_BATCH = 6

# No server-side extension whitelist -- that turned out to be an unreliable
# gate (real devices hand the browser filenames/MIME types that don't match
# cleanly, e.g. extensionless UUID names from some camera/file-picker flows,
# which kept rejecting genuinely fine files even after trying to recover the
# extension from the MIME type). The file picker's `accept` attribute (see
# core/ui/templates.py) is now the only filter, client-side; whatever makes
# it through gets saved as-is.
_UNSAFE_CHARS_RE = re.compile(r"[^A-Za-z0-9._-]+")
_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def uploads_root() -> str:
    return os.path.join(get_brain_base_dir(), "_uploads")


def resolve_upload_path(batch: str, filename: str) -> str | None:
    """Path-safety-checked lookup for GET /api/uploads/<batch>/<filename>.

    batch/filename ultimately come from the request path, so both must be
    bare tokens (no path separators or traversal) and the resolved file must
    actually live under uploads_root() -- returns None otherwise."""
    if not batch or not filename or not _SAFE_TOKEN_RE.match(batch) or not _SAFE_TOKEN_RE.match(filename):
        return None
    root = os.path.realpath(uploads_root())
    candidate = os.path.realpath(os.path.join(root, batch, filename))
    if os.path.commonpath([root, candidate]) != root or not os.path.isfile(candidate):
        return None
    return candidate


def _sanitize_filename(name: str) -> str:
    """Strip any directory components and unsafe characters -- name is
    client-supplied and gets joined directly into a filesystem path."""
    base = os.path.basename((name or "").strip()) or "file"
    base = _UNSAFE_CHARS_RE.sub("_", base)[-120:]
    return base or "file"


def save_uploaded_files(files: list) -> list:
    """Save up to MAX_FILES_PER_BATCH {filename, data (base64)} entries into a
    fresh per-batch directory. Returns one result dict per input entry, in
    order, each either {"filename", "path"} or {"filename", "error"}."""
    if not isinstance(files, list):
        return []

    batch_id = uuid.uuid4().hex
    batch_dir = os.path.join(uploads_root(), batch_id)
    results = []
    for entry in files[:MAX_FILES_PER_BATCH]:
        if not isinstance(entry, dict):
            continue
        raw_filename = str(entry.get("filename", ""))
        content_type = str(entry.get("content_type", ""))
        filename = _sanitize_filename(raw_filename)
        data_len = len(str(entry.get("data", "")))
        print(f"[Upload] received filename={raw_filename!r} sanitized={filename!r} content_type={content_type!r} b64_len={data_len}", file=sys.stderr)

        data_b64 = entry.get("data", "")
        try:
            # validate=False (the default): tolerate stray whitespace/newlines
            # some browsers/base64 paths introduce, instead of hard-failing on
            # anything not in the strict alphabet -- the size/emptiness checks
            # below still catch genuinely broken input.
            raw = base64.b64decode(str(data_b64), validate=False)
        except Exception as e:
            print(f"[Upload] rejected {filename!r}: base64 decode failed: {e}", file=sys.stderr)
            results.append({"filename": filename, "error": "잘못된 파일 데이터입니다."})
            continue
        if not raw:
            print(f"[Upload] rejected {filename!r}: decoded to 0 bytes", file=sys.stderr)
            results.append({"filename": filename, "error": "빈 파일입니다."})
            continue
        if len(raw) > MAX_FILE_BYTES:
            print(f"[Upload] rejected {filename!r}: {len(raw)} bytes > {MAX_FILE_BYTES}", file=sys.stderr)
            results.append({"filename": filename, "error": f"파일이 너무 큽니다(최대 {MAX_FILE_BYTES // (1024*1024)}MB)."})
            continue
        try:
            os.makedirs(batch_dir, exist_ok=True)
            dest = os.path.join(batch_dir, filename)
            with open(dest, "wb") as f:
                f.write(raw)
            print(f"[Upload] saved {dest!r} ({len(raw)} bytes)", file=sys.stderr)
            results.append({
                "filename": filename,
                "path": dest,
                "url": f"api/uploads/{batch_id}/{filename}",
            })
        except Exception as e:
            print(f"[Upload] rejected {filename!r}: write failed: {e}", file=sys.stderr)
            results.append({"filename": filename, "error": str(e)})

    if len(files) > MAX_FILES_PER_BATCH:
        for entry in files[MAX_FILES_PER_BATCH:]:
            filename = _sanitize_filename(str(entry.get("filename", ""))) if isinstance(entry, dict) else "file"
            results.append({"filename": filename, "error": f"한 번에 최대 {MAX_FILES_PER_BATCH}개까지만 첨부할 수 있습니다."})

    return results
