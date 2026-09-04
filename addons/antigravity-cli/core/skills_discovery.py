"""Agent Skills discovery (`/skills` in the TUI has no headless equivalent).

Per official docs (antigravity.google/docs/cli/plugins/), skills are plain
markdown files with YAML frontmatter, discovered from two fixed locations:
    {workspace}/.agents/skills/{skill}.md   (workspace-specific)
    ~/.gemini/antigravity-cli/skills/{skill}.md   (global)
Flat files (unlike agents, which use a per-agent subdirectory) -- this module
otherwise mirrors core/agent_discovery.py's frontmatter-scan approach.
"""

import os
import re

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*", re.DOTALL)
_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")


def _workspace_root() -> str:
    for p in ["/homeassistant", "/config"]:
        if os.path.isdir(p):
            return p
    return os.path.expanduser("~")


def _skill_search_dirs() -> list:
    home = os.environ.get("HOME") or os.path.expanduser("~")
    return [
        ("workspace", os.path.join(_workspace_root(), ".agents", "skills")),
        ("global", os.path.join(home, ".gemini", "antigravity-cli", "skills")),
    ]


def _parse_frontmatter(text: str) -> dict:
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


def list_available_skills() -> list:
    """Discover all markdown skills visible to this install, workspace overriding global."""
    skills = {}
    for source, base_dir in _skill_search_dirs():
        if not os.path.isdir(base_dir):
            continue
        try:
            entries = sorted(os.listdir(base_dir))
        except Exception:
            continue
        for filename in entries:
            if not filename.endswith(".md"):
                continue
            skill_id = filename[:-3]
            md_path = os.path.join(base_dir, filename)
            if not os.path.isfile(md_path):
                continue
            try:
                with open(md_path, "r", encoding="utf-8", errors="ignore") as f:
                    fm = _parse_frontmatter(f.read())
            except Exception:
                fm = {}
            if skill_id in skills and source == "global":
                continue  # workspace copy already claimed this id
            skills[skill_id] = {
                "id": skill_id,
                "name": fm.get("name") or skill_id,
                "description": fm.get("description") or "",
                "source": source,
            }
    return sorted(skills.values(), key=lambda s: s["name"].lower())
