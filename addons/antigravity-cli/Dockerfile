ARG BUILD_FROM=ghcr.io/hassio-addons/debian-base:9.4.0
FROM ${BUILD_FROM}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# 1. Base tools, dev environments, HA analysis tools, GitHub CLI (gh) & Korean fonts
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    git \
    jq \
    sudo \
    tmux \
    nano \
    python3 \
    python3-pip \
    python3-venv \
    procps \
    ripgrep \
    sqlite3 \
    yamllint \
    locales \
    fonts-noto-cjk \
    qemu-user \
    qemu-user-static \
    gh \
    && rm -rf /var/lib/apt/lists/*

# Install uv (blazing fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/ \
    && mv /root/.local/bin/uvx /usr/local/bin/

# Set UTF-8 Locales for complete Korean language support and keep env for s6-overlay
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    S6_KEEP_ENV=1

# 3. Install yq (YAML processor)
ARG BUILD_ARCH=amd64
RUN if [ "${BUILD_ARCH}" = "amd64" ] || [ "${BUILD_ARCH}" = "x86_64" ]; then YQ_ARCH="amd64"; \
    elif [ "${BUILD_ARCH}" = "aarch64" ] || [ "${BUILD_ARCH}" = "arm64" ]; then YQ_ARCH="arm64"; \
    else YQ_ARCH="amd64"; fi \
    && curl -fsSL "https://github.com/mikefarah/yq/releases/latest/download/yq_linux_${YQ_ARCH}" -o /usr/local/bin/yq \
    && chmod +x /usr/local/bin/yq

# 4. Install ttyd for Ingress web terminal
RUN if [ "${BUILD_ARCH}" = "amd64" ] || [ "${BUILD_ARCH}" = "x86_64" ]; then ARCH="x86_64"; \
    elif [ "${BUILD_ARCH}" = "aarch64" ] || [ "${BUILD_ARCH}" = "arm64" ]; then ARCH="aarch64"; \
    elif [ "${BUILD_ARCH}" = "armv7" ]; then ARCH="armhf"; \
    else ARCH="x86_64"; fi \
    && curl -fsSL "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.${ARCH}" -o /usr/local/bin/ttyd \
    && chmod +x /usr/local/bin/ttyd

# 5. Install Google Antigravity CLI
RUN curl -fsSL https://antigravity.google/cli/install.sh | bash

# 5a. Bake in this repo's bundled/ tree (rules, hooks, custom agents, and a
# vendored fallback snapshot of the HA best-practices skill) so run.sh has a
# single, versioned source of truth to deploy from at boot -- see run.sh's
# deploy_managed_file/deploy_managed_dir for how these reach the persistent
# /config volume without clobbering local edits on every rebuild.
COPY bundled/ /usr/local/share/antigravity-cli-bundled/

# 5b. Smart Upstream Skill Fetch: Compare GitHub remote commit against local bundled commit
# Avoids re-downloading the entire tarball when the local snapshot is already at the latest upstream commit.
RUN mkdir -p /usr/local/share/antigravity-cli-skills \
    && LOCAL_COMMIT="$(cat /usr/local/share/antigravity-cli-bundled/skills/.upstream_commit 2>/dev/null || echo '')" \
    && REMOTE_COMMIT="$(git ls-remote https://github.com/homeassistant-ai/skills.git refs/heads/main 2>/dev/null | awk '{print $1}')" \
    && if [ -n "$REMOTE_COMMIT" ] && [ "$REMOTE_COMMIT" != "$LOCAL_COMMIT" ]; then \
         echo "[INFO] Newer upstream skill detected ($REMOTE_COMMIT != $LOCAL_COMMIT) -- downloading..." \
         && ( curl -fsSL https://github.com/homeassistant-ai/skills/archive/refs/heads/main.tar.gz -o /tmp/ha-skills.tar.gz \
              && mkdir -p /tmp/ha-skills-extract \
              && tar -xzf /tmp/ha-skills.tar.gz -C /tmp/ha-skills-extract \
              && cp -r /tmp/ha-skills-extract/skills-main/skills/home-assistant-best-practices /usr/local/share/antigravity-cli-skills/ \
              && rm -rf /tmp/ha-skills.tar.gz /tmp/ha-skills-extract \
            ) || ( echo "[WARN] GitHub download failed, falling back to bundled snapshot" \
                   && cp -r /usr/local/share/antigravity-cli-bundled/skills/home-assistant-best-practices /usr/local/share/antigravity-cli-skills/ ); \
       else \
         echo "[INFO] Bundled skill is up-to-date ($LOCAL_COMMIT) -- using local snapshot" \
         && cp -r /usr/local/share/antigravity-cli-bundled/skills/home-assistant-best-practices /usr/local/share/antigravity-cli-skills/; \
       fi

# 6. Automatically install CLI packages (HA CLI, Python AI tools) + a small
# pure-Python websocket client -- entity-registry metadata (hidden_by, used
# by core/ha_registry.py to keep a user-hidden device from being swept into
# a room-wide control command) is WebSocket-only in stock HA, REST has no
# equivalent. Best-effort like the rest of this line: core/ha_registry.py
# catches ImportError/connection failures and degrades to "no hidden-device
# filtering" rather than breaking device control if this fails to install.
RUN pip3 install --no-cache-dir --break-system-packages numpy homeassistant-cli websocket-client smbprotocol || true

# 7. Copy core modules, run script and API server
COPY core/ /usr/local/bin/core/
COPY antigravity_api.py /usr/local/bin/antigravity_api.py
COPY run.sh /run.sh
ENV PYTHONPATH="/usr/local/bin:${PYTHONPATH}"
RUN sed -i -e 's/\r$//' /run.sh /usr/local/bin/antigravity_api.py \
    && chmod +x /run.sh /usr/local/bin/antigravity_api.py

WORKDIR /config
CMD [ "/run.sh" ]
