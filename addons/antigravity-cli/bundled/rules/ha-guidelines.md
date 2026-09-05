---
name: ha-guidelines
description: Always prioritize using ha-mcp tools over direct curl API calls when controlling or querying Home Assistant
trigger: always_on
---

# Home Assistant Guidelines

## Tools & Integrations
- Always prioritize using `ha-mcp` tools (`control_activate`, `get_entity_state`, `search_entities`, etc.) when interacting with Home Assistant entities, devices, and states.
- Avoid using direct shell `curl` commands to the Home Assistant REST API unless explicitly requested or when MCP tools are unavailable for the specific task.
