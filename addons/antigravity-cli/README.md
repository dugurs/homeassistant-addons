# Google Antigravity CLI - Home Assistant Add-on

[![Current Version](https://img.shields.io/badge/version-1.3.1--beta.1-blue.svg)](config.yaml)

이 애드온은 Home Assistant 내부에서 **Google Antigravity CLI (`agy`)**를 구동하고, Home Assistant의 모든 기기와 상태를 AI 요원이 직접 제어할 수 있도록 완벽하게 연동해 주는 커스텀 애드온입니다.

*   **웹 기반 듀얼 인터페이스**: 인그레스 대시보드 안에서 곧바로 웹 터미널(ttyd/tmux)과 직관적인 반응형 웹 UI 지원
*   **완벽한 MCP 연동**: 공식 `ha-mcp`를 `stdio`로 실행해 조명 제어, 센서 읽기, 자동화 관리 등 88개 이상의 HA 전용 도구 제공
*   **경량 관제 모니터링 모드 (`enable_chat_ui: false`)**: 리모트 데몬 위주 사용 시 웹 UI 채팅을 꺼서 200~300MB 메모리 스파이크를 원천 방지하고 가벼운 실시간 대시보드로 전환
*   **모바일 2×2 반응형 뷰 & 실시간 사용률 그래프**: 스마트폰 환경에 최적화된 2×2 상태 카드 그리드 및 초고해상도 실시간 CPU/RAM 스파크라인 차트
*   **리모트 데몬 원격 제어 (`agy remote-control serve`)**: 구글 공식 원격 웹 대시보드(`antigravity.google.com`) 연동 및 안전한 끄기 잠금(busy lock) 지원
*   **백그라운드 세션 유지**: 브라우저를 닫아도 `tmux` 세션에서 작업이 계속 유지
*   **영구 저장소**: 설정/인증/스킬 등이 `/config/.gemini`에 안전하게 보관되어 재시작/리빌드 후에도 유지

📖 **[고속 제어 모드 명령어 가이드](https://dugurs.github.io/homeassistant-addons/fast-control-guide/)** — 자연어로 쓸 수 있는 전체 명령어와 활용법 정리  
📖 **[CLI 추론 모드 가이드](https://dugurs.github.io/homeassistant-addons/cli-reasoning-guide/)** — agy 기반 심층 에이전트의 로그인, 모델·에이전트 선택, 파일 첨부, MCP 연동 정리

### 🧩 기본 제공 구성 요소

설치 즉시 아래가 자동으로 세팅됩니다 (업데이트해도 유지됨). 자세한 설명은 **설명(Documentation)** 탭 참고:

*   **MCP**: 공식 `ha-mcp` (조명 제어·센서 조회·자동화 관리 등 88개 이상 도구, 토큰 자동 주입) — 출처: [homeassistant-ai/ha-mcp](https://github.com/homeassistant-ai/ha-mcp)
*   **에이전트 스킬**: `home-assistant-best-practices` (자동화/헬퍼/대시보드 작성 시 베스트 프랙티스 자동 참고) — 출처: [homeassistant-ai/skills](https://github.com/homeassistant-ai/skills/tree/main/skills/home-assistant-best-practices)
*   **커스텀 에이전트 5종** (CLI 모드에서 전환): Orchestrator(기본)·Automation Engineer·Dashboard Designer·Diagnostics Operator·Smart Controller
*   **훅**: `ha-file-guard` — HA 핵심 파일(`.storage`, `secrets.yaml`, `configuration.yaml` 등) 삭제/덮어쓰기 무조건 차단
*   **하네스 규칙**: `ha-guidelines`(ha-mcp 도구 우선 사용), `ha-file-safety`(삭제/덮어쓰기 전 승인 필수 + 핵심 데이터는 승인해도 거부)

### 📦 웹 UI에 포함된 오픈소스 라이브러리

*   **[jsdiff](https://github.com/kpdecker/jsdiff)** (`diff` 9.0.0, BSD-3-Clause) — CLI 추론 모드의 파일 수정 내역을 실제 줄 단위로 비교해 보여주는 diff 뷰어에 사용. 외부 네트워크 요청 없이 애드온에 직접 내장(vendoring)되어 있습니다.

자세한 설치 방법, 사용법, 문제 해결은 **설명(Documentation)** 탭을 참고하세요.
