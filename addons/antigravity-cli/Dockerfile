ARG BUILD_FROM=ghcr.io/hassio-addons/debian-base:7.3.3
FROM ${BUILD_FROM}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# 1. Base tools, dev environments, HA analysis tools & Korean fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
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

# 2. Install GitHub CLI (gh)
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

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

# 5b. Bake in the homeassistant-ai/skills "home-assistant-best-practices" Agent
# Skill (SKILL.md + references/) so it's available out of the box. Placed
# outside ~/.gemini here because run.sh symlinks /root/.gemini -> the
# persistent /config/.gemini addon_config volume on every start (see run.sh);
# run.sh copies this baked copy into ~/.gemini/config/skills/ on first boot.
# Prefer the live GitHub fetch (freshest content); if the network call fails
# during image build (rate limit, transient outage, offline build), fall
# back to the vendored snapshot checked into bundled/skills/ above instead of
# failing the whole build.
RUN mkdir -p /usr/local/share/antigravity-cli-skills \
    && ( curl -fsSL https://github.com/homeassistant-ai/skills/archive/refs/heads/main.tar.gz -o /tmp/ha-skills.tar.gz \
         && mkdir -p /tmp/ha-skills-extract \
         && tar -xzf /tmp/ha-skills.tar.gz -C /tmp/ha-skills-extract \
         && cp -r /tmp/ha-skills-extract/skills-main/skills/home-assistant-best-practices /usr/local/share/antigravity-cli-skills/ \
         && rm -rf /tmp/ha-skills.tar.gz /tmp/ha-skills-extract \
       ) || ( echo "[WARN] GitHub fetch for home-assistant-best-practices skill failed -- using vendored bundled/skills fallback" \
         && rm -rf /usr/local/share/antigravity-cli-skills/home-assistant-best-practices \
         && cp -r /usr/local/share/antigravity-cli-bundled/skills/home-assistant-best-practices /usr/local/share/antigravity-cli-skills/ )

# 6. Automatically install CLI packages (HA CLI, Python AI tools)
RUN pip3 install --no-cache-dir --break-system-packages "numpy<2" homeassistant-cli || true

# 7. Copy core modules, run script and API server
COPY core/ /usr/local/bin/core/
COPY antigravity_api.py /usr/local/bin/antigravity_api.py
COPY run.sh /run.sh
ENV PYTHONPATH="/usr/local/bin:${PYTHONPATH}"
RUN sed -i -e 's/\r$//' /run.sh /usr/local/bin/antigravity_api.py \
    && chmod +x /run.sh /usr/local/bin/antigravity_api.py

WORKDIR /config
CMD [ "/run.sh" ]
