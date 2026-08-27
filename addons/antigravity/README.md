# Google Antigravity CLI - Home Assistant Add-on

[![Current Version](https://img.shields.io/badge/version-1.0.52-blue.svg)](config.yaml)

이 애드온은 Home Assistant 내부에서 **Google Antigravity CLI (`agy`)**를 구동하고, Home Assistant의 모든 기기와 상태를 AI 요원이 직접 제어할 수 있도록 완벽하게 연동해 주는 커스텀 애드온입니다.

## ✨ 주요 기능 (Features)

*   **웹 기반 터미널 (Web Terminal):** Home Assistant 대시보드 내에서 곧바로 Antigravity CLI에 접속할 수 있습니다.
*   **완벽한 MCP(Model Context Protocol) 연동:** 
    *   내장된 Node.js 기반의 **HTTP (SSE) MCP 서버**(`@jango-blockchained/homeassistant-mcp`)를 통해 50개 이상의 Home Assistant 전용 도구(조명 제어, 센서 읽기, 이벤트 구독 등)를 AI에게 즉시 제공합니다.
    *   기존 `stdio` 통신 방식의 64KB 페이로드 제한을 완벽하게 우회하여 수백 개의 기기가 있는 환경에서도 쾌적하고 안정적으로 작동합니다.
*   **백그라운드 세션 유지 (Tmux):** 브라우저 창을 닫아도 AI의 작업과 채팅 세션이 백그라운드(`tmux`)에서 그대로 유지됩니다.
*   **영구 저장소 (Persistence):** AI의 설정, 인증 정보, 사용자가 만든 스킬 등은 Home Assistant의 `/config/.gemini` 폴더에 안전하게 영구 저장되어 애드온을 재시작하거나 업데이트해도 날아가지 않습니다.

## 🚀 설치 및 실행 (Installation)

1.  Home Assistant의 **Settings > Add-ons > Add-on Store** 로 이동합니다.
2.  우측 상단의 점 3개 메뉴를 눌러 **Repositories**를 선택하고, 이 커스텀 애드온의 저장소 URL을 추가합니다.
3.  목록에서 **"Google Antigravity CLI"** 애드온을 찾아 설치합니다.
4.  **"Start"** 버튼을 눌러 애드온을 실행합니다.
5.  **"Open Web UI"** 버튼을 클릭하면 브라우저에 쾌적한 터미널이 열리며 AI와의 대화가 시작됩니다.

## 🛠 사용 방법 (Usage)

터미널이 열리면 일반적인 대화형 AI를 쓰듯이 프롬프트(`>`)에 자연어로 명령을 내리시면 됩니다.

**명령어 예시:**
> *"거실 온도 몇 도야?"*
> *"집에 켜져 있는 조명 다 꺼줘"*
> *"최근 1시간 동안 냉장고 전력 사용량 그래프 그려줘"*

### ⚙️ 설정 (Configuration)

기본적으로 애드온이 Home Assistant의 `SUPERVISOR_TOKEN`을 자동으로 감지하여 모든 권한을 알아서 설정합니다. 사용자가 수동으로 IP나 토큰을 입력할 필요가 없습니다.

*   `ha_sse_url` (선택 사항): 외부 서버의 MCP SSE URL을 연결하고 싶을 때만 사용하며, 비워두면 내장된 HA 서버를 자동 사용합니다.

## 📝 문제 해결 (Troubleshooting)

*   **AI가 기기를 제어하려고 할 때 권한을 묻는다면?**
    최초 1회 실행 시 보안을 위해 도구 접근 권한을 물어봅니다. 선택지에서 **"Yes, and always allow... (Persist to settings.json)"** 항목을 선택하시면 이후부터는 묻지 않고 스스로 제어합니다.
*   **CLI에서 한 번에 모든 권한을 허용하려면?**
    채팅창에 *"모든 home-assistant 도구를 영구 허용하도록 내 ~/.gemini/config/settings.json 파일을 수정해 줘."* 라고 입력하면 AI가 스스로 권한 설정을 일괄 수정해 줍니다.

## 🏗 아키텍처 및 내부 구조

*   **ttyd + tmux**: 브라우저와 터미널 환경을 이어줍니다.
*   **Node.js 22 + FastMCP**: `0.0.0.0:7123` 포트로 SSE(Server-Sent Events) 프로토콜을 열어 대용량 기기 스키마 목록을 안전하게 Antigravity CLI와 통신합니다.
*   **Bash 래퍼 스크립트**: x86_64 및 ARM(QEMU) 환경 모두에서 구동될 수 있도록 동적으로 바이너리 호환성을 맞춰줍니다.
