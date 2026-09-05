"""Home Assistant entity/device-registry access via the Supervisor-proxied
Core WebSocket API.

REST (/api/states, what core/ha_client.py's get_ha_states() uses for
everything else) only carries runtime state/attributes -- registry-level
metadata (which entity/device belongs to which area, which integration
created it, whether the user hid it) has never been exposed over HA's REST
API, only over its WebSocket API. This module does those queries once per
cache window and reuses the result, since a fresh WebSocket round-trip on
every single control command would undercut the fast dispatcher's whole
"0.05s" premise for the common case where none of this is even needed.

Two unrelated features currently need registry data, so both are folded
into one cached snapshot fetched over one WebSocket connection rather than
two separate ones:

- `hidden_by` (whether the user hid an entity from their dashboard). Added
  after a 2026-09-05 incident: a room-wide command's candidate list
  silently included a "거실 플러그" (living room outlet) the user had
  deliberately hidden in HA because it powers their household server --
  turning it off knocked the server, and therefore HA itself, offline. See
  core/ha_client.py's resolve_control_scope() for how the hidden set
  returned here is actually used.
- Area-based Music Assistant player lookup (see find_music_assistant_sibling()
  below), for the "OO에 음악 틀어줘" playlist-pick-list feature (see
  core/music_assistant.py / core/ha_client.py's _h_media()).
"""

import json
import threading
import time

from core.system_info import get_supervisor_token

_CACHE_TTL_SECONDS = 60
_cache_lock = threading.Lock()
_cache_snapshot: dict | None = None
_cache_timestamp = 0.0

_EMPTY_SNAPSHOT = {"hidden_ids": set(), "entity_area": {}, "entity_model": {}, "ma_players": []}


def _fetch_registry_snapshot() -> dict:
    """One WebSocket round-trip: authenticate, pull the full entity AND
    device registries, and reduce them to just what callers in this add-on
    need:

    - hidden_ids: entity_ids with hidden_by set
    - entity_area: entity_id -> area_id (falling back to the entity's
      device's area_id when the entity itself has no direct override --
      same precedence HA's own UI uses)
    - entity_model: entity_id -> the entity's device's `model` string (see
      find_music_assistant_sibling()'s use of this below)
    - ma_players: [{entity_id, area_id, model}] for every media_player.*
      entity whose registry `platform` is "music_assistant" -- Music
      Assistant creates its OWN separate media_player entity per configured
      player (e.g. media_player.ma_bed_speaker) rather than reusing the
      underlying Cast/other integration's entity (media_player.bed_speaker);
      the two share nothing but an area, confirmed live -- calling
      music_assistant.play_media on the native Cast entity is silently
      accepted by the REST layer but never actually starts playback since
      that entity doesn't belong to the music_assistant integration at all.

    Raises on any failure -- caller decides the fallback.
    """
    import websocket  # websocket-client; may not be installed, see Dockerfile

    token = get_supervisor_token()
    if not token:
        return dict(_EMPTY_SNAPSHOT)

    ws = websocket.create_connection("ws://supervisor/core/websocket", timeout=5)
    try:
        greeting = json.loads(ws.recv())
        if greeting.get("type") != "auth_required":
            return dict(_EMPTY_SNAPSHOT)

        ws.send(json.dumps({"type": "auth", "access_token": token}))
        auth_result = json.loads(ws.recv())
        if auth_result.get("type") != "auth_ok":
            return dict(_EMPTY_SNAPSHOT)

        ws.send(json.dumps({"id": 1, "type": "config/entity_registry/list"}))
        entity_result = json.loads(ws.recv())
        ws.send(json.dumps({"id": 2, "type": "config/device_registry/list"}))
        device_result = json.loads(ws.recv())
        if not entity_result.get("success") or not device_result.get("success"):
            return dict(_EMPTY_SNAPSHOT)

        device_area = {d["id"]: d.get("area_id") for d in device_result.get("result", [])}
        device_model = {d["id"]: d.get("model") for d in device_result.get("result", [])}
        entities = entity_result.get("result", [])

        hidden_ids = {e["entity_id"] for e in entities if e.get("hidden_by")}
        entity_area = {}
        entity_model = {}
        ma_players = []
        for e in entities:
            eid = e.get("entity_id")
            if not eid:
                continue
            device_id = e.get("device_id")
            area = e.get("area_id") or device_area.get(device_id)
            model = device_model.get(device_id)
            entity_area[eid] = area
            entity_model[eid] = model
            if e.get("platform") == "music_assistant" and eid.startswith("media_player."):
                ma_players.append({"entity_id": eid, "area_id": area, "model": model})

        return {
            "hidden_ids": hidden_ids,
            "entity_area": entity_area,
            "entity_model": entity_model,
            "ma_players": ma_players,
        }
    finally:
        try:
            ws.close()
        except Exception:
            pass


def _get_snapshot() -> dict:
    """Cached registry snapshot (see _fetch_registry_snapshot()).

    Best-effort: any failure (websocket-client not installed, HA
    unreachable, auth failure, ...) returns an empty snapshot (or the last
    good cached value, if any) rather than raising -- every feature built on
    this degrades to a no-op instead of breaking device control entirely.
    """
    global _cache_snapshot, _cache_timestamp
    with _cache_lock:
        now = time.time()
        if _cache_snapshot is not None and (now - _cache_timestamp) < _CACHE_TTL_SECONDS:
            return _cache_snapshot
        try:
            fresh = _fetch_registry_snapshot()
        except Exception:
            fresh = _cache_snapshot if _cache_snapshot is not None else dict(_EMPTY_SNAPSHOT)
        _cache_snapshot = fresh
        _cache_timestamp = now
        return fresh


def get_hidden_entity_ids() -> set:
    """Cached set of entity_ids currently hidden in the HA entity registry."""
    return _get_snapshot().get("hidden_ids", set())


def get_all_music_assistant_players() -> list:
    """Every media_player.* entity whose registry `platform` is
    "music_assistant" -- i.e. every player Music Assistant itself actually
    knows about (see music-assistant.io's Player Providers docs: MA's own
    native player entity is the officially recommended target over a
    device's native HA integration entity whenever both exist).

    Used for the "OO에 음악 틀어줘" pick-list's speaker selector (see
    core/ha_client.py's _h_media()) -- lets the user redirect playback to
    ANY Music-Assistant-known player, not just the one auto-resolved from
    the room named in the command. Each item is {entity_id, area_id, model}
    (see _fetch_registry_snapshot()); the caller cross-references
    entity_id against a fresh states list for a human-readable name, since
    the registry itself doesn't carry the live friendly_name.
    """
    return list(_get_snapshot().get("ma_players") or [])


def find_music_assistant_sibling(entity_id: str) -> str | None:
    """Given a "normal" media_player entity_id (e.g. media_player.bed_speaker,
    a native Cast entity), return the entity_id of the Music-Assistant-owned
    player for the SAME physical speaker (e.g. media_player.ma_bed_speaker),
    or None when there isn't one (Music Assistant not installed, this
    particular speaker was never added to it, or -- see below -- more than
    one MA player shares the room and neither device model narrows it down).

    Matched by shared area first -- MA's own player entities are named after
    however the user labeled them when adding to MA (not derived from the
    underlying entity's name at all, confirmed live: "거실 스피커"'s MA
    twin is literally named "ma living speaker"), so area is the only
    reliable link between the two. But a room commonly has several MA
    players (a Nest Hub, a Chromecast Audio, a Cast group, a Google Home
    Mini, ...), confirmed live for "안방": area alone picked "ma bed
    nesthub" over the actually-wanted "ma bed speaker" purely by WebSocket
    response order. Device `model` (e.g. "Chromecast Audio") is identical
    between an entity and its MA twin even though the name isn't, so it's
    used to disambiguate -- and if it still can't (model missing/shared),
    this deliberately gives up rather than guessing the wrong physical
    speaker, same "ask/fall back instead of guess" rule this add-on applies
    everywhere else a room has more than one candidate device.
    """
    snapshot = _get_snapshot()
    ma_players = snapshot.get("ma_players") or []
    if not ma_players:
        return None
    area = snapshot.get("entity_area", {}).get(entity_id)
    if not area:
        return None
    area_matches = [p for p in ma_players if p.get("area_id") == area]
    if not area_matches:
        return None
    if len(area_matches) == 1:
        return area_matches[0].get("entity_id")

    model = snapshot.get("entity_model", {}).get(entity_id)
    if model:
        model_matches = [p for p in area_matches if p.get("model") == model]
        if len(model_matches) == 1:
            return model_matches[0].get("entity_id")
    return None
