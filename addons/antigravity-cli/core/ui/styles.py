"""Web UI CSS Stylesheet."""

CSS_STYLES = """
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
    
    /* Modern Slim Custom Scrollbar */
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: transparent;
    }
    ::-webkit-scrollbar-thumb {
      background: rgba(148, 163, 184, 0.25);
      border-radius: 4px;
      transition: background 0.2s ease;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: rgba(148, 163, 184, 0.45);
    }

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
    /* Header Buttons & Toggles */
    .sidebar-toggle-btn {
      background: var(--bg-base);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 1.1rem;
      transition: all 0.15s ease;
    }
    .sidebar-toggle-btn:hover {
      border-color: var(--accent-blue);
      color: var(--accent-blue);
    }
    .build-badge {
      background: rgba(148, 163, 184, 0.1);
      color: var(--text-muted);
      font-size: 0.7rem;
      font-family: 'Fira Code', monospace;
      padding: 2px 6px;
      border-radius: 6px;
      border: 1px solid var(--border-color);
      font-weight: 500;
    }
    .new-chat-btn-header {
      background: var(--badge-bg);
      border: 1px solid var(--badge-border);
      color: var(--accent-blue);
      font-size: 0.76rem;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.15s ease;
      margin-left: 4px;
    }
    .new-chat-btn-header:hover {
      background: var(--accent-blue);
      color: #ffffff;
    }

    /* App Layout (Sidebar + Main) */
    .app-layout {
      flex: 1;
      display: flex;
      position: relative;
      overflow: hidden;
    }

    /* Session Sidebar */
    .session-sidebar {
      width: 280px;
      background: var(--bg-card);
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      transition: margin-left 0.25s ease, transform 0.25s ease;
      z-index: 40;
    }
    .session-sidebar.collapsed {
      margin-left: -280px;
    }
    .sidebar-top {
      padding: 12px 14px;
      display: flex;
      gap: 8px;
      align-items: center;
      border-bottom: 1px solid var(--border-subtle);
    }
    .new-chat-btn-sidebar {
      flex: 1;
      background: var(--accent-blue);
      color: #ffffff;
      border: none;
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 0.84rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: opacity 0.15s ease;
    }
    .new-chat-btn-sidebar:hover { opacity: 0.9; }
    .sidebar-close-btn {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      width: 32px;
      height: 32px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.85rem;
    }
    .sidebar-section-title {
      padding: 10px 14px 6px;
      font-size: 0.74rem;
      font-weight: 700;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .refresh-sessions-btn {
      background: transparent;
      border: none;
      cursor: pointer;
      font-size: 0.85rem;
      opacity: 0.6;
    }
    .refresh-sessions-btn:hover { opacity: 1; }

    .session-list {
      flex: 1;
      overflow-y: auto;
      padding: 6px 8px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .session-loading {
      padding: 20px;
      text-align: center;
      font-size: 0.8rem;
      color: var(--text-muted);
    }
    .session-card {
      padding: 10px 12px;
      border-radius: 8px;
      border: 1px solid transparent;
      background: transparent;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      gap: 4px;
      transition: all 0.15s ease;
      text-align: left;
    }
    .session-card:hover {
      background: var(--table-stripe);
      border-color: var(--border-color);
    }
    .session-card.active {
      background: var(--badge-bg);
      border-color: var(--badge-border);
    }
    .session-card-title {
      font-size: 0.84rem;
      font-weight: 600;
      color: var(--text-bold);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .session-card-meta {
      display: flex;
      justify-content: space-between;
      font-size: 0.72rem;
      color: var(--text-muted);
    }

    /* Mobile Overlay */
    .sidebar-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.45);
      backdrop-filter: blur(2px);
      z-index: 35;
    }
    @media (max-width: 768px) {
      .session-sidebar {
        position: fixed;
        top: 0;
        bottom: 0;
        left: 0;
        transform: translateX(-100%);
        margin-left: 0 !important;
      }
      .session-sidebar.open {
        transform: translateX(0);
      }
      .sidebar-overlay.open {
        display: block;
      }
    }

    /* History Pagination Header */
    .history-load-more {
      display: flex;
      justify-content: center;
      padding: 8px 0;
    }
    .history-load-more button {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      font-size: 0.78rem;
      padding: 6px 14px;
      border-radius: 14px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .history-load-more button:hover {
      color: var(--accent-blue);
      border-color: var(--accent-blue);
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
    
    /* Thought & Tool Step Timeline Accordion */
    .thought-box {
      margin-bottom: 12px;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      background: var(--bg-base);
      overflow: hidden;
      transition: all 0.2s ease;
    }
    .thought-header {
      padding: 8px 12px;
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-muted);
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      user-select: none;
      background: var(--bg-base);
      outline: none;
    }
    .thought-header:hover {
      color: var(--accent-blue);
      background: var(--table-stripe);
    }
    .thought-title-wrap {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .thought-status-icon {
      font-size: 0.8rem;
      display: inline-block;
      animation: spinThought 1.5s linear infinite;
    }
    .thought-status-icon.done {
      animation: none;
    }
    @keyframes spinThought {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .step-timeline-list {
      list-style: none;
      padding: 6px 12px 10px 12px;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 6px;
      border-top: 1px solid var(--border-subtle);
    }
    .step-item {
      font-size: 0.76rem;
      color: var(--text-main);
      display: flex;
      align-items: flex-start;
      gap: 6px;
      line-height: 1.4;
      animation: stepFadeIn 0.25s ease-out;
    }
    @keyframes stepFadeIn {
      0% { opacity: 0; transform: translateY(3px); }
      100% { opacity: 1; transform: translateY(0); }
    }
    .step-bullet {
      color: var(--accent-blue);
      font-weight: bold;
      flex-shrink: 0;
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

    /* Terminal Log & Tool Steps Box */
    .term-box {
      background: var(--code-bg);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      margin-bottom: 8px;
      overflow: hidden;
    }
    .term-header {
      background: var(--table-header);
      padding: 6px 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--border-subtle);
      font-size: 0.74rem;
      user-select: none;
    }
    .term-dots {
      display: flex;
      gap: 4px;
    }
    .term-dots span, .term-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: rgba(148, 163, 184, 0.4);
    }
    .term-title {
      font-weight: 600;
      color: var(--text-bold);
      flex: 1;
      margin-left: 8px;
    }
    .term-badge {
      font-size: 0.68rem;
      padding: 1px 6px;
      border-radius: 4px;
      background: var(--badge-bg);
      color: var(--accent-blue);
    }
    .term-body {
      padding: 8px 12px;
      max-height: 220px;
      overflow-y: auto;
      overflow-x: hidden;
      font-family: 'Fira Code', monospace;
      font-size: 0.74rem;
      line-height: 1.45;
    }
    .term-line {
      display: flex;
      gap: 6px;
      margin-bottom: 4px;
      word-break: break-all;
      white-space: pre-wrap;
    }
    .term-time {
      color: var(--text-muted);
      opacity: 0.7;
      flex-shrink: 0;
    }
    .term-text {
      color: var(--text-main);
      flex: 1;
      word-break: break-all;
      white-space: pre-wrap;
    }
    .term-text.think { color: #c084fc; }
    .term-text.tool { color: var(--accent-cyan); }
    .term-text.file { color: var(--accent-yellow); }
    .term-text.cmd { color: var(--accent-blue); }
    .term-text.init { color: var(--accent-green); }
    .term-text.done { color: var(--accent-green); }
    .term-text.error { color: var(--accent-red); }

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

    .answer-content h1, .answer-content h2, .answer-content h3, .answer-content h4, .answer-content h5, .answer-content h6 {
      color: var(--text-bold);
      font-weight: 700;
      margin: 12px 0 6px 0;
      line-height: 1.35;
    }
    .answer-content h1 { font-size: 1.25rem; }
    .answer-content h2 { font-size: 1.15rem; }
    .answer-content h3 { font-size: 1.02rem; }
    .answer-content h4 { font-size: 0.94rem; }
    .answer-content h5 { font-size: 0.88rem; }
    .answer-content p { margin: 6px 0; }
    .answer-content hr {
      border: none;
      border-top: 1px solid var(--border-color);
      margin: 14px 0;
      opacity: 0.7;
    }

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

    /* Callout & Alerts & Real-time Terminal Badges */
    .callout {
      border-left: 3px solid var(--callout-tip-border);
      background: var(--callout-tip-bg);
      padding: 6px 12px;
      border-radius: 0 6px 6px 0;
      margin: 6px 0;
      font-size: 0.82rem;
      line-height: 1.45;
    }
    .callout.warning {
      border-left-color: var(--callout-warn-border);
      background: var(--callout-warn-bg);
    }
    .callout.thinking {
      border-left-color: #a855f7;
      background: rgba(168, 85, 247, 0.08);
      color: #d8b4fe;
      font-style: italic;
    }
    .callout.tool {
      border-left-color: #3b82f6;
      background: rgba(59, 130, 246, 0.08);
      color: #93c5fd;
      font-family: 'Fira Code', monospace;
      font-size: 0.80rem;
    }
    .callout.file {
      border-left-color: #14b8a6;
      background: rgba(20, 184, 166, 0.08);
      color: #5eead4;
      font-size: 0.80rem;
    }
    .callout.cmd {
      border-left-color: #f59e0b;
      background: rgba(245, 158, 11, 0.08);
      color: #fcd34d;
      font-family: 'Fira Code', monospace;
      font-size: 0.80rem;
    }
    .callout.init {
      border-left-color: #6366f1;
      background: rgba(99, 102, 241, 0.08);
      color: #a5b4fc;
      font-size: 0.82rem;
      font-weight: 600;
    }
    .callout.done {
      border-left-color: #10b981;
      background: rgba(16, 185, 129, 0.08);
      color: #6ee7b7;
      font-size: 0.80rem;
    }
    /* Terminal Console Window Box (Real-time Live Operation Stream) */
    .term-box {
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 8px;
      margin-bottom: 12px;
      overflow: hidden;
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.25);
    }
    .term-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #161b22;
      padding: 5px 10px;
      border-bottom: 1px solid #30363d;
      font-size: 0.70rem;
      color: #8b949e;
      font-family: 'Fira Code', Consolas, monospace;
      user-select: none;
    }
    .term-dots {
      display: flex;
      gap: 5px;
    }
    .term-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
    }
    .term-dot.red { background: #ff5f56; }
    .term-dot.yellow { background: #ffbd2e; }
    .term-dot.green { background: #27c93f; }
    .term-title {
      font-weight: 600;
      color: #c9d1d9;
      font-size: 0.72rem;
    }
    .term-badge {
      font-size: 0.65rem;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 10px;
      letter-spacing: 0.5px;
    }
    .term-badge.live {
      background: rgba(35, 134, 54, 0.2);
      color: #3fb950;
      border: 1px solid rgba(63, 185, 80, 0.3);
      animation: pulseLive 1.2s infinite ease-in-out;
    }
    .term-badge.done {
      background: rgba(110, 118, 129, 0.15);
      color: #8b949e;
      border: 1px solid #30363d;
    }
    .term-body {
      padding: 8px 12px;
      max-height: 180px;
      overflow-y: auto;
      font-family: 'Fira Code', Consolas, Monaco, monospace;
      font-size: 0.72rem;
      line-height: 1.4;
      color: #c9d1d9;
      background: #0d1117;
    }
    .term-body::-webkit-scrollbar {
      width: 5px;
    }
    .term-body::-webkit-scrollbar-thumb {
      background: #30363d;
      border-radius: 3px;
    }
    .term-line {
      display: flex;
      gap: 6px;
      margin-bottom: 2px;
      word-break: break-all;
    }
    .term-time {
      color: #6e7681;
      flex-shrink: 0;
      font-size: 0.68rem;
    }
    .term-text { flex: 1; }
    .term-text.init { color: #58a6ff; font-weight: 600; }
    .term-text.think { color: #d2a8ff; font-style: italic; }
    .term-text.tool { color: #79c0ff; }
    .term-text.file { color: #56d364; }
    .term-text.cmd { color: #e3b341; }
    .term-text.done { color: #3fb950; font-weight: 600; }
    .term-text.error { color: #f85149; }

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
""".strip()
