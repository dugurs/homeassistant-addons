"""Hooks discovery (`/hooks` in the TUI has no headless equivalent).

Per official docs (antigravity.google/docs/cli/plugins/): "Hooks are defined
inside a plugin's `hooks.json` or configured inside your primary
`settings.json` file." No exact internal schema is documented, so this reads
both sources defensively and reports only top-level key names + how many
entries each holds -- safe against an undocumented shape changing under us.

Sources read:
    /root/.gemini/antigravity-cli/settings.json         (matches run.sh's
        SETTINGS_FILE -- HOME=/root in this container) -- its own top-level
        "hooks" key, if present.
    ~/.gemini/antigravity-cli/plugins/<name>/hooks.json  (per plugin)
"""

import json
import os


def _settings_path() -> str:
    home = os.environ.get("HOME") or os.path.expanduser("~")
    return os.path.join(home, ".gemini", "antigravity-cli", "settings.json")


def _plugins_dir() -> str:
    home = os.environ.get("HOME") or os.path.expanduser("~")
    return os.path.join(home, ".gemini", "antigravity-cli", "plugins")


def _entry_count(value) -> int:
    if isinstance(value, dict):
        return len(value)
    if isinstance(value, list):
        return len(value)
    return 1


def _hooks_from_json_obj(hooks_obj) -> list:
    if not isinstance(hooks_obj, dict):
        return []
    return [{"key": key, "count": _entry_count(value)} for key, value in hooks_obj.items()]


def list_active_hooks() -> list:
    """Best-effort listing of every hooks source this install has -- see module docstring."""
    result = []

    settings_path = _settings_path()
    if os.path.isfile(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8", errors="ignore") as f:
                settings = json.load(f)
            for entry in _hooks_from_json_obj(settings.get("hooks")):
                result.append({"source": "settings.json", **entry})
        except Exception:
            pass

    plugins_dir = _plugins_dir()
    if os.path.isdir(plugins_dir):
        try:
            plugin_names = sorted(os.listdir(plugins_dir))
        except Exception:
            plugin_names = []
        for plugin_name in plugin_names:
            hooks_json_path = os.path.join(plugins_dir, plugin_name, "hooks.json")
            if not os.path.isfile(hooks_json_path):
                continue
            try:
                with open(hooks_json_path, "r", encoding="utf-8", errors="ignore") as f:
                    plugin_hooks = json.load(f)
                for entry in _hooks_from_json_obj(plugin_hooks):
                    result.append({"source": f"plugin:{plugin_name}", **entry})
            except Exception:
                pass

    return result
