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
HA_DENY_RULES='[
  "command(rm -rf)",
  "command(sudo)",
  "write_file(/config/.storage/)",
  "write_file(/config/secrets.yaml)",
  "write_file(/config/configuration.yaml)",
  "write_file(/config/.uuid)",
  "write_file(/config/.HA_VERSION)",
  "write_file(/config/home-assistant_v2.db)",
  "write_file(/config/.cloud/)",
  "write_file(/config/.gemini/)",
  "write_file(/backup/)"
]'
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

# Auto-configure global file-safety rule: require explicit approval before any
# delete/overwrite, and hard-refuse touching HA's own critical config data.
# Injected as an always-on rule (same mechanism as ha-guidelines.md above) so
# it applies in every mode -- including Mode 3's headless
# --dangerously-skip-permissions path, where the settings.json `deny` list
# above is not enforced (see the NOTE next to HA_DENY_RULES).
if [ ! -f /root/.gemini/config/rules/ha-file-safety.md ]; then
    cat << 'SAFETY_EOF' > /root/.gemini/config/rules/ha-file-safety.md
---
name: ha-file-safety
description: Require explicit user approval before deleting or overwriting any file, and never touch Home Assistant's critical config data under any circumstance
trigger: always_on
---

# Home Assistant 파일 안전 수칙 (반드시 준수)

## 1. 파일 삭제/덮어쓰기 전 사전 승인 필수
사용자의 요청을 처리하다가 파일이나 폴더를 **삭제(rm, unlink 등)하거나 기존 내용을 되돌릴 수 없게 덮어써야 하는 경우**, 절대로 먼저 실행하지 말 것. 반드시 다음 순서를 따를 것:
1. 삭제/변경하려는 파일의 **정확한 전체 경로 목록**을 나열한다.
2. 대상 파일이 **총 몇 개**인지 명시한다.
3. **왜** 삭제/변경이 필요한지 이유를 설명한다.
4. 위 내용을 답변으로 제시하고, 실제 삭제/덮어쓰기 명령은 실행하지 않은 채 답변을 마치고 **사용자의 다음 메시지에서 명확한 승인**("네", "삭제해줘", "진행해", "확인" 등)이 올 때까지 기다린다.
5. 사용자가 승인하기 전에는 `rm`, 파일을 덮어쓰는 이동/치환 등 되돌리기 어려운 작업을 절대 먼저 수행하지 않는다.
6. 대상이 단 1개 파일이어도 이 규칙은 동일하게 적용된다. "간단한 작업이니 그냥 진행"하지 않는다.

## 2. 절대 삭제·수정 금지 (사용자가 명시적으로 요청해도 거부하고 위험성을 설명할 것)
아래 항목은 Home Assistant 운영에 필수적인 핵심 데이터이며, 삭제/수정 시 되돌릴 수 없는 손상(엔티티·기기·자동화 전체 소실, 로그인 불가, 클라우드 연동 끊김 등)이 발생한다. 사용자가 삭제나 "초기화"를 요청하더라도 **절대로 실행하지 말고**, 왜 위험한지 설명한 뒤 대안(HA 자체 백업/복원 기능, 공식 설정 UI를 통한 개별 삭제 등)을 제안할 것. 이름이 일부만 일치하거나 "정리해줘", "청소해줘" 같은 모호한 요청에도 아래 항목은 절대 포함시키지 말 것.

| 경로 | 내용물 | 위험 |
|---|---|---|
| `/config/.storage/` (폴더 전체) | 엔티티·기기·영역 레지스트리, 로그인 계정, 연동된 통합구성요소(Config Entries), 대시보드 설정 등 HA의 모든 핵심 상태 | 삭제 시 모든 기기·자동화·연동이 초기화되고 로그인 계정도 사라짐 |
| `/config/secrets.yaml` | 비밀번호·토큰 등 민감정보 | 삭제 시 이를 참조하는 모든 설정이 깨짐 |
| `/config/configuration.yaml` | HA 메인 설정 파일 | 삭제 시 HA 부팅 불가 |
| `/config/.uuid` | 이 HA 인스턴스의 고유 식별자 | 삭제 시 Nabu Casa Cloud/모바일 앱 연동 등이 끊김 |
| `/config/.HA_VERSION` | 내부 버전 마커 | 삭제 시 업데이트/마이그레이션 로직 오작동 가능 |
| `/config/home-assistant_v2.db` (`-wal`, `-shm` 포함) | 히스토리/로그북 레코더 데이터베이스 | 삭제 시 과거 이력 데이터 전부 소실 |
| `/config/.cloud/` | Nabu Casa Cloud 인증 토큰 | 삭제 시 Cloud 연동(리모트 액세스, Google/Alexa 연동 등) 끊김 |
| `/config/.gemini/` | 이 애드온(Antigravity CLI) 자신의 설정·인증·대화 기록 | 삭제 시 AI 에이전트 자신의 로그인/세션이 초기화됨 (자기 자신을 삭제하지 말 것) |
| `/config/automations.yaml`, `/config/scripts.yaml`, `/config/scenes.yaml` | 사용자가 작성한 자동화/스크립트/씬 정의 | 삭제 시 해당 자동화가 전부 소실 |
| `/config/custom_components/` | 사용자가 설치한 커스텀 통합(HACS 등) | 삭제 시 관련 통합이 전부 작동 중지 |
| `/backup/` (폴더 전체) | Home Assistant 백업 아카이브 | 삭제 시 재해 복구 수단 자체가 사라짐 |

## 3. 그 외 파일
위 목록에 없는 일반 파일(예: `www/`의 이미지, 로그 파일 등)이라도 규칙 1(사전 승인)은 동일하게 적용된다.
SAFETY_EOF
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
