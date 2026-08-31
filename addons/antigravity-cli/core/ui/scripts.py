"""Web UI Frontend Client JavaScript Application."""

JS_SCRIPTS = """
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

        // Update Header Badge
        const headerCpu = document.getElementById('header-cpu');
        const headerRam = document.getElementById('header-ram');
        if (headerCpu) headerCpu.textContent = `⚙️ CPU: 애드온 ${addonCpu.toFixed(1)}% (전체 ${sysCpu.toFixed(1)}%)`;
        if (headerRam) headerRam.textContent = `💾 RAM: ${addonRamMb}MB (${addonRamPct.toFixed(1)}%) | 전체 ${sysRamPct.toFixed(0)}%`;

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

        // Mode 3 Conditional Enable/Disable
        const opt3 = document.getElementById('opt-mode-3');
        const modeSel = document.getElementById('stream-mode');
        if (opt3) {
          if (data.agy_stream_supported) {
            opt3.disabled = false;
            opt3.textContent = '🚀 모드 3: Google Antigravity Headless CLI (실시간 NDJSON)';
          } else {
            opt3.disabled = true;
            opt3.textContent = '🚀 모드 3: Google Antigravity (AVX 미지원으로 비활성화)';
            if (modeSel && modeSel.value === '3') {
              modeSel.value = '1';
              localStorage.setItem('antigravity_stream_mode', '1');
            }
          }
        }

        if (isResourcePanelOpen) {
          renderCharts();
        }
      } catch (e) {}
    }

    function onModeChange(val) {
      localStorage.setItem('antigravity_stream_mode', val);
    }

    window.addEventListener('DOMContentLoaded', async () => {
      const savedMode = localStorage.getItem('antigravity_stream_mode') || '1';
      const sel = document.getElementById('stream-mode');
      if (sel) sel.value = savedMode;
      const sessBadge = document.getElementById('session-tokens');
      if (sessBadge) sessBadge.textContent = sessionTotalTokens.toLocaleString();

      // Initial Status Poll
      await pollStatus();

      // Start 3-second Periodic Status Polling
      setInterval(pollStatus, 3000);
    });

    function updateSendBtn() {
      const input = document.getElementById('user-input');
      const btn = document.getElementById('send-btn');
      const hasText = input.value.trim().length > 0;
      btn.style.opacity = hasText ? '1' : '0.4';
      btn.style.background = hasText ? 'var(--accent-blue)' : 'var(--bg-bubble-user)';
      btn.style.transform = hasText ? 'scale(1.05)' : 'scale(1)';
      btn.style.cursor = hasText ? 'pointer' : 'default';
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

    let currentConversationId = localStorage.getItem('antigravity_active_conv_id') || '';

    async function sendMessage() {
      const input = document.getElementById('user-input');
      const btn = document.getElementById('send-btn');
      const modeSel = document.getElementById('stream-mode');
      const streamMode = modeSel ? parseInt(modeSel.value) : 1;
      const prompt = input.value.trim();
      if (!prompt) return;

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
            is_mobile: isMobile
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
              } else if (ev.type === 'live_log' || ev.type === 'tool') {
                streamUI.addLiveLog(ev.content);
              } else if (ev.type === 'chunk') {
                streamUI.appendChunk(ev.content);
              } else if (ev.type === 'text') {
                streamUI.setText(ev.content);
              } else if (ev.type === 'done') {
                streamUI.finish(ev.tokens);
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
