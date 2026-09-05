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

# ---------------------------------------------------------------------------
# Bundled asset deployment (rules, hooks, agents, skills)
#
# /config (addon_config) is a persistent volume that survives restarts AND
# rebuilds, so a plain "if [ ! -f target ]; then generate; fi" can only ever
# create a file once -- fixing a bug in one of these bundled files and
# rebuilding the image does NOT get the fix onto an already-running install,
# since the stale copy from before the fix still exists at that path forever.
#
# A blind unconditional overwrite on every boot fixes that but destroys any
# local addition (e.g. the user, or the agent itself, appending a custom
# rule to ha-file-safety.md, or a custom hook alongside ha_file_guard.py).
#
# Instead we keep a persistent shadow copy of the bundled content as it
# looked the last time it was deployed (BASE), and do a real 3-way text
# merge (`git merge-file`: TARGET as "ours", BASE as the common ancestor,
# the current bundled file as "theirs") so an addon-side fix and a local
# addition both survive unless they edit the exact same lines, in which case
# standard <<<<<<< conflict markers are left for a human/agent to resolve
# instead of silently guessing which side wins.
BASE_SHADOW_ROOT="/config/.antigravity_cli_bundled_base"

deploy_managed_file() {
    # $1 = bundled source file (absolute path, already resolved in the image)
    # $2 = absolute deployment target path (under the persistent .gemini tree)
    local bundled="$1" target="$2"
    local base="${BASE_SHADOW_ROOT}${target}"
    [ -f "$bundled" ] || return 0
    mkdir -p "$(dirname "$target")" "$(dirname "$base")"

    if [ ! -f "$target" ]; then
        cp "$bundled" "$target"
        cp "$bundled" "$base"
        return 0
    fi

    if [ ! -f "$base" ]; then
        # No merge history yet for this target (fresh install, or upgrading
        # from a pre-merge-logic version of this addon) -- we can't tell
        # whether the existing file has local additions, so leave it alone
        # this boot rather than risk clobbering something on a blind guess.
        # Recording the bundled content as the base now means the next
        # boot's diff starts from a known point instead of guessing forever.
        cp "$bundled" "$base"
        return 0
    fi

    cmp -s "$base" "$bundled" && return 0  # bundled default hasn't changed

    if git merge-file -q "$target" "$base" "$bundled" >/dev/null 2>&1; then
        cp "$bundled" "$base"
    else
        echo "[WARN] antigravity-cli: merge conflict updating ${target} (bundled default changed and local edits conflict) -- resolve the <<<<<<< markers manually" >&2
        # Base intentionally left unchanged so the same 3-way merge is
        # retried against the same inputs on the next boot until resolved.
    fi
}

deploy_managed_dir() {
    # $1 = bundled source dir, $2 = absolute deployment target dir
    local bundled_dir="$1" target_dir="$2"
    [ -d "$bundled_dir" ] || return 0
    while IFS= read -r -d '' f; do
        local sub="${f#"$bundled_dir"/}"
        deploy_managed_file "$f" "${target_dir}/${sub}"
    done < <(find "$bundled_dir" -type f -print0)
}

# Ensure persistent directories for Antigravity credentials in addon_config (/config = /addon_configs/antigravity)
mkdir -p /config/.gemini
mkdir -p /config/.config
mkdir -p /config/.local_share
mkdir -p /config/.uv_cache

# Persist uv package cache across addon rebuilds (avoids re-downloading ha-mcp every update)
export UV_CACHE_DIR="/config/.uv_cache"

# Symlink entire ~/.gemini and ~/.config to /config so all auth tokens survive rebuilds
rm -rf /root/.gemini
ln -sfn /config/.gemini /root/.gemini

rm -rf /root/.config
ln -sfn /config/.config /root/.config

mkdir -p /root/.local
rm -rf /root/.local/share
ln -sfn /config/.local_share /root/.local/share

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
#
# NOTE on Mode 3 (headless `agy -p ... --dangerously-skip-permissions`,
# core/streamer.py stream_headless_cli): that flag auto-approves every tool
# call and is documented upstream to bypass the permissions engine entirely,
# so the `deny` list below is NOT a hard block in that specific headless
# path (removing the flag there is not an option either -- headless mode has
# a documented upstream bug where it hangs forever on any prompt it can't
# auto-approve, ignoring `allow`/timeouts alike: dangerously-skip-permissions
# is the only way headless streaming works at all today).
#
# `deny` IS a real, enforced hard block for the interactive web terminal
# (ttyd/tmux `agy` session, which runs WITHOUT --dangerously-skip-permissions)
# -- so it's kept as defense-in-depth there. The actual protection for Mode 3
# is the ha-file-safety.md always-on rule below, which every mode reads as
# context regardless of --dangerously-skip-permissions.
mkdir -p /root/.gemini/antigravity-cli
SETTINGS_FILE="/root/.gemini/antigravity-cli/settings.json"
# Source of truth: bundled/hooks/deny_rules.json in the addon repo (baked
# into the image at build time) -- kept in sync with PROTECTED in
# bundled/hooks/ha_file_guard.py and the table in bundled/rules/ha-file-safety.md.
HA_DENY_RULES="$(cat /usr/local/share/antigravity-cli-bundled/hooks/deny_rules.json)"
if [ ! -f "$SETTINGS_FILE" ]; then
    cat << SETTINGS_EOF > "$SETTINGS_FILE"
{
  "permissions": {
    "allow": [
      "mcp(home-assistant/*)"
    ],
    "deny": $HA_DENY_RULES
  }
}
SETTINGS_EOF
else
    if command -v jq >/dev/null 2>&1; then
        jq --argjson deny "$HA_DENY_RULES" \
           '.permissions.allow = ((.permissions.allow // []) + ["mcp(home-assistant/*)"] | unique) | .permissions.deny = ((.permissions.deny // []) + $deny | unique)' \
           "$SETTINGS_FILE" > "${SETTINGS_FILE}.tmp" 2>/dev/null && mv "${SETTINGS_FILE}.tmp" "$SETTINGS_FILE"
    fi
fi

# Auto-configure global rules for HA MCP. Source of truth:
# bundled/rules/*.md in the addon repo, deployed via the 3-way-merge helper
# above so a bundled-content fix survives a rebuild without erasing any rule
# text a user (or the agent) appended locally.
mkdir -p /root/.gemini/config/rules
deploy_managed_file "/usr/local/share/antigravity-cli-bundled/rules/ha-guidelines.md" "/root/.gemini/config/rules/ha-guidelines.md"

# File-safety rule: require explicit approval before any delete/overwrite,
# and hard-refuse touching HA's own critical config data. Injected as an
# always-on rule (same mechanism as ha-guidelines.md above) so it applies in
# every mode -- including Mode 3's headless --dangerously-skip-permissions
# path, where the settings.json `deny` list above is not enforced (see the
# NOTE next to HA_DENY_RULES).
deploy_managed_file "/usr/local/share/antigravity-cli-bundled/rules/ha-file-safety.md" "/root/.gemini/config/rules/ha-file-safety.md"

# Hard-block HA-critical file deletion/overwrite via a PreToolUse hook.
#
# Unlike the `deny` permission list above (bypassed by
# --dangerously-skip-permissions) or the ha-file-safety.md rule (an
# instruction the model can in principle ignore), a hook is a synchronous
# "run a script, read its JSON decision" contract with no human prompt
# involved at all -- per antigravity.google/docs/hooks/, PreToolUse fires
# before a tool executes and a `{"decision":"deny",...}` on stdout blocks it
# outright, regardless of --dangerously-skip-permissions. This should apply
# in Mode 3 headless too (it's not the same interactive-approval-UI code
# path that's documented to hang headless -- see the NOTE on HA_DENY_RULES
# above) but that has NOT been live-verified against this container's agy
# build yet; treat it as the enforced backstop only after confirming a real
# denied attempt in chat.
#
# Source of truth: bundled/hooks/ha_file_guard.py in the addon repo,
# deployed via the same 3-way-merge helper as the rules above.
mkdir -p /root/.gemini/hooks
deploy_managed_file "/usr/local/share/antigravity-cli-bundled/hooks/ha_file_guard.py" "/root/.gemini/hooks/ha_file_guard.py"
chmod +x /root/.gemini/hooks/ha_file_guard.py

HOOK_DEF="$(cat /usr/local/share/antigravity-cli-bundled/hooks/hook_registration.json)"

# Register the hook two ways, since the documented registration surface is
# ambiguous between sources (a workspace .agents/hooks.json vs a top-level
# "hooks" key in settings.json -- core/hooks_discovery.py already expects to
# find hooks in settings.json). Registering in both is harmless (worst case
# the same check runs twice) and doesn't depend on picking the one right
# answer before it's been live-tested. Both are structural JSON documents a
# user could have added other entries to, so these stay jq merges (which
# already preserve unrelated keys) rather than the file-level 3-way merge
# used for the plain-text rule/hook files above.
mkdir -p "${WORKDIR}/.agents"
AGENTS_HOOKS_FILE="${WORKDIR}/.agents/hooks.json"
if [ ! -f "$AGENTS_HOOKS_FILE" ]; then
    printf '{\n  "ha-file-guard": %s\n}\n' "$HOOK_DEF" > "$AGENTS_HOOKS_FILE"
elif command -v jq >/dev/null 2>&1; then
    jq --argjson h "$HOOK_DEF" '.["ha-file-guard"] = $h' "$AGENTS_HOOKS_FILE" > "${AGENTS_HOOKS_FILE}.tmp" 2>/dev/null && mv "${AGENTS_HOOKS_FILE}.tmp" "$AGENTS_HOOKS_FILE"
fi

if command -v jq >/dev/null 2>&1; then
    jq --argjson h "$HOOK_DEF" '.hooks["ha-file-guard"] = $h' "$SETTINGS_FILE" > "${SETTINGS_FILE}.tmp" 2>/dev/null && mv "${SETTINGS_FILE}.tmp" "$SETTINGS_FILE"
fi

# Install the baked-in Home Assistant best-practices Agent Skill (see
# Dockerfile step 5b -- GitHub fetch with a vendored bundled/skills fallback
# on network failure) into the persistent global skills dir. Deployed
# per-file via the merge helper, same as the rules/hook above, so a skill
# update (new/changed reference file) reaches an existing install on the
# next boot without wiping any local customization.
deploy_managed_dir "/usr/local/share/antigravity-cli-skills/home-assistant-best-practices" "/root/.gemini/config/skills/home-assistant-best-practices"

# Custom agents for Mode 3 (`agy --agent <id>`, core/agent_discovery.py) --
# same bundled + merge-deploy treatment as the rules/hooks/skills above.
# Deployed to the global agents dir (not the workspace one) so they show up
# regardless of which HA config directory is mounted as the workspace.
deploy_managed_dir "/usr/local/share/antigravity-cli-bundled/agents" "/root/.gemini/config/agents"

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

# Pre-initialize tmux session for web terminal (standby at bash)
if ! tmux -u has-session -t main 2>/dev/null; then
    tmux -u new-session -d -s main -c "${WORKDIR}" bash
fi

# Launch internal ttyd on port 7682 in background
echo "[INFO] Starting ttyd on internal port 7682..."
/usr/local/bin/ttyd \
    -p 7682 \
    -W \
    -b /terminal \
    -t fontSize=15 \
    -t theme='{"background": "#1e1e1e"}' \
    tmux -u new-session -A -s main -c "${WORKDIR}" bash &
TTYD_PID=$!

# Start Antigravity Dual Ingress Web UI (port 7681) & REST API (port 8000)
API_PORT="8000"
if [ -f /data/options.json ]; then
    API_PORT=$(jq -r '.api_port // 8000' /data/options.json 2>/dev/null || echo "8000")
    if [ "$API_PORT" = "null" ] || [ -z "$API_PORT" ]; then
        API_PORT="8000"
    fi
fi
export ANTIGRAVITY_API_PORT="${API_PORT}"
echo "[INFO] Starting Antigravity Dual Ingress Server on 7681 and REST API on ${API_PORT}..."

trap "kill -TERM $TTYD_PID 2>/dev/null || true; exit 0" SIGTERM SIGINT

exec python3 /usr/local/bin/antigravity_api.py
