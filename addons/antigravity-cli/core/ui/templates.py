"""Web UI HTML Templates."""

HTML_BODY = """
<header>
    <div class="brand">
      <button class="sidebar-toggle-btn" id="sidebar-toggle-btn" onclick="toggleSessionSidebar()" title="대화 목록 사이드바 열기/닫기">☰</button>
      <span>🤖 Antigravity AI</span>
      <span class="brand-badge">Real-time</span>
      <span class="build-badge" title="Web UI 빌드 번호">{UI_BUILD_VERSION}</span>
      <button class="new-chat-btn-header" onclick="startNewSession()" title="새 대화 시작">＋ 새 대화</button>
    </div>
    <div class="header-right">
      <div class="resource-badge" id="resource-badge" onclick="toggleResourcePanel()" title="클릭하여 상단 실시간 그래프 패널 고정/해제">
        <span id="header-cpu">⚙️ CPU: 애드온 0.0% (전체 0.0%)</span>
        <span class="badge-pipe">|</span>
        <span id="header-ram">💾 RAM: 0MB</span>
      </div>
      <div class="session-token-badge" onclick="resetTokens()" title="클릭 시 누적 토큰 초기화" style="cursor: pointer;">🪙 누적: <strong id="session-tokens">0</strong> Tokens</div>
      <button class="theme-toggle-btn" id="theme-toggle-btn" onclick="toggleTheme()" title="다크/라이트 테마 전환">🌙 다크</button>
      <div class="nav-tabs">
        <button class="tab-btn active" onclick="switchTab('chat')">💬 AI Chat</button>
        <button class="tab-btn" onclick="switchTab('terminal')">🖥️ Terminal</button>
      </div>
    </div>
  </header>

  <!-- Top Pinned Resource Panel (Collapsible) -->
  <div id="top-resource-panel" class="top-resource-panel">
    <div class="panel-inner">
      <div class="panel-header">
        <div class="panel-title">
          <span>📊 시스템 및 애드온 리소스 실시간 모니터</span>
          <span class="panel-sub">3초 실시간 갱신 · 듀얼 오버레이 차트</span>
        </div>
        <button class="panel-close-btn" onclick="toggleResourcePanel()" title="상단 고정 패널 닫기">✕ 닫기</button>
      </div>
      <div class="panel-grid">
        <div class="chart-box">
          <div class="chart-top">
            <span class="chart-title">⚙️ CPU 사용률 추이 (듀얼)</span>
            <div class="chart-legend">
              <span class="lg-item lg-purple">● 애드온: <strong id="val-addon-cpu">0.0%</strong></span>
              <span class="lg-item lg-blue">● 시스템 전체: <strong id="val-sys-cpu">0.0%</strong></span>
            </div>
          </div>
          <div class="canvas-holder">
            <canvas id="cpu-dual-chart" width="460" height="75"></canvas>
          </div>
        </div>
        <div class="chart-box">
          <div class="chart-top">
            <span class="chart-title">💾 RAM 점유율 추이 (듀얼)</span>
            <div class="chart-legend">
              <span class="lg-item lg-green">● 애드온: <strong id="val-addon-ram">0MB (0%)</strong></span>
              <span class="lg-item lg-cyan">● 시스템 전체: <strong id="val-sys-ram">0GB (0%)</strong></span>
            </div>
          </div>
          <div class="canvas-holder">
            <canvas id="ram-dual-chart" width="460" height="75"></canvas>
          </div>
        </div>
      </div>
      <div class="panel-stats">
        <div class="pstat"><span>애드온 메모리</span><strong id="pstat-addon-ram">-</strong></div>
        <div class="pstat"><span>시스템 전체 RAM</span><strong id="pstat-sys-ram">-</strong></div>
        <div class="pstat"><span>가동 시간 (Uptime)</span><strong id="pstat-uptime">-</strong></div>
        <div class="pstat"><span>Antigravity Stream</span><strong id="pstat-stream">-</strong></div>
      </div>
    </div>
  </div>

  <div class="app-layout">
    <!-- Collapsible Session Sidebar -->
    <aside id="session-sidebar" class="session-sidebar">
      <div class="sidebar-top">
        <button class="new-chat-btn-sidebar" onclick="startNewSession()">＋ 새 대화 시작</button>
        <button class="sidebar-close-btn" onclick="toggleSessionSidebar()" title="사이드바 닫기">✕</button>
      </div>
      <div class="sidebar-section-title">
        <span>📜 이전 대화 목록</span>
        <button class="refresh-sessions-btn" onclick="loadSessionsList()" title="목록 새로고침">🔄</button>
      </div>
      <div id="session-list" class="session-list">
        <!-- Dynamically populated session cards -->
        <div class="session-loading">세션 목록 불러오는 중...</div>
      </div>
    </aside>

    <div class="sidebar-overlay" id="sidebar-overlay" onclick="toggleSessionSidebar()"></div>

    <main>
      <!-- Chat View -->
      <section id="chat-view" class="tab-view active">
        <div class="chat-container" id="chat-box">
          <div id="history-load-more" class="history-load-more" style="display: none;">
            <button onclick="loadMoreHistory()">⬆️ 이전 대화 더보기</button>
          </div>
          <div class="hero-card" id="chat-hero-card">
            <h2>Google Antigravity 스마트홈 실시간 어시스턴트</h2>
            <p>자연어 발화 및 Antigravity AI 딥 브레인이 연동된 실시간 스트리밍 대시보드입니다.</p>
            <div class="quick-chips">
              <div class="chip" onclick="sendQuick('우리집 종합 상황 알려줘')">🏠 종합 상황</div>
              <div class="chip" onclick="sendQuick('각 방 온도 알려줘')">🌡️ 각 방 온도</div>
              <div class="chip" onclick="sendQuick('각 방 습도 알려줘')">💧 각 방 습도</div>
              <div class="chip" onclick="sendQuick('켜져 있는 조명 목록')">💡 켜진 조명</div>
              <div class="chip" onclick="sendQuick('시스템 에러 로그 확인')">⚠️ 에러 로그</div>
              <div class="chip" onclick="sendQuick('오늘 날씨와 환경 분석해줘')">🌤️ 날씨 & 환경 분석</div>
            </div>
          </div>
        </div>
        <div class="input-bar-wrap">
          <div class="mode-bar">
            <label for="stream-mode">
              <span>⚙️ 실시간 스트림 엔진:</span>
            </label>
            <select id="stream-mode" class="mode-select" onchange="onModeChange(this.value)">
              <option value="1" selected>🧠 모드 1: AI 딥 브레인 분석 (다차원 공기질 & AI 조언)</option>
              <option value="2">⚡ 모드 2: 초고속 스마트홈 즉답 (0.05초 즉시 제어 & 대시보드)</option>
              <option value="3" id="opt-mode-3">🚀 모드 3: Google Antigravity Headless CLI (실시간 NDJSON)</option>
            </select>
          </div>
          <div class="input-bar">
            <textarea id="user-input" placeholder="무엇이든 물어보거나 지시하세요... (Shift+Enter 줄바꿈)" rows="1" oninput="updateSendBtn()" onkeydown="handleKey(event)"></textarea>
            <button class="send-btn" id="send-btn" onclick="sendMessage()">➤</button>
          </div>
        </div>
      </section>

      <!-- Terminal View -->
      <section id="terminal-view" class="tab-view">
        <iframe id="terminal-iframe" src="./terminal/"></iframe>
      </section>
    </main>
  </div>
""".strip()
