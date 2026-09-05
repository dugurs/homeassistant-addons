"""Music Assistant integration -- recent-playlist lookup for the "OO에 음악/
노래 틀어줘" natural-language command.

A bare "음악 틀어줘" names no specific song/artist/playlist, so there is
nothing for a plain HA service call to act on -- unlike "OO 등 켜" there is
no single obvious target. Rather than guessing (or just asking the question
back in plain text), when the resolved speaker has a Music-Assistant-managed
sibling entity (see core/ha_registry.py's find_music_assistant_sibling()),
this offers the user's own recently-played playlists as a clickable pick
list (see core/ha_client.py's _h_media() and core/ui/scripts.py's
setPlaylistCard()).

Two Music Assistant services are involved:
- `music_assistant.get_library` (media_type="playlist") -- lists the
  library, used here for the recent-playlists pick list. Requires a
  `config_entry_id`, which HA's REST API has no endpoint for (config entries
  are WebSocket/admin-API only) -- fetched once via the same Supervisor
  Core-WebSocket proxy core/ha_registry.py uses, and cached the same way.
- `music_assistant.play_media` (called directly from the frontend via the
  existing /api/device/control endpoint once the user clicks a playlist --
  see ALLOWED_CARD_SERVICES in core/ha_client.py) -- actually starts
  playback. Must target the Music-Assistant-owned entity specifically:
  confirmed live that calling it on the native Cast entity (e.g.
  media_player.bed_speaker) is silently accepted over REST but never
  actually starts anything, since that entity doesn't belong to the
  music_assistant integration at all -- see find_music_assistant_sibling().
"""

import json
import threading
import time
import urllib.request

from core.system_info import get_supervisor_token

_CACHE_TTL_SECONDS = 60
_cache_lock = threading.Lock()
_cache_entry_id: str | None = None
_cache_checked = False
_cache_timestamp = 0.0


def _fetch_config_entry_id() -> str | None:
    """One-shot WebSocket round-trip: authenticate, ask for the
    music_assistant integration's config entry, return its entry_id (or
    None if the add-on/integration isn't set up at all). Mirrors
    core/ha_registry.py's _fetch_hidden_entity_ids() connection dance."""
    import websocket  # websocket-client; may not be installed, see Dockerfile

    token = get_supervisor_token()
    if not token:
        return None

    ws = websocket.create_connection("ws://supervisor/core/websocket", timeout=5)
    try:
        greeting = json.loads(ws.recv())
        if greeting.get("type") != "auth_required":
            return None

        ws.send(json.dumps({"type": "auth", "access_token": token}))
        auth_result = json.loads(ws.recv())
        if auth_result.get("type") != "auth_ok":
            return None

        ws.send(json.dumps({"id": 1, "type": "config_entries/get", "domain": "music_assistant"}))
        result = json.loads(ws.recv())
        if not result.get("success"):
            return None

        entries = result.get("result") or []
        return entries[0]["entry_id"] if entries else None
    finally:
        try:
            ws.close()
        except Exception:
            pass


def get_config_entry_id() -> str | None:
    """Cached Music Assistant config_entry_id, or None when the add-on
    isn't installed/configured. Best-effort like ha_registry.get_hidden_
    entity_ids() -- any failure (websocket-client missing, HA unreachable,
    integration not set up) just means "treat as unavailable", never an
    exception the caller has to handle."""
    global _cache_entry_id, _cache_checked, _cache_timestamp
    with _cache_lock:
        now = time.time()
        if _cache_checked and (now - _cache_timestamp) < _CACHE_TTL_SECONDS:
            return _cache_entry_id
        try:
            fresh = _fetch_config_entry_id()
        except Exception:
            fresh = None
        _cache_entry_id = fresh
        _cache_checked = True
        _cache_timestamp = now
        return fresh


def get_recent_playlists(limit: int = 9) -> list:
    """Up to `limit` playlists from the user's Music Assistant library,
    most-recently-played first. Empty list (never raises) when Music
    Assistant isn't available or the request fails for any reason."""
    entry_id = get_config_entry_id()
    if not entry_id:
        return []
    token = get_supervisor_token()
    if not token:
        return []

    url = "http://supervisor/core/api/services/music_assistant/get_library?return_response"
    payload = json.dumps({
        "config_entry_id": entry_id,
        "media_type": "playlist",
        "order_by": "last_played_desc",
        # A bare top-level "limit" -- confirmed against the official docs'
        # own get_library example (music-assistant.io's Get Library Action
        # page). An earlier nested {"pagination": {"limit": N}} guess was
        # rejected outright (400) since that key doesn't exist on this
        # service at all.
        "limit": limit,
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status not in (200, 201):
                return []
            body = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    items = (body.get("service_response") or {}).get("items") or []
    return [
        {"uri": it.get("uri"), "name": it.get("name"), "image": it.get("image")}
        for it in items[:limit]
        if it.get("uri") and it.get("name")
    ]
