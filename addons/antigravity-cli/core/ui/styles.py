"""Web UI CSS Stylesheet."""

CSS_STYLES = """
/* Exact color tokens recovered from the rolled-back React/assistant-ui build
   (git history, orphaned commit) that the reference screenshots came from --
   not approximated from the screenshot, read directly out of its
   tailwind.config.js / index.css. --bg-card-high == that build's literal
   `bg-card` (#18181b, used for the composer/dropdowns); --bg-card here is
   its `bg-subtle` (#121215, used for header/sidebar). */
:root, [data-theme="dark"] {
      --bg-base: #09090b;
      --bg-card: #121215;
      --bg-card-high: #18181b;
      --bg-card-hover: #222227;
      --bg-bubble-user: #2563eb;
      --bg-bubble-bot: #18181b;
      --text-main: #f4f4f5;
      --text-muted: #a1a1aa;
      --text-dim: #71717a;
      --text-bold: #ffffff;
      --accent-blue: #38bdf8;
      --accent-cyan: #38bdf8;
      --accent-green: #10b981;
      --accent-yellow: #f59e0b;
      --accent-red: #ef4444;
      --accent-purple: #a855f7;
      --border-color: #27272a;
      --border-subtle: rgba(255, 255, 255, 0.08);
      --code-bg: #09090b;
      --table-header: #18181b;
      --table-stripe: rgba(255, 255, 255, 0.03);
      --badge-bg: rgba(56, 189, 248, 0.1);
      --badge-border: rgba(56, 189, 248, 0.3);
      --callout-tip-bg: rgba(56, 189, 248, 0.08);
      --callout-tip-border: #38bdf8;
      --callout-warn-bg: rgba(245, 158, 11, 0.1);
      --callout-warn-border: #f59e0b;
      --list-bullet: #38bdf8;
    }

    [data-theme="light"] {
      --bg-base: #ffffff;
      --bg-card: #f8fafc;
      --bg-card-high: #f1f5f9;
      --bg-card-hover: #e2e8f0;
      --bg-bubble-user: #2563eb;
      --bg-bubble-bot: #f1f5f9;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --text-dim: #94a3b8;
      --text-bold: #020617;
      --accent-blue: #0284c7;
      --accent-cyan: #0284c7;
      --accent-green: #059669;
      --accent-yellow: #d97706;
      --accent-red: #dc2626;
      --accent-purple: #9333ea;
      --border-color: #e2e8f0;
      --border-subtle: rgba(0, 0, 0, 0.06);
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
    
    /* Modern Slim Scrollbar */
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
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: var(--bg-base);
      color: var(--text-main);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: background-color 0.2s ease, color 0.2s ease;
    }

    .icon { display: inline-flex; width: 1em; height: 1em; }
    .icon svg { width: 100%; height: 100%; display: block; }
    .icon-btn-lg {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      background: transparent;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 17px;
      cursor: pointer;
      transition: all 0.15s ease;
      flex-shrink: 0;
    }
    .icon-btn-lg:hover { color: var(--text-main); border-color: var(--accent-blue); background: var(--bg-card-high); }
    .icon-amber { color: var(--accent-yellow); }
    .amber-text { color: var(--accent-yellow); }

    /* Compact icon-only button -- same family as .icon-btn-lg (header /
       left-menu / composer buttons) at a size that fits inline inside a chat
       bubble (message copy buttons, reasoning-log copy, view-toggle tabs). */
    .icon-btn-sm {
      width: 22px;
      height: 22px;
      border-radius: 6px;
      border: 1px solid var(--border-color);
      background: transparent;
      color: var(--text-muted);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.15s ease;
      flex-shrink: 0;
    }
    .icon-btn-sm .icon { width: 13px; height: 13px; }
    .icon-btn-sm:hover { color: var(--text-main); border-color: var(--accent-blue); background: var(--bg-card-high); }
    .icon-btn-sm.copied { color: var(--accent-green); border-color: var(--accent-green); background: rgba(16, 185, 129, 0.15); }

    /* Header */
    header {
      height: 48px;
      background: var(--bg-card);
      border-bottom: 1px solid var(--border-color);
      padding: 0 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
      overflow: hidden;
    }
    .brand { display: flex; align-items: center; gap: 8px; min-width: 0; }
    .brand-name {
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 700;
      font-size: 0.85rem;
      color: var(--text-bold);
      white-space: nowrap;
    }
    .brand-emoji { font-size: 1rem; flex-shrink: 0; }
    .brand-badge {
      background: rgba(56, 189, 248, 0.1);
      color: var(--accent-blue);
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 999px;
      border: 1px solid rgba(56, 189, 248, 0.3);
      font-weight: 600;
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
    }

    .header-stat-pill {
      font-size: 11px;
      background: var(--bg-card-high);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 4px 10px;
      border-radius: 999px;
      font-weight: 500;
      white-space: nowrap;
      display: flex;
      align-items: center;
      gap: 5px;
      cursor: pointer;
      transition: border-color 0.2s ease;
    }
    .header-stat-pill:hover { border-color: var(--accent-blue); }
    .header-stat-pill:hover {
      border-color: var(--accent-green);
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
    }
    .stat-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .stat-dot-green { background: var(--accent-green); }
    .stat-dot-blue { background: var(--accent-blue); }
    .stat-sep {
      color: var(--text-dim);
      opacity: 0.7;
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
    /* Charts stay side-by-side (one row) at every width -- only the header
       bar and the stat-box row were removed; on narrow screens everything
       inside just scales down instead of the charts stacking into 2 rows. */
    .panel-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
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
    @media (max-width: 768px) {
      .top-resource-panel { padding: 8px 10px; }
      .panel-grid { gap: 6px; }
      .chart-box { padding: 6px 8px; }
      .chart-top { margin-bottom: 3px; font-size: 0.62rem; }
      .chart-legend { gap: 4px; font-size: 0.58rem; }
      .canvas-holder { height: 40px; }
    }

    /* .icon-btn-lg (defined near the top) now covers both the theme toggle
       and sidebar toggle buttons -- same 32x32 rounded-lg icon-button shape
       in the recovered source. */
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
      padding: 10px 10px 4px;
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: space-between;
    }
    .sidebar-top .sidebar-nav-title { padding: 0; }
    .sidebar-new-chat-wrap { padding: 8px; display: flex; }
    .new-chat-btn-sidebar {
      flex: 1;
      width: 100%;
      box-sizing: border-box;
      background: var(--bg-card-high);
      color: var(--text-bold);
      border: 1px solid var(--border-color);
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.15s ease;
    }
    .new-chat-btn-sidebar:hover { background: var(--bg-card-hover); border-color: rgba(56, 189, 248, 0.5); }
    .new-chat-btn-sidebar .icon-blue { color: var(--accent-blue); }
    .new-chat-btn-sidebar .kbd-hint { margin-left: auto; }
    .kbd-hint {
      font-size: 10px;
      font-weight: 400;
      color: var(--text-dim);
      background: var(--bg-base);
      border: 1px solid var(--border-color);
      padding: 1px 6px;
      border-radius: 4px;
    }
    .sidebar-close-btn {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      width: 32px;
      height: 32px;
      border-radius: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
    }
    /* Desktop: sidebar stays open via the header hamburger, no separate close needed */
    @media (min-width: 769px) {
      .sidebar-close-btn { display: none; }
    }

    /* Sidebar Navigation (Chat / Terminal) */
    .sidebar-nav-title {
      padding: 8px 10px 4px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-dim);
    }
    .sidebar-nav {
      display: flex;
      flex-direction: column;
      gap: 2px;
      padding: 0 8px;
    }
    .sidebar-divider {
      height: 1px;
      background: var(--border-color);
      margin: 6px 12px;
    }
    .sidebar-nav-item {
      display: flex;
      align-items: center;
      gap: 8px;
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 6px 10px;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 500;
      cursor: pointer;
      text-align: left;
      transition: all 0.15s ease;
    }
    .sidebar-nav-item:hover { background: var(--bg-card-high); color: var(--text-main); }
    .sidebar-nav-item.active {
      background: var(--bg-card-high);
      border-color: var(--border-color);
      color: var(--accent-blue);
      font-weight: 700;
    }

    .sidebar-section-title {
      padding: 8px 10px 4px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-dim);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }
    .sidebar-section-title > span { flex: 1; }
    .session-select-btn {
      background: transparent;
      border: none;
      color: var(--accent-blue);
      font-size: 10px;
      font-weight: 600;
      cursor: pointer;
      text-transform: none;
      padding: 2px 6px;
      border-radius: 4px;
    }
    .session-select-btn:hover { background: var(--border-subtle); }

    .sidebar-bottom-slot { flex-shrink: 0; }
    .session-select-toolbar {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px;
      border-top: 1px solid var(--border-color);
    }
    .session-select-toolbar button {
      flex: 1;
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-dim);
      font-size: 11px;
      font-weight: 500;
      padding: 6px 8px;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      transition: all 0.15s ease;
    }
    .session-select-toolbar button:hover { color: var(--text-main); border-color: var(--text-muted); }
    .session-delete-btn {
      background: rgba(239, 68, 68, 0.1) !important;
      color: var(--accent-red) !important;
      border-color: rgba(239, 68, 68, 0.3) !important;
      font-weight: 600 !important;
    }
    .session-delete-btn:hover { background: rgba(239, 68, 68, 0.18) !important; }
    .session-delete-btn:disabled {
      background: var(--border-subtle) !important;
      color: var(--text-dim) !important;
      border-color: var(--border-color) !important;
      cursor: not-allowed;
      opacity: 0.6;
    }
    .sidebar-footer {
      padding: 8px;
      text-align: center;
      font-size: 10px;
      color: var(--text-dim);
      border-top: 1px solid var(--border-color);
    }

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
      position: relative;
      padding: 6px 10px;
      border-radius: 8px;
      border: 1px solid transparent;
      background: transparent;
      cursor: pointer;
      display: flex;
      align-items: flex-start;
      gap: 8px;
      transition: all 0.15s ease;
      text-align: left;
    }
    .session-card:hover {
      background: var(--bg-card-high);
      color: var(--text-main);
    }
    .session-card:hover .session-card-delete-btn { opacity: 1; }
    .session-card.active {
      background: var(--bg-card-high);
      border-color: var(--border-color);
      color: var(--accent-blue);
    }
    .session-card.active .session-card-title { color: var(--accent-blue); font-weight: 700; }
    .session-card.selected {
      background: rgba(56, 189, 248, 0.1);
      border-color: rgba(56, 189, 248, 0.3);
    }
    .session-card-checkbox {
      flex-shrink: 0;
      color: var(--accent-blue);
      width: 14px;
      height: 14px;
      margin-top: 1px;
    }
    .session-card-body {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .session-card-title {
      font-size: 0.78rem;
      font-weight: 500;
      color: var(--text-main);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    input.session-card-title-input {
      font-family: inherit;
      width: 100%;
      background: var(--bg-base);
      border: 1px solid var(--accent-blue);
      border-radius: 4px;
      padding: 1px 4px;
      outline: none;
    }
    .session-card-meta {
      font-size: 10px;
      color: var(--text-dim);
      display: flex;
      gap: 6px;
    }
    .session-card-delete-btn {
      flex-shrink: 0;
      opacity: 0;
      background: transparent;
      border: none;
      color: var(--text-dim);
      padding: 4px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .session-card-delete-btn:hover { color: var(--accent-red); background: rgba(239, 68, 68, 0.1); }

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
    .history-status-text {
      font-size: 0.78rem;
      color: var(--text-muted);
      padding: 6px 14px;
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
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 24px;
    }
    .hero-badge {
      display: inline-block;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: var(--accent-blue);
      font-size: 11px;
      font-weight: 600;
      padding: 2px 10px;
      border-radius: 999px;
      margin-bottom: 8px;
    }
    .hero-card h2 { font-size: 1.375rem; margin-bottom: 4px; color: var(--text-bold); font-weight: 700; letter-spacing: -0.01em; }
    .hero-card p { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 16px; }
    .quick-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      width: 100%;
      max-width: 32rem;
    }
    @media (max-width: 640px) {
      .quick-grid { grid-template-columns: repeat(2, 1fr); }
    }
    .quick-card {
      background: var(--bg-card-high);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 10px;
      font-size: 0.75rem;
      font-weight: 500;
      color: var(--text-main);
      cursor: pointer;
      text-align: left;
      transition: all 0.15s ease;
      font-family: inherit;
    }
    .quick-card:hover {
      background: var(--bg-card-hover);
      border-color: rgba(56, 189, 248, 0.5);
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
      border-radius: 20px;
      word-break: break-word;
      box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .bubble img {
      display: block;
      max-width: 240px;
      max-height: 240px;
      border-radius: 12px;
      margin: 4px 0;
      cursor: zoom-in;
      object-fit: cover;
    }
    .msg-row.user .bubble {
      background: var(--bg-bubble-user);
      color: #ffffff;
      border-bottom-right-radius: 6px;
      font-size: 0.93rem;
      line-height: 1.5;
    }
    .msg-row.bot .bubble {
      background: var(--bg-bubble-bot);
      color: var(--text-main);
      border: 1px solid var(--border-color);
      border-bottom-left-radius: 6px;
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
      padding: 4px 7px;
      border-radius: 4px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
    }
    .view-tab .icon { width: 13px; height: 13px; }
    .view-tab.active {
      background: var(--bg-bubble-user);
      color: #ffffff;
    }
    /* .top-copy-btn layers onto .icon-btn-sm (sizing/layout) -- this just
       overrides its resting color to match the segmented view-toggle next to it. */
    .top-copy-btn {
      background: var(--bg-base);
    }
    .top-copy-btn:hover {
      background: var(--badge-bg);
      color: var(--accent-blue);
      border-color: var(--accent-blue);
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

    /* ==========================================================================
       GitHub Dark/Light Standard Markdown Typography & Elements
       ========================================================================== */
    .answer-content {
      font-size: 0.875rem;
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
    .term-header-left {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }
    .term-header-right {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
    }
    .term-mode-tag {
      font-weight: 700;
      font-size: 0.68rem;
      white-space: nowrap;
    }
    .term-title {
      font-weight: 600;
      color: #c9d1d9;
      font-size: 0.72rem;
    }
    /* Icon-only copy button for the reasoning log itself -- term-box always
       renders in this fixed dark console palette regardless of app theme, so
       (unlike .icon-btn-sm elsewhere) this doesn't use the themed CSS vars. */
    .term-copy-btn {
      width: 18px;
      height: 18px;
      border-radius: 5px;
      border: 1px solid #30363d;
      background: transparent;
      color: #8b949e;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      flex-shrink: 0;
      transition: all 0.15s ease;
    }
    .term-copy-btn .icon { width: 11px; height: 11px; }
    .term-copy-btn:hover { color: #c9d1d9; border-color: #8b949e; background: rgba(255, 255, 255, 0.06); }
    .term-copy-btn.copied { color: #3fb950; border-color: #3fb950; background: rgba(35, 134, 54, 0.2); }
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
      overflow-x: auto;
      font-family: 'Fira Code', Consolas, Monaco, monospace;
      font-size: 0.72rem;
      line-height: 1.4;
      color: #c9d1d9;
      background: #0d1117;
    }
    .term-body::-webkit-scrollbar {
      width: 5px;
      height: 5px;
    }
    .term-body::-webkit-scrollbar-thumb {
      background: #30363d;
      border-radius: 3px;
    }
    /* Terminal-style lines don't wrap -- long tool-call args/commands scroll
       horizontally in .term-body instead, same as a real terminal. width:
       max-content lets a line grow past the box so overflow-x actually
       triggers; min-width:100% keeps short lines filling the width. */
    .term-line {
      display: flex;
      gap: 6px;
      margin-bottom: 2px;
      width: max-content;
      min-width: 100%;
    }
    .term-time {
      color: #6e7681;
      flex-shrink: 0;
      font-size: 0.68rem;
      white-space: nowrap;
    }
    .term-text {
      white-space: pre;
    }
    .term-text.init { color: #58a6ff; font-weight: 600; }
    .term-text.think { color: #d2a8ff; font-style: italic; }
    .term-text.tool { color: #79c0ff; }
    .term-text.file { color: #56d364; }
    .term-text.cmd { color: #e3b341; }
    .term-text.done { color: #3fb950; font-weight: 600; }
    .term-text.error { color: #f85149; }
    .diff-add { color: #3fb950; }
    .diff-del { color: #f85149; }

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
      background: var(--bg-base);
      padding: 10px 20px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex-shrink: 0;
    }
    /* Unified composer: textarea on top, toolbar (attach/mode/model/mic/send) below, one bordered box */
    .composer {
      position: relative;
      background: var(--bg-card-high);
      border: 1px solid var(--border-color);
      border-radius: 22px;
      padding: 12px;
      transition: border-color 0.2s;
    }
    .composer:focus-within { border-color: #3f3f46; }

    /* "/" slash-command autocomplete -- appears above the textarea while
       composing a command name (see updateSlashCommandMenu() in scripts.py),
       same visual family as .model-dropdown. */
    .slash-command-menu {
      display: none;
      position: absolute;
      bottom: calc(100% + 6px);
      left: 12px;
      right: 12px;
      max-width: 420px;
      max-height: 240px;
      overflow-y: auto;
      background: var(--bg-card-high);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      box-shadow: 0 8px 28px rgba(0,0,0,0.35);
      padding: 6px;
      z-index: 45;
      flex-direction: column;
      gap: 1px;
    }
    .slash-command-menu.open { display: flex; }
    .slash-command-row {
      display: flex;
      flex-direction: column;
      gap: 1px;
      border-radius: 8px;
      padding: 6px 10px;
      cursor: pointer;
    }
    .slash-command-row:hover, .slash-command-row.active { background: rgba(255, 255, 255, 0.05); }
    .slash-command-row .cmd {
      font-family: 'Fira Code', monospace;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-main);
    }
    .slash-command-row .desc { font-size: 0.72rem; color: var(--text-muted); }
    .composer-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-top: 2px;
    }
    .composer-toolbar-left, .composer-toolbar-right {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .icon-sm { font-size: 12px; }
    .icon-dim { color: var(--text-dim); }
    .mode-color-amber { color: var(--accent-yellow); }
    .mode-color-purple { color: var(--accent-purple); }
    .mode-color-sky { color: var(--accent-blue); }

    .attach-btn {
      width: 24px;
      height: 24px;
      border-radius: 999px;
      background: var(--bg-card-hover);
      border: none;
      color: var(--text-dim);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      flex-shrink: 0;
      transition: all 0.15s ease;
    }
    .attach-btn:hover { color: var(--text-main); }
    .attach-btn .icon { width: 14px; height: 14px; }
    .attach-btn.disabled { opacity: 0.35; cursor: not-allowed; }

    /* Pending attachment chips, shown above the textarea before sending (Mode 3 only) */
    .attach-preview-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding-bottom: 8px;
      margin-bottom: 8px;
      border-bottom: 1px dashed var(--border-color);
    }
    .attach-chip {
      position: relative;
      display: flex;
      align-items: center;
      gap: 6px;
      background: var(--bg-card-hover);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 4px 8px 4px 4px;
      max-width: 260px;
    }
    .attach-chip.attach-chip-error { border-color: var(--accent-red); }
    .attach-chip img {
      width: 28px;
      height: 28px;
      border-radius: 6px;
      object-fit: cover;
      flex-shrink: 0;
    }
    .attach-chip-file-icon { font-size: 16px; }
    .attach-chip-text {
      display: flex;
      flex-direction: column;
      min-width: 0;
      gap: 1px;
    }
    .attach-chip-name {
      font-size: 0.72rem;
      color: var(--text-main);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .attach-chip-status { font-size: 0.68rem; color: var(--text-dim); }
    .attach-chip-status-error {
      color: var(--accent-red);
      white-space: normal;
      line-height: 1.3;
    }
    .attach-chip-remove {
      background: none;
      border: none;
      color: var(--text-dim);
      cursor: pointer;
      font-size: 0.9rem;
      line-height: 1;
      padding: 0 2px;
    }
    .attach-chip-remove:hover { color: var(--accent-red); }

    /* Uploaded attachment thumbnails shown inside the user's own chat bubble */
    .bubble-attachments {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 6px;
      justify-content: flex-end;
    }
    .bubble-attachment-thumb {
      width: 64px;
      height: 64px;
      border-radius: 10px;
      object-fit: cover;
      border: 1px solid var(--border-color);
    }
    .bubble-attachment-file {
      font-size: 0.75rem;
      background: var(--bg-card-hover);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 4px 8px;
      color: var(--text-main);
    }

    .mic-btn, .send-btn {
      width: 28px;
      height: 28px;
      border-radius: 999px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      flex-shrink: 0;
      border: none;
      transition: all 0.15s ease;
    }
    .mic-btn { background: transparent; color: var(--text-dim); }
    .mic-btn:hover { color: var(--text-main); background: var(--bg-card-hover); }
    .mic-btn.recording { background: var(--accent-red); color: #fff; animation: mic-pulse 1.2s infinite; }
    @keyframes mic-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
    .mic-btn .icon { width: 15px; height: 15px; }

    .send-btn {
      background: var(--bg-card-hover);
      color: var(--text-dim);
      opacity: 0.7;
    }
    .send-btn:disabled { cursor: not-allowed; }
    .send-btn.has-text {
      background: #e4e4e7;
      color: #18181b;
      opacity: 1;
      cursor: pointer;
    }
    .send-btn.has-text:hover { background: #ffffff; }
    .send-btn .icon { width: 14px; height: 14px; }
    /* Mode 3 generation in flight -- send button doubles as a stop button
       (see updateSendBtn()/stopGeneration() in core/ui/scripts.py). */
    .send-btn.stopping {
      background: var(--accent-red);
      color: #fff;
      opacity: 1;
      cursor: pointer;
    }
    .send-btn.stopping:hover { background: #dc2626; }

    /* Model / Effort Picker (Mode 3), also reused by the Engine Mode picker */
    .model-picker {
      position: relative;
    }
    .mode-picker-btn {
      display: flex;
      align-items: center;
      gap: 5px;
      background: var(--bg-card-hover);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 4px 8px;
      border-radius: 8px;
      font-size: 0.72rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
    }
    .mode-picker-btn:hover { background: var(--bg-card-high); }
    .mode-picker-btn .icon { width: 12px; height: 12px; }
    .model-picker-name { font-weight: 600; }
    .model-effort-tag {
      color: var(--text-dim);
      font-family: ui-monospace, monospace;
      font-size: 11px;
    }
    /* Compact variant of .usage-mini-ring for the model-picker button --
       just the ring, no label/percentage, sized to match the button's own
       12px icons rather than the 16px used in the usage dropdown rows. */
    .model-picker-usage-ring {
      width: 8.8px;
      height: 8.8px;
    }
    .model-picker-usage-ring::before {
      inset: 1.1px; /* scaled down from the base 2px so the ring stays the same relative thickness */
    }

    .model-dropdown {
      display: none;
      position: absolute;
      bottom: calc(100% + 8px);
      left: 0;
      width: 256px;
      background: var(--bg-card-high);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      box-shadow: 0 8px 28px rgba(0,0,0,0.35);
      padding: 6px;
      z-index: 40;
      flex-direction: column;
      gap: 2px;
    }
    #stream-mode-dropdown.model-dropdown { width: 240px; }
    .model-dropdown.open { display: flex; }
    .model-dropdown-title {
      font-size: 11px;
      font-weight: 600;
      color: var(--text-dim);
      padding: 4px 10px;
    }
    .model-dropdown-list {
      /* Fixed 7-model catalog -- never needs to scroll. overflow-y:auto here
         would implicitly force overflow-x:auto too (CSS spec: visible
         computes to auto when the other axis is a scroll value), which
         clips the .effort-flyout popping out to the right of each row. */
      display: flex;
      flex-direction: column;
      gap: 1px;
    }
    .model-dropdown-loading, .model-dropdown-error, .usage-panel-loading, .usage-panel-error {
      padding: 10px 8px;
      font-size: 0.78rem;
      color: var(--text-muted);
      text-align: center;
    }

    /* Engine Mode rows (amber-selected, per the recovered source) */
    .mode-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 8px 10px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.8rem;
      color: var(--text-muted);
      transition: all 0.15s ease;
    }
    .mode-row:hover { background: rgba(255, 255, 255, 0.06); color: var(--text-main); }
    .mode-row.active { background: rgba(245, 158, 11, 0.2); color: #fcd34d; font-weight: 600; }
    .mode-row.disabled { opacity: 0.3; cursor: not-allowed; }
    .mode-row-left { display: flex; align-items: center; gap: 8px; min-width: 0; }
    .mode-row-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

    /* Model rows */
    .model-row {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      border-radius: 8px;
      padding: 6px 10px;
      cursor: pointer;
      font-size: 0.8rem;
      color: var(--text-muted);
      transition: background 0.15s ease;
    }
    .model-row:hover { background: rgba(255, 255, 255, 0.05); color: var(--text-main); }
    .model-row.active { background: var(--bg-card-hover); color: var(--text-main); }
    .model-row.disabled { opacity: 0.4; }
    .model-row.disabled .model-row-main { cursor: not-allowed; }
    .model-row-main {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      min-width: 0;
    }
    .model-row-name {
      flex: 1;
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .model-row-right { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
    .model-row-effort {
      font-size: 10px;
      color: var(--text-dim);
      font-family: ui-monospace, monospace;
    }
    .model-row-badge {
      display: inline-flex;
      align-items: center;
      gap: 2px;
      font-size: 9px;
      font-weight: 600;
      padding: 1px 5px;
      border-radius: 4px;
      background: var(--bg-card-hover);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      white-space: nowrap;
    }
    .model-row-badge .icon { width: 8px; height: 8px; opacity: 0.6; }
    .model-row-caret {
      background: transparent;
      border: none;
      color: var(--text-dim);
      display: flex;
      cursor: pointer;
      padding: 2px;
    }
    .model-row:hover .model-row-caret { color: var(--text-muted); }
    .model-row-caret .icon { width: 13px; height: 13px; }
    .model-row-check .icon { width: 13px; height: 13px; color: var(--text-main); }

    .effort-flyout {
      display: none;
      position: absolute;
      left: calc(100% + 6px);
      top: 0;
      min-width: 100px;
      background: var(--bg-card-high);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      box-shadow: 0 8px 28px rgba(0,0,0,0.35);
      padding: 6px;
      z-index: 50;
    }
    .effort-flyout.open,
    .model-row:hover .effort-flyout { display: block; }
    /* Narrow screens: there's no room to the right of a 256px-wide dropdown
       -- drop the flyout below the row instead, right-aligned so it stays
       inside the dropdown's own bounds. */
    @media (max-width: 640px) {
      .effort-flyout {
        left: auto;
        right: 0;
        top: 100%;
        margin-top: 4px;
      }
    }
    .effort-option {
      padding: 6px 10px;
      font-size: 0.78rem;
      border-radius: 8px;
      cursor: pointer;
      color: var(--text-muted);
      white-space: nowrap;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .effort-option:hover { background: rgba(255, 255, 255, 0.06); color: var(--text-main); }
    .effort-option.selected { background: var(--bg-card-hover); color: var(--accent-blue); font-weight: 700; }
    .effort-option .icon { width: 13px; height: 13px; }

    .usage-view-row {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      margin-top: 4px;
      padding: 6px 10px;
      border-top: 1px solid var(--border-color);
      color: var(--text-dim);
      font-size: 0.78rem;
      cursor: default;
      border-radius: 0 0 8px 8px;
    }
    .usage-view-row:hover { background: rgba(255, 255, 255, 0.05); color: var(--text-main); }
    .usage-view-row > span:first-child { display: flex; align-items: center; gap: 6px; }
    .usage-view-row .icon { width: 13px; height: 13px; }

    .usage-panel {
      display: none;
      position: absolute;
      bottom: calc(100% + 8px);
      left: calc(100% + 8px);
      width: 260px;
      background: var(--bg-card-high);
      border: 1px solid var(--border-color);
      border-radius: 20px;
      box-shadow: 0 8px 28px rgba(0,0,0,0.35);
      padding: 10px;
      z-index: 40;
    }
    .usage-panel.open { display: block; }
    /* Narrow screens: popping out to the right of the picker runs off-screen
       -- pin it near the bottom of the viewport instead, independent of the
       picker's own position, so it's always fully visible. */
    @media (max-width: 640px) {
      .usage-panel {
        position: fixed;
        left: 12px;
        right: 12px;
        bottom: 90px;
        top: auto;
        width: auto;
      }
    }
    .usage-family-title {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-muted);
      padding: 6px 4px 4px;
    }
    .usage-family-title:not(:first-child) { border-top: 1px solid var(--border-color); margin-top: 4px; }
    .usage-credits-line {
      font-size: 0.75rem;
      color: var(--text-main);
      padding: 2px 4px 8px;
    }
    .usage-credits-line a { color: var(--accent-blue); }
    .usage-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 5px 4px;
    }
    .usage-row-label {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }
    .usage-row-label > span:first-child {
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-main);
    }
    .usage-row-hint {
      font-size: 0.66rem;
      color: var(--text-muted);
    }
    .usage-row-gauge {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
    }
    .usage-row-pct {
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--text-main);
      min-width: 2.4em;
      text-align: right;
    }
    .usage-mini-ring {
      --pct: 0;
      --ring-color: var(--accent-green);
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: conic-gradient(var(--ring-color) calc(var(--pct) * 1%), var(--border-color) 0);
      position: relative;
      flex-shrink: 0;
    }
    .usage-mini-ring::before {
      content: '';
      position: absolute;
      inset: 2px;
      border-radius: 50%;
      background: var(--bg-card);
    }

    /* Model row: quota-exhausted warning + selected checkmark */
    .model-row-warning { font-size: 0.72rem; flex-shrink: 0; }
    .model-row-check {
      color: var(--accent-blue);
      font-weight: 700;
      font-size: 0.85rem;
      flex-shrink: 0;
      margin-left: 2px;
    }

    /* Baseline quota-reached banner (above the mode/model bar) */
    .quota-banner {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      background: rgba(245, 158, 11, 0.1);
      border: 1px solid var(--callout-warn-border, var(--accent-yellow));
      border-radius: 16px;
      padding: 10px 12px;
    }
    .quota-banner-icon { font-size: 1rem; line-height: 1.3; }
    .quota-banner-body { flex: 1; min-width: 0; }
    .quota-banner-title {
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 2px;
    }
    .quota-banner-desc {
      font-size: 0.76rem;
      color: var(--text-muted);
      line-height: 1.4;
    }
    .quota-banner-dismiss {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-main);
      font-size: 0.75rem;
      padding: 4px 10px;
      border-radius: 6px;
      cursor: pointer;
      flex-shrink: 0;
    }
    .quota-banner-dismiss:hover { background: var(--border-subtle); }

    textarea {
      display: block;
      width: 100%;
      background: transparent;
      border: none;
      color: var(--text-main);
      font-size: 0.875rem;
      font-family: inherit;
      resize: none;
      outline: none;
      min-height: 26px;
      max-height: 120px;
      line-height: 1.5;
      padding: 2px 4px;
    }
    textarea::placeholder { color: var(--text-dim); }

    .toast-msg {
      position: fixed;
      left: 50%;
      bottom: 90px;
      transform: translateX(-50%) translateY(8px);
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 0.8rem;
      font-weight: 500;
      box-shadow: 0 6px 20px rgba(0,0,0,0.3);
      opacity: 0;
      transition: opacity 0.2s ease, transform 0.2s ease;
      z-index: 200;
      pointer-events: none;
    }
    .toast-msg.show { opacity: 1; transform: translateX(-50%) translateY(0); }

    /* Terminal View */
    #terminal-view { height: 100%; display: none; width: 100%; position: relative; }
    #terminal-view.active { display: block; }
    iframe { width: 100%; height: 100%; border: none; background: #000; }

    /* "agy를 실행하시겠습니까?" prompt shown on entering the terminal tab,
       instead of dropping straight into the bare bash cursor. */
    .terminal-confirm-overlay {
      position: absolute;
      inset: 0;
      z-index: 5;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.55);
    }
    .terminal-confirm-box {
      background: var(--bg-card-high);
      border: 1px solid var(--border-color);
      border-radius: 14px;
      padding: 20px 24px;
      text-align: center;
      box-shadow: 0 8px 28px rgba(0,0,0,0.4);
    }
    .terminal-confirm-box p {
      color: var(--text-main);
      font-size: 0.95rem;
      font-weight: 600;
      margin: 0 0 14px 0;
    }
    .terminal-confirm-actions {
      display: flex;
      gap: 10px;
      justify-content: center;
    }
    .terminal-confirm-actions button {
      padding: 6px 22px;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--border-color);
    }
    .terminal-confirm-yes {
      background: var(--accent-blue);
      color: #fff;
      border-color: var(--accent-blue);
    }
    .terminal-confirm-no {
      background: var(--bg-base);
      color: var(--text-main);
    }

    /* Click-to-enlarge lightbox for any image inside a chat bubble */
    .image-lightbox-overlay {
      position: fixed;
      inset: 0;
      z-index: 60;
      display: none;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.85);
      cursor: zoom-out;
    }
    .image-lightbox-overlay.open { display: flex; }
    .image-lightbox-overlay img {
      max-width: 92vw;
      max-height: 92vh;
      border-radius: 8px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.6);
    }

    /* Help / Feedback modal (header info button) */
    .help-overlay {
      position: fixed;
      inset: 0;
      z-index: 50;
      display: none;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.55);
    }
    .help-overlay.open { display: flex; }
    .help-box {
      background: var(--bg-card-high);
      border: 1px solid var(--border-color);
      border-radius: 14px;
      padding: 22px 24px;
      width: min(420px, 90vw);
      box-shadow: 0 8px 28px rgba(0,0,0,0.4);
    }
    .help-box-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
    }
    .help-box-top h3 { margin: 0; font-size: 1rem; color: var(--text-bold); }
    .help-box-close {
      background: none;
      border: none;
      color: var(--text-dim);
      cursor: pointer;
      padding: 2px;
    }
    .help-section { margin-bottom: 14px; }
    .help-section h4 {
      margin: 0 0 6px;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-dim);
    }
    .help-section ul {
      margin: 0;
      padding-left: 18px;
      font-size: 0.85rem;
      color: var(--text-main);
      line-height: 1.7;
    }
    .help-section a {
      color: var(--accent-blue);
      text-decoration: none;
      font-size: 0.85rem;
    }
    .help-section a:hover { text-decoration: underline; }
""".strip()
