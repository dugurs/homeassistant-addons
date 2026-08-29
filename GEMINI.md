# Home Assistant Workspace Rules

- **MCP Tools Execution**: When working in this workspace, Home Assistant MCP tools (home-assistant server) should be executed directly without requiring step-by-step confirmation, as requested by the user.
- **Git Operations & File Sync Auto-Approval**: All Git operations (`git init`, `add`, `commit`, `push`, `branch`, `remote`), file synchronization (`python sync_files.py`), Samba file copies (`\\HOMEASSISTANT\config\...`, `\\HOMEASSISTANT\local_apps\...`), add-on rebuilds, and Core restarts are strictly pre-approved and must be executed immediately without asking for repetitive confirmation.
- **Strict Pre-Approval Gate for Code Changes**: Any source code modification, feature addition, or bug fix plan must ALWAYS be reported with (1) Root Cause and (2) Action Plan and receive explicit user approval BEFORE implementation.
- **Best Practices**: Follow standard Home Assistant best practices (home-assistant-best-practices resource guidelines), prioritizing entity_id over device_id and leveraging native helpers and automations.
