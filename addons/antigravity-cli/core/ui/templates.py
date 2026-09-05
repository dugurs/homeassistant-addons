"""Web UI HTML Templates."""

from core.ui import UI_BUILD_VERSION

_SVG = 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'

# Lucide-equivalent icons (the recovered React build used lucide-react
# throughout -- these are the same glyphs as inline SVG, stroke=currentColor
# so size/color are set by the .icon wrapper in CSS, not baked into the markup).
ICON_MENU = f'<svg {_SVG}><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/></svg>'
ICON_MOON = f'<svg {_SVG}><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
ICON_SUN = f'<svg {_SVG}><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>'
ICON_COINS = f'<svg {_SVG}><circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1 1 10.34 18"/><path d="M7 6h1v4"/><path d="M16.71 13.88l.7.71-2.82 2.82"/></svg>'
ICON_PLUS = f'<svg {_SVG}><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>'
ICON_MESSAGE = f'<svg {_SVG}><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
ICON_TERMINAL = f'<svg {_SVG}><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>'
ICON_TRASH = f'<svg {_SVG}><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>'
ICON_CHECK_SQUARE = f'<svg {_SVG}><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>'
ICON_SQUARE = f'<svg {_SVG}><rect x="3" y="3" width="18" height="18" rx="2"/></svg>'
ICON_ARROW_UP = f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>'
ICON_MIC = f'<svg {_SVG}><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>'
ICON_ZAP = f'<svg {_SVG}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
ICON_BRAIN = f'<svg {_SVG}><path d="M9.5 2A2.5 2.5 0 0 0 7 4.5v.5A2.5 2.5 0 0 0 4.5 7.5 2.5 2.5 0 0 0 3 9.9 2.5 2.5 0 0 0 4.5 14a2.5 2.5 0 0 0 2.5 2.5V19a2.5 2.5 0 0 0 5 0V4.5A2.5 2.5 0 0 0 9.5 2z"/><path d="M14.5 2A2.5 2.5 0 0 1 17 4.5v.5a2.5 2.5 0 0 1 2.5 2.5A2.5 2.5 0 0 1 21 9.9 2.5 2.5 0 0 1 19.5 14a2.5 2.5 0 0 1-2.5 2.5V19a2.5 2.5 0 0 1-5 0V4.5A2.5 2.5 0 0 1 14.5 2z"/></svg>'
ICON_CHEVRON_DOWN = f'<svg {_SVG}><polyline points="6 9 12 15 18 9"/></svg>'
ICON_CHEVRON_UP = f'<svg {_SVG}><polyline points="18 15 12 9 6 15"/></svg>'
ICON_CHEVRON_RIGHT = f'<svg {_SVG}><polyline points="9 18 15 12 9 6"/></svg>'
ICON_CHECK = f'<svg {_SVG}><polyline points="20 6 9 17 4 12"/></svg>'
ICON_BAR_CHART = f'<svg {_SVG}><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'
ICON_INFO = f'<svg {_SVG}><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
ICON_X = f'<svg {_SVG}><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
ICON_USER = f'<svg {_SVG}><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'

# Compact badge text ("b13") -- short like the reference's "v2.0", full version stays in the tooltip.
_UI_VERSION_SHORT = "b" + UI_BUILD_VERSION.rsplit(".", 1)[-1] if "beta." in UI_BUILD_VERSION else UI_BUILD_VERSION

HTML_BODY = f"""
<header>
    <div class="brand">
      <button class="icon-btn-lg" id="sidebar-toggle-btn" onclick="toggleSessionSidebar()" title="대화 목록 사이드바 열기/닫기"><span class="icon">{ICON_MENU}</span></button>
      <div class="brand-name">
        <span class="brand-emoji">🤖</span>
        <span>Antigravity AI</span>
        <span class="brand-badge" id="build-badge" title="배포 빌드 번호 (업데이트 반영 확인용): {UI_BUILD_VERSION}">{_UI_VERSION_SHORT}</span>
      </div>
    </div>
    <div class="header-right">
      <button class="header-stat-pill" id="resource-badge" onclick="toggleResourcePanel()" title="클릭하여 상단 실시간 그래프 패널 고정/해제">
        <span class="stat-dot stat-dot-green"></span>
        <span id="header-cpu">0.0%</span>
        <span class="stat-sep">·</span>
        <span class="stat-dot stat-dot-blue"></span>
        <span id="header-ram">0MB</span>
      </button>
      <button class="icon-btn-lg" id="theme-toggle-btn" onclick="toggleTheme()" title="다크/라이트 테마 전환"><span class="icon" id="theme-toggle-icon">{ICON_MOON}</span></button>
      <button class="icon-btn-lg" id="help-btn" onclick="toggleHelpPanel()" title="도움말 / 피드백"><span class="icon">{ICON_INFO}</span></button>
    </div>
  </header>

  <div class="image-lightbox-overlay" id="image-lightbox-overlay" onclick="closeImageLightbox()">
    <img id="image-lightbox-img" src="" alt="">
  </div>

  <div class="help-overlay" id="help-overlay" onclick="if(event.target===this) toggleHelpPanel()">
    <div class="help-box">
      <div class="help-box-top">
        <h3>도움말 &amp; 피드백</h3>
        <button class="help-box-close" onclick="toggleHelpPanel()"><span class="icon">{ICON_X}</span></button>
      </div>
      <div class="help-section">
        <h4>실행 모드</h4>
        <ul>
          <li><strong>고속 제어 모드</strong> — 기기 제어/상태 조회를 즉시 처리하고, 날씨·환경 질문엔 센서 기반 분석/조언도 함께 제공</li>
          <li><strong>CLI 추론 모드</strong> — Antigravity CLI(agy) 기반 심층 에이전트</li>
        </ul>
      </div>
      <div class="help-section">
        <h4>단축키</h4>
        <ul>
          <li><span class="mono">Ctrl+K</span> — 새 대화 시작</li>
          <li><span class="mono">Enter</span> — 전송, <span class="mono">Shift+Enter</span> — 줄바꿈</li>
          <li><span class="mono">/codesearch &lt;검색어&gt;</span> — 워크스페이스 코드 검색(agy 연동 없는 자체 grep)</li>
        </ul>
      </div>
      <div class="help-section">
        <h4>MCP 연동</h4>
        <ul id="help-mcp-list"><li>불러오는 중...</li></ul>
      </div>
      <div class="help-section">
        <h4>스킬 (Skills)</h4>
        <ul id="help-skills-list"><li>불러오는 중...</li></ul>
      </div>
      <div class="help-section">
        <h4>훅 (Hooks)</h4>
        <ul id="help-hooks-list"><li>불러오는 중...</li></ul>
      </div>
      <div class="help-section">
        <h4>버그 신고 / 기능 제안</h4>
        <a href="https://github.com/dugurs/homeassistant-addons/issues" target="_blank" rel="noopener">GitHub Issues에 남기기 ↗</a>
      </div>
    </div>
  </div>

  <!-- Top Pinned Resource Panel (Collapsible) -->
  <div id="top-resource-panel" class="top-resource-panel">
    <div class="panel-inner">
      <div class="panel-grid">
        <div class="chart-box">
          <div class="chart-top">
            <span class="chart-title">⚙️ CPU</span>
            <div class="chart-legend">
              <span class="lg-item lg-purple">● 애드온 <strong id="val-addon-cpu">0.0%</strong></span>
              <span class="lg-item lg-blue">● 전체 <strong id="val-sys-cpu">0.0%</strong></span>
            </div>
          </div>
          <div class="canvas-holder">
            <canvas id="cpu-dual-chart" width="460" height="75"></canvas>
          </div>
        </div>
        <div class="chart-box">
          <div class="chart-top">
            <span class="chart-title">💾 RAM</span>
            <div class="chart-legend">
              <span class="lg-item lg-green">● 애드온 <strong id="val-addon-ram">0MB (0%)</strong></span>
              <span class="lg-item lg-cyan">● 전체 <strong id="val-sys-ram">0GB (0%)</strong></span>
            </div>
          </div>
          <div class="canvas-holder">
            <canvas id="ram-dual-chart" width="460" height="75"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="app-layout">
    <!-- Collapsible Session Sidebar -->
    <aside id="session-sidebar" class="session-sidebar">
      <div class="sidebar-top">
        <div class="sidebar-nav-title">내비게이션</div>
        <button class="sidebar-close-btn" onclick="toggleSessionSidebar()" title="사이드바 닫기"><span class="icon">{ICON_X}</span></button>
      </div>
      <nav class="sidebar-nav">
        <button class="sidebar-nav-item active" id="nav-tab-chat" onclick="switchTab('chat')"><span class="icon">{ICON_MESSAGE}</span><span>AI 채팅 대화창</span></button>
        <button class="sidebar-nav-item" id="nav-tab-terminal" onclick="switchTab('terminal')"><span class="icon">{ICON_TERMINAL}</span><span>웹 터미널 (ttyd)</span></button>
      </nav>
      <div class="sidebar-divider"></div>
      <div class="sidebar-new-chat-wrap">
        <button class="new-chat-btn-sidebar" onclick="startNewSession()">
          <span class="icon icon-blue">{ICON_PLUS}</span>
          <span>새 대화 시작</span>
          <span class="kbd-hint">Ctrl+K</span>
        </button>
      </div>
      <div class="sidebar-divider"></div>
      <div class="sidebar-section-title">
        <span id="session-list-title">최근 대화 기록 (0)</span>
        <button class="session-select-btn" id="session-select-btn" onclick="toggleSessionSelectMode()">선택</button>
      </div>
      <div id="session-list" class="session-list">
        <div class="session-loading">세션 목록 불러오는 중...</div>
      </div>
      <div class="sidebar-bottom-slot">
        <div class="session-select-toolbar" id="session-select-toolbar" style="display:none;">
          <button onclick="selectAllSessions()"><span id="session-select-all-label">전체 선택</span></button>
          <button class="session-delete-btn" id="session-delete-btn" onclick="deleteSelectedSessions()" disabled>
            <span class="icon">{ICON_TRASH}</span><span>선택 삭제 (<span id="session-delete-count">0</span>)</span>
          </button>
        </div>
        <div class="sidebar-footer" id="sidebar-footer">총 0개 세션</div>
      </div>
    </aside>

    <div class="sidebar-overlay" id="sidebar-overlay" onclick="toggleSessionSidebar()"></div>

    <main>
      <!-- Chat View -->
      <section id="chat-view" class="tab-view active">
        <div class="chat-container" id="chat-box">
          <div class="hero-card" id="chat-hero-card">
            <span class="hero-badge">Google Antigravity Engine</span>
            <h2>무엇을 도와드릴까요?</h2>
            <p>Home Assistant 스마트홈 제어 및 환경 분석 실시간 AI 어시스턴트입니다.</p>
            <div class="quick-grid">
              <button class="quick-card" onclick="sendQuick('우리집 종합 상황 알려줘')">🏠 우리집 종합 상황</button>
              <button class="quick-card" onclick="sendQuick('각 방 온도 알려줘')">🌡️ 각 방 온도 조회</button>
              <button class="quick-card" onclick="sendQuick('각 방 습도 알려줘')">💧 각 방 습도 조회</button>
              <button class="quick-card" onclick="sendQuick('켜져 있는 조명 목록')">💡 켜진 조명 목록</button>
              <button class="quick-card" onclick="sendQuick('시스템 에러 로그 확인')">⚠️ 에러 로그 진단</button>
              <button class="quick-card" onclick="sendQuick('오늘 날씨와 환경 분석해줘')">🌤️ 날씨 & 환경 분석</button>
            </div>
          </div>
        </div>
        <div class="input-bar-wrap">
          <div class="quota-banner" id="quota-banner" style="display:none;">
            <span class="quota-banner-icon">⚠️</span>
            <div class="quota-banner-body">
              <div class="quota-banner-title">기본 모델 할당량 소진</div>
              <div class="quota-banner-desc" id="quota-banner-desc"></div>
            </div>
            <button class="quota-banner-dismiss" onclick="dismissQuotaBanner()">닫기</button>
          </div>
          <div class="composer" id="composer">
            <div class="attach-preview-row" id="attach-preview-row" style="display:none;"></div>
            <input type="file" id="attach-file-input" multiple accept=".py,.js,.ts,.java,.c,.cpp,.go,.rs,.sh,.bat,.ps1,.json,.yaml,.yml,.xml,.toml,.ini,.env,.csv,.tsv,.txt,.md,.pdf,.docx,.png,.jpg,.jpeg,.webp,.gif" style="display:none;" onchange="handleFilesSelected(event)">
            <textarea id="user-input" placeholder="무엇이든 물어보세요" rows="1" oninput="updateSendBtn(); autoResizeTextarea(); updateSlashCommandMenu()" onkeydown="handleKey(event)" onblur="closeSlashCommandMenu()"></textarea>
            <div class="slash-command-menu" id="slash-command-menu"></div>
            <div class="composer-toolbar">
              <div class="composer-toolbar-left">
                <button class="attach-btn" id="attach-btn" onclick="triggerFileAttach()" title="파일 또는 이미지 추가 (CLI 추론 모드 전용)"><span class="icon">{ICON_PLUS}</span></button>

                <div class="model-picker" id="stream-mode-picker">
                  <button class="mode-picker-btn" id="stream-mode-btn" onclick="toggleStreamModePicker()" title="실행 모드 변경">
                    <span class="icon" id="stream-mode-icon">{ICON_ZAP}</span>
                    <span id="stream-mode-current">제어</span>
                    <span class="icon icon-sm">{ICON_CHEVRON_DOWN}</span>
                  </button>
                  <div class="model-dropdown" id="stream-mode-dropdown">
                    <div class="model-dropdown-title">실행 모드 (Mode)</div>
                    <div id="stream-mode-list" class="model-dropdown-list"></div>
                  </div>
                </div>

                <div class="model-picker" id="model-picker">
                  <button class="mode-picker-btn model-picker-btn" id="model-picker-btn" onclick="toggleModelPicker()" title="모델 및 Thinking Effort 변경">
                    <span class="icon icon-sm icon-dim">{ICON_PLUS}</span>
                    <span id="model-picker-current" class="model-picker-name">모델 선택</span>
                    <span class="model-effort-tag" id="model-picker-effort" style="display:none;"></span>
                    <span class="usage-mini-ring model-picker-usage-ring" id="model-picker-usage-ring" style="display:none;"></span>
                    <span class="icon icon-sm">{ICON_CHEVRON_UP}</span>
                  </button>
                  <div class="model-dropdown" id="model-dropdown">
                    <div class="model-dropdown-title">Model</div>
                    <div id="model-dropdown-list" class="model-dropdown-list">
                      <div class="model-dropdown-loading">모델 목록 불러오는 중...</div>
                    </div>
                    <div class="usage-view-row" id="usage-view-row" onmouseenter="openUsagePanel()" onmouseleave="closeUsagePanel()">
                      <span><span class="icon icon-sm">{ICON_BAR_CHART}</span><span>View Usage</span></span>
                      <span class="icon icon-sm">{ICON_CHEVRON_RIGHT}</span>
                    </div>
                  </div>
                  <div class="usage-panel" id="usage-panel" onmouseenter="openUsagePanel()" onmouseleave="closeUsagePanel()">
                    <div class="usage-panel-loading">사용량 불러오는 중...</div>
                  </div>
                </div>

                <div class="model-picker" id="agent-picker" style="display:none;">
                  <button class="mode-picker-btn model-picker-btn" id="agent-picker-btn" onclick="toggleAgentPicker()" title="커스텀 에이전트 변경">
                    <span class="icon icon-sm icon-dim">{ICON_USER}</span>
                    <span id="agent-picker-current" class="model-picker-name">Default agent</span>
                    <span class="icon icon-sm">{ICON_CHEVRON_UP}</span>
                  </button>
                  <div class="model-dropdown" id="agent-dropdown">
                    <div class="model-dropdown-title">Agent</div>
                    <div id="agent-dropdown-list" class="model-dropdown-list"></div>
                  </div>
                </div>
              </div>
              <div class="composer-toolbar-right">
                <button class="mic-btn" id="mic-btn" onclick="toggleRecording()" title="음성으로 질문하기"><span class="icon">{ICON_MIC}</span></button>
                <button class="send-btn" id="send-btn" onclick="sendMessage()"><span class="icon">{ICON_ARROW_UP}</span></button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Terminal View -->
      <section id="terminal-view" class="tab-view">
        <div id="terminal-confirm-overlay" class="terminal-confirm-overlay" style="display:none;">
          <div class="terminal-confirm-box">
            <p>agy(Antigravity CLI)를 실행할까요?</p>
            <div class="terminal-confirm-actions">
              <button class="terminal-confirm-yes" onclick="confirmRunAgy(true)">Yes</button>
              <button class="terminal-confirm-no" onclick="confirmRunAgy(false)">No</button>
            </div>
          </div>
        </div>
        <iframe id="terminal-iframe" src="./terminal/"></iframe>
      </section>
    </main>
  </div>
""".strip()
