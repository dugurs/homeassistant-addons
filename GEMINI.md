# Home Assistant Workspace Rules

- **MCP Tools Execution**: When working in this workspace, Home Assistant MCP tools (home-assistant server) should be executed directly without requiring step-by-step confirmation, as requested by the user.
- **Mandatory Pre-Modification Briefing & Approval Gate**: Before modifying any code, API, UI, or configuration, the assistant MUST first report (1) Root Cause Analysis, and (2) Proposed Improvement Direction / Action Plan, and await explicit user approval before executing the changes.
- **Zero-Popup Command Execution Rule**: Strictly avoid running inline commands like `python -c "..."`. Always use the categorized Python task scripts:
  - `python sync_files.py` : Samba file synchronization + Local Gitea git push
  - `python check_status.py` : Add-on health, RAM, CPU & port status check
  - `python test_chat_api.py` : Chat API & real-time SSE streaming verification
  - `python check_ha_logs.py` : System error log diagnosis
  - `python runner.py` : General ad-hoc testing & custom logic execution
- **Best Practices**: Follow standard Home Assistant best practices (home-assistant-best-practices resource guidelines), prioritizing entity_id over device_id and leveraging native helpers and automations.
