# Home Assistant Workspace Rules

- **MCP Tools Execution**: When working in this workspace, Home Assistant MCP tools (home-assistant server) should be executed directly without requiring step-by-step confirmation, as requested by the user.
- **Python Commands, File Sync & Local Gitea Auto-Approval**: All file synchronization (`python -c ...`, `python sync_files.py`), file copies to Samba shares (`\\HOMEASSISTANT\config\...`, `\\HOMEASSISTANT\local_apps\...`), add-on rebuilds, Core restarts, and local Gitea (192.168.0.26:3000) git commits/pushes are strictly pre-approved and must be executed immediately without asking for repetitive confirmation.
- **Best Practices**: Follow standard Home Assistant best practices (home-assistant-best-practices resource guidelines), prioritizing entity_id over device_id and leveraging native helpers and automations.
