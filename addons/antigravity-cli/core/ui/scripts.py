"""Web UI Frontend Client JavaScript Application."""

JS_SCRIPTS = """
function showToast(text) {
      let toast = document.getElementById('global-toast');
      if (!toast) {
        toast = document.createElement('div');
        toast.id = 'global-toast';
        toast.className = 'toast-msg';
        document.body.appendChild(toast);
      }
      toast.textContent = text;
      toast.classList.add('show');
      clearTimeout(toast._hideTimer);
      toast._hideTimer = setTimeout(() => toast.classList.remove('show'), 2000);
    }

    function notSupportedYet(feature) {
      showToast(`${feature} 기능은 아직 지원되지 않습니다.`);
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
        closeSidebarForTerminalMode();
        const overlay = document.getElementById('terminal-confirm-overlay');
        if (overlay) overlay.style.display = 'flex';
      }
    }

    // "agy를 실행하시겠습니까?" Yes/No shown on entering the terminal tab
    // (see switchTab above), instead of landing straight on the bash cursor.
    // Yes types `agy` + Enter into the same persistent tmux session ttyd is
    // attached to (server-side, via /api/terminal/run_agy) -- exactly what
    // the user would've typed by hand. No just dismisses the prompt.
    async function confirmRunAgy(shouldRun) {
      const overlay = document.getElementById('terminal-confirm-overlay');
      if (overlay) overlay.style.display = 'none';
      if (!shouldRun) return;
      try {
        const apiUrl = new URL('api/run_agy', window.location.href).href;
        await fetch(apiUrl, { method: 'POST' });
      } catch (e) {}
    }

    // Terminal mode wants the full width -- close the left session sidebar
    // (collapsed on desktop, slid-out on mobile) the same way its own close
    // controls would, rather than leaving it open over the terminal.
    function closeSidebarForTerminalMode() {
      const sidebar = document.getElementById('session-sidebar');
      if (!sidebar) return;
      if (window.innerWidth <= 768) {
        sidebar.classList.remove('open');
        const overlay = document.getElementById('sidebar-overlay');
        if (overlay) overlay.classList.remove('open');
      } else {
        sidebar.classList.add('collapsed');
      }
    }

    const ICON_MOON_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    const ICON_SUN_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';

    // Icon set for the chat bubbles -- same Lucide-equivalent inline-SVG,
    // stroke=currentColor style as the composer/left-menu icons in
    // core/ui/templates.py (that file can't be reused directly here since
    // these are swapped in dynamically at runtime, not baked into initial HTML).
    const ICON_COPY_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
    // ICON_CHECK_SVG already declared further below (model/agent picker
    // checkmarks) -- reused here for copy-button feedback, see flashCopied().
    const ICON_EYE_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
    const ICON_CODE_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>';
    const ICON_STOP_SVG = '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';
    // Restored history bubbles only (see buildUserRow) -- "되돌리기": rewinds
    // the conversation back to this message, see rewindToStep().
    const ICON_REWIND_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7"/><polyline points="3 4 3 9 8 9"/></svg>';
    const ICON_ARROW_UP_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>';

    function toggleTheme() {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('antigravity_theme', next);
      const icon = document.getElementById('theme-toggle-icon');
      if (icon) icon.innerHTML = next === 'dark' ? ICON_MOON_SVG : ICON_SUN_SVG;
    }

    // MCP status is cached from the /api/status poll that's already running
    // (see pollStatus()); skills/hooks are fetched once, lazily, the first
    // time the Help modal actually opens (static-ish data, no need to poll).
    let lastMcpStatus = null;
    let helpPanelOpenedOnce = false;

    function renderHelpMcpStatus() {
      const el = document.getElementById('help-mcp-list');
      if (!el) return;
      if (!lastMcpStatus || !lastMcpStatus.configured || !(lastMcpStatus.servers || []).length) {
        el.innerHTML = '<li>연동된 MCP 서버가 없습니다.</li>';
        return;
      }
      el.innerHTML = lastMcpStatus.servers.map(s =>
        `<li><span class="mono">${s.name}</span> — ${s.transport === 'sse' ? '외부 URL(SSE)' : 'stdio'} 방식으로 설정됨</li>`
      ).join('');
    }

    // Populated by loadHelpSkillsAndHooks(), read by toggleSkillInfo() --
    // descriptions can run several sentences (e.g. HA best-practices skill),
    // so they're shown in a popover on click instead of inline in the list.
    let helpSkillsData = [];
    const ICON_INFO_SM = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>';

    async function loadHelpSkillsAndHooks() {
      const skillsEl = document.getElementById('help-skills-list');
      const hooksEl = document.getElementById('help-hooks-list');
      try {
        const res = await fetch('api/skills');
        const data = await res.json();
        const skills = data.skills || [];
        helpSkillsData = skills;
        if (skillsEl) {
          skillsEl.innerHTML = skills.length
            ? skills.map((s, i) => `<li><span class="mono">${s.name}</span>${s.description ? ` <button type="button" class="skill-info-btn" data-skill-index="${i}" title="설명 보기">${ICON_INFO_SM}</button>` : ''}</li>`).join('')
            : '<li>등록된 스킬이 없습니다.</li>';
        }
      } catch (e) {
        if (skillsEl) skillsEl.innerHTML = '<li>스킬 목록을 불러오지 못했습니다.</li>';
      }
      try {
        const res = await fetch('api/hooks');
        const data = await res.json();
        const hooks = data.hooks || [];
        if (hooksEl) {
          hooksEl.innerHTML = hooks.length
            ? hooks.map(h => `<li><span class="mono">${h.source}</span> · ${h.key} (${h.count}개)</li>`).join('')
            : '<li>활성화된 훅이 없습니다.</li>';
        }
      } catch (e) {
        if (hooksEl) hooksEl.innerHTML = '<li>훅 목록을 불러오지 못했습니다.</li>';
      }
    }

    function toggleHelpPanel() {
      const overlay = document.getElementById('help-overlay');
      if (!overlay) return;
      overlay.classList.toggle('open');
      if (overlay.classList.contains('open') && !helpPanelOpenedOnce) {
        helpPanelOpenedOnce = true;
        renderHelpMcpStatus();
        loadHelpSkillsAndHooks();
      }
      if (!overlay.classList.contains('open')) closeSkillInfoPopover();
    }

    function closeSkillInfoPopover() {
      const popover = document.getElementById('skill-info-popover');
      if (popover) { popover.classList.remove('open'); popover._forBtn = null; }
    }

    function toggleSkillInfo(btn) {
      const skill = helpSkillsData[parseInt(btn.getAttribute('data-skill-index'), 10)];
      if (!skill) return;
      let popover = document.getElementById('skill-info-popover');
      if (!popover) {
        popover = document.createElement('div');
        popover.id = 'skill-info-popover';
        popover.className = 'info-popover';
        document.body.appendChild(popover);
      }
      const wasOpenForThis = popover.classList.contains('open') && popover._forBtn === btn;
      closeSkillInfoPopover();
      if (wasOpenForThis) return;
      popover.textContent = skill.description || '(설명 없음)';
      popover._forBtn = btn;
      popover.classList.add('open');
      const rect = btn.getBoundingClientRect();
      const popRect = popover.getBoundingClientRect();
      let left = Math.min(rect.left, window.innerWidth - popRect.width - 12);
      left = Math.max(12, left);
      let top = rect.bottom + 6;
      if (top + popRect.height > window.innerHeight - 12) top = Math.max(12, rect.top - popRect.height - 6);
      popover.style.left = left + 'px';
      popover.style.top = top + 'px';
    }

    // Delegated: works for skill-info buttons re-rendered by loadHelpSkillsAndHooks().
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.skill-info-btn');
      if (btn) { e.stopPropagation(); toggleSkillInfo(btn); return; }
      const popover = document.getElementById('skill-info-popover');
      if (popover && popover.classList.contains('open') && !popover.contains(e.target)) {
        closeSkillInfoPopover();
      }
    });

    function getCurrentTimeStr() {
      const now = new Date();
      return now.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
    }

    // Icon-only copy feedback shared by every copy button in the chat --
    // swaps the icon to a checkmark briefly instead of the old text-swap
    // (buttons here carry no label, see copyUserMessage/copyReasoningLog/copyMessageTop).
    function flashCopied(btn) {
      const icon = btn.querySelector('.icon');
      if (icon) icon.innerHTML = ICON_CHECK_SVG;
      btn.classList.add('copied');
      setTimeout(() => {
        if (icon) icon.innerHTML = ICON_COPY_SVG;
        btn.classList.remove('copied');
      }, 2000);
    }

    function copyUserMessage(btn) {
      const bubble = btn.closest('.bubble-wrap').querySelector('.bubble');
      const text = bubble.getAttribute('data-raw') || bubble.innerText;
      navigator.clipboard.writeText(text).then(() => flashCopied(btn)).catch(() => {});
    }

    // Copies the reasoning/tool-call log itself (term-body) -- distinct from
    // copyMessageTop()'s final-answer markdown copy.
    function copyReasoningLog(btn) {
      const termBox = btn.closest('.term-box');
      const body = termBox ? termBox.querySelector('.term-body') : null;
      const text = body ? body.innerText : '';
      if (!text) return;
      navigator.clipboard.writeText(text).then(() => flashCopied(btn)).catch(() => {});
    }

    // Shared user-bubble skeleton -- mirrors buildBotBubbleDOM below: one
    // markup module used identically whether the message is being typed live
    // (appendUserMessage) or rebuilt from restored history (buildUserRow),
    // so both go through the exact same formatMarkdown() pipeline. Attachments
    // (rendered as `![name](url)` / file links, see sendMessage()) and the
    // user's own typed text share one bubble with no separate thumbnail-strip
    // markup needed.
    function buildUserBubbleDOM(markdownText, timeStr) {
      const row = document.createElement('div');
      row.className = 'msg-row user';
      row.innerHTML = `
        <div class="bubble-wrap">
          <div class="bubble markdown-body"></div>
          <div class="msg-meta user">
            <span class="meta-time">${timeStr}</span>
            <button class="icon-btn-sm" onclick="copyUserMessage(this)" title="복사"><span class="icon">${ICON_COPY_SVG}</span></button>
          </div>
        </div>
      `;
      const bubble = row.querySelector('.bubble');
      bubble.innerHTML = formatMarkdown(markdownText);
      bubble.setAttribute('data-raw', markdownText);
      return row;
    }

    function appendUserMessage(markdownText) {
      const box = document.getElementById('chat-box');
      const row = buildUserBubbleDOM(markdownText, getCurrentTimeStr());
      box.appendChild(row);
      box.scrollTop = box.scrollHeight;
    }

    // Click-to-enlarge for any image rendered inside a chat bubble (user
    // attachments and any images an AI response happens to include) --
    // delegated so it works on content injected later via innerHTML.
    document.addEventListener('click', (e) => {
      const img = e.target.closest('.bubble img');
      if (!img) return;
      openImageLightbox(img.src, img.alt || '');
    });

    function openImageLightbox(src, alt) {
      const overlay = document.getElementById('image-lightbox-overlay');
      const img = document.getElementById('image-lightbox-img');
      if (!overlay || !img) return;
      img.src = src;
      img.alt = alt || '';
      overlay.classList.add('open');
    }

    function closeImageLightbox() {
      const overlay = document.getElementById('image-lightbox-overlay');
      const img = document.getElementById('image-lightbox-img');
      if (overlay) overlay.classList.remove('open');
      if (img) img.src = '';
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
      navigator.clipboard.writeText(text).then(() => flashCopied(btn)).catch(() => {});
    }

    // Shared bot-bubble skeleton -- the ONE markup template for a bot reply,
    // used identically whether the answer is arriving live (createBotStreamMessage)
    // or being rendered from restored history (buildRestoredBotRow). Previously
    // these were two separately-maintained HTML strings that had drifted apart
    // (no header/view-toggle/raw-view on restored bubbles), which is what made
    // restored conversations look different from a live answer.
    function buildBotBubbleDOM(modeText, modeClass, timeStr) {
      const row = document.createElement('div');
      row.className = 'msg-row bot';
      row.innerHTML = `
        <div class="bubble-wrap">
          <!-- Reasoning/tool-call timeline -- a plain, open-flowing block
               OUTSIDE .bubble on purpose (previously nested inside it, which
               doubly boxed the log: the dark terminal panel *and* the bubble
               card around that). header always visible (carries the mode
               tag), body only shown once there's an actual line to show. -->
          <div class="term-box">
            <div class="term-header">
              <span class="term-mode-tag ${modeClass}">${modeText}</span>
              <button class="term-badge live">● LIVE</button>
              <button class="term-copy-btn" onclick="copyReasoningLog(this)" title="추론 로그 복사"><span class="icon">${ICON_COPY_SVG}</span></button>
            </div>
            <div class="term-body" style="display: none;"></div>
          </div>
          <div class="bubble">
            <div class="bubble-header">
              <div class="view-toggle-wrap">
                <button class="view-tab active" onclick="switchMsgView(this, 'parsed')" title="렌더링 보기"><span class="icon">${ICON_EYE_SVG}</span></button>
                <button class="view-tab" onclick="switchMsgView(this, 'raw')" title="원문 보기"><span class="icon">${ICON_CODE_SVG}</span></button>
              </div>
              <button class="top-copy-btn icon-btn-sm" onclick="copyMessageTop(this)" title="마크다운 원문 복사"><span class="icon">${ICON_COPY_SVG}</span></button>
            </div>
            <!-- Main Final Answer Content -->
            <div class="answer-content"><span style="color: var(--text-muted); animation: pulseLive 1.5s infinite ease-in-out;">⚡ Antigravity CLI 실시간 처리 중...</span></div>
            <pre class="raw-markdown-view" style="display: none;"><code></code></pre>
          </div>
          <div class="msg-meta bot">
            <span class="meta-time">${timeStr}</span>
            <span class="meta-latency" style="display: none;"></span>
            <span class="meta-tokens" style="display: none;"></span>
          </div>
        </div>
      `;
      return {
        row,
        termBox: row.querySelector('.term-box'),
        termBody: row.querySelector('.term-body'),
        termBadge: row.querySelector('.term-badge'),
        answerContent: row.querySelector('.answer-content'),
        rawCode: row.querySelector('.raw-markdown-view code'),
        latencyEl: row.querySelector('.meta-latency'),
        tokensEl: row.querySelector('.meta-tokens'),
      };
    }

    // Short "[고속]/[복합]/[CLI]" tag for the reasoning-log header, derived
    // from STREAM_MODES (defined further below) so the picker's mode names
    // and the bubble's mode tag can never drift apart the way the old
    // hardcoded emoji-badge text did.
    function modeBadgeFor(streamMode) {
      const m = STREAM_MODES.find(x => x.value === String(streamMode)) || STREAM_MODES[0];
      return { text: `[${m.shortName}]`, cls: m.colorClass };
    }

    // Single reasoning-log line renderer -- used by both a live stream
    // (createBotStreamMessage's addLiveLog) and a restored turn
    // (buildRestoredBotRow), so a re-loaded conversation's log looks exactly
    // like it did while it was actually streaming instead of a separately
    // hand-rolled markup. timeStr is optional -- restored steps don't carry
    // a reliable per-line timestamp, so that span is simply omitted.
    function formatTermLineHTML(logStr, timeStr) {
      let lineClass = 'term-text';
      if (logStr.includes('💭') || logStr.includes('[추론]')) lineClass += ' think';
      else if (logStr.includes('🔧') || logStr.includes('[도구') || logStr.includes('[HA 도구]')) lineClass += ' tool';
      else if (logStr.includes('📄') || logStr.includes('📝') || logStr.includes('[파일')) lineClass += ' file';
      else if (logStr.includes('⚙️') || logStr.includes('[명령어')) lineClass += ' cmd';
      else if (logStr.includes('🚀') || logStr.includes('[세션')) lineClass += ' init';
      else if (logStr.includes('✅') || logStr.includes('[완료')) lineClass += ' done';
      else if (logStr.includes('⚠️') || logStr.includes('오류') || logStr.includes('인증')) lineClass += ' error';

      // write_to_file/replace_file_content (see formatToolCallLogStr) append a
      // '- old' / '+ new' diff body after the header line -- colorize those
      // lines instead of the flat escape below.
      const esc = s => s.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      const lines = String(logStr).split('\\n');
      const isDiff = lines.some(l => l.startsWith('+ ') || l.startsWith('- '));
      const safeText = isDiff
        ? lines.map(l => {
            const e = esc(l);
            if (l.startsWith('+ ')) return `<span class="diff-add">${e}</span>`;
            if (l.startsWith('- ')) return `<span class="diff-del">${e}</span>`;
            return e;
          }).join('\\n')
        : esc(String(logStr));
      const tsHtml = timeStr ? `<span class="term-time">[${timeStr}]</span> ` : '';
      return `<div class="term-line">${tsHtml}<span class="${lineClass}">${safeText}</span></div>`;
    }

    // Mirrors the tool-name branching in core/streamer.py's tail_transcript()
    // so a restored tool-call step (raw {name, args, ...} from transcript.jsonl)
    // renders through formatTermLineHTML() with the exact same label text a
    // live run would have streamed for that same call -- see buildRestoredBotRow().
    // Unwraps agy's double-JSON-encoded tool-call arg values -- mirrors
    // _agy_str() in core/streamer.py's tail_transcript(); see that
    // function's docstring for why (CodeContent/TargetContent/AbsolutePath/
    // etc. arrive as a JSON string literal *inside* the already-parsed
    // outer value).
    function agyStr(v) {
      if (typeof v === 'string' && v.length >= 2 && v[0] === '"' && v[v.length - 1] === '"') {
        try { return JSON.parse(v); } catch (e) {}
      }
      return v;
    }

    // Mirrors _diff_log_lines() in core/streamer.py -- write_to_file/
    // replace_file_content already scope old/new content to the exact
    // changed range, so a real line-matching diff algorithm isn't needed.
    function diffLogLines(oldText, newText) {
      const lines = [];
      if (oldText) lines.push(...String(oldText).split('\\n').map(l => `- ${l}`));
      if (newText) lines.push(...String(newText).split('\\n').map(l => `+ ${l}`));
      return lines.join('\\n');
    }

    // Mirrors _diff_stat() in core/streamer.py.
    function diffStat(oldText, newText) {
      const added = newText ? String(newText).split('\\n').length : 0;
      const removed = oldText ? String(oldText).split('\\n').length : 0;
      return `+${added} -${removed}`;
    }

    // Mirrors _result_stat() in core/streamer.py -- a short badge summarizing
    // a tool's GENERIC follow-up result (see buildStepsFromResponses()).
    function resultStat(tname, content) {
      const text = content || '';
      if (tname === 'find_by_name') {
        const m = /Found (\\d+) results?/.exec(text);
        if (m) return `${m[1]}개 결과`;
      } else if (tname === 'grep_search') {
        const m = /Found (\\d+) (?:matches|results?)/i.exec(text);
        if (m) return `${m[1]}개 결과`;
      } else if (tname === 'run_command') {
        const lines = text.trim().split('\\n').filter(Boolean);
        if (lines.length) return `${lines.length}줄 출력`;
      }
      return '';
    }

    const DETAIL_CAP = 6000; // mirrors _cap_detail() in core/streamer.py
    function capDetail(text) {
      if (text && text.length > DETAIL_CAP) return text.slice(0, DETAIL_CAP) + '\\n...(생략)';
      return text || '';
    }

    // Mirrors _classify_tool_call() in core/streamer.py -- same tool name ->
    // display shape mapping, so a restored tool_calls array (via
    // buildStepsFromResponses()) renders through the identical reasoning-
    // timeline UI a live SSE reasoning_step would have built.
    function classifyToolCall(tname, args, desc) {
      args = args || {};
      if (tname === 'call_mcp_tool') {
        const tcalled = agyStr(args.ToolName) || 'mcp';
        const tcalledDisplay = (typeof tcalled === 'string' && tcalled.includes('/')) ? tcalled.replace('/', ' / ') : tcalled;
        let targs = args.Arguments || {};
        // agy sometimes logs Arguments as a JSON-encoded string rather than a
        // nested object (same shape MCP wire args take) -- without this, a
        // real tool call with actual parameters (e.g. ha_search's
        // domain_filter) silently loses its whole "Tool arguments" block.
        if (typeof targs === 'string') { try { targs = JSON.parse(targs); } catch (e) {} }
        const argsJson = (targs && typeof targs === 'object' && Object.keys(targs).length) ? JSON.stringify(targs, null, 2) : '';
        return { group: 'ha', verb: 'MCP Tool:', target: tcalledDisplay, stat: '', detail: '', args_json: argsJson, needsResult: true };
      }
      if (tname === 'view_file') {
        const fpath = agyStr(args.AbsolutePath) || '';
        const fname = fpath ? fpath.split(/[\\\\/]/).pop() : 'file';
        return { group: 'explore', explore_kind: 'file', verb: '확인', target: fname + (desc ? ` (${desc})` : ''), stat: '', detail: '', needsResult: true };
      }
      if (tname === 'run_command') {
        const cmdStr = agyStr(args.CommandLine) || '';
        return { group: 'command', verb: '명령어', target: cmdStr, stat: '', detail: '', needsResult: true };
      }
      if (tname === 'search_web') {
        const q = agyStr(args.query) || '';
        return { group: 'web', explore_kind: 'search', verb: '웹 검색', target: q, stat: '', detail: '', needsResult: true };
      }
      if (tname === 'find_by_name') {
        const pattern = agyStr(args.Pattern) || '';
        return { group: 'explore', explore_kind: 'search', verb: '파일명 검색', target: pattern, stat: '', detail: '', needsResult: true };
      }
      if (tname === 'grep_search') {
        const query = agyStr(args.Query) || desc;
        return { group: 'explore', explore_kind: 'search', verb: '검색', target: query, stat: '', detail: '', needsResult: true };
      }
      if (tname === 'replace_file_content') {
        const fpath = agyStr(args.TargetFile) || '';
        const fname = fpath ? fpath.split(/[\\\\/]/).pop() : 'file';
        const oldC = agyStr(args.TargetContent) || '';
        const newC = agyStr(args.ReplacementContent) || '';
        const instr = agyStr(args.Instruction) || desc;
        return { group: 'edit', verb: '수정', target: fname + (instr ? ` (${instr})` : ''), stat: diffStat(oldC, newC), detail: diffLogLines(oldC, newC), needsResult: false };
      }
      if (tname === 'write_to_file') {
        const fpath = agyStr(args.TargetFile) || '';
        const fname = fpath ? fpath.split(/[\\\\/]/).pop() : 'file';
        const newC = agyStr(args.CodeContent) || '';
        const overwrite = agyStr(args.Overwrite) === 'true';
        const added = newC ? String(newC).split('\\n').length : 0;
        const stat = overwrite ? `+${added} (덮어씀)` : `+${added}`;
        return { group: 'edit', verb: overwrite ? '덮어쓰기' : '생성', target: fname + (desc ? ` (${desc})` : ''), stat, detail: diffLogLines('', newC), needsResult: false };
      }
      return { group: 'other', verb: '도구 실행', target: `${tname} ${desc}`.trim(), stat: '', detail: '', needsResult: true };
    }

    // Mirrors tail_transcript()'s buffering loop in core/streamer.py -- turns
    // a restored turn's raw response steps (thinking/tool_calls/content, in
    // order, GENERIC result steps included) into the same reasoning-step
    // shape a live SSE stream sends, so a restored conversation's timeline
    // renders exactly like it did live (see createReasoningTimeline()). A
    // GENERIC step's content right after a tool call is agy's own result for
    // that call -- fold it in instead of showing it as a separate line.
    function buildStepsFromResponses(responses) {
      const steps = [];
      let pending = null;
      let prevCreated = null;

      function flush() {
        if (pending) { steps.push(pending); pending = null; }
      }

      responses.forEach(step => {
        const stype = step.type || '';
        const created = step.created_at ? new Date(step.created_at) : null;
        let durationSec = null;
        if (created && prevCreated) durationSec = Math.max(0, Math.round((created - prevCreated) / 1000));
        if (created) prevCreated = created;

        const tcs = Array.isArray(step.tool_calls) ? step.tool_calls : [];
        const thinking = (step.thinking || '').trim();
        const content = step.content || '';

        if (stype === 'GENERIC' && content && tcs.length === 0 && pending) {
          pending.detail = capDetail(content);
          if (!pending.stat) pending.stat = resultStat(pending.tname, content);
          flush();
          return;
        }

        flush();

        if (thinking) {
          const clean = thinking.replace(/\\n\\n/g, ' · ').replace(/\\n/g, ' ');
          steps.push({ kind: 'thinking', text: clean, duration_sec: durationSec });
        }

        tcs.forEach(tc => {
          const tname = tc.name || 'tool';
          let args = tc.args || {};
          if (typeof args === 'string') { try { args = JSON.parse(args); } catch (e) {} }
          if (!args || typeof args !== 'object') args = {};
          const summary = agyStr(tc.toolSummary || args.toolSummary || '') || '';
          const action = agyStr(tc.toolAction || args.toolAction || '') || '';
          const desc = summary || action || '';

          const cls = classifyToolCall(tname, args, desc);
          const needsResult = cls.needsResult;
          delete cls.needsResult;
          const row = Object.assign({ kind: 'tool', tname, duration_sec: durationSec }, cls);
          if (needsResult) {
            flush();
            pending = row;
          } else {
            steps.push(row);
          }
        });
      });

      flush();
      return steps;
    }

    // Turns a raw stat like "+18 -0" into HTML with the +N/-M counts
    // colorized the same way a diff body's added/removed lines are.
    function stepStatHTML(stat) {
      if (!stat) return '';
      const esc = s => String(s).replace(/</g, '&lt;').replace(/>/g, '&gt;');
      let html = esc(stat);
      html = html.replace(/\\+(\\d+)/, '<span class="diff-add">+$1</span>');
      html = html.replace(/-(\\d+)/, '<span class="diff-del">-$1</span>');
      return `<span class="step-stat">${html}</span>`;
    }

    function stepDetailHTML(detail, isDiff) {
      if (!detail) return '';
      const esc = s => String(s).replace(/</g, '&lt;').replace(/>/g, '&gt;');
      let body;
      if (isDiff) {
        body = String(detail).split('\\n').map(l => {
          const e = esc(l);
          if (l.startsWith('+ ')) return `<span class="diff-add">${e}</span>`;
          if (l.startsWith('- ')) return `<span class="diff-del">${e}</span>`;
          return e;
        }).join('\\n');
      } else {
        body = esc(detail);
      }
      return `<div class="step-detail">${body}</div>`;
    }

    // MCP tool calls (call_mcp_tool) show labeled "Tool arguments"/"Tool
    // Output" JSON blocks instead of the generic diff/text stepDetailHTML --
    // matches Antigravity's own reasoning-timeline UI. "Tool Output" only
    // appears once/if a matching GENERIC result step arrives (see
    // buildStepsFromResponses()/_classify_tool_call's needs_result) --
    // unconfirmed whether agy's transcript actually logs one for MCP calls
    // the way it does for its own native tools, so this degrades to just
    // showing arguments if row.detail never gets filled in.
    // Lightweight regex-based JSON syntax highlighter (no library -- the
    // artifact CSP here only allows scripts from a small CDN allowlist, and
    // this is small enough not to need one). Input must already be escaped
    // HTML-safe text; matches keys/strings/numbers/booleans/null and wraps
    // each in a colored span (see .json-* in core/ui/styles.py).
    function highlightJSON(escapedJsonText) {
      return escapedJsonText.replace(
        /("(\\\\u[a-fA-F0-9]{4}|\\\\.|[^\\\\"])*"(\\s*:)?|\\b(?:true|false)\\b|\\bnull\\b|-?\\d+(?:\\.\\d+)?(?:[eE][+-]?\\d+)?)/g,
        (match) => {
          let cls = 'json-number';
          if (/^"/.test(match)) {
            cls = /:$/.test(match) ? 'json-key' : 'json-string';
          } else if (/true|false/.test(match)) {
            cls = 'json-boolean';
          } else if (/null/.test(match)) {
            cls = 'json-null';
          }
          return `<span class="${cls}">${match}</span>`;
        }
      );
    }

    // Renders a JSON string as a highlighted block if it parses as JSON,
    // else falls back to plain escaped text -- Tool arguments is always
    // valid JSON (built server/client-side from a real object), but Tool
    // Output is agy's raw GENERIC result text, which for find_by_name/
    // run_command/search_web is plain prose/stdout, not JSON. A real MCP
    // tool's result (ha_search etc.) also isn't pure JSON -- agy prefixes it
    // with plain "Created At: .../Completed At: ..." lines before the actual
    // JSON payload, which fails a whole-string JSON.parse -- so past that
    // first failure, split off everything before the first {/[ and retry
    // parsing just the tail; the prefix still renders, just unhighlighted.
    function jsonOrPlainHTML(text) {
      const esc = s => String(s).replace(/</g, '&lt;').replace(/>/g, '&gt;');
      const tryParse = (s) => {
        try { return JSON.stringify(JSON.parse(s), null, 2); } catch (e) { return null; }
      };
      let pretty = tryParse(text);
      if (pretty !== null) return highlightJSON(esc(pretty));
      const m = /[{[]/.exec(text);
      if (m) {
        pretty = tryParse(text.slice(m.index));
        if (pretty !== null) return esc(text.slice(0, m.index)) + highlightJSON(esc(pretty));
      }
      return esc(text);
    }

    // HTML-attribute-safe escape for stashing a block's raw text in
    // data-raw (copyToolIoBlock reads it back) -- distinct from esc()'s
    // element-content escaping, which doesn't touch quotes.
    function escAttr(s) {
      return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function copyToolIoBlock(btn) {
      const raw = btn.getAttribute('data-raw') || '';
      if (!raw) return;
      navigator.clipboard.writeText(raw).then(() => flashCopied(btn)).catch(() => {});
    }

    function toolIoLabelHTML(label, raw) {
      return `<div class="tool-io-label">${label}<button class="icon-btn-sm tool-io-copy-btn" data-raw="${escAttr(raw)}" onclick="copyToolIoBlock(this)" title="복사"><span class="icon">${ICON_COPY_SVG}</span></button></div>`;
    }

    function toolIoDetailHTML(argsJson, detail) {
      let html = '';
      if (argsJson) {
        html += toolIoLabelHTML('Tool arguments', argsJson) + `<div class="tool-io-block">${jsonOrPlainHTML(argsJson)}</div>`;
      }
      if (detail) {
        html += toolIoLabelHTML('Tool Output', detail) + `<div class="tool-io-block">${jsonOrPlainHTML(detail)}</div>`;
      }
      return html ? `<div class="step-detail tool-io">${html}</div>` : '';
    }

    function stepIconFor(row) {
      if (row.kind === 'thinking') return '💭';
      if (row.group === 'web') return '🌐';
      if (row.group === 'explore') return row.explore_kind === 'file' ? '📄' : '🔍';
      if (row.group === 'edit') return row.verb === '생성' ? '📝' : '✏️';
      if (row.group === 'command') return '⚙️';
      if (row.group === 'ha') return '🔧';
      return '🔧';
    }

    // Returns HTML (not plain text) so the counts can be bolded, matching
    // the reference UI's "Explored **2** files, **3** searches".
    // Filenames/paths render in monospace (matches the reference UI's
    // "Analyzed {} ha_search.json" styling) -- anything else (a search
    // query, a command line, an MCP tool name) stays plain text.
    function stepTargetHTML(row) {
      const esc = s => String(s).replace(/</g, '&lt;').replace(/>/g, '&gt;');
      const isFileLike = row.group === 'edit' || (row.group === 'explore' && row.explore_kind === 'file');
      return isFileLike ? `<code>${esc(row.target)}</code>` : esc(row.target);
    }

    function stepGroupSummaryHTML(fileCount, searchCount) {
      const parts = [];
      if (fileCount > 0) parts.push(`파일 <strong>${fileCount}</strong>개 탐색`);
      if (searchCount > 0) parts.push(`검색 <strong>${searchCount}</strong>회`);
      return parts.length ? parts.join(', ') : '탐색';
    }

    // Expand/collapse one reasoning-timeline row (thinking / group / a
    // group's child / a standalone tool row) -- delegated onclick target for
    // every .step-row-header createReasoningTimeline() builds.
    function toggleStepRow(headerEl) {
      const row = headerEl.closest('.step-row, .step-child');
      if (row) row.classList.toggle('expanded');
    }

    // termBadge (the "Worked for Ns"/"⏳ Ns 작업 중" master collapse toggle)
    // always carries a trailing chevron reflecting termBody's open/closed
    // state. Kept as a plain trailing character in textContent (not a nested
    // <span>) so setTermBadgeText() can be called freely without worrying
    // about clobbering a child element on every re-render.
    function setTermBadgeText(termBadge, termBody, baseText) {
      if (!termBadge) return;
      termBadge.dataset.baseText = baseText;
      const isOpen = termBody && termBody.style.display !== 'none';
      termBadge.textContent = `${baseText} ${isOpen ? '▾' : '▸'}`;
    }
    function toggleTermBody(termBadge, termBody) {
      if (!termBody) return;
      termBody.style.display = (termBody.style.display === 'none') ? 'block' : 'none';
      setTermBadgeText(termBadge, termBody, (termBadge && termBadge.dataset.baseText) || '');
    }

    // Grouped, expandable reasoning timeline -- the Antigravity-IDE-style
    // "Explored N files, M searches" / "Thought for Xs" / "Edited file +N -M"
    // log. addStep() is called once per step in order, live (via the SSE
    // reasoning_step event, see createBotStreamMessage) or all at once (a
    // restored turn's buildStepsFromResponses() output, see
    // buildRestoredBotRow) -- both paths produce the identical timeline.
    // Consecutive explore/web tool steps merge into one collapsible group;
    // anything else (thinking, edit, command, ha tool call) is its own
    // top-level row and closes whatever group was open.
    function createReasoningTimeline(termBody) {
      let openGroup = null; // { el, fileCount, searchCount }
      let seq = 0;
      const MERGEABLE = { explore: true, web: true };

      function closeGroup() { openGroup = null; }

      function childRowHTML(row, key) {
        const esc = s => String(s).replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const hasDetail = !!row.detail || !!row.args_json;
        return `<div class="step-child" data-key="${key}">
          <div class="step-row-header"${hasDetail ? ' onclick="toggleStepRow(this)"' : ''}>
            <span class="chevron">${hasDetail ? '▸' : ''}</span>
            <span class="step-icon">${stepIconFor(row)}</span>
            <span class="step-verb">${esc(row.verb)}</span>
            <span class="step-target">${stepTargetHTML(row)}</span>
            ${stepStatHTML(row.stat)}
          </div>
          ${row.group === 'ha' ? toolIoDetailHTML(row.args_json, row.detail) : stepDetailHTML(row.detail, row.group === 'edit')}
        </div>`;
      }

      function standaloneRowHTML(row, key) {
        const esc = s => String(s).replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const hasDetail = !!row.detail || !!row.args_json;
        return `<div class="step-row tool-row" data-key="${key}">
          <div class="step-row-header"${hasDetail ? ' onclick="toggleStepRow(this)"' : ''}>
            <span class="chevron">${hasDetail ? '▸' : ''}</span>
            <span class="step-icon">${stepIconFor(row)}</span>
            <span class="step-verb">${esc(row.verb)}</span>
            <span class="step-target">${stepTargetHTML(row)}</span>
            ${stepStatHTML(row.stat)}
          </div>
          ${row.group === 'ha' ? toolIoDetailHTML(row.args_json, row.detail) : stepDetailHTML(row.detail, row.group === 'edit')}
        </div>`;
      }

      function thinkingRowHTML(row, key) {
        const esc = s => String(s).replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const durText = (row.duration_sec != null && row.duration_sec > 0) ? `${row.duration_sec}초 동안 생각함` : '생각함';
        return `<div class="step-row think-row" data-key="${key}">
          <div class="step-row-header" onclick="toggleStepRow(this)">
            <span class="chevron">▸</span>
            <span class="step-icon">💭</span>
            <span class="step-label">${durText}</span>
          </div>
          <div class="step-detail">${esc(row.text)}</div>
        </div>`;
      }

      // Starts expanded (unlike a thinking block or an individual tool's
      // detail, which start collapsed) -- matches the reference UI, where
      // an "Explored N files, M searches" group shows its rows right away
      // and only the leaf-level detail needs a click.
      function newGroupHTML(key) {
        return `<div class="step-row group-row expanded" data-key="${key}">
          <div class="step-row-header" onclick="toggleStepRow(this)">
            <span class="chevron">▸</span>
            <span class="step-icon">📂</span>
            <span class="step-label group-summary"></span>
          </div>
          <div class="step-children"></div>
        </div>`;
      }

      return {
        addStep: function(row) {
          seq++;
          const key = `s${seq}`;
          if (row.kind === 'thinking') {
            closeGroup();
            termBody.insertAdjacentHTML('beforeend', thinkingRowHTML(row, key));
            return;
          }
          if (MERGEABLE[row.group]) {
            if (!openGroup) {
              termBody.insertAdjacentHTML('beforeend', newGroupHTML(`g${seq}`));
              openGroup = { el: termBody.lastElementChild, fileCount: 0, searchCount: 0 };
            }
            if (row.explore_kind === 'file') openGroup.fileCount++;
            else openGroup.searchCount++;
            const summaryEl = openGroup.el.querySelector('.group-summary');
            if (summaryEl) summaryEl.innerHTML = stepGroupSummaryHTML(openGroup.fileCount, openGroup.searchCount);
            const childrenEl = openGroup.el.querySelector('.step-children');
            if (childrenEl) childrenEl.insertAdjacentHTML('beforeend', childRowHTML(row, key));
          } else {
            closeGroup();
            termBody.insertAdjacentHTML('beforeend', standaloneRowHTML(row, key));
          }
        }
      };
    }

    function formatToolCallLogStr(tc) {
      const tname = tc.name || 'tool';
      let args = tc.args || {};
      if (typeof args === 'string') {
        try { args = JSON.parse(args); } catch (e) {}
      }
      const isObj = args && typeof args === 'object' && !Array.isArray(args);
      const summary = agyStr(tc.toolSummary || (isObj ? args.toolSummary : '')) || '';
      const action = agyStr(tc.toolAction || (isObj ? args.toolAction : '')) || '';
      const desc = summary || action || '';

      // No length caps below (mirrors core/streamer.py's tail_transcript()) --
      // the reasoning-log box scrolls horizontally instead of wrapping (see
      // .term-body in core/ui/styles.py), so truncating threw content away
      // for no display reason.
      if (tname === 'call_mcp_tool' && isObj) {
        const tcalled = agyStr(args.ToolName) || 'mcp';
        const targs = args.Arguments || {};
        const argStr = (targs && typeof targs === 'object') ? JSON.stringify(targs) : String(targs);
        return `🔧 [HA 도구] ${tcalled} ${argStr}`;
      }
      if (tname === 'view_file' && isObj) {
        const fpath = agyStr(args.AbsolutePath) || '';
        const fname = fpath ? fpath.split(/[\\\\/]/).pop() : 'file';
        return `📄 [파일 확인] ${fname}${desc ? ` (${desc})` : ''}`;
      }
      if (tname === 'run_command' && isObj) {
        const cmdStr = agyStr(args.CommandLine) || '';
        return `⚙️ [명령어] ${cmdStr}`;
      }
      if (tname === 'search_web') {
        const q = isObj ? (args.query || '') : String(args);
        return `🌐 [웹 검색] ${q}`;
      }
      if (tname === 'replace_file_content' && isObj) {
        const fpath = agyStr(args.TargetFile) || '';
        const fname = fpath ? fpath.split(/[\\\\/]/).pop() : 'file';
        const oldC = agyStr(args.TargetContent) || '';
        const newC = agyStr(args.ReplacementContent) || '';
        const instr = agyStr(args.Instruction) || desc;
        const header = `✏️ [파일 수정] ${fname}${instr ? ` (${instr})` : ''}`;
        const body = diffLogLines(oldC, newC);
        return body ? `${header}\n${body}` : header;
      }
      if (tname === 'write_to_file' && isObj) {
        const fpath = agyStr(args.TargetFile) || '';
        const fname = fpath ? fpath.split(/[\\\\/]/).pop() : 'file';
        const newC = agyStr(args.CodeContent) || '';
        const overwrite = agyStr(args.Overwrite) === 'true';
        const label = overwrite ? '파일 덮어쓰기' : '파일 생성';
        const header = `📝 [${label}] ${fname}${desc ? ` (${desc})` : ''}`;
        const body = diffLogLines('', newC);
        return body ? `${header}\n${body}` : header;
      }
      return `🔧 [도구 실행] ${tname} ${desc || ''}`;
    }

    function createBotStreamMessage(streamMode) {
      const box = document.getElementById('chat-box');
      const timeStr = getCurrentTimeStr();
      const startTime = performance.now();

      const { text: modeText, cls: modeClass } = modeBadgeFor(streamMode);
      const { row, termBody, termBadge, answerContent, rawCode, latencyEl, tokensEl } =
        buildBotBubbleDOM(modeText, modeClass, timeStr);
      box.appendChild(row);
      box.scrollTop = box.scrollHeight;

      let answerText = "";
      let finished = false;
      let hasAnswerStarted = false;
      let hasReasoningStep = false;
      let userToggledTermBody = false;
      const timeline = createReasoningTimeline(termBody);

      // termBadge doubles as the reasoning-log's master collapse toggle --
      // ticks while live, freezes to a duration once done (see finish()),
      // and a manual click always wins over the auto-collapse-on-done below.
      if (termBadge) {
        termBadge.onclick = function() {
          userToggledTermBody = true;
          toggleTermBody(termBadge, termBody);
        };
      }

      const liveTimer = setInterval(() => {
        if (finished) return;
        const elapsed = ((performance.now() - startTime) / 1000);
        if (elapsed >= 0.5) {
          if (latencyEl) {
            latencyEl.textContent = `⏳ ${elapsed.toFixed(1)}초 실시간 처리 중...`;
            latencyEl.style.display = 'inline';
          }
          setTermBadgeText(termBadge, termBody, `⏳ ${elapsed.toFixed(0)}초 작업 중`);
        }
      }, 100);

      return {
        addLiveLog: function(logStr) {
          if (!termBody) return;
          termBody.style.display = 'block';
          const now = new Date();
          const ts = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`;
          termBody.insertAdjacentHTML('beforeend', formatTermLineHTML(logStr, ts));
          termBody.scrollTop = termBody.scrollHeight;
          box.scrollTop = box.scrollHeight;
        },
        addTool: function(toolStr) {
          this.addLiveLog(toolStr);
        },
        addReasoningStep: function(stepData) {
          if (!termBody || !stepData) return;
          hasReasoningStep = true;
          termBody.style.display = 'block';
          timeline.addStep(stepData);
          termBody.scrollTop = termBody.scrollHeight;
          box.scrollTop = box.scrollHeight;
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
          const totalSec = Math.round((performance.now() - startTime) / 1000);
          if (termBadge) {
            termBadge.classList.remove('live');
            termBadge.classList.add('done');
          }
          // Auto-collapse the reasoning log once the answer is in -- same
          // "done reasoning -> collapse to a one-line summary" behavior as
          // Claude's/Antigravity's own thinking UI. A manual click already
          // wins (userToggledTermBody), so this never fights the user.
          if (termBody && hasReasoningStep && !userToggledTermBody) {
            termBody.style.display = 'none';
          }
          setTermBadgeText(termBadge, termBody, `🕐 ${totalSec}초 동안 작업함`);
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
    // 3s poll x 60 points = 3 minutes of visible history (was 24 = 72s, felt
    // like it scrolled by too fast).
    const MAX_HISTORY = 60;
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
        // On mobile the session sidebar is a fixed overlay spanning the full
        // viewport height, including where this panel renders -- having both
        // open at once looked like the graph floating on top of the menu.
        // Only one makes sense open at a time on a screen this narrow.
        if (window.innerWidth <= 768) {
          const sidebar = document.getElementById('session-sidebar');
          const overlay = document.getElementById('sidebar-overlay');
          if (sidebar && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            if (overlay) overlay.classList.remove('open');
          }
        }
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

        // Mode 3 (CLI 모드) Conditional Enable/Disable
        cliModeSupported = !!data.agy_stream_supported;
        if (!cliModeSupported && currentStreamMode === '3') {
          currentStreamMode = '1';
          localStorage.setItem('antigravity_stream_mode', '1');
          updateStreamModeButton();
        }
        renderStreamModeList();

        // Cached for the Help modal's "MCP 연동" section (see
        // renderHelpMcpStatus()) -- no need for a separate fetch since this
        // poll already runs continuously.
        lastMcpStatus = data.mcp_status || null;
        if (helpPanelOpenedOnce) renderHelpMcpStatus();

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
      { value: '1', icon: ICON_ZAP_SVG, colorClass: 'mode-color-amber', shortName: '고속', name: '고속 제어 모드', desc: '0.05초 네이티브 기기 즉시 제어 & 빠른 질의' },
      { value: '2', icon: ICON_BRAIN_SVG, colorClass: 'mode-color-purple', shortName: '복합', name: '고속 제어 & 스마트 모드', desc: '다차원 환경 분석 & 스마트 어드바이스' },
      { value: '3', icon: ICON_TERMINAL_SVG, colorClass: 'mode-color-sky', shortName: 'CLI', name: 'CLI 추론 모드', desc: '공식 agy 0초 실시간 스트리밍 엔진' },
    ];
    let currentStreamMode = localStorage.getItem('antigravity_stream_mode') || '3';
    let cliModeSupported = true;

    function updateStreamModeButton() {
      const nameEl = document.getElementById('stream-mode-current');
      const iconEl = document.getElementById('stream-mode-icon');
      const m = STREAM_MODES.find(x => x.value === currentStreamMode) || STREAM_MODES[0];
      if (nameEl) nameEl.textContent = m.shortName;
      if (iconEl) { iconEl.innerHTML = m.icon; iconEl.className = `icon ${m.colorClass}`; }
      updateAttachBtnState();
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
        updateModelPickerUsageRing();
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
      updateModelPickerUsageRing();
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
      updateModelPickerUsageRing();
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
      const agentPicker = document.getElementById('agent-picker');
      if (agentPicker && !agentPicker.contains(e.target)) {
        closeAgentPicker();
      }
    });

    // Custom agent picker (Mode 3, `agy --agent <id>`). Discovered from
    // .agents/agents/*/agent.md and ~/.gemini/config/agents/*/agent.md (see
    // core/agent_discovery.py) -- most installs have none defined, so the
    // whole picker stays hidden until at least one is found.
    let agentCatalog = [];
    let currentAgentId = localStorage.getItem('antigravity_agent_id') || '';

    async function loadAgentCatalog() {
      try {
        const apiUrl = new URL('api/agents', window.location.href).href;
        const res = await fetch(apiUrl);
        const data = await res.json();
        agentCatalog = data.agents || [];
      } catch (e) {
        agentCatalog = [];
      }
      const picker = document.getElementById('agent-picker');
      if (!picker) return;
      if (agentCatalog.length === 0) {
        picker.style.display = 'none';
        return;
      }
      if (!agentCatalog.some(a => a.id === currentAgentId)) currentAgentId = '';
      picker.style.display = '';
      renderAgentDropdownList();
      updateAgentPickerButton();
    }

    function updateAgentPickerButton() {
      const nameEl = document.getElementById('agent-picker-current');
      if (!nameEl) return;
      const agent = agentCatalog.find(a => a.id === currentAgentId);
      nameEl.textContent = agent ? agent.name : 'Default agent';
    }

    function renderAgentDropdownList() {
      const list = document.getElementById('agent-dropdown-list');
      if (!list) return;
      const rows = [{ id: '', name: 'Default agent', description: '' }, ...agentCatalog];
      list.innerHTML = rows.map(a => `
        <div class="model-row ${a.id === currentAgentId ? 'active' : ''}">
          <div class="model-row-main" onclick="selectAgent('${a.id}')">
            <span class="model-row-name">${a.name}</span>
          </div>
          <div class="model-row-right">
            ${a.id === currentAgentId ? `<span class="model-row-check"><span class="icon">${ICON_CHECK_SVG}</span></span>` : ''}
          </div>
        </div>
      `).join('');
    }

    function selectAgent(id) {
      currentAgentId = id;
      localStorage.setItem('antigravity_agent_id', currentAgentId);
      updateAgentPickerButton();
      renderAgentDropdownList();
      closeAgentPicker();
    }

    function toggleAgentPicker() {
      const dropdown = document.getElementById('agent-dropdown');
      if (!dropdown) return;
      const opening = !dropdown.classList.contains('open');
      closeModelPicker();
      closeStreamModePicker();
      dropdown.classList.toggle('open', opening);
    }

    function closeAgentPicker() {
      const dropdown = document.getElementById('agent-dropdown');
      if (dropdown) dropdown.classList.remove('open');
    }

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
      updateModelPickerUsageRing();
      appendCreditsLine();
    }

    // G1 credit balance -- separate slash command/endpoint from the
    // weekly/5-hour model quota above (see core/usage_client.py
    // get_credits_snapshot()). Fetched independently and appended once
    // confirmed available, rather than baked into renderUsagePanelFromData's
    // main render, so a slow/failed credits call never blocks the quota bars.
    async function appendCreditsLine() {
      const panel = document.getElementById('usage-panel');
      if (!panel) return;
      try {
        const apiUrl = new URL('api/credits', window.location.href).href;
        const res = await fetch(apiUrl);
        const data = await res.json();
        const remaining = data.available && data.data ? data.data.remaining_credits : undefined;
        if (typeof remaining !== 'number') return;
        const upgradeUri = data.data.upgrade_uri;
        const row = document.createElement('div');
        row.innerHTML = `<div class="usage-family-title">G1 크레딧</div>` +
          `<div class="usage-credits-line">잔여 ${remaining}개${upgradeUri ? ` · <a href="${upgradeUri}" target="_blank" rel="noopener">업그레이드</a>` : ''}</div>`;
        panel.appendChild(row);
      } catch (e) {}
    }

    // Small ring gauge inline in the model-picker button itself, right after
    // the effort tag ("Low"/"Medium"/"High") -- no separate panel/block, no
    // label or percentage text, just the ring. Prefers the weekly limit
    // (the more meaningful long-term budget); falls back to the 5-hour
    // window only if weekly isn't available for this family; hides entirely
    // if neither is (no fabricated "N/A" ring).
    function updateModelPickerUsageRing() {
      const ring = document.getElementById('model-picker-usage-ring');
      if (!ring) return;
      const model = modelCatalog.find(m => m.slug === currentModelSlug);
      const stats = model ? familyUsage[model.family] : null;

      let pct = null;
      let hint = '';
      if (stats && typeof stats.weekly_remaining_pct === 'number') {
        pct = stats.weekly_remaining_pct;
        hint = `주간 잔여 ${pct}%`;
      } else if (stats && typeof stats.five_hour_remaining_pct === 'number') {
        pct = stats.five_hour_remaining_pct;
        hint = `5시간 잔여 ${pct}%`;
      }

      if (pct === null) {
        ring.style.display = 'none';
        return;
      }
      const color = pct <= 15 ? 'var(--accent-red)' : pct <= 40 ? 'var(--accent-yellow)' : 'var(--accent-green)';
      ring.style.setProperty('--pct', pct);
      ring.style.setProperty('--ring-color', color);
      ring.title = hint;
      ring.style.display = 'inline-block';
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
    // Raw transcript steps are grouped into turns (one USER_INPUT + every
    // following non-USER_INPUT step up to the next USER_INPUT) before any
    // pagination happens. Paginating by raw step count instead of by turn
    // used to slice straight through a turn's reasoning/tool-call steps --
    // a Mode 3 turn alone can be dozens of steps (one PLANNER_RESPONSE per
    // tool call) -- which showed up as an answer bubble with no question
    // above it, or a question followed by a fake "작업이 완료되었습니다"
    // placeholder once the rest loaded. Paginating by whole turns instead
    // makes that structurally impossible.
    let sessionTurns = [];
    let renderedFromTurnIndex = 0;
    let isLoadingMoreHistory = false;
    let historyScrollObserver = null;
    const HISTORY_TURNS_PER_PAGE = 10;

    function toggleSessionSidebar() {
      const sidebar = document.getElementById('session-sidebar');
      const overlay = document.getElementById('sidebar-overlay');
      if (window.innerWidth <= 768) {
        const opening = !sidebar.classList.contains('open');
        sidebar.classList.toggle('open', opening);
        overlay.classList.toggle('open', opening);
        // Same reasoning as toggleResourcePanel()'s mobile guard -- avoid the
        // resource panel appearing to float above the opened sidebar.
        if (opening && isResourcePanelOpen) {
          const panel = document.getElementById('top-resource-panel');
          if (panel) panel.classList.remove('open');
          isResourcePanelOpen = false;
        }
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
    const ICON_EDIT_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>';

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

    function startInlineRename(cid, evt) {
      if (evt) evt.stopPropagation();
      const card = evt.target.closest('.session-card');
      if (!card) return;
      const titleEl = card.querySelector('.session-card-title');
      if (!titleEl || titleEl.tagName === 'INPUT') return;
      const currentTitle = titleEl.textContent;
      const input = document.createElement('input');
      input.className = 'session-card-title session-card-title-input';
      input.value = currentTitle;
      input.onclick = (e) => e.stopPropagation();
      input.onkeydown = (e) => {
        e.stopPropagation();
        if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
        else if (e.key === 'Escape') { e.preventDefault(); input.dataset.cancelled = '1'; input.blur(); }
      };
      input.onblur = () => commitInlineRename(cid, currentTitle, input);
      titleEl.replaceWith(input);
      input.focus();
      input.select();
    }

    async function commitInlineRename(cid, previousTitle, input) {
      const title = input.value.trim();
      if (input.dataset.cancelled || !title || title === previousTitle) {
        loadSessionsList();
        return;
      }
      try {
        const apiUrl = new URL('api/sessions/' + encodeURIComponent(cid), window.location.href).href;
        await fetch(apiUrl, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title })
        });
      } catch (e) {}
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
            ${!sessionSelectMode ? `<button class="session-card-delete-btn" onclick="startInlineRename('${cid}', event)" title="제목 변경"><span class="icon">${ICON_EDIT_SVG}</span></button>` : ''}
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

    function teardownHistoryScrollObserver() {
      if (historyScrollObserver) {
        historyScrollObserver.disconnect();
        historyScrollObserver = null;
      }
    }

    function startNewSession() {
      teardownHistoryScrollObserver();
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

    // Group a flat transcript into turns: one USER_INPUT plus every following
    // non-USER_INPUT step up to the next USER_INPUT. Pagination and rendering
    // both operate on these groups, never on raw step indices -- that's what
    // guarantees a turn's reasoning/tool-call steps can never be split across
    // a page boundary.
    function buildSessionTurns(steps) {
      const turns = [];
      let i = 0;
      while (i < steps.length) {
        const step = steps[i];
        const isUserStart = step.type === 'USER_INPUT';
        const turn = { user: isUserStart ? step : null, responses: [] };
        if (isUserStart) i++;
        else turn.responses.push(step), i++; // defensive: responses with no leading USER_INPUT
        while (i < steps.length && steps[i].type !== 'USER_INPUT') {
          turn.responses.push(steps[i]);
          i++;
        }
        turns.push(turn);
      }
      return turns;
    }

    async function openSession(cid) {
      if (!cid) return;
      teardownHistoryScrollObserver();
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

        sessionTurns = buildSessionTurns(loadedHistorySteps);
        renderedFromTurnIndex = Math.max(0, sessionTurns.length - HISTORY_TURNS_PER_PAGE);

        const statusDiv = document.createElement('div');
        statusDiv.id = 'history-load-status';
        statusDiv.className = 'history-load-more';
        box.appendChild(statusDiv);

        renderTurnsRange(renderedFromTurnIndex, sessionTurns.length, false);
        updateHistoryStatusIndicator();
        setupHistoryScrollObserver();
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

    // Best-effort mode badge for a restored turn. record_mode1_interaction /
    // record_mode2_interaction (core/session_manager.py) always prefix their
    // synthetic `thinking` text this way; a turn with neither prefix ran
    // through Mode 3 (agy), whose native transcript entries don't use this
    // convention. No explicit "which mode" field is stored per turn, so this
    // is inferred rather than authoritative.
    function inferTurnModeBadge(turn) {
      for (const r of turn.responses) {
        if (typeof r.thinking === 'string') {
          if (r.thinking.startsWith('AI 딥 브레인')) return modeBadgeFor('2');
          if (r.thinking.startsWith('초고속 스마트홈 엔진')) return modeBadgeFor('1');
        }
      }
      return modeBadgeFor('3');
    }

    // Restored user turn -- same buildUserBubbleDOM module appendUserMessage()
    // uses live, so a re-loaded conversation renders markdown identically to
    // one that was just typed (previously this hand-escaped plain text instead).
    function buildUserRow(step) {
      const timeStr = step.created_at ? new Date(step.created_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }) : '';
      const cleanText = cleanUserPromptString(step.content || '');
      const row = buildUserBubbleDOM(cleanText, timeStr);
      // Rewind is only meaningful on a restored (already-saved) turn, so the
      // button is added here rather than inside buildUserBubbleDOM (shared
      // with the live-typing path in appendUserMessage(), which has no
      // step_index yet). Hidden for any turn whose source_cid isn't the
      // conversation actually open (see get_session_history()'s source_cid
      // tagging): a turn from an earlier, superseded segment of a Modes-1/2
      // -> Mode-3 hand-off chain lives in a *different* physical transcript
      // file than the one rewind_session() would truncate, so a step_index
      // from there can't be safely applied here.
      const isRewindableFile = !step.source_cid || step.source_cid === currentConversationId;
      if (typeof step.step_index === 'number' && isRewindableFile) {
        const meta = row.querySelector('.msg-meta.user');
        if (meta) {
          const btn = document.createElement('button');
          btn.className = 'icon-btn-sm';
          btn.title = '이 메시지로 되돌리기';
          btn.innerHTML = `<span class="icon">${ICON_REWIND_SVG}</span>`;
          btn.onclick = (e) => rewindToStep(step.step_index, e);
          meta.appendChild(btn);
        }
      }
      return row;
    }

    // Truncates the conversation back to `stepIndex` (discards every step
    // after it) and reloads the session view. See core/session_manager.py
    // rewind_session() for what this actually does server-side -- notably,
    // continuing the chat afterward starts agy on a fresh id rather than
    // truly erasing agy's own memory of the discarded turns (no --rewind
    // flag exists), which the confirm text below says plainly rather than
    // implying a guarantee the addon can't back up.
    async function rewindToStep(stepIndex, evt) {
      if (evt) evt.stopPropagation();
      if (!currentConversationId) return;
      const ok = confirm(
        '이 메시지부터 이후의 대화 내용이 모두 삭제됩니다.\\n' +
        '이어서 대화하면 새 CLI 세션으로 시작되며, 남겨진 대화 내용은 맥락으로 함께 전달됩니다.\\n\\n' +
        '되돌리시겠습니까?'
      );
      if (!ok) return;
      try {
        const apiUrl = new URL(`api/sessions/${encodeURIComponent(currentConversationId)}/rewind`, window.location.href).href;
        const res = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ step_index: stepIndex }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
      } catch (e) {
        alert('되돌리기에 실패했습니다: ' + e.message);
        return;
      }
      await openSession(currentConversationId);
      loadSessionsList();
    }

    // Builds a restored bot turn using the exact same markup as a live answer
    // (buildBotBubbleDOM) -- just filled in all at once instead of
    // progressively. Unlike a live answer, a restored turn never shows a
    // latency badge (there's no real elapsed time to report).
    function buildRestoredBotRow(turn) {
      let finalContent = '';
      let lastTimeStr = '';
      let firstCreated = null;
      let lastCreated = null;

      turn.responses.forEach(cur => {
        if (cur.created_at) {
          lastTimeStr = new Date(cur.created_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
          const d = new Date(cur.created_at);
          if (!firstCreated) firstCreated = d;
          lastCreated = d;
        }
        // PLANNER_RESPONSE's own content is the model's actual final answer --
        // a GENERIC step's content is a tool's *result* (see
        // buildStepsFromResponses()), not the answer, so only count this one.
        if (cur.type === 'PLANNER_RESPONSE' && cur.content && typeof cur.content === 'string' && cur.content.trim()) {
          finalContent = cur.content.trim();
        }
      });

      // Mirrors tail_transcript()'s buffering in core/streamer.py -- turns
      // the raw response steps into the same reasoning-step shape a live SSE
      // stream sends, so a restored conversation's timeline (grouped
      // explore/search, "Thought for Xs", diff stats, expandable tool
      // results) looks exactly like it did while actually streaming.
      const steps = buildStepsFromResponses(turn.responses);

      const { text: modeText, cls: modeClass } = inferTurnModeBadge(turn);
      const { row, termBody, termBadge, answerContent, rawCode } =
        buildBotBubbleDOM(modeText, modeClass, lastTimeStr);

      // A restored turn is always "done" -- never actually live -- regardless
      // of whether it had any reasoning/tool-call steps to show. Collapsed by
      // default (unlike a live answer's auto-collapse-on-finish, a restored
      // one was never expanded in the first place) -- click the badge to see it.
      let totalSecText = '';
      if (firstCreated && lastCreated && lastCreated > firstCreated) {
        totalSecText = `🕐 ${Math.round((lastCreated - firstCreated) / 1000)}초 동안 작업함`;
      }
      termBadge.classList.remove('live');
      termBadge.classList.add('done');

      if (steps.length > 0) {
        termBadge.onclick = function() { toggleTermBody(termBadge, termBody); };
        setTermBadgeText(termBadge, termBody, totalSecText || '● COMPLETED');
        const timeline = createReasoningTimeline(termBody);
        steps.forEach(s => timeline.addStep(s));
      } else {
        termBadge.textContent = totalSecText || '● COMPLETED';
      }

      const displayAnswer = finalContent || (steps.length > 0 ? '작업이 완료되었습니다.' : '답변이 없습니다.');
      answerContent.innerHTML = formatMarkdown(displayAnswer);
      answerContent.setAttribute('data-raw', displayAnswer);
      if (rawCode) rawCode.textContent = displayAnswer;
      return row;
    }

    // Renders turns [fromIdx, toIdx) of sessionTurns. prepend=true inserts
    // above the existing content (used when auto-loading older turns) instead
    // of appending at the bottom (initial load).
    function renderTurnsRange(fromIdx, toIdx, prepend) {
      const box = document.getElementById('chat-box');
      const statusEl = document.getElementById('history-load-status');
      const fragment = document.createDocumentFragment();

      for (let t = fromIdx; t < toIdx; t++) {
        const turn = sessionTurns[t];
        if (turn.user) fragment.appendChild(buildUserRow(turn.user));
        if (turn.responses.length > 0) fragment.appendChild(buildRestoredBotRow(turn));
      }

      if (prepend && statusEl) {
        box.insertBefore(fragment, statusEl.nextSibling);
      } else {
        box.appendChild(fragment);
      }
    }

    function updateHistoryStatusIndicator() {
      const statusEl = document.getElementById('history-load-status');
      if (!statusEl) return;
      if (renderedFromTurnIndex <= 0) {
        statusEl.innerHTML = `<span class="history-status-text">🏁 더 이상 이전 대화가 없습니다</span>`;
        teardownHistoryScrollObserver();
      } else {
        statusEl.innerHTML = `<span class="history-status-text">⬆️ 위로 스크롤하면 이전 대화 ${renderedFromTurnIndex}개를 더 불러옵니다</span>`;
      }
    }

    // Auto-loads older turns as the user scrolls near the top of chat-box --
    // no button, matches "더 이상 대화가 없으면 없다고 보여주고" (show an
    // end-of-history message once exhausted, keep loading automatically
    // until then).
    function loadMoreHistoryTurns() {
      if (isLoadingMoreHistory || renderedFromTurnIndex <= 0) return;
      isLoadingMoreHistory = true;

      const box = document.getElementById('chat-box');
      const oldScrollHeight = box.scrollHeight;
      const oldScrollTop = box.scrollTop;

      const newFrom = Math.max(0, renderedFromTurnIndex - HISTORY_TURNS_PER_PAGE);
      const newTo = renderedFromTurnIndex;
      renderedFromTurnIndex = newFrom;

      renderTurnsRange(newFrom, newTo, true);
      updateHistoryStatusIndicator();

      // Restore relative scroll position so prepended content doesn't yank
      // the viewport.
      const newScrollHeight = box.scrollHeight;
      box.scrollTop = oldScrollTop + (newScrollHeight - oldScrollHeight);

      isLoadingMoreHistory = false;
    }

    function setupHistoryScrollObserver() {
      teardownHistoryScrollObserver();
      if (renderedFromTurnIndex <= 0) return; // already showing everything
      const box = document.getElementById('chat-box');
      const statusEl = document.getElementById('history-load-status');
      if (!box || !statusEl) return;
      historyScrollObserver = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) loadMoreHistoryTurns();
      }, { root: box, rootMargin: '200px 0px 0px 0px', threshold: 0 });
      historyScrollObserver.observe(statusEl);
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
      await loadAgentCatalog();
      prefetchUsage();

      // Start 3-second Periodic Status Polling
      setInterval(pollStatus, 3000);
      // Keep the usage snapshot warm so opening "View Usage" feels instant
      setInterval(prefetchUsage, 55000);
    });

    // Mode 3 stop/cancel state -- set by sendMessage() while a generation is
    // in flight, read by updateSendBtn() to swap the send button into a stop
    // button. Modes 1/2 finish near-instantly with no cancellable backend
    // process (see core/streamer.py), so the swap only ever applies to Mode 3.
    let isStreamActive = false;
    let activeStreamId = '';
    let activeAbortController = null;
    let activeStreamModeForStop = 0;

    function updateSendBtn() {
      const input = document.getElementById('user-input');
      const btn = document.getElementById('send-btn');
      const icon = btn.querySelector('.icon');
      if (isStreamActive && activeStreamModeForStop === 3) {
        btn.classList.add('stopping');
        if (icon) icon.innerHTML = ICON_STOP_SVG;
        btn.disabled = false;
        return;
      }
      btn.classList.remove('stopping');
      if (icon) icon.innerHTML = ICON_ARROW_UP_SVG;
      const hasText = input.value.trim().length > 0;
      btn.classList.toggle('has-text', hasText);
      btn.disabled = !hasText;
    }

    // Stops an in-flight Mode 3 generation: tells the backend to kill the
    // agy process (see core/streamer.py stop_stream / POST /api/chat/stop)
    // and aborts the client-side fetch for immediate UI feedback.
    function stopGeneration() {
      if (activeStreamId) {
        fetch(new URL('api/chat/stop', window.location.href).href, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ stream_id: activeStreamId }),
        }).catch(() => {});
      }
      if (activeAbortController) activeAbortController.abort();
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

    // Textarea auto-grow, capped at 3 lines (measured from the element's own
    // computed line-height so it stays correct regardless of font metrics).
    function autoResizeTextarea() {
      const el = document.getElementById('user-input');
      if (!el) return;
      el.style.height = 'auto';
      const lineHeight = parseFloat(getComputedStyle(el).lineHeight) || 21;
      const maxHeight = Math.round(lineHeight * 3);
      const next = Math.min(el.scrollHeight, maxHeight);
      el.style.height = next + 'px';
      el.style.overflowY = el.scrollHeight > maxHeight ? 'auto' : 'hidden';
    }

    // File attachments -- Mode 3 (CLI 추론 모드) only. agy's own `view_file`
    // tool reads and visually understands an image given just its absolute
    // path in a headless -p prompt (confirmed live), so there's no direct
    // multimodal API integration here -- just save the bytes and reference
    // the returned path in the prompt text. Modes 1/2 never invoke agy, so
    // the attach button stays disabled outside Mode 3 (see
    // updateAttachBtnState(), called from updateStreamModeButton()).
    let pendingAttachments = [];
    let attachmentSeq = 0;

    function updateAttachBtnState() {
      const btn = document.getElementById('attach-btn');
      if (!btn) return;
      const enabled = currentStreamMode === '3';
      btn.classList.toggle('disabled', !enabled);
      btn.title = enabled ? '파일 또는 이미지 추가' : '파일 첨부는 CLI 추론 모드에서만 가능합니다';
    }

    function triggerFileAttach() {
      if (currentStreamMode !== '3') {
        notSupportedYet('파일 첨부는 CLI 추론 모드에서만');
        return;
      }
      const input = document.getElementById('attach-file-input');
      if (input) input.click();
    }

    function isImageFile(file) {
      return file.type && file.type.startsWith('image/');
    }

    function readFileAsDataURL(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }

    // Files are only staged (local preview, no network call) on selection --
    // the actual upload happens in sendMessage(), bundled with the message
    // send itself, so "attach + type + send" reads as one action instead of
    // two separate steps. Shared by the file-picker (handleFilesSelected)
    // and clipboard image paste (see the 'paste' listener below).
    async function stageFiles(files) {
      if (!files || files.length === 0) return;
      const entries = [];
      for (const file of files) {
        const id = ++attachmentSeq;
        let previewUrl = null;
        if (isImageFile(file)) {
          try { previewUrl = await readFileAsDataURL(file); } catch (e) {}
        }
        entries.push({ id, filename: file.name, previewUrl, isImage: isImageFile(file), path: null, url: null, uploading: false, error: null, file });
      }
      pendingAttachments = pendingAttachments.concat(entries);
      renderAttachPreviewRow();
    }

    async function handleFilesSelected(event) {
      const files = Array.from(event.target.files || []);
      event.target.value = ''; // allow re-selecting the same file later
      await stageFiles(files);
    }

    // Ctrl+V an image straight into the composer to attach it -- same
    // staging path as the file-picker button (stageFiles()), same Mode 3
    // restriction (see triggerFileAttach()). Only intercepts when the
    // clipboard actually carries image data; a plain text paste falls
    // through untouched so normal typing keeps working.
    (function setupImagePaste() {
      const input = document.getElementById('user-input');
      if (!input) return;
      input.addEventListener('paste', async (e) => {
        const items = e.clipboardData && e.clipboardData.items;
        if (!items) return;
        const imageFiles = [];
        for (const item of items) {
          if (item.kind === 'file' && item.type && item.type.startsWith('image/')) {
            const file = item.getAsFile();
            if (file) imageFiles.push(file);
          }
        }
        if (imageFiles.length === 0) return; // no image in clipboard -- let normal text paste proceed

        e.preventDefault();
        if (currentStreamMode !== '3') {
          notSupportedYet('파일 첨부는 CLI 추론 모드에서만');
          return;
        }
        // Clipboard images usually have no real filename (or the browser's
        // generic "image.png" for every single paste) -- synthesize a unique
        // one so the preview chip and upload payload aren't blank/ambiguous.
        const named = imageFiles.map((f, i) => {
          if (f.name && f.name !== 'image.png') return f;
          const ext = (f.type.split('/')[1] || 'png').split('+')[0];
          return new File([f], `클립보드_이미지_${Date.now()}_${i + 1}.${ext}`, { type: f.type });
        });
        await stageFiles(named);
      });
    })();

    async function uploadAttachment(entry) {
      entry.uploading = true;
      entry.error = null;
      renderAttachPreviewRow();
      try {
        const dataUrl = entry.previewUrl || await readFileAsDataURL(entry.file);
        const base64 = dataUrl.split(',')[1] || '';
        const apiUrl = new URL('api/upload', window.location.href).href;
        const res = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ files: [{ filename: entry.filename, data: base64, content_type: entry.file.type || '' }] })
        });
        entry.uploading = false;
        if (!res.ok) {
          entry.error = `업로드 실패 (HTTP ${res.status})`;
        } else {
          const data = await res.json();
          const result = (data.files || [])[0];
          if (result && result.path) {
            entry.path = result.path;
            entry.url = result.url;
          } else {
            entry.error = (result && result.error) || '업로드 실패';
          }
        }
      } catch (e) {
        entry.uploading = false;
        entry.error = `업로드 실패: ${e.message || e}`;
      }
      renderAttachPreviewRow();
    }

    function removeAttachment(id) {
      pendingAttachments = pendingAttachments.filter(a => a.id !== id);
      renderAttachPreviewRow();
    }

    function renderAttachPreviewRow() {
      const row = document.getElementById('attach-preview-row');
      if (!row) return;
      if (pendingAttachments.length === 0) {
        row.style.display = 'none';
        row.innerHTML = '';
        return;
      }
      row.style.display = 'flex';
      row.innerHTML = pendingAttachments.map(a => `
        <div class="attach-chip ${a.error ? 'attach-chip-error' : ''}">
          ${a.isImage && a.previewUrl
            ? `<img src="${a.previewUrl}" alt="">`
            : `<span class="attach-chip-file-icon">📄</span>`}
          <span class="attach-chip-text">
            <span class="attach-chip-name">${a.filename}</span>
            ${a.uploading ? `<span class="attach-chip-status">업로드 중…</span>` : ''}
            ${a.error ? `<span class="attach-chip-status attach-chip-status-error">⚠️ ${a.error}</span>` : ''}
          </span>
          <button class="attach-chip-remove" onclick="removeAttachment(${a.id})">&times;</button>
        </div>
      `).join('');
    }

    function sendQuick(prompt) {
      const input = document.getElementById('user-input');
      input.value = prompt;
      updateSendBtn();
      autoResizeTextarea();
      sendMessage();
    }

    // "/" slash-command autocomplete -- placeholder text ("/ for actions")
    // implied this was always meant to exist, never actually wired up.
    // Scope kept to commands genuinely confirmed to work through this chat
    // (not agy's full TUI slash-command list -- most of those are
    // interactive-only and untested in headless -p mode):
    //   /codesearch -- client-side only (core/codesearch.py), never touches agy
    //   /usage, /credits -- confirmed live: agy -p "/usage"|"/credits" both
    //     return real data in headless print mode (see core/usage_client.py)
    const SLASH_COMMANDS = [
      { cmd: '/codesearch', usage: '/codesearch <검색어>', desc: '워크스페이스 코드 검색 (agy 연동 없는 자체 grep)', insertSuffix: ' ' },
      { cmd: '/usage', usage: '/usage', desc: '모델 사용량/쿼터 조회 (CLI 추론 모드)', insertSuffix: '' },
      { cmd: '/credits', usage: '/credits', desc: 'G1 크레딧 잔량 조회 (CLI 추론 모드)', insertSuffix: '' },
    ];
    let slashMenuVisibleCommands = [];
    let slashMenuActiveIndex = -1;

    function isSlashMenuOpen() {
      const menu = document.getElementById('slash-command-menu');
      return !!menu && menu.classList.contains('open');
    }

    // Only triggers when "/" starts the WHOLE message and no space has been
    // typed yet (i.e. still composing the command name itself) -- matches
    // Slack/Discord-style slash-command UX, and doesn't hijack a literal "/"
    // typed mid-sentence.
    function updateSlashCommandMenu() {
      const input = document.getElementById('user-input');
      if (!input) return;
      const match = /^\/([a-zA-Z가-힣]*)$/.exec(input.value);
      if (!match) {
        closeSlashCommandMenu();
        return;
      }
      const typed = match[1].toLowerCase();
      slashMenuVisibleCommands = SLASH_COMMANDS.filter(c => c.cmd.slice(1).toLowerCase().startsWith(typed));
      if (slashMenuVisibleCommands.length === 0) {
        closeSlashCommandMenu();
        return;
      }
      slashMenuActiveIndex = 0;
      renderSlashCommandMenu();
      const menu = document.getElementById('slash-command-menu');
      if (menu) menu.classList.add('open');
    }

    function renderSlashCommandMenu() {
      const menu = document.getElementById('slash-command-menu');
      if (!menu) return;
      menu.innerHTML = slashMenuVisibleCommands.map((c, i) => `
        <div class="slash-command-row ${i === slashMenuActiveIndex ? 'active' : ''}" onmousedown="event.preventDefault(); selectSlashCommand(${i})">
          <span class="cmd">${c.usage}</span>
          <span class="desc">${c.desc}</span>
        </div>
      `).join('');
    }

    function closeSlashCommandMenu() {
      const menu = document.getElementById('slash-command-menu');
      if (menu) menu.classList.remove('open');
      slashMenuVisibleCommands = [];
      slashMenuActiveIndex = -1;
    }

    function selectSlashCommand(index) {
      const c = slashMenuVisibleCommands[index];
      const input = document.getElementById('user-input');
      if (!c || !input) return;
      input.value = c.cmd + (c.insertSuffix || '');
      closeSlashCommandMenu();
      updateSendBtn();
      autoResizeTextarea();
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }

    function handleKey(e) {
      if (isSlashMenuOpen()) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          slashMenuActiveIndex = (slashMenuActiveIndex + 1) % slashMenuVisibleCommands.length;
          renderSlashCommandMenu();
          return;
        }
        if (e.key === 'ArrowUp') {
          e.preventDefault();
          slashMenuActiveIndex = (slashMenuActiveIndex - 1 + slashMenuVisibleCommands.length) % slashMenuVisibleCommands.length;
          renderSlashCommandMenu();
          return;
        }
        if (e.key === 'Enter' || e.key === 'Tab') {
          e.preventDefault();
          selectSlashCommand(slashMenuActiveIndex);
          return;
        }
        if (e.key === 'Escape') {
          e.preventDefault();
          closeSlashCommandMenu();
          return;
        }
      }
      updateSendBtn();
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    }

    // Self-implemented /codesearch (see core/codesearch.py) -- a plain
    // workspace grep, rendered through the same bot-bubble skeleton as a
    // real answer (createBotStreamMessage/.setText()/.finish()) so it looks
    // native in the chat instead of needing a separate results panel.
    async function runCodeSearch(query, streamMode) {
      const input = document.getElementById('user-input');
      appendUserMessage(`/codesearch ${query}`);
      input.value = '';
      closeSlashCommandMenu();
      autoResizeTextarea();

      const streamUI = createBotStreamMessage(streamMode);
      try {
        const apiUrl = new URL('api/codesearch', window.location.href).href;
        const res = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query }),
        });
        const data = await res.json();
        const matches = data.matches || [];
        const root = data.root || '';
        if (matches.length === 0) {
          streamUI.setText(`\`${query}\`에 대한 검색 결과가 없습니다. (검색 루트: \`${root}\`)`);
        } else {
          const lines = matches.map(m => `**${m.file}:${m.line}**\\n\`\`\`\\n${m.text}\\n\`\`\``).join('\\n\\n');
          const suffix = data.truncated ? `\\n\\n_(결과가 많아 상위 ${matches.length}개만 표시했습니다)_` : '';
          streamUI.setText(`검색어 \`${query}\` — ${matches.length}개 결과 (검색 루트: \`${root}\`)\\n\\n${lines}${suffix}`);
        }
      } catch (e) {
        streamUI.setText(`[오류] 코드 검색 실패: ${e.message || e}`);
      } finally {
        streamUI.finish();
        input.focus();
      }
    }

    async function sendMessage() {
      // While a Mode 3 generation is in flight, the send button doubles as a
      // stop button (see updateSendBtn()) -- clicking it here means "stop",
      // not "send".
      if (isStreamActive) {
        stopGeneration();
        return;
      }

      const input = document.getElementById('user-input');
      const btn = document.getElementById('send-btn');
      const streamMode = parseInt(currentStreamMode) || 1;
      const typedText = input.value.trim();
      if (!typedText && pendingAttachments.length === 0) return;
      if (pendingAttachments.some(a => a.uploading)) return; // already sending

      // Self-implemented /codesearch -- agy has no headless code-search
      // command (see core/codesearch.py), so this bypasses the SSE chat
      // pipeline entirely and just greps the workspace directly. Matches
      // "/codesearch" alone (no query yet) too -- not just "/codesearch "
      // with a trailing space -- since typedText is already .trim()'d above
      // and would otherwise fall through and get sent to agy as a literal,
      // meaningless chat prompt instead of a clear "type a query" nudge.
      const codesearchMatch = /^\/codesearch(?:\s+(.*))?$/i.exec(typedText);
      if (codesearchMatch) {
        const query = (codesearchMatch[1] || '').trim();
        if (!query) {
          showToast('검색어를 입력하세요. 예: /codesearch 조명');
          return;
        }
        await runCodeSearch(query, streamMode);
        return;
      }

      // Upload happens here, bundled into the send action itself, rather than
      // eagerly on file selection -- "attach + type + send" is one step.
      // Attempt every not-yet-uploaded (or previously failed) attachment;
      // one that still errors is simply left out of the message below.
      const toUpload = pendingAttachments.filter(a => !a.path);
      if (toUpload.length > 0) {
        btn.disabled = true;
        await Promise.all(toUpload.map(uploadAttachment));
      }
      const readyAttachments = pendingAttachments.filter(a => a.path && !a.error);
      if (!typedText && readyAttachments.length === 0) {
        btn.disabled = false;
        updateSendBtn();
        return; // every attachment failed and there's no text -- nothing to send
      }

      // Attachments are woven in as markdown at the top of the message, in
      // two parallel versions: `path` (the container's absolute filesystem
      // path) is what actually goes to agy -- its own `view_file` tool reads
      // straight off disk and genuinely understands images given just that
      // path in a headless -p prompt (confirmed live, see core/uploads.py).
      // `url` (this server's own GET /api/uploads/<batch>/<file>) is what the
      // *browser* renders instead, since it can't load a raw container path.
      // Non-image files use a plain bold label instead of a markdown link --
      // the container path isn't browser-fetchable either way, so a link
      // would just be dead weight.
      const bodyText = typedText || '첨부된 파일을 확인해줘.';
      const attachmentsMarkdownFor = (pathField) => readyAttachments.map(a =>
        a.isImage ? `![${a.filename}](${a[pathField]})` : `📄 **${a.filename}**`
      ).join('\\n');

      const prompt = readyAttachments.length > 0
        ? `${attachmentsMarkdownFor('path')}\\n\\n${bodyText}`
        : bodyText;
      const displayMarkdown = readyAttachments.length > 0
        ? `${attachmentsMarkdownFor('url')}\\n\\n${bodyText}`
        : bodyText;

      const hero = document.getElementById('chat-hero-card');
      if (hero) hero.remove();

      appendUserMessage(displayMarkdown);
      input.value = '';
      closeSlashCommandMenu();
      autoResizeTextarea();
      pendingAttachments = [];
      renderAttachPreviewRow();

      // Attachments only work under Mode 3 (agy's view_file tool) -- force it
      // even if the disabled attach button was somehow bypassed while another
      // mode was selected, so the referenced paths are actually usable.
      const effectiveStreamMode = readyAttachments.length > 0 ? 3 : streamMode;
      const streamUI = createBotStreamMessage(effectiveStreamMode);
      const isDirectLLM = prompt.startsWith('ai ') || prompt.startsWith('/llm');
      const isMobile = window.innerWidth < 768;

      isStreamActive = true;
      activeStreamModeForStop = effectiveStreamMode;
      activeStreamId = '';
      activeAbortController = new AbortController();
      updateSendBtn();

      try {
        const apiUrl = new URL('api/chat', window.location.href).href;
        const res = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          signal: activeAbortController.signal,
          body: JSON.stringify({
            prompt: prompt,
            conversation_id: currentConversationId,
            is_direct_llm: isDirectLLM,
            stream_mode: effectiveStreamMode,
            client_width: window.innerWidth,
            is_mobile: isMobile,
            model: resolveCurrentModelSlug(),
            agent: currentAgentId
          })
        });

        if (!res.ok) {
          streamUI.setText(`[오류] 서버 응답 코드 HTTP ${res.status}`);
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
              } else if (ev.type === 'stream_id') {
                activeStreamId = ev.content;
              } else if (ev.type === 'live_log' || ev.type === 'tool') {
                streamUI.addLiveLog(ev.content);
              } else if (ev.type === 'reasoning_step') {
                streamUI.addReasoningStep(ev.data);
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
        if (err.name === 'AbortError') {
          if (!streamUI.hasContent()) streamUI.setText('⏹️ 중지되었습니다.');
        } else if (!streamUI.hasContent()) {
          streamUI.setText(`[오류] 실시간 스트림 연결 실패: ${err.message}`);
        }
        streamUI.finish();
      } finally {
        isStreamActive = false;
        activeStreamId = '';
        activeAbortController = null;
        activeStreamModeForStop = 0;
        btn.disabled = false;
        updateSendBtn();
        input.focus();
      }
    }
""".strip()
