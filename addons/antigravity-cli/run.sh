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

# Symlink persistent paths to /root so auth survives rebuilds/restarts and is included in addon backups
rm -rf /root/.gemini
ln -sfn /config/.gemini /root/.gemini

mkdir -p /root/.config
rm -rf /root/.config/antigravity
ln -sfn /config/.config /root/.config/antigravity

mkdir -p /root/.local/share
rm -rf /root/.local/share/antigravity
ln -sfn /config/.local_share /root/.local/share/antigravity

# Auto-configure official Home Assistant MCP Server
mkdir -p /root/.gemini/config

SSE_URL=""
if [ -f /data/options.json ]; then
    SSE_URL=$(jq -r '.ha_sse_url // empty' /data/options.json 2>/dev/null || true)
fi

if [ -n "$SSE_URL" ] && [ "$SSE_URL" != "null" ]; then
    cat << MCP_EOF > /root/.gemini/config/mcp_config.json
{
  "mcpServers": {
    "home-assistant": {
      "serverUrl": "$SSE_URL"
    }
  }
}
MCP_EOF
else
    # Fallback to Node.js HTTP (SSE) server! This bypasses the stdio limitations!
    
    export HASS_HOST="http://supervisor/core"
    export JWT_SECRET="dummy-jwt-secret-for-stdio-transport-needs-32-chars-minimum"
    if [ -z "$SUPERVISOR_TOKEN" ] && [ -f /var/run/s6/container_environment/SUPERVISOR_TOKEN ]; then
        export SUPERVISOR_TOKEN=$(cat /var/run/s6/container_environment/SUPERVISOR_TOKEN)
    fi
    if [ -z "$SUPERVISOR_TOKEN" ] && [ -f /proc/1/environ ]; then
        export SUPERVISOR_TOKEN=$(tr '\0' '\n' < /proc/1/environ | grep '^SUPERVISOR_TOKEN=' | cut -d= -f2-)
    fi
    export HASS_TOKEN="${SUPERVISOR_TOKEN}"
    
    # Find the global HTTP server script
    HTTP_SERVER_SCRIPT="/usr/lib/node_modules/@jango-blockchained/homeassistant-mcp/dist/http-server.mjs"
    if [ ! -f "$HTTP_SERVER_SCRIPT" ]; then
        # Fallback to standard npm global path
        HTTP_SERVER_SCRIPT="/usr/local/lib/node_modules/@jango-blockchained/homeassistant-mcp/dist/http-server.mjs"
    fi
    
    # Run the HTTP server in the background
    if [ -f "$HTTP_SERVER_SCRIPT" ]; then
        echo "Starting Home Assistant MCP HTTP Server on port 7123..."
        node "$HTTP_SERVER_SCRIPT" > /config/mcp-server.log 2>&1 &
    else
        echo "[ERROR] Could not find HTTP server script for homeassistant-mcp"
    fi
    
    cat << MCP_EOF > /root/.gemini/config/mcp_config.json
{
  "mcpServers": {
    "home-assistant": {
      "serverUrl": "http://localhost:7123/mcp"
    }
  }
}
MCP_EOF
fi

# Auto-configure global rules for HA MCP
mkdir -p /root/.gemini/config/rules
if [ ! -f /root/.gemini/config/rules/ha-guidelines.md ]; then
    cat << 'RULE_EOF' > /root/.gemini/config/rules/ha-guidelines.md
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
    # Check if native CPU supports pclmulqdq/pclmul
    if grep -q -E "\bpclmulqdq\b|\bpclmul\b" /proc/cpuinfo 2>/dev/null; then
        exec "$TARGET_BIN" "$@"
    elif command -v /usr/bin/qemu-x86_64 >/dev/null 2>&1; then
        exec /usr/bin/qemu-x86_64 -cpu max "$TARGET_BIN" "$@"
    else
        exec "$TARGET_BIN" "$@"
    fi
else
    # ARM64 (Raspberry Pi 4/5, Apple Silicon, etc.) or other architectures
    exec "$TARGET_BIN" "$@"
fi
WRAPPER_EOF
chmod +x /usr/local/bin/agy

# Pre-initialize tmux session and auto-launch agy
if ! tmux -u has-session -t main 2>/dev/null; then
    tmux -u new-session -d -s main -c "${WORKDIR}" bash
    tmux -u send-keys -t main "agy" C-m
fi

# Launch ttyd attached to persistent tmux session (force UTF-8)
exec /usr/local/bin/ttyd \
    -p 7681 \
    -W \
    -t fontSize=15 \
    -t theme='{"background": "#1e1e1e"}' \
    tmux -u new-session -A -s main -c "${WORKDIR}" bash
