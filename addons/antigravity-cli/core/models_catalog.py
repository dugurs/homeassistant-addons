"""Antigravity model catalog -- static fallback only, used when `agy models`
can't be queried live (see core/model_discovery.py, the source of truth).

This is a snapshot of a real `agy models` response (2026-09), not a guess
from documentation -- an earlier docs-sourced version of this catalog used
wrong slugs (dashes instead of dots: "gemini-3-7-flash" vs the real
"gemini-3.7-flash") and wrongly assumed a separate `--effort` flag existed;
in reality effort is baked into the slug itself (gemini-3.7-flash-high vs
-medium vs -low are three distinct slugs), which is why `variant_slugs`
below maps each effort to its real, directly-invocable slug. There is no
`gemini-3.5-flash` on this account at all.

The quota UI groups models into the same two pools the CLI's `/usage` panel
reports against: Gemini models share one pool, Claude+GPT-OSS share the other.
"""

MODEL_CATALOG = [
    {"slug": "gemini-3.7-flash", "label": "Gemini 3.7 Flash", "family": "gemini", "badge": "Fast",
     "efforts": ["low", "medium", "high"], "default_effort": "high",
     "variant_slugs": {"high": "gemini-3.7-flash-high", "medium": "gemini-3.7-flash-medium", "low": "gemini-3.7-flash-low"}},
    {"slug": "gemini-3.6-flash", "label": "Gemini 3.6 Flash", "family": "gemini", "badge": "Fast",
     "efforts": ["low", "medium", "high"], "default_effort": "high",
     "variant_slugs": {"high": "gemini-3.6-flash-high", "medium": "gemini-3.6-flash-medium", "low": "gemini-3.6-flash-low"}},
    {"slug": "gemini-3.1-pro", "label": "Gemini 3.1 Pro", "family": "gemini", "badge": "Pro",
     "efforts": ["low", "high"], "default_effort": "high",
     "variant_slugs": {"high": "gemini-3.1-pro-high", "low": "gemini-3.1-pro-low"}},
    {"slug": "claude-sonnet-4-6", "label": "Claude Sonnet 4.6 (Thinking)", "family": "claude_gpt", "badge": "Claude",
     "efforts": [], "default_effort": "", "variant_slugs": {"": "claude-sonnet-4-6"}},
    {"slug": "claude-opus-4-6-thinking", "label": "Claude Opus 4.6 (Thinking)", "family": "claude_gpt", "badge": "Opus",
     "efforts": [], "default_effort": "", "variant_slugs": {"": "claude-opus-4-6-thinking"}},
    {"slug": "gpt-oss-120b", "label": "GPT-OSS 120B", "family": "claude_gpt", "badge": "OSS",
     "efforts": ["medium"], "default_effort": "medium", "variant_slugs": {"medium": "gpt-oss-120b-medium"}},
]

FAMILY_LABELS = {
    "gemini": "Gemini Models",
    "claude_gpt": "Claude and GPT models",
}

DEFAULT_MODEL_SLUG = "gemini-3.7-flash"
