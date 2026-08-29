"""Web UI HTML, CSS, and JS template module for Antigravity Dual Ingress with GitHub Dark/Light Markdown."""

HTML_INDEX = """<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Google Antigravity Smart Home</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root, [data-theme="dark"] {
      --bg-base: #0a0e17;
      --bg-card: #111827;
      --bg-bubble-user: #0284c7;
      --bg-bubble-bot: #162032;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --text-bold: #ffffff;
      --accent-blue: #38bdf8;
      --accent-cyan: #06b6d4;
      --accent-green: #10b981;
      --accent-yellow: #f59e0b;
      --accent-red: #ef4444;
      --border-color: rgba(255, 255, 255, 0.1);
      --border-subtle: rgba(255, 255, 255, 0.05);
      --code-bg: #090d16;
      --table-header: #1e293b;
      --table-stripe: rgba(255, 255, 255, 0.02);
      --badge-bg: rgba(56, 189, 248, 0.12);
      --badge-border: rgba(56, 189, 248, 0.25);
      --callout-tip-bg: rgba(56, 189, 248, 0.08);
      --callout-tip-border: #38bdf8;
      --callout-warn-bg: rgba(245, 158, 11, 0.1);
      --callout-warn-border: #f59e0b;
      --list-bullet: #38bdf8;
    }

    [data-theme="light"] {
      --bg-base: #f8fafc;
      --bg-card: #ffffff;
      --bg-bubble-user: #0284c7;
      --bg-bubble-bot: #ffffff;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --text-bold: #020617;
      --accent-blue: #0284c7;
      --accent-cyan: #0891b2;
      --accent-green: #059669;
      --accent-yellow: #d97706;
      --accent-red: #dc2626;
      --border-color: rgba(0, 0, 0, 0.1);
      --border-subtle: rgba(0, 0, 0, 0.04);
      --code-bg: #f1f5f9;
      --table-header: #f1f5f9;
      --table-stripe: rgba(0, 0, 0, 0.02);
      --badge-bg: rgba(2, 132, 199, 0.08);
      --badge-border: rgba(2, 132, 199, 0.2);
      --callout-tip-bg: rgba(2, 132, 199, 0.06);
      --callout-tip-border: #0284c7;
      --callout-warn-bg: rgba(217, 119, 6, 0.08);
      --callout-warn-border: #d97706;
      --list-bullet: #0284c7;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg-base);
      color: var(--text-main);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: background-color 0.2s ease, color 0.2s ease;
    }
    
    /* Header */
    header {
      background: var(--bg-card);
      border-bottom: 1px solid var(--border-color);
      padding: 10px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.1rem; }
    .brand-badge {
      background: var(--badge-bg);
      color: var(--accent-blue);
      font-size: 0.72rem;
      padding: 2px 8px;
      border-radius: 12px;
      border: 1px solid var(--badge-border);
      font-weight: 600;
    }
    
    .header-right {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .session-token-badge {
      font-size: 11px;
      background: var(--badge-bg);
      border: 1px solid var(--badge-border);
      color: var(--accent-blue);
      padding: 4px 10px;
      border-radius: 12px;
      font-weight: 600;
      white-space: nowrap;
    }

    .resource-badge {
      font-size: 11px;
      background: var(--badge-bg);
      border: 1px solid var(--badge-border);
      color: var(--accent-green);
      padding: 4px 10px;
      border-radius: 12px;
      font-weight: 600;
      white-space: nowrap;
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .resource-badge:hover {
      border-color: var(--accent-green);
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
    }
    .badge-pipe {
      color: var(--border-color);
      opacity: 0.8;
    }

    /* Sticky Top Resource Panel */
    .top-resource-panel {
      display: none;
      background: var(--bg-card);
      border-bottom: 1px solid var(--border-color);
      box-shadow: 0 4px 16px rgba(0,0,0,0.08);
      padding: 12px 20px;
      animation: panelSlide 0.2s ease-out;
      z-index: 50;
    }
    .top-resource-panel.open {
      display: block;
    }
    @keyframes panelSlide {
      0% { opacity: 0; transform: translateY(-8px); }
      100% { opacity: 1; transform: translateY(0); }
    }
    .panel-inner {
      max-width: 1080px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .panel-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--text-bold);
    }
    .panel-sub {
      font-size: 0.72rem;
      font-weight: 400;
      color: var(--text-muted);
    }
    .panel-close-btn {
      background: var(--bg-base);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      font-size: 0.76rem;
      font-weight: 600;
      cursor: pointer;
      padding: 3px 8px;
      border-radius: 6px;
      transition: all 0.15s ease;
    }
    .panel-close-btn:hover {
      color: var(--accent-blue);
      border-color: var(--accent-blue);
    }
    .panel-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    @media (max-width: 768px) {
      .panel-grid { grid-template-columns: 1fr; }
    }
    .chart-box {
      background: var(--bg-base);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 10px 14px;
    }
    .chart-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
      font-size: 0.78rem;
    }
    .chart-title {
      font-weight: 700;
      color: var(--text-bold);
    }
    .chart-legend {
      display: flex;
      gap: 8px;
      font-size: 0.73rem;
    }
    .lg-item {
      display: flex;
      align-items: center;
      gap: 3px;
    }
    .lg-purple { color: #c084fc; }
    .lg-blue { color: var(--accent-blue); }
    .lg-green { color: var(--accent-green); }
    .lg-cyan { color: #06b6d4; }

    .canvas-holder {
      width: 100%;
      height: 70px;
      position: relative;
    }
    .canvas-holder canvas {
      width: 100%;
      height: 100%;
      display: block;
    }
    .panel-stats {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
    }
    @media (max-width: 768px) {
      .panel-stats { grid-template-columns: 1fr 1fr; }
    }
    .pstat {
      background: var(--bg-base);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 6px 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.74rem;
    }
    .pstat span { color: var(--text-muted); }
    .pstat strong { color: var(--text-bold); }

    .theme-toggle-btn {
      background: var(--bg-base);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 5px 10px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.8rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.2s ease;
    }
    .theme-toggle-btn:hover {
      border-color: var(--accent-blue);
      color: var(--accent-blue);
    }

    .nav-tabs { display: flex; gap: 6px; }
    .tab-btn {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 5px 12px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.82rem;
      font-weight: 600;
      transition: all 0.2s ease;
    }
    .tab-btn.active {
      background: var(--accent-blue);
      color: #ffffff;
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
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .hero-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 14px;
      padding: 18px;
      margin-bottom: 4px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .hero-card h2 { font-size: 1.12rem; margin-bottom: 6px; color: var(--text-bold); font-weight: 700; }
    .hero-card p { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 12px; }
    .quick-chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip {
      background: var(--bg-base);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 5px 11px;
      border-radius: 14px;
      font-size: 0.78rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .chip:hover {
      background: var(--accent-blue);
      color: #ffffff;
      border-color: var(--accent-blue);
      transform: translateY(-1px);
    }

    /* Messages */
    .msg-row { display: flex; width: 100%; }
    .msg-row.user { justify-content: flex-end; }
    .msg-row.bot { justify-content: flex-start; }
    
    .bubble-wrap {
      display: flex;
      flex-direction: column;
      max-width: 88%;
      min-width: 280px;
    }
    .msg-row.user .bubble-wrap { align-items: flex-end; }
    .msg-row.bot .bubble-wrap { align-items: flex-start; }

    .bubble {
      width: 100%;
      padding: 14px 18px;
      border-radius: 12px;
      word-break: break-word;
      box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .msg-row.user .bubble {
      background: var(--bg-bubble-user);
      color: #ffffff;
      border-bottom-right-radius: 2px;
      font-size: 0.93rem;
      line-height: 1.5;
    }
    .msg-row.bot .bubble {
      background: var(--bg-bubble-bot);
      color: var(--text-main);
      border: 1px solid var(--border-color);
      border-bottom-left-radius: 2px;
    }

    /* Bot Bubble Header & View Toggle */
    .bubble-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 8px;
      margin-bottom: 10px;
      border-bottom: 1px solid var(--border-subtle);
    }
    .view-toggle-wrap {
      display: flex;
      gap: 4px;
      background: var(--bg-base);
      padding: 2px;
      border-radius: 6px;
      border: 1px solid var(--border-color);
    }
    .view-tab {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 0.73rem;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.15s ease;
    }
    .view-tab.active {
      background: var(--accent-blue);
      color: #ffffff;
    }
    .top-copy-btn {
      background: var(--bg-base);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 0.73rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.15s ease;
    }
    .top-copy-btn:hover {
      background: var(--badge-bg);
      color: var(--accent-blue);
      border-color: var(--accent-blue);
    }
    .top-copy-btn.copied {
      background: rgba(16, 185, 129, 0.15);
      color: var(--accent-green);
      border-color: var(--accent-green);
    }
    .raw-markdown-view {
      display: none;
      font-family: 'Fira Code', monospace;
      font-size: 0.83rem;
      line-height: 1.5;
      color: var(--text-main);
      background: var(--code-bg);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 12px;
      white-space: pre-wrap;
      word-break: break-all;
      overflow-x: auto;
      margin: 4px 0;
    }

    /* Header Mode Badge */
    .header-left-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .mode-badge {
      font-size: 0.72rem;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: 6px;
      background: var(--badge-bg);
      color: var(--accent-blue);
      border: 1px solid var(--badge-border);
      white-space: nowrap;
    }
    .mode-badge.fast {
      background: rgba(16, 185, 129, 0.12);
      color: var(--accent-green);
      border-color: rgba(16, 185, 129, 0.25);
    }
    .mode-badge.cli {
      background: rgba(168, 85, 247, 0.12);
      color: #c084fc;
      border-color: rgba(168, 85, 247, 0.3);
    }

    .live-progress-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.76rem;
      font-weight: 500;
      padding: 4px 10px;
      border-radius: 6px;
      background: rgba(59, 130, 246, 0.12);
      color: var(--accent-blue);
      border: 1px solid rgba(59, 130, 246, 0.3);
      margin-bottom: 8px;
      animation: pulseLive 2s infinite ease-in-out;
    }
    @keyframes pulseLive {
      0%, 100% { opacity: 0.95; transform: scale(1); }
      50% { opacity: 0.65; transform: scale(0.99); }
    }

    /* Message Metadata Footer */
    .msg-meta {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 6px;
      font-size: 0.72rem;
      color: var(--text-muted);
      padding: 0 2px;
    }
    .msg-meta.user { justify-content: flex-end; }
    
    .meta-latency {
      background: var(--badge-bg);
      color: var(--accent-blue);
      padding: 2px 7px;
      border-radius: 6px;
      font-weight: 600;
      border: 1px solid var(--badge-border);
    }

    .meta-tokens {
      color: var(--accent-blue);
      font-weight: 600;
      background: var(--badge-bg);
      padding: 2px 7px;
      border-radius: 6px;
      border: 1px solid var(--badge-border);
      white-space: nowrap;
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
      transition: all 0.15s ease;
    }
    .copy-btn:hover {
      background: var(--bg-base);
      color: var(--text-main);
      border-color: var(--accent-blue);
    }
    .copy-btn.copied {
      background: rgba(16, 185, 129, 0.15);
      color: var(--accent-green);
      border-color: var(--accent-green);
    }

    /* ==========================================================================
       GitHub Dark/Light Standard Markdown Typography & Elements
       ========================================================================== */
    .answer-content {
      font-size: 0.935rem;
      line-height: 1.65;
      color: var(--text-main);
    }

    .answer-content h1, .answer-content h2, .answer-content h3, .answer-content h4 {
      color: var(--text-bold);
      font-weight: 700;
      margin: 14px 0 8px 0;
      line-height: 1.35;
    }
    .answer-content h2 { font-size: 1.15rem; }
    .answer-content h3 { font-size: 1.02rem; }
    .answer-content p { margin: 6px 0; }

    .answer-content strong {
      color: var(--text-bold);
      font-weight: 600;
    }

    /* Nested Lists & Tree Hierarchy */
    .answer-content ul, .answer-content ol {
      margin: 6px 0 8px 0;
      padding-left: 22px;
    }
    .answer-content ul { list-style-type: disc; }
    .answer-content ul ul { list-style-type: circle; margin: 3px 0; padding-left: 18px; }
    .answer-content ul ul ul { list-style-type: square; margin: 2px 0; padding-left: 18px; }

    .answer-content li {
      margin-bottom: 4px;
      line-height: 1.6;
    }
    .answer-content li::marker {
      color: var(--list-bullet);
    }

    /* Callout & Alerts */
    .callout {
      border-left: 4px solid var(--callout-tip-border);
      background: var(--callout-tip-bg);
      padding: 10px 14px;
      border-radius: 0 8px 8px 0;
      margin: 10px 0;
      font-size: 0.88rem;
      line-height: 1.55;
    }
    .callout.warning {
      border-left-color: var(--callout-warn-border);
      background: var(--callout-warn-bg);
    }
    .callout strong { color: var(--text-bold); }

    /* Tables */
    .table-wrapper {
      width: 100%;
      overflow-x: auto;
      margin: 12px 0;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      background: var(--bg-base);
    }
    .bubble table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
      text-align: left;
    }
    .bubble th, .bubble td {
      border: 1px solid var(--border-color);
      padding: 8px 12px;
    }
    .bubble th {
      background: var(--table-header);
      color: var(--accent-blue);
      font-weight: 600;
    }
    .bubble tr:nth-child(even) {
      background: var(--table-stripe);
    }

    /* Code Blocks & Inline Code */
    .code-block-wrap {
      position: relative;
      margin: 10px 0;
      background: var(--code-bg);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      overflow: hidden;
    }
    .code-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--table-header);
      padding: 4px 10px;
      font-size: 0.74rem;
      color: var(--text-muted);
      font-family: 'Fira Code', monospace;
    }
    .code-copy-btn {
      background: transparent;
      border: none;
      color: var(--accent-blue);
      cursor: pointer;
      font-size: 0.72rem;
      padding: 2px 6px;
      border-radius: 4px;
    }
    .code-copy-btn:hover { background: var(--badge-bg); }
    .bubble pre {
      padding: 10px 12px;
      overflow-x: auto;
      font-size: 0.82rem;
      line-height: 1.45;
      margin: 0;
      font-family: 'Fira Code', monospace;
      color: var(--text-main);
    }
    .bubble code {
      font-family: 'Fira Code', monospace;
      font-size: 0.84rem;
      background: var(--code-bg);
      border: 1px solid var(--border-color);
      padding: 1px 5px;
      border-radius: 4px;
      color: var(--accent-cyan);
    }
    .bubble pre code {
      border: none;
      padding: 0;
      background: transparent;
      color: inherit;
    }

    /* Bottom Input Bar */
    .input-bar-wrap {
      background: var(--bg-card);
      border-top: 1px solid var(--border-color);
      padding: 10px 20px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex-shrink: 0;
    }
    .mode-bar {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 0.82rem;
      color: var(--text-muted);
    }
    .mode-select {
      background: var(--bg-base);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 500;
      outline: none;
      cursor: pointer;
    }
    .mode-select:focus { border-color: var(--accent-blue); }

    .input-bar {
      display: flex;
      gap: 10px;
      align-items: flex-end;
      background: var(--bg-base);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 8px 12px;
      transition: border-color 0.2s;
    }
    .input-bar:focus-within { border-color: var(--accent-blue); }
    textarea {
      flex: 1;
      background: transparent;
      border: none;
      color: var(--text-main);
      font-size: 0.92rem;
      font-family: inherit;
      resize: none;
      outline: none;
      max-height: 120px;
      line-height: 1.45;
    }
    .send-btn {
      background: var(--bg-bubble-user);
      border: none;
      color: #fff;
      width: 34px;
      height: 34px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 1.1rem;
      transition: all 0.15s ease-in-out;
      flex-shrink: 0;
    }
    .send-btn:disabled {
      opacity: 0.25 !important;
      cursor: not-allowed !important;
    }

    /* Terminal View */
    #terminal-view { height: 100%; display: none; width: 100%; }
    #terminal-view.active { display: block; }
    iframe { width: 100%; height: 100%; border: none; background: #000; }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span>🤖 Antigravity AI</span>
      <span class="brand-badge">Real-time</span>
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

  <main>
    <!-- Chat View -->
    <section id="chat-view" class="tab-view active">
      <div class="chat-container" id="chat-box">
        <div class="hero-card">
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

  <script>
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

      // 2. Multi-line Blockquotes & Callouts
      src = src.replace(/((?:^&gt;.*(?:\\r?\\n|$))+)/gm, function(match) {
        let lines = match.trim().split(/\\r?\\n/).map(l => l.replace(/^&gt;\\s?/, '').trim());
        let firstLine = lines[0] || '';
        let calloutType = 'tip';
        let icon = '💡';
        
        if (/^\\[!(WARNING|CAUTION|IMPORTANT)\\]/i.test(firstLine)) {
          calloutType = 'warning';
          icon = '⚠️';
          lines[0] = lines[0].replace(/^\\[!(WARNING|CAUTION|IMPORTANT)\\]\\s*/i, '');
        } else if (/^\\[!(NOTE|INFO|TIP)\\]/i.test(firstLine)) {
          calloutType = 'tip';
          icon = '💡';
          lines[0] = lines[0].replace(/^\\[!(NOTE|INFO|TIP)\\]\\s*/i, '');
        }
        
        let inner = lines.filter(l => l.length > 0).join('<br>');
        return '<div class="callout ' + calloutType + '"><strong>' + icon + '</strong> ' + inner + '</div>';
      });

      // 3. Fenced Code Blocks
      src = src.replace(/```([a-zA-Z0-9_-]*)\\r?\\n([\\s\\S]*?)```/g, function(match, lang, code) {
        const langStr = lang || 'text';
        return '<div class="code-block-wrap">' +
               '<div class="code-header"><span>' + langStr + '</span>' +
               '<button class="code-copy-btn" onclick="copyCodeBlock(this)">📋 복사</button></div>' +
               '<pre><code>' + code.trim() + '</code></pre></div>';
      });

      // 4. Tables
      src = src.replace(/\\|(.+)\\|\\r?\\n\\|[-|\\s:]+\\|\\r?\\n((?:\\|.*\\|\\r?\\n?)*)/g, function(match, header, rows) {
        let headers = header.split('|').map(h => h.trim()).filter(h => h);
        let rowLines = rows.trim().split(/\\r?\\n/);
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
      src = src.replace(/\\*\\*\\*(.*?)\\*\\*\\*/g, '<strong><em>$1</em></strong>');
      src = src.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
      src = src.replace(/\\*(.*?)\\*/g, '<em>$1</em>');

      // 6. Multi-level Nested Lists Parser
      let lines = src.split(/\\r?\\n/);
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
        let listMatch = line.match(/^(\\s*)([•\\-\\*]|\\d+\\.)\\s+(.*)$/);

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

      return out.join('<br>').replace(/(<\\/ul>|<div class="table-wrapper">.*<\\/div>|<div class="code-block-wrap">.*<\\/div>|<div class="callout.*?<\\/div>)<br>/g, '$1');
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
            <div class="live-progress-badge" style="display: none;">
              <span class="live-status-text"></span>
            </div>
            <div class="answer-content"><span style="color: var(--text-muted);">🤖 스마트홈 데이터 분석 중...</span></div>
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

      const liveBadge = row.querySelector('.live-progress-badge');
      const liveStatusText = row.querySelector('.live-status-text');
      const answerContent = row.querySelector('.answer-content');
      const rawCode = row.querySelector('.raw-markdown-view code');
      const latencyEl = row.querySelector('.meta-latency');
      const tokensEl = row.querySelector('.meta-tokens');

      let answerText = "";
      let finished = false;

      const liveTimer = setInterval(() => {
        if (finished) return;
        const elapsed = ((performance.now() - startTime) / 1000).toFixed(1);
        if (elapsed >= 1.0 && latencyEl) {
          latencyEl.textContent = `⏳ ${elapsed}초 분석 중...`;
          latencyEl.style.display = 'inline';
        }
      }, 100);

      return {
        addTool: function(toolStr) {
          if (liveBadge && liveStatusText) {
            liveStatusText.textContent = toolStr;
            liveBadge.style.display = 'inline-flex';
            box.scrollTop = box.scrollHeight;
          }
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
          if (liveBadge) {
            liveBadge.style.display = 'none';
          }
          const latency = ((performance.now() - startTime) / 1000).toFixed(2);
          if (latencyEl) {
            latencyEl.textContent = `⚡ ${latency}초`;
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

          const lines = buffer.split(/\\r?\\n/);
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
  </script>
</body>
</html>
"""
