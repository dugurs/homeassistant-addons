#!/usr/bin/env bash
set -e

echo "[INFO] Starting Web Terminal with persistent tmux session..."

export HOME=/root
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export LANGUAGE=C.UTF-8
export PYTHONIOENCODING=utf-8

# Determine primary workspace (favor /homeassistant if available, fallback to /config)
if [ -d "/homeassistant" ]; then
    WORKDIR="/homeassistant"
else
    WORKDIR="/config"
fi
cd "${WORKDIR}" 2>/dev/null || cd /root

# Ensure persistent directories for Antigravity credentials in addon_config (/config = /addon_configs/antigravity)
mkdir -p /config/.gemini
mkdir -p /config/.config
mkdir -p /config/.local_share
mkdir -p /config/.uv_cache

# Persist uv package cache across addon rebuilds (avoids re-downloading ha-mcp every update)
export UV_CACHE_DIR="/config/.uv_cache"

# Symlink persistent paths to /root so auth survives rebuilds/restarts and is included in addon backups
rm -rf /root/.gemini
ln -sfn /config/.gemini /root/.gemini

mkdir -p /root/.config
rm -rf /root/.config/antigravity
ln -sfn /config/.config /root/.config/antigravity

mkdir -p /root/.local/share
rm -rf /root/.local/share/antigravity
ln -sfn /config/.local_share /root/.local/share/antigravity

# Auto-configure Home Assistant MCP Server (stdio mode for Antigravity CLI)
mkdir -p /root/.gemini/config

# Read SUPERVISOR_TOKEN from multiple sources
if [ -z "$SUPERVISOR_TOKEN" ] && [ -f /var/run/s6/container_environment/SUPERVISOR_TOKEN ]; then
    export SUPERVISOR_TOKEN=$(cat /var/run/s6/container_environment/SUPERVISOR_TOKEN)
fi
if [ -z "$SUPERVISOR_TOKEN" ] && [ -f /proc/1/environ ]; then
    export SUPERVISOR_TOKEN=$(tr '\0' '\n' < /proc/1/environ | grep '^SUPERVISOR_TOKEN=' | cut -d= -f2-)
fi

SSE_URL=""
if [ -f /data/options.json ]; then
    SSE_URL=$(jq -r '.ha_sse_url // empty' /data/options.json 2>/dev/null || true)
fi

if [ -n "$SSE_URL" ] && [ "$SSE_URL" != "null" ]; then
    # User supplied an external SSE/Streamable-HTTP URL (e.g. ha-mcp Custom Component webhook URL)
    echo "[INFO] Using user-supplied HA MCP URL: $SSE_URL"
    cat <<MCP_EOF > /root/.gemini/config/mcp_config.json
{
  "mcpServers": {
    "home-assistant": {
      "serverUrl": "$SSE_URL"
    }
  }
}
MCP_EOF
else
    # Default: stdio transport via uvx ha-mcp@latest
    # Antigravity CLI only supports stdio MCP transport (not SSE/HTTP).
    # uvx launches ha-mcp as a subprocess; env vars allow ha-mcp to reach HA API.
    echo "[INFO] Configuring ha-mcp via stdio (uvx). SUPERVISOR_TOKEN available: $([ -n "$SUPERVISOR_TOKEN" ] && echo yes || echo no)"
    cat <<MCP_EOF > /root/.gemini/config/mcp_config.json
{
  "mcpServers": {
    "home-assistant": {
      "command": "uvx",
      "args": ["ha-mcp@latest"],
      "env": {
        "HOMEASSISTANT_URL": "http://supervisor/core",
        "HOMEASSISTANT_TOKEN": "${SUPERVISOR_TOKEN}"
      }
    }
  }
}
MCP_EOF
fi

# Auto-configure Antigravity CLI settings and permissions for HA MCP
mkdir -p /root/.gemini/antigravity-cli
SETTINGS_FILE="/root/.gemini/antigravity-cli/settings.json"
if [ ! -f "$SETTINGS_FILE" ]; then
    cat << 'SETTINGS_EOF' > "$SETTINGS_FILE"
{
  "permissions": {
    "allow": [
      "mcp(home-assistant/*)"
    ]
  }
}
SETTINGS_EOF
else
    if command -v jq >/dev/null 2>&1; then
        jq '.permissions.allow = ((.permissions.allow // []) + ["mcp(home-assistant/*)"] | unique)' "$SETTINGS_FILE" > "${SETTINGS_FILE}.tmp" 2>/dev/null && mv "${SETTINGS_FILE}.tmp" "$SETTINGS_FILE"
    fi
fi

# Auto-configure global rules for HA MCP
mkdir -p /root/.gemini/config/rules
if [ ! -f /root/.gemini/config/rules/ha-guidelines.md ]; then
    cat << 'RULE_EOF' > /root/.gemini/config/rules/ha-guidelines.md
---
name: ha-guidelines
description: Always prioritize using ha-mcp tools over direct curl API calls when controlling or querying Home Assistant
trigger: always_on
---

# Home Assistant Guidelines

## Tools & Integrations
- Always prioritize using `ha-mcp` tools (`control_activate`, `get_entity_state`, `search_entities`, etc.) when interacting with Home Assistant entities, devices, and states.
- Avoid using direct shell `curl` commands to the Home Assistant REST API unless explicitly requested or when MCP tools are unavailable for the specific task.
RULE_EOF
fi

# Tmux configuration
if [ ! -f /root/.tmux.conf ]; then
    cat << 'TMUX_EOF' > /root/.tmux.conf
set -g default-terminal "xterm-256color"
set -g history-limit 10000
set -q -g status-utf8 on
setw -q -g utf8 on
TMUX_EOF
fi

# Bashrc configuration with HA API and CLI helpers
if ! grep -q "SUPERVISOR_TOKEN" /root/.bashrc 2>/dev/null; then
    cat << 'BASH_EOF' >> /root/.bashrc
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export HASS_SERVER="http://supervisor/core"
export HASS_TOKEN="${SUPERVISOR_TOKEN}"
export PATH="$PATH:/root/.local/bin"
alias ll='ls -la'
alias cdha='cd /homeassistant'
alias cdcfg='cd /config'
alias ha-config-check='hass-cli config check 2>/dev/null || ha core check'
alias ha-logs='ha core logs'
alias agy='/usr/local/bin/agy'
BASH_EOF
fi

# Create smart universal agy wrapper (supports native x86_64, ARM64, and QEMU fallback)
cat << 'WRAPPER_EOF' > /usr/local/bin/agy
#!/usr/bin/env bash
TARGET_BIN="/root/.local/bin/agy"
if [ ! -f "$TARGET_BIN" ]; then
    echo "[ERROR] Antigravity CLI binary not found at $TARGET_BIN"
    exit 1
fi

ARCH=$(uname -m)

if [ "$ARCH" = "x86_64" ] || [ "$ARCH" = "amd64" ]; then
    if ( "$TARGET_BIN" --help >/dev/null 2>&1 ) 2>/dev/null; then
        exec "$TARGET_BIN" "$@"
    else
        if command -v qemu-x86_64-static >/dev/null 2>&1; then
            exec qemu-x86_64-static -cpu max "$TARGET_BIN" "$@"
        elif command -v qemu-x86_64 >/dev/null 2>&1; then
            exec qemu-x86_64 -cpu max "$TARGET_BIN" "$@"
        else
            exec "$TARGET_BIN" "$@"
        fi
    fi
else
    # ARM64 (Raspberry Pi 4/5, Apple Silicon, etc.) or other architectures
    exec "$TARGET_BIN" "$@"
fi
WRAPPER_EOF
chmod +x /usr/local/bin/agy

# Pre-warm uvx cache for ha-mcp BEFORE starting agy (with timeout guard)
# Runs uvx in background + kills after 45s to avoid hanging run.sh
echo "[INFO] ha-mcp 캐시 사전 준비 중 (최대 45초)..."
(timeout 45 uvx ha-mcp@latest < /dev/null > /dev/null 2>&1 || true) &
PREWARM_PID=$!
# Wait up to 45s but exit early if uvx finishes sooner
for i in $(seq 1 45); do
    if ! kill -0 $PREWARM_PID 2>/dev/null; then
        break
    fi
    # Check if ha-mcp package is already in the uv cache
    if find "${UV_CACHE_DIR}" -name "ha_mcp*" -maxdepth 5 2>/dev/null | grep -q .; then
        echo "[INFO] ha-mcp 캐시 준비 완료"
        break
    fi
    sleep 1
done
kill $PREWARM_PID 2>/dev/null || true
wait $PREWARM_PID 2>/dev/null || true

# Start background Antigravity Status API server for Home Assistant Custom Integration (antigravity_cli)
if [ -f /usr/local/bin/antigravity_api.py ]; then
    API_PORT="8000"
    if [ -f /data/options.json ]; then
        API_PORT=$(jq -r '.api_port // 8000' /data/options.json 2>/dev/null || echo "8000")
        if [ "$API_PORT" = "null" ] || [ -z "$API_PORT" ]; then
            API_PORT="8000"
        fi
    fi
    export ANTIGRAVITY_API_PORT="${API_PORT}"
    echo "[INFO] Starting Antigravity Status API server on port ${API_PORT}..."
    python3 /usr/local/bin/antigravity_api.py &
    API_PID=$!
    trap "kill -TERM $API_PID 2>/dev/null || true; exit 0" SIGTERM SIGINT
fi

# Pre-initialize tmux session for web terminal (standby at bash)
if ! tmux -u has-session -t main 2>/dev/null; then
    tmux -u new-session -d -s main -c "${WORKDIR}" bash
fi

# Launch ttyd attached to persistent tmux session (force UTF-8)
exec /usr/local/bin/ttyd \
    -p 7681 \
    -W \
    -t fontSize=15 \
    -t theme='{"background": "#1e1e1e"}' \
    tmux -u new-session -A -s main -c "${WORKDIR}" bash
