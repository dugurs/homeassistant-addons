"""Web UI HTML, CSS, and JS template module for Antigravity Dual Ingress."""

HTML_INDEX = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Google Antigravity Smart Home</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-main: #0a0e17;
      --bg-card: #111827;
      --bg-bubble-user: #2563eb;
      --bg-bubble-bot: #1e293b;
      --accent-blue: #38bdf8;
      --accent-green: #10b981;
      --text-main: #f3f4f6;
      --text-muted: #94a3b8;
      --border-color: #334155;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-main);
      color: var(--text-main);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    
    /* Header */
    header {
      background: var(--bg-card);
      border-bottom: 1px solid var(--border-color);
      padding: 10px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }
    .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.1rem; }
    .brand-badge {
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent-blue);
      font-size: 0.72rem;
      padding: 2px 8px;
      border-radius: 12px;
      border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .nav-tabs { display: flex; gap: 6px; }
    .tab-btn {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 600;
      transition: all 0.2s;
    }
    .tab-btn.active {
      background: var(--accent-blue);
      color: #0f172a;
      border-color: var(--accent-blue);
    }

    /* Main Container */
    main { flex: 1; position: relative; overflow: hidden; }
    .tab-view { width: 100%; height: 100%; display: none; }
    .tab-view.active { display: flex; flex-direction: column; }

    /* Chat View */
    .chat-container {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .hero-card {
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 8px;
    }
    .hero-card h2 { font-size: 1.15rem; margin-bottom: 6px; color: var(--text-main); }
    .hero-card p { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 14px; }
    .quick-chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip {
      background: #1e293b;
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 6px 12px;
      border-radius: 16px;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.2s;
    }
    .chip:hover { background: var(--bg-bubble-user); border-color: var(--bg-bubble-user); transform: translateY(-1px); }

    /* Messages */
    .msg-row { display: flex; width: 100%; }
    .msg-row.user { justify-content: flex-end; }
    .msg-row.bot { justify-content: flex-start; }
    
    .bubble-wrap {
      display: flex;
      flex-direction: column;
      max-width: 85%;
    }
    .msg-row.user .bubble-wrap { align-items: flex-end; }
    .msg-row.bot .bubble-wrap { align-items: flex-start; }

    .bubble {
      width: 100%;
      padding: 12px 16px;
      border-radius: 14px;
      font-size: 0.92rem;
      line-height: 1.5;
      word-break: break-word;
    }
    .msg-row.user .bubble { background: var(--bg-bubble-user); color: #fff; border-bottom-right-radius: 2px; }
    .msg-row.bot .bubble {
      background: var(--bg-bubble-bot);
      color: var(--text-main);
      border: 1px solid var(--border-color);
      border-bottom-left-radius: 2px;
    }

    /* Message Metadata (Time, Latency, Copy) */
    .msg-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 5px;
      font-size: 0.72rem;
      color: var(--text-muted);
      padding: 0 4px;
    }
    .msg-meta.user { justify-content: flex-end; }
    
    .meta-latency {
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent-blue);
      padding: 1px 6px;
      border-radius: 6px;
      font-weight: 600;
    }

    .copy-btn {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 0.72rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.2s;
    }
    .copy-btn:hover {
      background: #1e293b;
      color: var(--text-main);
      border-color: var(--accent-blue);
    }
    .copy-btn.copied {
      background: rgba(16, 185, 129, 0.2);
      color: var(--accent-green);
      border-color: var(--accent-green);
    }

    /* Rich Markdown Styles */
    .table-wrapper {
      width: 100%;
      overflow-x: auto;
      margin: 12px 0;
      border: 1px solid var(--border-color);
      border-radius: 10px;
      background: #0f172a;
    }
    .bubble table {
      width: 100%;
      min-width: 380px;
      border-collapse: collapse;
      font-size: 0.85rem;
    }
    .bubble th, .bubble td {
      border: 1px solid var(--border-color);
      padding: 8px 12px;
      text-align: left;
    }
    .bubble th {
      background: #1e293b;
      color: var(--accent-blue);
      font-weight: 600;
    }
    .bubble tr:nth-child(even) {
      background: rgba(255, 255, 255, 0.02);
    }
    
    .code-block-wrap {
      position: relative;
      margin: 10px 0;
      background: #090d16;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      overflow: hidden;
    }
    .code-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #1e293b;
      padding: 4px 10px;
      font-size: 0.75rem;
      color: var(--text-muted);
      font-family: monospace;
    }
    .code-copy-btn {
      background: transparent;
      border: none;
      color: var(--accent-blue);
      cursor: pointer;
      font-size: 0.72rem;
      padding: 2px 6px;
      border-radius: 4px;
      transition: all 0.2s;
    }
    .code-copy-btn:hover {
      background: rgba(56, 189, 248, 0.2);
    }
    .bubble pre {
      padding: 10px 12px;
      overflow-x: auto;
      font-size: 0.82rem;
      line-height: 1.45;
      margin: 0;
      font-family: 'Fira Code', monospace;
      color: #e2e8f0;
    }
    .bubble code {
      font-family: 'Fira Code', monospace;
      color: var(--accent-blue);
      background: rgba(56, 189, 248, 0.1);
      padding: 2px 4px;
      border-radius: 4px;
      font-size: 0.85em;
    }
    .bubble pre code {
      background: transparent;
      padding: 0;
      color: inherit;
    }

    .callout {
      border-left: 4px solid var(--accent-blue);
      background: rgba(56, 189, 248, 0.08);
      padding: 10px 14px;
      border-radius: 0 8px 8px 0;
      margin: 10px 0;
      font-size: 0.88rem;
    }
    .callout.warning {
      border-left-color: #f59e0b;
      background: rgba(245, 158, 11, 0.08);
    }
    .callout.tip {
      border-left-color: #10b981;
      background: rgba(16, 185, 129, 0.08);
    }

    .bubble ul, .bubble ol {
      margin-left: 20px;
      margin-top: 6px;
      margin-bottom: 6px;
    }

    @media (max-width: 768px) {
      .bubble-wrap { max-width: 95%; }
      .bubble { padding: 10px 12px; font-size: 0.88rem; }
      .hero-card { padding: 14px; }
      .quick-chips { gap: 6px; }
      .chip { font-size: 0.75rem; padding: 4px 10px; }
    }

    /* Live Tool Accordion */
    .tool-box {
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid #334155;
      border-radius: 8px;
      margin-bottom: 10px;
      overflow: hidden;
      font-size: 0.82rem;
    }
    .tool-header {
      padding: 6px 12px;
      background: #1e293b;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      font-weight: 600;
      color: var(--accent-blue);
    }
    .tool-content { padding: 8px 12px; display: block; max-height: 250px; overflow-y: auto; color: var(--text-muted); font-family: monospace; }

    /* Input Area */
    .input-bar-wrap {
      background: var(--bg-card);
      border-top: 1px solid var(--border-color);
      padding: 10px 20px 14px 20px;
      flex-shrink: 0;
    }
    .mode-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
      padding: 0 4px;
      font-size: 0.78rem;
    }
    .mode-bar label {
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 500;
    }
    .mode-select {
      background: #1e293b;
      color: var(--accent-blue);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 4px 10px;
      font-size: 0.78rem;
      outline: none;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.2s;
    }
    .mode-select:hover {
      border-color: var(--accent-blue);
    }
    .mode-select option {
      background: #0f172a;
      color: var(--text-main);
    }
    .input-bar {
      display: flex;
      gap: 10px;
      background: var(--bg-main);
      border: 1px solid var(--border-color);
      border-radius: 24px;
      padding: 6px 12px 6px 16px;
      align-items: center;
    }
    .input-bar textarea {
      flex: 1;
      background: transparent;
      border: none;
      color: var(--text-main);
      font-size: 0.95rem;
      outline: none;
      resize: none;
      height: 24px;
      max-height: 100px;
      line-height: 1.5;
    }
    .send-btn {
      background: var(--bg-bubble-user);
      border: none;
      color: #fff;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      opacity: 0.4;
      font-size: 1.1rem;
      transition: all 0.2s ease-in-out;
    }
    .send-btn:hover:not(:disabled) {
      opacity: 1 !important;
      background: var(--accent-blue) !important;
      transform: scale(1.1) !important;
    }
    .send-btn:disabled {
      opacity: 0.2 !important;
      cursor: not-allowed !important;
    }

    /* Terminal View */
    #terminal-view { height: 100%; display: none; width: 100%; }
    #terminal-view.active { display: block; }
    iframe { width: 100%; height: 100%; border: none; background: #1e1e1e; }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span>🤖 Antigravity AI</span>
      <span class="brand-badge">Real-time Stream</span>
    </div>
    <div class="nav-tabs">
      <button class="tab-btn active" onclick="switchTab('chat')">💬 AI Chat</button>
      <button class="tab-btn" onclick="switchTab('terminal')">🖥️ Terminal</button>
    </div>
  </header>

  <main>
    <!-- Chat View -->
    <section id="chat-view" class="tab-view active">
      <div class="chat-container" id="chat-box">
        <div class="hero-card">
          <h2>Google Antigravity 스마트홈 실시간 어시스턴트</h2>
          <p>자연어 발화 및 Antigravity CLI AI 딥 브레인이 연동된 실시간 스트리밍 대시보드입니다.</p>
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
            <option value="1">📜 모드 1: Transcript 추적 (사고과정 & 도구호출 가시화)</option>
            <option value="2">🖥️ 모드 2: PTY 터미널 스트림 (실시간 터미널 렌더링)</option>
            <option value="3" selected>⚡ 모드 3: 하이브리드 고속 (스마트홈 0.05초 즉답)</option>
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

  <script>
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

    function formatMarkdown(text) {
      if (!text) return "";
      let raw = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      
      // Multi-line Callouts / Blockquotes
      raw = raw.replace(/((?:^&gt;.*(?:\n|$))+)/gm, function(match) {
        let lines = match.trim().split('\n').map(l => l.replace(/^&gt;\s?/, '').trim());
        let firstLine = lines[0] || '';
        let calloutType = 'tip';
        let icon = '💡';
        
        if (/^\[!(WARNING|CAUTION|IMPORTANT)\]/i.test(firstLine)) {
          calloutType = 'warning';
          icon = '⚠️';
          lines[0] = lines[0].replace(/^\[!(WARNING|CAUTION|IMPORTANT)\]\s*/i, '');
        } else if (/^\[!(NOTE|INFO|TIP)\]/i.test(firstLine)) {
          calloutType = 'tip';
          icon = '💡';
          lines[0] = lines[0].replace(/^\[!(NOTE|INFO|TIP)\]\s*/i, '');
        }
        
        let inner = lines.filter(l => l.length > 0).join('<br>');
        return `<div class="callout ${calloutType}"><strong>${icon}</strong> ${inner}</div>`;
      });

      // Code blocks with header & copy button
      raw = raw.replace(/```([a-zA-Z0-9_-]*)\\n([\\s\\S]*?)```/g, function(match, lang, code) {
        const langStr = lang || 'code';
        return `
          <div class="code-block-wrap">
            <div class="code-header">
              <span>${langStr}</span>
              <button class="code-copy-btn" onclick="copyCodeBlock(this)">📋 복사</button>
            </div>
            <pre><code>${code.trim()}</code></pre>
          </div>
        `;
      });

      // Inline code
      raw = raw.replace(/`([^`]+)`/g, '<code>$1</code>');

      // Responsive Tables wrapped in table-wrapper
      raw = raw.replace(/\\|(.+)\\|\\n\\|[-|\\s:]+\\|\\n((?:\\|.*\\|\\n?)*)/g, function(match, header, rows) {
        let headers = header.split('|').map(h => h.trim()).filter(h => h);
        let rowLines = rows.trim().split('\\n');
        let html = '<div class="table-wrapper"><table><thead><tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr></thead><tbody>';
        rowLines.forEach(r => {
          let cols = r.split('|').map(c => c.trim()).filter(c => c);
          if (cols.length) {
            html += '<tr>' + cols.map(c => `<td>${c}</td>`).join('') + '</tr>';
          }
        });
        html += '</tbody></table></div>';
        return html;
      });

      // Bold & Italic
      raw = raw.replace(/\\*\\*\\*(.*?)\\*\\*\\*/g, '<strong><em>$1</em></strong>');
      raw = raw.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
      raw = raw.replace(/\\*(.*?)\\*/g, '<em>$1</em>');

      // Task lists
      raw = raw.replace(/^\\s*[-*]\\s+\\[x\\]\\s*(.*)$/gim, '<li style="list-style:none;">☑️ $1</li>');
      raw = raw.replace(/^\\s*[-*]\\s+\\[ \\]\\s*(.*)$/gim, '<li style="list-style:none;">⬜ $1</li>');

      // Lists & bullets
      raw = raw.replace(/^[•\\-] (.*)$/gm, '<li>$1</li>');
      raw = raw.replace(/((?:<li>.*<\\/li>\\s*)+)/g, '<ul>$1</ul>');

      // Numbered lists
      raw = raw.replace(/^(\\d+)\\.\\s+(.*)$/gm, '<li><strong>$1.</strong> $2</li>');

      // Line breaks
      raw = raw.replace(/\\n/g, '<br>');
      return raw;
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

    function createBotStreamMessage() {
      const box = document.getElementById('chat-box');
      const row = document.createElement('div');
      const timeStr = getCurrentTimeStr();
      const startTime = performance.now();
      row.className = 'msg-row bot';
      row.innerHTML = `
        <div class="bubble-wrap">
          <div class="bubble">
            <div class="tool-box" style="display: none;">
              <div class="tool-header" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
                <span class="tool-title">🔍 AI 도구 호출 진행 중...</span>
                <span>▼</span>
              </div>
              <div class="tool-content"></div>
            </div>
            <div class="answer-content"><span style="color: var(--text-muted);">🤖 스마트홈 데이터 분석 중...</span></div>
          </div>
          <div class="msg-meta bot">
            <span class="meta-time">${timeStr}</span>
            <span class="meta-latency" style="display: none;"></span>
            <button class="copy-btn" onclick="copyMessage(this)">📋 복사</button>
          </div>
        </div>
      `;
      box.appendChild(row);
      box.scrollTop = box.scrollHeight;

      const toolBox = row.querySelector('.tool-box');
      const toolTitle = row.querySelector('.tool-title');
      const toolContent = row.querySelector('.tool-content');
      const answerContent = row.querySelector('.answer-content');
      const latencyEl = row.querySelector('.meta-latency');

      let toolList = [];
      let answerText = "";

      const liveTimer = setInterval(() => {
        const elapsed = ((performance.now() - startTime) / 1000).toFixed(1);
        if (elapsed >= 1.0 && latencyEl) {
          latencyEl.textContent = `⏳ ${elapsed}초 분석 중...`;
          latencyEl.style.display = 'inline';
        }
      }, 100);

      return {
        addTool: function(toolStr) {
          toolList.push(toolStr);
          toolBox.style.display = 'block';
          toolTitle.textContent = `🔍 AI 도구 호출 진행 중 (${toolList.length}단계)`;
          toolContent.innerHTML = toolList.map(t => '• ' + t.replace(/</g, "&lt;")).join('<br>');
          box.scrollTop = box.scrollHeight;
        },
        appendChunk: function(chunk) {
          answerText += chunk;
          answerContent.innerHTML = formatMarkdown(answerText);
          box.scrollTop = box.scrollHeight;
        },
        setText: function(text) {
          answerText = text;
          answerContent.innerHTML = formatMarkdown(answerText);
          box.scrollTop = box.scrollHeight;
        },
        finish: function() {
          clearInterval(liveTimer);
          const latency = ((performance.now() - startTime) / 1000).toFixed(2);
          if (latencyEl) {
            latencyEl.textContent = `⚡ ${latency}초`;
            latencyEl.style.display = 'inline';
          }
          if (toolList.length > 0) {
            toolTitle.textContent = `🔍 AI 도구 호출 완료 (${toolList.length}단계)`;
          }
          if (!answerText) {
            answerContent.innerHTML = "답변 작성을 완료했습니다.";
          }
          answerContent.setAttribute('data-raw', answerText);
          box.scrollTop = box.scrollHeight;
        }
      };
    }

    function onModeChange(val) {
      localStorage.setItem('antigravity_stream_mode', val);
    }

    window.addEventListener('DOMContentLoaded', () => {
      const savedMode = localStorage.getItem('antigravity_stream_mode') || '3';
      const sel = document.getElementById('stream-mode');
      if (sel) sel.value = savedMode;
    });

    function updateSendBtn() {
      const input = document.getElementById('user-input');
      const btn = document.getElementById('send-btn');
      const hasText = input.value.trim().length > 0;
      btn.style.opacity = hasText ? '1' : '0.4';
      btn.style.background = hasText ? '#38bdf8' : 'var(--bg-bubble-user)';
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
      const streamMode = modeSel ? parseInt(modeSel.value) : 3;
      const prompt = input.value.trim();
      if (!prompt) return;

      appendUserMessage(prompt);
      input.value = '';
      btn.disabled = true;
      updateSendBtn();

      const streamUI = createBotStreamMessage();
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

          const lines = buffer.split('\\n');
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
                streamUI.finish();
              }
            } catch (e) {}
          }
        }
        streamUI.finish();
      } catch (err) {
        streamUI.setText(`[오류] 실시간 스트림 연결 실패: ${err.message}`);
      } finally {
        btn.disabled = false;
        updateSendBtn();
        input.focus();
      }
    }
  </script>
</body>
</html>
"""
