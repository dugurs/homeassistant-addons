"""Web UI Frontend Client JavaScript Application."""

JS_SCRIPTS = """
function notSupportedYet(feature) {
      let toast = document.getElementById('global-toast');
      if (!toast) {
        toast = document.createElement('div');
        toast.id = 'global-toast';
        toast.className = 'toast-msg';
        document.body.appendChild(toast);
      }
      toast.textContent = `${feature} 기능은 아직 지원되지 않습니다.`;
      toast.classList.add('show');
      clearTimeout(toast._hideTimer);
      toast._hideTimer = setTimeout(() => toast.classList.remove('show'), 2000);
    }

    function switchTab(tabId) {
      const navChat = document.getElementById('nav-tab-chat');
      const navTerminal = document.getElementById('nav-tab-terminal');
      if (navChat) navChat.classList.toggle('active', tabId === 'chat');
      if (navTerminal) navTerminal.classList.toggle('active', tabId === 'terminal');
      const chatView = document.getElementById('chat-view');
      const termView = document.getElementById('terminal-view');
      if (tabId === 'chat') {
        if (chatView) chatView.classList.add('active');
        if (termView) termView.classList.remove('active');
      } else if (tabId === 'terminal') {
        if (chatView) chatView.classList.remove('active');
        if (termView) termView.classList.add('active');
      }
    }

    const ICON_MOON_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    const ICON_SUN_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';

    function toggleTheme() {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('antigravity_theme', next);
      const icon = document.getElementById('theme-toggle-icon');
      if (icon) icon.innerHTML = next === 'dark' ? ICON_MOON_SVG : ICON_SUN_SVG;
    }

    function getCurrentTimeStr() {
      const now = new Date();
      return now.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
    }

    function copyMessage(btn) {
      const bubble = btn.closest('.bubble-wrap').querySelector('.answer-content');
      const text = bubble.getAttribute('data-raw') || bubble.innerText;
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = '✓ 복사완료';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = '📋 복사';
          btn.classList.remove('copied');
        }, 2000);
      }).catch(() => {
        btn.textContent = '❌ 실패';
        setTimeout(() => { btn.textContent = '📋 복사'; }, 2000);
      });
    }

    function appendUserMessage(text) {
      const box = document.getElementById('chat-box');
      const row = document.createElement('div');
      const timeStr = getCurrentTimeStr();
      row.className = 'msg-row user';
      row.innerHTML = `
        <div class="bubble-wrap">
          <div class="bubble">${text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
          <div class="msg-meta user"><span class="meta-time">${timeStr}</span></div>
        </div>
      `;
      box.appendChild(row);
      box.scrollTop = box.scrollHeight;
    }

    let sessionTotalTokens = parseInt(localStorage.getItem('antigravity_total_tokens') || '0', 10);

    function resetTokens() {
      if (confirm("누적 토큰 카운터를 0으로 초기화하시겠습니까?")) {
        sessionTotalTokens = 0;
        localStorage.setItem('antigravity_total_tokens', '0');
        const sessBadge = document.getElementById('session-tokens');
        if (sessBadge) sessBadge.textContent = '0';
      }
    }

    function switchMsgView(btn, viewType) {
      const bubble = btn.closest('.bubble');
      const tabs = bubble.querySelectorAll('.view-tab');
      tabs.forEach(t => t.classList.remove('active'));
      btn.classList.add('active');

      const parsedView = bubble.querySelector('.answer-content');
      const rawView = bubble.querySelector('.raw-markdown-view');

      if (viewType === 'raw') {
        parsedView.style.display = 'none';
        rawView.style.display = 'block';
      } else {
        parsedView.style.display = 'block';
        rawView.style.display = 'none';
      }
    }

    function copyMessageTop(btn) {
      const bubble = btn.closest('.bubble');
      const rawCode = bubble.querySelector('.raw-markdown-view code');
      const text = rawCode ? rawCode.textContent : '';
      navigator.clipboard.writeText(text).then(() => {
        btn.innerHTML = '✓ 복사완료';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.innerHTML = '📋 복사';
          btn.classList.remove('copied');
        }, 2000);
      });
    }

    function createBotStreamMessage(streamMode) {
      const box = document.getElementById('chat-box');
      const row = document.createElement('div');
      const timeStr = getCurrentTimeStr();
      const startTime = performance.now();
      
      let modeText = '🧠 AI 딥 브레인';
      let modeClass = 'mode-badge';
      if (streamMode === 3) {
        modeText = '🚀 Headless CLI';
        modeClass = 'mode-badge cli';
      } else if (streamMode === 2) {
        modeText = '⚡ 초고속 스마트홈';
        modeClass = 'mode-badge fast';
      }

      row.className = 'msg-row bot';
      row.innerHTML = `
        <div class="bubble-wrap">
          <div class="bubble">
            <div class="bubble-header">
              <div class="header-left-group">
                <span class="${modeClass}">${modeText}</span>
                <div class="view-toggle-wrap">
                  <button class="view-tab active" onclick="switchMsgView(this, 'parsed')">🎨 렌더링</button>
                  <button class="view-tab" onclick="switchMsgView(this, 'raw')">📝 원문</button>
                </div>
              </div>
              <button class="top-copy-btn" onclick="copyMessageTop(this)" title="마크다운 원문 복사">📋 복사</button>
            </div>
            <!-- Mini Terminal Live Window for real-time operations -->
            <div class="term-box" style="display: none;">
              <div class="term-header">
                <div class="term-dots">
                  <span class="term-dot red"></span>
                  <span class="term-dot yellow"></span>
                  <span class="term-dot green"></span>
                </div>
                <span class="term-title">💻 Antigravity Terminal Live</span>
                <span class="term-badge live">● LIVE</span>
              </div>
              <div class="term-body"></div>
            </div>
            <!-- Main Final Answer Content -->
            <div class="answer-content"><span style="color: var(--text-muted); animation: pulseLive 1.5s infinite ease-in-out;">⚡ Antigravity CLI 실시간 처리 중...</span></div>
            <pre class="raw-markdown-view" style="display: none;"><code></code></pre>
          </div>
          <div class="msg-meta bot">
            <span class="meta-time">${timeStr}</span>
            <span class="meta-latency" style="display: none;"></span>
            <span class="meta-tokens" style="display: none;"></span>
            <button class="copy-btn" onclick="copyMessage(this)">📋 전체 복사</button>
          </div>
        </div>
      `;
      box.appendChild(row);
      box.scrollTop = box.scrollHeight;

      const termBox = row.querySelector('.term-box');
      const termBody = row.querySelector('.term-body');
      const termBadge = row.querySelector('.term-badge');
      const answerContent = row.querySelector('.answer-content');
      const rawCode = row.querySelector('.raw-markdown-view code');
      const latencyEl = row.querySelector('.meta-latency');
      const tokensEl = row.querySelector('.meta-tokens');

      let answerText = "";
      let finished = false;
      let hasAnswerStarted = false;

      const liveTimer = setInterval(() => {
        if (finished) return;
        const elapsed = ((performance.now() - startTime) / 1000).toFixed(1);
        if (elapsed >= 0.5 && latencyEl) {
          latencyEl.textContent = `⏳ ${elapsed}초 실시간 처리 중...`;
          latencyEl.style.display = 'inline';
        }
      }, 100);

      return {
        addLiveLog: function(logStr) {
          if (!termBox || !termBody) return;
          termBox.style.display = 'block';
          const lineEl = document.createElement('div');
          lineEl.className = 'term-line';
          
          let lineClass = 'term-text';
          if (logStr.includes('💭') || logStr.includes('[추론]')) lineClass += ' think';
          else if (logStr.includes('🔧') || logStr.includes('[도구') || logStr.includes('[HA 도구]')) lineClass += ' tool';
          else if (logStr.includes('📄') || logStr.includes('[파일')) lineClass += ' file';
          else if (logStr.includes('⚙️') || logStr.includes('[명령어')) lineClass += ' cmd';
          else if (logStr.includes('🚀') || logStr.includes('[세션')) lineClass += ' init';
          else if (logStr.includes('✅') || logStr.includes('[완료')) lineClass += ' done';
          else if (logStr.includes('⚠️') || logStr.includes('오류') || logStr.includes('인증')) lineClass += ' error';

          const now = new Date();
          const ts = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`;
          
          lineEl.innerHTML = `<span class="term-time">[${ts}]</span> <span class="${lineClass}">${logStr}</span>`;
          termBody.appendChild(lineEl);
          termBody.scrollTop = termBody.scrollHeight;
          box.scrollTop = box.scrollHeight;
        },
        addTool: function(toolStr) {
          this.addLiveLog(toolStr);
        },
        appendChunk: function(chunk) {
          if (!hasAnswerStarted) {
            hasAnswerStarted = true;
            answerText = "";
          }
          answerText += chunk;
          answerContent.innerHTML = formatMarkdown(answerText);
          if (rawCode) rawCode.textContent = answerText;
          box.scrollTop = box.scrollHeight;
        },
        setText: function(text) {
          hasAnswerStarted = true;
          answerText = text;
          answerContent.innerHTML = formatMarkdown(answerText);
          if (rawCode) rawCode.textContent = answerText;
          box.scrollTop = box.scrollHeight;
        },
        hasContent: function() {
          return answerText && answerText.trim().length > 0;
        },
        finish: function(tokensMeta) {
          if (finished) return;
          finished = true;
          clearInterval(liveTimer);
          if (termBadge) {
            termBadge.textContent = '● COMPLETED';
            termBadge.classList.remove('live');
            termBadge.classList.add('done');
          }
          const latency = ((performance.now() - startTime) / 1000).toFixed(2);
          if (latencyEl) {
            latencyEl.textContent = `⚡ ${latency}초 완료`;
            latencyEl.style.display = 'inline';
          }
          if (tokensMeta && tokensMeta.total) {
            if (tokensEl) {
              tokensEl.textContent = `🪙 ${tokensMeta.total} Tokens (In: ${tokensMeta.input} / Out: ${tokensMeta.output}) | ${tokensMeta.speed_tps} tok/s`;
              tokensEl.style.display = 'inline';
            }
            sessionTotalTokens += tokensMeta.total;
            localStorage.setItem('antigravity_total_tokens', sessionTotalTokens.toString());
            const sessBadge = document.getElementById('session-tokens');
            if (sessBadge) sessBadge.textContent = sessionTotalTokens.toLocaleString();
          }
          if (!hasAnswerStarted || !answerText) {
            answerContent.innerHTML = "<span style='color: var(--text-muted);'>✅ 작업이 완료되었습니다.</span>";
            if (rawCode) rawCode.textContent = "작업이 완료되었습니다.";
          }
          answerContent.setAttribute('data-raw', answerText);
          box.scrollTop = box.scrollHeight;
        }
      };
    }

    // Sticky Resource Panel & Dual-Line History
    const MAX_HISTORY = 24;
    const addonCpuHistory = [];
    const sysCpuHistory = [];
    const addonRamHistory = [];
    const sysRamHistory = [];
    let isResourcePanelOpen = false;

    function toggleResourcePanel() {
      const panel = document.getElementById('top-resource-panel');
      if (!panel) return;
      isResourcePanelOpen = !panel.classList.contains('open');
      panel.classList.toggle('open', isResourcePanelOpen);
      if (isResourcePanelOpen) {
        renderCharts();
      }
    }

    function formatUptime(seconds) {
      if (!seconds) return '0초';
      const h = Math.floor(seconds / 3600);
      const m = Math.floor((seconds % 3600) / 60);
      const s = seconds % 60;
      if (h > 0) return `${h}시간 ${m}분`;
      if (m > 0) return `${m}분 ${s}초`;
      return `${s}초`;
    }

    function drawDualSparkline(canvasId, dataSys, dataAddon, maxScale, colorSys, colorAddon, fillAddon) {
      const canvas = document.getElementById(canvasId);
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;

      ctx.clearRect(0, 0, w, h);

      if (!dataSys || dataSys.length === 0) return;

      // Draw subtle horizontal grid lines (25%, 50%, 75%)
      ctx.strokeStyle = 'rgba(150, 150, 150, 0.15)';
      ctx.lineWidth = 1;
      for (let y of [0.25, 0.5, 0.75]) {
        ctx.beginPath();
        ctx.moveTo(0, h * y);
        ctx.lineTo(w, h * y);
        ctx.stroke();
      }

      const step = w / Math.max(MAX_HISTORY - 1, 1);
      const len = dataSys.length;
      const startX = w - ((len - 1) * step);

      const makePoints = (dList) => {
        return dList.map((val, i) => {
          const x = startX + (i * step);
          const ratio = Math.min(1, Math.max(0, val / maxScale));
          const y = h - 6 - (ratio * (h - 12));
          return { x, y, val };
        });
      };

      const ptsSys = makePoints(dataSys);
      const ptsAddon = makePoints(dataAddon);

      // 1. Draw Addon Gradient Area Fill
      if (ptsAddon.length >= 2) {
        ctx.beginPath();
        ctx.moveTo(ptsAddon[0].x, h);
        ctx.lineTo(ptsAddon[0].x, ptsAddon[0].y);
        for (let i = 1; i < ptsAddon.length; i++) {
          ctx.lineTo(ptsAddon[i].x, ptsAddon[i].y);
        }
        ctx.lineTo(ptsAddon[ptsAddon.length - 1].x, h);
        ctx.closePath();

        const grad = ctx.createLinearGradient(0, 0, 0, h);
        grad.addColorStop(0, fillAddon);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.fill();
      }

      // 2. Draw System Line (dashed or solid)
      if (ptsSys.length >= 2) {
        ctx.beginPath();
        ctx.moveTo(ptsSys[0].x, ptsSys[0].y);
        for (let i = 1; i < ptsSys.length; i++) {
          ctx.lineTo(ptsSys[i].x, ptsSys[i].y);
        }
        ctx.strokeStyle = colorSys;
        ctx.lineWidth = 1.6;
        ctx.setLineDash([4, 3]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // 3. Draw Addon Line (Solid thick)
      if (ptsAddon.length >= 2) {
        ctx.beginPath();
        ctx.moveTo(ptsAddon[0].x, ptsAddon[0].y);
        for (let i = 1; i < ptsAddon.length; i++) {
          ctx.lineTo(ptsAddon[i].x, ptsAddon[i].y);
        }
        ctx.strokeStyle = colorAddon;
        ctx.lineWidth = 2.2;
        ctx.stroke();
      }

      // 4. Draw Current Endpoint Dots
      if (ptsSys.length > 0) {
        const lpSys = ptsSys[ptsSys.length - 1];
        ctx.fillStyle = colorSys;
        ctx.beginPath();
        ctx.arc(lpSys.x, lpSys.y, 3.5, 0, Math.PI * 2);
        ctx.fill();
      }
      if (ptsAddon.length > 0) {
        const lpAddon = ptsAddon[ptsAddon.length - 1];
        ctx.fillStyle = colorAddon;
        ctx.beginPath();
        ctx.arc(lpAddon.x, lpAddon.y, 4.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    }

    function renderCharts() {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const sysCpuCol = isDark ? '#60a5fa' : '#2563eb';
      const addonCpuCol = isDark ? '#c084fc' : '#9333ea';
      const addonCpuFill = isDark ? 'rgba(192, 132, 252, 0.3)' : 'rgba(147, 51, 234, 0.2)';

      const sysRamCol = isDark ? '#38bdf8' : '#0284c7';
      const addonRamCol = isDark ? '#34d399' : '#059669';
      const addonRamFill = isDark ? 'rgba(52, 211, 153, 0.3)' : 'rgba(5, 150, 105, 0.2)';

      drawDualSparkline('cpu-dual-chart', sysCpuHistory, addonCpuHistory, 100, sysCpuCol, addonCpuCol, addonCpuFill);
      drawDualSparkline('ram-dual-chart', sysRamHistory, addonRamHistory, 100, sysRamCol, addonRamCol, addonRamFill);
    }

    async function pollStatus() {
      try {
        const res = await fetch('api/status');
        if (!res.ok) return;
        const data = await res.json();

        // Addon vs System CPU
        const addonCpu = typeof data.addon_cpu_usage === 'number' ? data.addon_cpu_usage : (typeof data.cpu_usage === 'number' ? data.cpu_usage : 0);
        const sysCpu = typeof data.system_cpu_usage === 'number' ? data.system_cpu_usage : (typeof data.cpu_usage === 'number' ? data.cpu_usage : 0);

        addonCpuHistory.push(addonCpu);
        if (addonCpuHistory.length > MAX_HISTORY) addonCpuHistory.shift();
        sysCpuHistory.push(sysCpu);
        if (sysCpuHistory.length > MAX_HISTORY) sysCpuHistory.shift();

        // Addon vs System RAM
        const addonRamMb = data.addon_memory_mb || data.memory_usage || 0;
        const addonRamPct = typeof data.addon_memory_percent === 'number' ? data.addon_memory_percent : 0;
        const sysRamPct = typeof data.system_memory_percent === 'number' ? data.system_memory_percent : (typeof data.memory_percent === 'number' ? data.memory_percent : 0);

        addonRamHistory.push(addonRamPct);
        if (addonRamHistory.length > MAX_HISTORY) addonRamHistory.shift();
        sysRamHistory.push(sysRamPct);
        if (sysRamHistory.length > MAX_HISTORY) sysRamHistory.shift();

        // Update Header Badge (compact: addon CPU% · addon RAM MB)
        const headerCpu = document.getElementById('header-cpu');
        const headerRam = document.getElementById('header-ram');
        if (headerCpu) headerCpu.textContent = `${addonCpu.toFixed(1)}%`;
        if (headerRam) headerRam.textContent = `${Math.round(addonRamMb)}MB`;

        // Update Panel Legend Numbers
        const valAddonCpu = document.getElementById('val-addon-cpu');
        const valSysCpu = document.getElementById('val-sys-cpu');
        const valAddonRam = document.getElementById('val-addon-ram');
        const valSysRam = document.getElementById('val-sys-ram');

        if (valAddonCpu) valAddonCpu.textContent = `${addonCpu.toFixed(1)}%`;
        if (valSysCpu) valSysCpu.textContent = `${sysCpu.toFixed(1)}%`;
        if (valAddonRam) valAddonRam.textContent = `${addonRamMb}MB (${addonRamPct.toFixed(1)}%)`;
        if (valSysRam) valSysRam.textContent = `${data.used_memory_gb || 0}GB (${sysRamPct.toFixed(1)}%)`;

        // Update Panel Stat Boxes
        const pstatAddonRam = document.getElementById('pstat-addon-ram');
        const pstatSysRam = document.getElementById('pstat-sys-ram');
        const pstatUptime = document.getElementById('pstat-uptime');
        const pstatStream = document.getElementById('pstat-stream');

        if (pstatAddonRam) pstatAddonRam.textContent = `${addonRamMb} MB (${addonRamPct.toFixed(1)}%)`;
        if (pstatSysRam) pstatSysRam.textContent = `${data.used_memory_gb || 0}GB / ${data.total_memory_gb || 0}GB (${sysRamPct.toFixed(0)}%)`;
        if (pstatUptime) pstatUptime.textContent = formatUptime(data.uptime);
        if (pstatStream) {
          pstatStream.textContent = data.agy_stream_supported ? '✅ 지원 (Host 모드)' : '❌ 미지원 (kvm64)';
          pstatStream.style.color = data.agy_stream_supported ? 'var(--accent-green)' : 'var(--text-muted)';
        }

        // Mode 3 (CLI 모드) Conditional Enable/Disable
        cliModeSupported = !!data.agy_stream_supported;
        if (!cliModeSupported && currentStreamMode === '3') {
          currentStreamMode = '1';
          localStorage.setItem('antigravity_stream_mode', '1');
          updateStreamModeButton();
        }
        renderStreamModeList();

        if (isResourcePanelOpen) {
          renderCharts();
        }
      } catch (e) {}
    }

    // Engine Mode picker (stream_mode). Short label on the closed button,
    // full description per row when the dropdown is open -- same pattern as
    // the model picker.
    const ICON_ZAP_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>';
    const ICON_BRAIN_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 0 7 4.5v.5A2.5 2.5 0 0 0 4.5 7.5 2.5 2.5 0 0 0 3 9.9 2.5 2.5 0 0 0 4.5 14a2.5 2.5 0 0 0 2.5 2.5V19a2.5 2.5 0 0 0 5 0V4.5A2.5 2.5 0 0 0 9.5 2z"/><path d="M14.5 2A2.5 2.5 0 0 1 17 4.5v.5a2.5 2.5 0 0 1 2.5 2.5A2.5 2.5 0 0 1 21 9.9 2.5 2.5 0 0 1 19.5 14a2.5 2.5 0 0 1-2.5 2.5V19a2.5 2.5 0 0 1-5 0V4.5A2.5 2.5 0 0 1 14.5 2z"/></svg>';
    const ICON_TERMINAL_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>';
    const ICON_CHECK_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';

    const STREAM_MODES = [
      { value: '1', icon: ICON_ZAP_SVG, colorClass: 'mode-color-amber', shortName: '고속', name: '스마트홈 고속 제어', desc: '0.05초 네이티브 기기 즉시 제어 & 빠른 질의' },
      { value: '2', icon: ICON_BRAIN_SVG, colorClass: 'mode-color-purple', shortName: '복합', name: 'AI 딥 브레인', desc: '다차원 환경 분석 & 스마트 어드바이스' },
      { value: '3', icon: ICON_TERMINAL_SVG, colorClass: 'mode-color-sky', shortName: 'CLI', name: 'Antigravity CLI', desc: '공식 agy 0초 실시간 스트리밍 엔진' },
    ];
    let currentStreamMode = localStorage.getItem('antigravity_stream_mode') || '3';
    let cliModeSupported = true;

    function updateStreamModeButton() {
      const nameEl = document.getElementById('stream-mode-current');
      const iconEl = document.getElementById('stream-mode-icon');
      const m = STREAM_MODES.find(x => x.value === currentStreamMode) || STREAM_MODES[0];
      if (nameEl) nameEl.textContent = m.shortName;
      if (iconEl) { iconEl.innerHTML = m.icon; iconEl.className = `icon ${m.colorClass}`; }
    }

    function renderStreamModeList() {
      const list = document.getElementById('stream-mode-list');
      if (!list) return;
      list.innerHTML = STREAM_MODES.map(m => {
        const disabled = m.value === '3' && !cliModeSupported;
        const isActive = m.value === currentStreamMode;
        return `
          <div class="mode-row ${isActive ? 'active' : ''} ${disabled ? 'disabled' : ''}" ${disabled ? '' : `onclick="selectStreamMode('${m.value}')"`}>
            <div class="mode-row-left">
              <span class="icon ${m.colorClass}">${m.icon}</span>
              <span class="mode-row-name">${m.name}</span>
            </div>
            ${isActive ? `<span class="icon icon-sm mode-color-amber">${ICON_CHECK_SVG}</span>` : ''}
          </div>`;
      }).join('');
    }

    function selectStreamMode(value) {
      currentStreamMode = value;
      localStorage.setItem('antigravity_stream_mode', value);
      updateStreamModeButton();
      renderStreamModeList();
      closeStreamModePicker();
    }

    function toggleStreamModePicker() {
      const dropdown = document.getElementById('stream-mode-dropdown');
      if (!dropdown) return;
      const opening = !dropdown.classList.contains('open');
      closeModelPicker();
      const usagePanel = document.getElementById('usage-panel');
      if (usagePanel) usagePanel.classList.remove('open');
      dropdown.classList.toggle('open', opening);
    }

    function closeStreamModePicker() {
      const dropdown = document.getElementById('stream-mode-dropdown');
      if (dropdown) dropdown.classList.remove('open');
    }

    // Model / Effort Picker (Mode 3). There is no separate --effort flag --
    // effort is baked into the model slug itself (e.g. gemini-3.7-flash-high
    // vs -medium vs -low are three distinct slugs), so currentModelSlug here
    // is the picker's *group* id and currentEffort selects which of that
    // group's variant_slugs actually gets sent as --model.
    let modelCatalog = [];
    let familyLabels = {};
    let familyUsage = {};
    let dismissedQuotaKey = '';
    let currentModelSlug = localStorage.getItem('antigravity_model_slug') || '';
    let currentEffort = localStorage.getItem('antigravity_effort') || '';
    let policyDescription = '';
    const EFFORT_LABELS = { low: 'Low', medium: 'Medium', high: 'High' };

    function resolveCurrentModelSlug() {
      const model = modelCatalog.find(m => m.slug === currentModelSlug);
      if (!model) return currentModelSlug;
      const variants = model.variant_slugs || {};
      return variants[currentEffort] || variants[''] || Object.values(variants)[0] || model.slug;
    }

    function isFamilyWeeklyExhausted(family) {
      const stats = familyUsage[family];
      return !!stats && stats.weekly_remaining_pct === 0;
    }

    function formatResetTime(iso) {
      if (!iso) return '';
      try {
        return new Date(iso).toLocaleString('ko-KR', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
      } catch (e) {
        return iso;
      }
    }

    function capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''; }

    async function loadModelCatalog() {
      const list = document.getElementById('model-dropdown-list');
      try {
        const apiUrl = new URL('api/models', window.location.href).href;
        const res = await fetch(apiUrl);
        const data = await res.json();
        modelCatalog = data.models || [];
        familyLabels = data.family_labels || {};

        const knownSlugs = modelCatalog.map(m => m.slug);
        if (!currentModelSlug || knownSlugs.indexOf(currentModelSlug) === -1) {
          currentModelSlug = data.default_model || knownSlugs[0] || '';
        }
        const activeModel = modelCatalog.find(m => m.slug === currentModelSlug);
        if (activeModel && activeModel.efforts.indexOf(currentEffort) === -1) {
          currentEffort = activeModel.default_effort;
        }
        renderModelDropdownList();
        updateModelPickerButton();
      } catch (e) {
        if (list) list.innerHTML = '<div class="model-dropdown-error">⚠️ 모델 목록을 불러오지 못했습니다.</div>';
      }
    }

    function updateModelPickerButton() {
      const model = modelCatalog.find(m => m.slug === currentModelSlug);
      const nameEl = document.getElementById('model-picker-current');
      const effortEl = document.getElementById('model-picker-effort');
      if (nameEl) nameEl.textContent = model ? model.label : '모델 선택';
      if (effortEl) {
        if (model && model.efforts.length > 1) {
          effortEl.textContent = EFFORT_LABELS[currentEffort] || capitalize(currentEffort);
          effortEl.style.display = '';
        } else {
          effortEl.style.display = 'none';
        }
      }
    }

    const ICON_CHEVRON_RIGHT_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>';
    const ICON_INFO_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>';

    function renderModelDropdownList() {
      const list = document.getElementById('model-dropdown-list');
      if (!list) return;
      let html = '';
      modelCatalog.forEach(m => {
        const isActive = m.slug === currentModelSlug;
        const shownEffort = isActive ? currentEffort : m.default_effort;
        const hasEffortChoice = m.efforts.length > 1;
        const quotaExhausted = isFamilyWeeklyExhausted(m.family);
        const trailingIcon = hasEffortChoice
          ? `<button class="model-row-caret" onclick="toggleEffortFlyout(event, '${m.slug}')"><span class="icon">${ICON_CHEVRON_RIGHT_SVG}</span></button>`
          : isActive
          ? `<span class="model-row-check"><span class="icon">${ICON_CHECK_SVG}</span></span>`
          : `<span style="width:13px;display:inline-block;"></span>`;
        // A model with effort choices always opens the effort submenu on tap/click
        // (rather than immediately selecting its default effort and closing) --
        // hover still previews it on desktop, but touch has no hover at all, so
        // this is the only way to actually reach the effort options on mobile.
        const rowMainClick = hasEffortChoice ? `toggleEffortFlyout(event, '${m.slug}')` : `selectModel('${m.slug}')`;
        html += `
          <div class="model-row ${isActive ? 'active' : ''}">
            <div class="model-row-main" onclick="${rowMainClick}">
              <span class="model-row-name">${m.label}</span>
            </div>
            <div class="model-row-right">
              ${quotaExhausted ? '<span title="주간 할당량 소진">⚠️</span>' : ''}
              <span class="model-row-effort">${EFFORT_LABELS[shownEffort] || ''}</span>
              <span class="model-row-badge">${m.badge}<span class="icon">${ICON_INFO_SVG}</span></span>
              ${trailingIcon}
            </div>
            ${hasEffortChoice ? `
            <div class="effort-flyout" id="effort-flyout-${m.slug}">
              ${m.efforts.map(ef => `
                <div class="effort-option ${(isActive && currentEffort === ef) ? 'selected' : ''}" onclick="selectModelEffort(event, '${m.slug}', '${ef}')">
                  <span>${EFFORT_LABELS[ef]}</span>
                  ${(isActive && currentEffort === ef) ? `<span class="icon">${ICON_CHECK_SVG}</span>` : ''}
                </div>
              `).join('')}
            </div>` : ''}
          </div>`;
      });
      list.innerHTML = html;
    }

    function selectModel(slug) {
      const model = modelCatalog.find(m => m.slug === slug);
      if (!model) return;
      currentModelSlug = slug;
      currentEffort = model.default_effort;
      localStorage.setItem('antigravity_model_slug', currentModelSlug);
      localStorage.setItem('antigravity_effort', currentEffort);
      updateModelPickerButton();
      renderModelDropdownList();
      updateQuotaBanner();
      closeModelPicker();
    }

    function toggleEffortFlyout(evt, slug) {
      evt.stopPropagation();
      document.querySelectorAll('.effort-flyout.open').forEach(el => {
        if (el.id !== `effort-flyout-${slug}`) el.classList.remove('open');
      });
      const flyout = document.getElementById(`effort-flyout-${slug}`);
      if (flyout) flyout.classList.toggle('open');
    }

    function selectModelEffort(evt, slug, effort) {
      evt.stopPropagation();
      currentModelSlug = slug;
      currentEffort = effort;
      localStorage.setItem('antigravity_model_slug', currentModelSlug);
      localStorage.setItem('antigravity_effort', currentEffort);
      updateModelPickerButton();
      renderModelDropdownList();
      updateQuotaBanner();
      closeModelPicker();
    }

    function toggleModelPicker() {
      const dropdown = document.getElementById('model-dropdown');
      if (!dropdown) return;
      const opening = !dropdown.classList.contains('open');
      closeStreamModePicker();
      const usagePanel = document.getElementById('usage-panel');
      if (usagePanel) usagePanel.classList.remove('open');
      dropdown.classList.toggle('open', opening);
    }

    function closeModelPicker() {
      const dropdown = document.getElementById('model-dropdown');
      if (dropdown) dropdown.classList.remove('open');
      document.querySelectorAll('.effort-flyout.open').forEach(el => el.classList.remove('open'));
    }

    document.addEventListener('click', (e) => {
      const picker = document.getElementById('model-picker');
      if (picker && !picker.contains(e.target)) {
        closeModelPicker();
        const usagePanel = document.getElementById('usage-panel');
        if (usagePanel) usagePanel.classList.remove('open');
      }
      const streamPicker = document.getElementById('stream-mode-picker');
      if (streamPicker && !streamPicker.contains(e.target)) {
        closeStreamModePicker();
      }
    });

    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        startNewSession();
      }
    });

    let usagePanelCloseTimer = null;

    async function openUsagePanel() {
      clearTimeout(usagePanelCloseTimer);
      const panel = document.getElementById('usage-panel');
      if (!panel) return;
      panel.classList.add('open');
      // prefetchUsage() already keeps this panel rendered in the background
      // (see DOMContentLoaded / the 55s interval) -- only block on a fresh
      // fetch here if nothing has come back yet at all.
      if (Object.keys(familyUsage).length === 0) {
        await loadUsageSnapshot();
      }
    }

    function closeUsagePanel() {
      clearTimeout(usagePanelCloseTimer);
      usagePanelCloseTimer = setTimeout(() => {
        const panel = document.getElementById('usage-panel');
        if (panel) panel.classList.remove('open');
      }, 150);
    }

    function renderUsageBar(remainingPct, resetTime, label, windowKey, agyDescription) {
      // Matches the official Antigravity app's own usage panel: the gauge
      // shows *remaining* % (not used), as a small ring next to the number
      // rather than a big ring with the number inside it.
      const safeRemaining = (typeof remainingPct === 'number') ? Math.max(0, Math.min(100, remainingPct)) : null;
      const color = safeRemaining === null ? 'var(--text-muted)'
        : safeRemaining <= 15 ? 'var(--accent-red)'
        : safeRemaining <= 40 ? 'var(--accent-yellow)'
        : 'var(--accent-green)';
      // "N/A" (not "0%") when the account's response simply has no bucket
      // for this window at all -- distinct from an actual 0% remaining.
      const display = safeRemaining === null ? 'N/A' : `${safeRemaining}%`;
      const windowLabel = windowKey === 'weekly' ? '주간' : '5시간';
      // Prefer agy's own human-readable status line (has the real relative
      // refresh time, e.g. "will fully refresh in 6 days, 2 hours") over a
      // locally-generated one.
      const hint = agyDescription || (safeRemaining === null
        ? '이 계정 응답에는 해당 한도 정보가 없습니다.'
        : safeRemaining === 0
        ? `${windowLabel} 한도를 모두 사용했습니다.${resetTime ? ` ${formatResetTime(resetTime)}에 초기화됩니다.` : ''}`
        : `${windowLabel} 한도의 일부를 사용했습니다.`);
      return `
        <div class="usage-row">
          <div class="usage-row-label">
            <span>${label}</span>
            <span class="usage-row-hint">${hint}</span>
          </div>
          <div class="usage-row-gauge">
            <span class="usage-row-pct">${display}</span>
            <span class="usage-mini-ring" style="--pct: ${safeRemaining === null ? 0 : safeRemaining}; --ring-color: ${color};"></span>
          </div>
        </div>`;
    }

    function dismissQuotaBanner() {
      const banner = document.getElementById('quota-banner');
      if (banner) banner.style.display = 'none';
      dismissedQuotaKey = quotaKeyForCurrentModel();
    }

    function quotaKeyForCurrentModel() {
      const model = modelCatalog.find(m => m.slug === currentModelSlug);
      if (!model) return '';
      const stats = familyUsage[model.family];
      return `${model.family}:${stats ? stats.weekly_reset_time || '' : ''}`;
    }

    function updateQuotaBanner() {
      const banner = document.getElementById('quota-banner');
      const descEl = document.getElementById('quota-banner-desc');
      if (!banner || !descEl) return;
      const model = modelCatalog.find(m => m.slug === currentModelSlug);
      if (!model || !isFamilyWeeklyExhausted(model.family)) {
        banner.style.display = 'none';
        return;
      }
      const key = quotaKeyForCurrentModel();
      if (key === dismissedQuotaKey) return;
      const resetTime = familyUsage[model.family].weekly_reset_time;
      descEl.textContent = resetTime
        ? `이 모델의 주간 할당량을 모두 사용했습니다. ${formatResetTime(resetTime)}에 초기화됩니다.`
        : '이 모델의 주간 할당량을 모두 사용했습니다.';
      banner.style.display = 'flex';
    }

    function renderUsagePanelFromData(data) {
      const panel = document.getElementById('usage-panel');
      if (!panel) return;
      if (!data.available) {
        panel.innerHTML = `<div class="usage-panel-error">⚠️ 사용량 정보를 가져올 수 없습니다.<br>${data.reason || ''}</div>`;
        return;
      }
      familyUsage = data.families || {};
      policyDescription = data.policy_description || '';
      let html = '';
      const labels = data.family_labels || {};
      Object.keys(labels).forEach(fam => {
        const stats = familyUsage[fam] || {};
        html += `<div class="usage-family-title">${labels[fam]}</div>`;
        html += renderUsageBar(stats.weekly_remaining_pct, stats.weekly_reset_time, 'Weekly Limit Remaining', 'weekly', stats.weekly_description);
        html += renderUsageBar(stats.five_hour_remaining_pct, stats.five_hour_reset_time, 'Five Hour Limit Remaining', 'five_hour', stats.five_hour_description);
      });
      panel.innerHTML = html || '<div class="usage-panel-error">표시할 사용량 데이터가 없습니다.</div>';
      renderModelDropdownList();
      updateQuotaBanner();
    }


    // agy's own /usage refresh can take 10+ seconds, so warm the server-side
    // cache in the background instead of making the user wait every time
    // they open the panel -- see core/usage_client.py's _CACHE_TTL_SEC. Also
    // keeps the exhausted-model warning icons and the quota banner current
    // even while the usage panel itself is closed.
    async function prefetchUsage() {
      try {
        const apiUrl = new URL('api/usage', window.location.href).href;
        const res = await fetch(apiUrl);
        const data = await res.json();
        // Renders the (currently hidden) usage-panel content too, not just
        // the derived model warnings/banner -- so opening the panel later
        // shows this immediately instead of triggering its own fresh fetch.
        renderUsagePanelFromData(data);
      } catch (e) {}
    }

    async function loadUsageSnapshot() {
      const panel = document.getElementById('usage-panel');
      if (!panel) return;
      panel.innerHTML = '<div class="usage-panel-loading">사용량 불러오는 중...</div>';
      try {
        const apiUrl = new URL('api/usage', window.location.href).href;
        const res = await fetch(apiUrl);
        const data = await res.json();
        renderUsagePanelFromData(data);
      } catch (e) {
        panel.innerHTML = '<div class="usage-panel-error">⚠️ 사용량 조회 중 오류가 발생했습니다.</div>';
      }
    }

    // Session Management & History Restore
    let currentConversationId = localStorage.getItem('antigravity_active_conv_id') || '';
    let loadedHistorySteps = [];
    let currentHistoryRenderIndex = 0;
    const HISTORY_CHUNK_SIZE = 15;

    function toggleSessionSidebar() {
      const sidebar = document.getElementById('session-sidebar');
      const overlay = document.getElementById('sidebar-overlay');
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
      } else {
        sidebar.classList.toggle('collapsed');
      }
    }

    function decodeUnicodeString(str) {
      if (!str) return '';
      try {
        if (/\\\\u[0-9a-fA-F]{4}/.test(str)) {
          return str.replace(/\\\\u([0-9a-fA-F]{4})/g, function(match, hex) {
            return String.fromCharCode(parseInt(hex, 16));
          });
        }
      } catch (e) {}
      return str;
    }

    const ICON_CHECK_SQUARE_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>';
    const ICON_SQUARE_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>';
    const ICON_TRASH_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>';

    let sessionSelectMode = false;
    let selectedSessionIds = new Set();
    let lastLoadedSessionIds = [];

    function toggleSessionSelectMode() {
      sessionSelectMode = !sessionSelectMode;
      selectedSessionIds.clear();
      const btn = document.getElementById('session-select-btn');
      if (btn) btn.textContent = sessionSelectMode ? '완료' : '선택';
      loadSessionsList();
    }

    function updateSessionSelectToolbar() {
      const toolbar = document.getElementById('session-select-toolbar');
      const footer = document.getElementById('sidebar-footer');
      const allLabel = document.getElementById('session-select-all-label');
      const delBtn = document.getElementById('session-delete-btn');
      const delCount = document.getElementById('session-delete-count');
      if (toolbar) toolbar.style.display = sessionSelectMode ? 'flex' : 'none';
      if (footer) footer.style.display = sessionSelectMode ? 'none' : 'block';
      if (allLabel) allLabel.textContent = (selectedSessionIds.size > 0 && selectedSessionIds.size === lastLoadedSessionIds.length) ? '선택 해제' : '전체 선택';
      if (delBtn) delBtn.disabled = selectedSessionIds.size === 0;
      if (delCount) delCount.textContent = selectedSessionIds.size;
    }

    function selectAllSessions() {
      if (selectedSessionIds.size === lastLoadedSessionIds.length) {
        selectedSessionIds.clear();
      } else {
        lastLoadedSessionIds.forEach(id => selectedSessionIds.add(id));
      }
      loadSessionsList();
    }

    async function deleteSelectedSessions() {
      if (selectedSessionIds.size === 0) return;
      if (!confirm(`선택한 ${selectedSessionIds.size}개의 대화 기록을 삭제하시겠습니까?`)) return;
      try {
        const apiUrl = new URL('api/sessions', window.location.href).href;
        await fetch(apiUrl, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ conversation_ids: Array.from(selectedSessionIds) })
        });
      } catch (e) {}
      if (selectedSessionIds.has(currentConversationId)) startNewSession();
      selectedSessionIds.clear();
      sessionSelectMode = false;
      const btn = document.getElementById('session-select-btn');
      if (btn) btn.textContent = '선택';
      loadSessionsList();
    }

    async function deleteSingleSession(cid, evt) {
      if (evt) evt.stopPropagation();
      if (!confirm('이 대화 기록을 삭제하시겠습니까?')) return;
      try {
        const apiUrl = new URL('api/sessions/' + encodeURIComponent(cid), window.location.href).href;
        await fetch(apiUrl, { method: 'DELETE' });
      } catch (e) {}
      if (cid === currentConversationId) startNewSession();
      loadSessionsList();
    }

    async function loadSessionsList() {
      const listEl = document.getElementById('session-list');
      if (!listEl) return;
      try {
        const apiUrl = new URL('api/sessions', window.location.href).href;
        const res = await fetch(apiUrl);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const sessions = data.sessions || [];

        const titleEl = document.getElementById('session-list-title');
        if (titleEl) titleEl.textContent = `최근 대화 기록 (${sessions.length})`;
        const footerEl = document.getElementById('sidebar-footer');
        if (footerEl) footerEl.textContent = `총 ${sessions.length}개 세션`;
        const selectBtn = document.getElementById('session-select-btn');
        if (selectBtn) selectBtn.style.display = sessions.length > 0 ? '' : 'none';
        lastLoadedSessionIds = sessions.map(s => s.conversation_id);
        updateSessionSelectToolbar();

        if (sessions.length === 0) {
          listEl.innerHTML = "<div class='session-loading'>대화 기록이 없습니다.</div>";
          return;
        }

        listEl.innerHTML = '';
        sessions.forEach(sess => {
          const cid = sess.conversation_id;
          const isChecked = selectedSessionIds.has(cid);
          const card = document.createElement('div');
          card.className = `session-card ${cid === currentConversationId && !sessionSelectMode ? 'active' : ''} ${isChecked ? 'selected' : ''}`;
          card.setAttribute('data-cid', cid);
          card.onclick = sessionSelectMode
            ? () => toggleSessionSelected(cid, card)
            : () => openSession(cid);

          const displayTitle = decodeUnicodeString(sess.title || '새 대화');
          card.innerHTML = `
            ${sessionSelectMode ? `<span class="icon session-card-checkbox">${isChecked ? ICON_CHECK_SQUARE_SVG : ICON_SQUARE_SVG}</span>` : ''}
            <div class="session-card-body">
              <div class="session-card-title">${displayTitle}</div>
              <div class="session-card-meta"><span>${sess.date_str || ''}</span><span>·</span><span>${sess.turns}단계</span></div>
            </div>
            ${!sessionSelectMode ? `<button class="session-card-delete-btn" onclick="deleteSingleSession('${cid}', event)" title="대화 삭제"><span class="icon">${ICON_TRASH_SVG}</span></button>` : ''}
          `;
          listEl.appendChild(card);
        });
      } catch (err) {
        listEl.innerHTML = `<div class='session-loading' style='color: var(--accent-red);'>목록 로드 실패: ${err.message}</div>`;
      }
    }

    function toggleSessionSelected(cid, cardEl) {
      if (selectedSessionIds.has(cid)) {
        selectedSessionIds.delete(cid);
      } else {
        selectedSessionIds.add(cid);
      }
      cardEl.classList.toggle('selected', selectedSessionIds.has(cid));
      const iconEl = cardEl.querySelector('.session-card-checkbox');
      if (iconEl) iconEl.innerHTML = selectedSessionIds.has(cid) ? ICON_CHECK_SQUARE_SVG : ICON_SQUARE_SVG;
      updateSessionSelectToolbar();
    }

    function startNewSession() {
      currentConversationId = '';
      localStorage.removeItem('antigravity_active_conv_id');
      const box = document.getElementById('chat-box');
      box.innerHTML = `
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
      `;
      document.querySelectorAll('.session-card').forEach(c => c.classList.remove('active'));
      if (window.innerWidth <= 768) {
        toggleSessionSidebar();
      }
      document.getElementById('user-input').focus();
    }

    async function openSession(cid) {
      if (!cid) return;
      currentConversationId = cid;
      localStorage.setItem('antigravity_active_conv_id', cid);

      document.querySelectorAll('.session-card').forEach(c => {
        c.classList.toggle('active', c.getAttribute('data-cid') === cid);
      });

      if (window.innerWidth <= 768) {
        toggleSessionSidebar();
      }

      const box = document.getElementById('chat-box');
      box.innerHTML = "<div class='session-loading'>대화 히스토리 불러오는 중...</div>";

      try {
        const apiUrl = new URL(`api/sessions/${cid}`, window.location.href).href;
        const res = await fetch(apiUrl);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        loadedHistorySteps = data.history || [];

        box.innerHTML = '';
        if (loadedHistorySteps.length === 0) {
          box.innerHTML = "<div class='session-loading'>대화 내용이 비어 있습니다.</div>";
          return;
        }

        // Render latest chunk with pagination if long
        currentHistoryRenderIndex = Math.max(0, loadedHistorySteps.length - HISTORY_CHUNK_SIZE);

        if (currentHistoryRenderIndex > 0) {
          const loadMoreDiv = document.createElement('div');
          loadMoreDiv.id = 'history-load-more';
          loadMoreDiv.className = 'history-load-more';
          loadMoreDiv.innerHTML = `<button onclick="loadMoreHistory()">⬆️ 이전 대화 ${currentHistoryRenderIndex}개 더보기</button>`;
          box.appendChild(loadMoreDiv);
        }

        renderHistorySteps(currentHistoryRenderIndex, loadedHistorySteps.length);
        box.scrollTop = box.scrollHeight;
      } catch (err) {
        box.innerHTML = `<div class='session-loading' style='color: var(--accent-red);'>히스토리 로드 실패: ${err.message}</div>`;
      }
    }

    function cleanUserPromptString(str) {
      if (!str) return '';
      let text = str;
      const m = text.match(/<USER_REQUEST>([\\s\\S]*?)<\\/USER_REQUEST>/i);
      if (m && m[1]) {
        text = m[1].trim();
      } else {
        text = text.replace(/<[A-Z_]+>[\\s\\S]*?<\\/[A-Z_]+>/gi, '').trim();
      }
      return decodeUnicodeString(text);
    }

    function renderHistorySteps(fromIdx, toIdx, prepend = false) {
      const box = document.getElementById('chat-box');
      const loadMoreEl = document.getElementById('history-load-more');
      const fragment = document.createDocumentFragment();

      const slice = loadedHistorySteps.slice(fromIdx, toIdx);

      // Group interactions (USER_INPUT -> aggregated PLANNER_RESPONSES)
      let i = 0;
      while (i < slice.length) {
        const step = slice[i];
        if (step.type === 'USER_INPUT') {
          const row = document.createElement('div');
          row.className = 'msg-row user';
          const timeStr = step.created_at ? new Date(step.created_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }) : '';
          const cleanText = cleanUserPromptString(step.content || '');
          row.innerHTML = `
            <div class="bubble-wrap">
              <div class="bubble">${cleanText.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
              <div class="msg-meta user"><span class="meta-time">${timeStr}</span></div>
            </div>
          `;
          fragment.appendChild(row);
          i++;
        } else {
          // Gather ALL contiguous response/tool/planner steps until the next USER_INPUT
          let thinkingList = [];
          let toolCalls = [];
          let finalContent = '';
          let lastTimeStr = '';

          while (i < slice.length && slice[i].type !== 'USER_INPUT') {
            const cur = slice[i];
            if (cur.created_at) {
              lastTimeStr = new Date(cur.created_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
            }
            if (cur.thinking && typeof cur.thinking === 'string' && cur.thinking.trim()) {
              thinkingList.push(cur.thinking.trim());
            }
            if (cur.tool_calls && Array.isArray(cur.tool_calls)) {
              toolCalls = toolCalls.concat(cur.tool_calls);
            }
            if (cur.content && typeof cur.content === 'string' && cur.content.trim()) {
              finalContent = cur.content.trim();
            }
            i++;
          }

          const botRow = document.createElement('div');
          botRow.className = 'msg-row bot';

          let toolSectionHtml = '';
          if (thinkingList.length > 0 || toolCalls.length > 0) {
            let logLines = '';
            thinkingList.forEach(th => {
              logLines += `<div class="term-line"><span class="term-text think">💭 [추론] ${th.replace(/</g, "&lt;")}</span></div>`;
            });
            toolCalls.forEach(tc => {
              const tname = tc.name || 'tool';
              let act = '';
              if (tc.toolAction) act = tc.toolAction;
              else if (tc.toolSummary) act = tc.toolSummary;
              else if (tc.args) act = JSON.stringify(tc.args);
              logLines += `<div class="term-line"><span class="term-text tool">🔧 [도구] ${tname}: ${act.replace(/</g, "&lt;")}</span></div>`;
            });

            const totalCount = toolCalls.length + thinkingList.length;
            toolSectionHtml = `
              <details class="term-box" style="display: block; margin-bottom: 8px;">
                <summary class="term-header" style="cursor: pointer; list-style: none;">
                  <div class="term-dots"><span></span><span></span><span></span></div>
                  <span class="term-title">⚙️ 도구 실행 및 추론 로그 (${totalCount}건)</span>
                  <span class="term-badge done">클릭하여 펼치기/접기</span>
                </summary>
                <div class="term-body" style="max-height: 180px; overflow-y: auto;">
                  ${logLines}
                </div>
              </details>
            `;
          }

          const displayAnswer = finalContent || (toolCalls.length > 0 ? '작업이 완료되었습니다.' : '답변이 없습니다.');

          botRow.innerHTML = `
            <div class="bubble-wrap">
              <div class="bubble">
                ${toolSectionHtml}
                <div class="answer-content" data-raw="${displayAnswer.replace(/"/g, '&quot;')}">${formatMarkdown(displayAnswer)}</div>
              </div>
              <div class="msg-meta bot">
                <span class="meta-time">${lastTimeStr}</span>
                <span class="meta-latency">⚡ 복원됨</span>
              </div>
            </div>
          `;
          fragment.appendChild(botRow);
        }
      }

      if (prepend && loadMoreEl) {
        box.insertBefore(fragment, loadMoreEl.nextSibling);
      } else {
        box.appendChild(fragment);
      }
    }

    function loadMoreHistory() {
      const box = document.getElementById('chat-box');
      const loadMoreEl = document.getElementById('history-load-more');
      if (currentHistoryRenderIndex <= 0) {
        if (loadMoreEl) loadMoreEl.style.display = 'none';
        return;
      }

      const oldScrollHeight = box.scrollHeight;
      const oldScrollTop = box.scrollTop;

      const newFrom = Math.max(0, currentHistoryRenderIndex - HISTORY_CHUNK_SIZE);
      const newTo = currentHistoryRenderIndex;
      currentHistoryRenderIndex = newFrom;

      renderHistorySteps(newFrom, newTo, true);

      // Restore relative scroll position
      const newScrollHeight = box.scrollHeight;
      box.scrollTop = oldScrollTop + (newScrollHeight - oldScrollHeight);

      if (currentHistoryRenderIndex <= 0 && loadMoreEl) {
        loadMoreEl.style.display = 'none';
      } else if (loadMoreEl) {
        loadMoreEl.querySelector('button').textContent = `⬆️ 이전 대화 ${currentHistoryRenderIndex}개 더보기`;
      }
    }

    window.addEventListener('DOMContentLoaded', async () => {
      updateStreamModeButton();
      renderStreamModeList();
      const sessBadge = document.getElementById('session-tokens');
      if (sessBadge) sessBadge.textContent = sessionTotalTokens.toLocaleString();

      // Initial Status Poll & Load Session History List
      await pollStatus();
      await loadSessionsList();
      await loadModelCatalog();
      prefetchUsage();

      // Start 3-second Periodic Status Polling
      setInterval(pollStatus, 3000);
      // Keep the usage snapshot warm so opening "View Usage" feels instant
      setInterval(prefetchUsage, 55000);
    });

    function updateSendBtn() {
      const input = document.getElementById('user-input');
      const btn = document.getElementById('send-btn');
      const hasText = input.value.trim().length > 0;
      btn.classList.toggle('has-text', hasText);
      btn.disabled = !hasText;
    }

    // Voice input (Web Speech API) -- client-side only, no backend involved.
    let speechRecognition = null;
    let isRecording = false;

    function toggleRecording() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        alert('이 브라우저는 음성 인식(STT)을 지원하지 않습니다. Chrome 또는 Edge 브라우저를 권장합니다.');
        return;
      }
      const micBtn = document.getElementById('mic-btn');
      if (isRecording) {
        if (speechRecognition) speechRecognition.stop();
        isRecording = false;
        if (micBtn) micBtn.classList.remove('recording');
        return;
      }
      try {
        const recognition = new SpeechRecognition();
        recognition.lang = 'ko-KR';
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.onstart = () => {
          isRecording = true;
          if (micBtn) micBtn.classList.add('recording');
        };
        recognition.onresult = (event) => {
          const input = document.getElementById('user-input');
          const transcript = Array.from(event.results).map(r => r[0].transcript).join('');
          if (input) { input.value = transcript; updateSendBtn(); }
        };
        const stopRecording = () => {
          isRecording = false;
          if (micBtn) micBtn.classList.remove('recording');
        };
        recognition.onerror = stopRecording;
        recognition.onend = stopRecording;
        recognition.start();
        speechRecognition = recognition;
      } catch (e) {
        isRecording = false;
      }
    }

    function sendQuick(prompt) {
      const input = document.getElementById('user-input');
      input.value = prompt;
      updateSendBtn();
      sendMessage();
    }

    function handleKey(e) {
      updateSendBtn();
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    }

    async function sendMessage() {
      const input = document.getElementById('user-input');
      const btn = document.getElementById('send-btn');
      const streamMode = parseInt(currentStreamMode) || 1;
      const prompt = input.value.trim();
      if (!prompt) return;

      const hero = document.getElementById('chat-hero-card');
      if (hero) hero.remove();

      appendUserMessage(prompt);
      input.value = '';
      btn.disabled = true;
      updateSendBtn();

      const streamUI = createBotStreamMessage(streamMode);
      const isDirectLLM = prompt.startsWith('ai ') || prompt.startsWith('/llm');
      const isMobile = window.innerWidth < 768;

      try {
        const apiUrl = new URL('api/chat', window.location.href).href;
        const res = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: prompt,
            conversation_id: currentConversationId,
            is_direct_llm: isDirectLLM,
            stream_mode: streamMode,
            client_width: window.innerWidth,
            is_mobile: isMobile,
            model: resolveCurrentModelSlug()
          })
        });

        if (!res.ok) {
          streamUI.setText(`[오류] 서버 응답 코드 HTTP ${res.status}`);
          btn.disabled = false;
          updateSendBtn();
          return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split(/\\r?\\n/);
          buffer = lines.pop();

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || !trimmed.startsWith('data:')) continue;
            const jsonStr = trimmed.slice(5).trim();
            try {
              const ev = JSON.parse(jsonStr);
              if (ev.type === 'session_init') {
                currentConversationId = ev.content;
                localStorage.setItem('antigravity_active_conv_id', currentConversationId);
                loadSessionsList();
              } else if (ev.type === 'live_log' || ev.type === 'tool') {
                streamUI.addLiveLog(ev.content);
              } else if (ev.type === 'chunk') {
                streamUI.appendChunk(ev.content);
              } else if (ev.type === 'text') {
                streamUI.setText(ev.content);
              } else if (ev.type === 'done') {
                streamUI.finish(ev.tokens);
                loadSessionsList();
              }
            } catch (e) {}
          }
        }
        streamUI.finish();
      } catch (err) {
        if (!streamUI.hasContent()) {
          streamUI.setText(`[오류] 실시간 스트림 연결 실패: ${err.message}`);
        }
        streamUI.finish();
      } finally {
        btn.disabled = false;
        updateSendBtn();
        input.focus();
      }
    }
""".strip()
