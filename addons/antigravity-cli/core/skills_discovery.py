"""Agent Skills discovery (`/skills` in the TUI has no headless equivalent).

The public docs (antigravity.google/docs/cli/plugins/) describe skills as
flat `{skill}.md` files, but that's stale: the actual shipped product (see
its own bundled `agy-customizations` skill, docs/skills.md) uses a
directory-per-skill layout, same as Claude's Agent Skills convention:
    {workspace}/.agents/skills/{skill}/SKILL.md   (workspace-specific)
    ~/.gemini/config/skills/{skill}/SKILL.md      (global)
Confirmed against a real local install: real global skills live under
~/.gemini/config/skills/<name>/SKILL.md, not the old
~/.gemini/antigravity-cli/skills/ path this module used to scan (that path
is actually where antigravity-cli/settings.json lives, not skills).
Each skill directory may also hold scripts/, examples/, resources/,
references/ -- this module only reads SKILL.md's frontmatter for the list;
the agent itself reads the rest on demand (progressive disclosure).
"""

import os
import re

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*", re.DOTALL)
_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")
_BLOCK_SCALAR_RE = re.compile(r"^[|>][+-]?\s*$")


def _workspace_root() -> str:
    for p in ["/homeassistant", "/config"]:
        if os.path.isdir(p):
            return p
    return os.path.expanduser("~")


def _skill_search_dirs() -> list:
    home = os.environ.get("HOME") or os.path.expanduser("~")
    return [
        ("workspace", os.path.join(_workspace_root(), ".agents", "skills")),
        ("global", os.path.join(home, ".gemini", "config", "skills")),
    ]


def _parse_frontmatter(text: str) -> dict:
    """`key: value` YAML-frontmatter parser, plus block scalars (`>`/`|`) --
    unlike agent.md (see agent_discovery.py), real-world SKILL.md files
    routinely write `description` as a folded/literal block so the trigger
    conditions read as a short paragraph or bullet list (confirmed both in
    antigravity's own bundled skills.md example and in the actual
    homeassistant-ai/skills SKILL.md this module now has to parse) -- a
    single-line-only reader would silently truncate description to just
    the `>` marker itself, which is exactly what happened before this fix."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fields = {}
    lines = m.group(1).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        kv = _KV_RE.match(line)
        if not kv:
            continue
        key, val = kv.group(1).strip(), kv.group(2).strip()
        if _BLOCK_SCALAR_RE.match(val):
            folded = val.startswith(">")
            block = []
            while i < len(lines) and (not lines[i].strip() or lines[i][:1] in (" ", "\t")):
                block.append(lines[i].strip())
                i += 1
            if folded:
                paragraphs, current = [], []
                for l in block:
                    if l:
                        current.append(l)
                    elif current:
                        paragraphs.append(" ".join(current))
                        current = []
                if current:
                    paragraphs.append(" ".join(current))
                val = "\n\n".join(paragraphs)
            else:
                val = "\n".join(block).strip("\n")
        elif len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        fields[key] = val
    return fields


def list_available_skills() -> list:
    """Discover all skills visible to this install, workspace overriding global."""
    skills = {}
    for source, base_dir in _skill_search_dirs():
        if not os.path.isdir(base_dir):
            continue
        try:
            entries = sorted(os.listdir(base_dir))
        except Exception:
            continue
        for skill_id in entries:
            md_path = os.path.join(base_dir, skill_id, "SKILL.md")
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
