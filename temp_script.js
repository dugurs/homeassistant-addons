
    // Theme Management
    function initTheme() {
      const savedTheme = localStorage.getItem('antigravity_theme') || 'dark';
      document.documentElement.setAttribute('data-theme', savedTheme);
      updateThemeBtn(savedTheme);
    }

    function toggleTheme() {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('antigravity_theme', next);
      updateThemeBtn(next);
    }

    function updateThemeBtn(theme) {
      const btn = document.getElementById('theme-toggle-btn');
      if (btn) {
        btn.innerHTML = theme === 'dark' ? '🌙 다크' : '☀️ 라이트';
      }
    }

    initTheme();

    function switchTab(tab) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-view').forEach(v => v.classList.remove('active'));
      if (tab === 'chat') {
        document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
        document.getElementById('chat-view').classList.add('active');
      } else {
        document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
        document.getElementById('terminal-view').classList.add('active');
      }
    }

    function copyCodeBlock(btn) {
      const code = btn.closest('.code-block-wrap').querySelector('code').innerText;
      navigator.clipboard.writeText(code).then(() => {
        btn.textContent = '✓ 복사완료';
        setTimeout(() => { btn.textContent = '📋 복사'; }, 2000);
      });
    }

    // =========================================================================
    // Robust Standard GFM Markdown Formatter with Nested Lists & Callouts
    // =========================================================================
    function formatMarkdown(text) {
      if (!text) return "";
      
      // 1. Escape HTML
      let src = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

      // 2. Multi-line Blockquotes & Terminal Callouts
      src = src.replace(/((?:^&gt;.*(?:\r?\n|$))+)/gm, function(match) {
        let lines = match.trim().split(/\r?\n/).map(l => l.replace(/^&gt;\s?/, '').trim());
        let firstLine = lines[0] || '';
        let calloutType = 'tip';
        
        if (firstLine.includes('💭') || firstLine.includes('[추론]')) {
          calloutType = 'thinking';
        } else if (firstLine.includes('🔧') || firstLine.includes('[HA 도구]') || firstLine.includes('[도구')) {
          calloutType = 'tool';
        } else if (firstLine.includes('📄') || firstLine.includes('[파일')) {
          calloutType = 'file';
        } else if (firstLine.includes('⚙️') || firstLine.includes('[명령어')) {
          calloutType = 'cmd';
        } else if (firstLine.includes('🚀') || firstLine.includes('[Antigravity')) {
          calloutType = 'init';
        } else if (firstLine.includes('✅') || firstLine.includes('[완료]')) {
          calloutType = 'done';
        } else if (/^\[!(WARNING|CAUTION|IMPORTANT)\]/i.test(firstLine)) {
          calloutType = 'warning';
          lines[0] = lines[0].replace(/^\[!(WARNING|CAUTION|IMPORTANT)\]\s*/i, '⚠️ ');
        } else if (/^\[!(NOTE|INFO|TIP)\]/i.test(firstLine)) {
          calloutType = 'tip';
          lines[0] = lines[0].replace(/^\[!(NOTE|INFO|TIP)\]\s*/i, '💡 ');
        }
        
        let inner = lines.filter(l => l.length > 0).join('<br>');
        return '<div class="callout ' + calloutType + '">' + inner + '</div>';
      });

      // 3. Fenced Code Blocks
      src = src.replace(/```([a-zA-Z0-9_-]*)\r?\n([\s\S]*?)```/g, function(match, lang, code) {
        const langStr = lang || 'text';
        return '<div class="code-block-wrap">' +
               '<div class="code-header"><span>' + langStr + '</span>' +
               '<button class="code-copy-btn" onclick="copyCodeBlock(this)">📋 복사</button></div>' +
               '<pre><code>' + code.trim() + '</code></pre></div>';
      });

      // 4. Tables
      src = src.replace(/\|(.+)\|\r?\n\|[-|\s:]+\|\r?\n((?:\|.*\|\r?\n?)*)/g, function(match, header, rows) {
        let headers = header.split('|').map(h => h.trim()).filter(h => h);
        let rowLines = rows.trim().split(/\r?\n/);
        let html = '<div class="table-wrapper"><table><thead><tr>' + headers.map(h => '<th>' + h + '</th>').join('') + '</tr></thead><tbody>';
        rowLines.forEach(r => {
          let cols = r.split('|').map(c => c.trim()).filter(c => c);
          if (cols.length) {
            html += '<tr>' + cols.map(c => '<td>' + c + '</td>').join('') + '</tr>';
          }
        });
        html += '</tbody></table></div>';
        return html;
      });

      // 5. Bold & Italic & Inline Code
      src = src.replace(/`([^`]+)`/g, '<code>$1</code>');
      src = src.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
      src = src.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      src = src.replace(/\*(.*?)\*/g, '<em>$1</em>');

      // 6. Multi-level Nested Lists Parser
      let lines = src.split(/\r?\n/);
      let out = [];
      let listStack = []; // stores indent levels

      function closeLists(targetLevel) {
        while (listStack.length > targetLevel) {
          listStack.pop();
          out.push('</ul>');
        }
      }

      for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        let listMatch = line.match(/^(\s*)([•\-\*]|\d+\.)\s+(.*)$/);

        if (listMatch) {
          let indentSpaces = listMatch[1].length;
          let content = listMatch[3];
          let level = Math.floor(indentSpaces / 2) + 1;

          if (level > listStack.length) {
            out.push('<ul>');
            listStack.push(level);
          } else if (level < listStack.length) {
            closeLists(level);
          }

          out.push('<li>' + content + '</li>');
        } else {
          closeLists(0);
          if (line.trim().length > 0) {
            out.push(line);
          }
        }
      }
      closeLists(0);

      return out.join('<br>').replace(/(<\/ul>|<div class="table-wrapper">.*<\/div>|<div class="code-block-wrap">.*<\/div>|<div class="callout.*?<\/div>)<br>/g, '$1');
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
            <div class="answer-content"><span style="color: var(--text-muted); animation: pulseLive 1.5s infinite ease-in-out;">⚡ Antigravity CLI 실시간 스트림 연결 중...</span></div>
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

      const answerContent = row.querySelector('.answer-content');
      const rawCode = row.querySelector('.raw-markdown-view code');
      const latencyEl = row.querySelector('.meta-latency');
      const tokensEl = row.querySelector('.meta-tokens');

      let answerText = "";
      let finished = false;

      const liveTimer = setInterval(() => {
        if (finished) return;
        const elapsed = ((performance.now() - startTime) / 1000).toFixed(1);
        if (elapsed >= 0.5 && latencyEl) {
          latencyEl.textContent = `⏳ ${elapsed}초 실시간 처리 중...`;
          latencyEl.style.display = 'inline';
        }
      }, 100);

      return {
        addTool: function(toolStr) {
          // Tool info is now directly delivered via inline chunks in real-time
        },
        appendChunk: function(chunk) {
          answerText += chunk;
          answerContent.innerHTML = formatMarkdown(answerText);
          if (rawCode) rawCode.textContent = answerText;
          box.scrollTop = box.scrollHeight;
        },
        setText: function(text) {
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
          if (!answerText) {
            answerContent.innerHTML = "답변 작성을 완료했습니다.";
            if (rawCode) rawCode.textContent = "답변 작성을 완료했습니다.";
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

          const lines = buffer.split(/\r?\n/);
          buffer = lines.pop();

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || !trimmed.startsWith('data:')) continue;
            const jsonStr = trimmed.slice(5).trim();
            try {
              const ev = JSON.parse(jsonStr);
              if (ev.type === 'tool') {
                streamUI.addTool(ev.content);
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
  