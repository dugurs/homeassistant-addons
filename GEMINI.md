# Home Assistant Workspace Rules

- **MCP Tools Execution**: When working in this workspace, Home Assistant MCP tools (home-assistant server) should be executed directly without requiring step-by-step confirmation, as requested by the user.
- **Git Operations & File Sync Auto-Approval**: All Git operations (`git init`, `add`, `commit`, `push`, `branch`, `remote`), file synchronization (`python sync_files.py`), Samba file copies (`\\HOMEASSISTANT\config\...`, `\\HOMEASSISTANT\local_apps\...`), add-on rebuilds, and Core restarts are strictly pre-approved and must be executed immediately without asking for repetitive confirmation.
- **Flexible Pre-Approval Gate for Major Decisions**: Large-scale architectural changes, breaking changes, or major design decisions require prior root cause & action plan reporting with explicit user approval. Routine bug fixes, path/parameter adjustments, validation, and testing are pre-approved to proceed autonomously with prompt reporting.
- **Zero-Popup Command Execution Rule**: Strictly avoid running inline commands like `python -c "..."`. Always use the categorized Python task scripts:
  - `python sync_files.py` : Samba file synchronization + Local Gitea git push
  - `python check_status.py` : Add-on health, RAM, CPU & port status check
  - `python test_chat_api.py` : Chat API & real-time SSE streaming verification
  - `python check_ha_logs.py` : System error log diagnosis
  - `python runner.py` : General ad-hoc testing & custom logic execution
- **Best Practices**: Follow standard Home Assistant best practices (home-assistant-best-practices resource guidelines), prioritizing entity_id over device_id and leveraging native helpers and automations.
