"""Custom agent discovery for Mode 3 (`agy --agent <name>`).

`agy agents` (the CLI's own listing subcommand) turned out to be a dead end
for this addon: it takes no `--output-format` flag at all (confirmed live --
`agy agents --output-format json` errors with "flags provided but not
defined: -output-format"), and on an install with no custom agents defined
it prints nothing, success or failure look identical from the outside.

Per the official docs (antigravity.google/docs/cli/commands/agents), custom
agents aren't something the CLI enumerates dynamically -- they're plain
Markdown files with YAML frontmatter the user authors themselves, discovered
from two fixed locations:
    {workspace}/.agents/agents/{agent_name}/agent.md   (workspace-specific)
    ~/.gemini/config/agents/{agent_name}/agent.md        (global)
So this module reads those directories directly instead of shelling out to
`agy agents`.
"""

import os
import re

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*", re.DOTALL)
_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")


def _workspace_root() -> str:
    """Mirror run.sh's WORKDIR selection (/homeassistant, falling back to /config)."""
    for p in ["/homeassistant", "/config"]:
        if os.path.isdir(p):
            return p
    return os.path.expanduser("~")


def _agent_search_dirs() -> list:
    """(source_label, base_dir) pairs to scan, workspace first so it can override global."""
    home = os.environ.get("HOME") or os.path.expanduser("~")
    return [
        ("workspace", os.path.join(_workspace_root(), ".agents", "agents")),
        ("global", os.path.join(home, ".gemini", "config", "agents")),
    ]


def _parse_frontmatter(text: str) -> dict:
    """Minimal `key: value` YAML-frontmatter parser -- agent.md only ever uses
    flat scalar fields (name, description), so a full YAML parser is unneeded."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fields = {}
    for line in m.group(1).splitlines():
        kv = _KV_RE.match(line)
        if not kv:
            continue
        key, val = kv.group(1).strip(), kv.group(2).strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        fields[key] = val
    return fields


def list_available_agents() -> list:
    """Discover all custom agents visible to this install, workspace overriding global."""
    agents = {}
    for source, base_dir in _agent_search_dirs():
        if not os.path.isdir(base_dir):
            continue
        try:
            entries = sorted(os.listdir(base_dir))
        except Exception:
            continue
        for agent_id in entries:
            md_path = os.path.join(base_dir, agent_id, "agent.md")
            if not os.path.isfile(md_path):
                continue
            try:
                with open(md_path, "r", encoding="utf-8", errors="ignore") as f:
                    fm = _parse_frontmatter(f.read())
            except Exception:
                fm = {}
            if agent_id in agents and source == "global":
                continue  # workspace copy already claimed this id
            agents[agent_id] = {
                "id": agent_id,
                "name": fm.get("name") or agent_id,
                "description": fm.get("description") or "",
                "source": source,
            }
    return sorted(agents.values(), key=lambda a: a["name"].lower())


def get_valid_agent_ids() -> set:
    """Every agent id this install actually has an agent.md for (--agent's valid values)."""
    return {a["id"] for a in list_available_agents()}
