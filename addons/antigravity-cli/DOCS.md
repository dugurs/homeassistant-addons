# Google Antigravity CLI - Home Assistant Add-on

[![Current Version](https://img.shields.io/badge/version-1.1.0--beta.82-blue.svg)](config.yaml)

이 애드온은 Home Assistant 내부에서 **Google Antigravity CLI (`agy`)**를 구동하고, Home Assistant의 모든 기기와 상태를 AI 요원이 직접 제어할 수 있도록 완벽하게 연동해 주는 커스텀 애드온입니다.

## ✨ 주요 기능 (Features)

*   **웹 기반 터미널 (Web Terminal):** Home Assistant 대시보드 내에서 곧바로 Antigravity CLI에 접속할 수 있습니다.
*   **완벽한 MCP(Model Context Protocol) 연동:**
    *   초고속 Python 패키지 매니저 `uv`를 통해 공식 **`ha-mcp`**를 **`stdio` 프로세스**로 실행하여 88개 이상의 Home Assistant 전용 도구(조명 제어, 센서 읽기, 자동화 관리 등)를 AI에게 즉시 제공합니다.
    *   Antigravity CLI의 공식 MCP 전송 방식인 `stdio`를 올바르게 활용하므로 `Method Not Allowed` 에러 없이 안정적으로 연결됩니다.
*   **백그라운드 세션 유지 (Tmux):** 브라우저 창을 닫아도 AI의 작업과 채팅 세션이 백그라운드(`tmux`)에서 그대로 유지됩니다.
*   **영구 저장소 (Persistence):** AI의 설정, 인증 정보, 사용자가 만든 스킬 등은 Home Assistant의 `/config/.gemini` 폴더에 안전하게 영구 저장되어 애드온을 재시작하거나 업데이트해도 날아가지 않습니다.

## 🚀 설치 및 실행 (Installation)

아래 버튼을 클릭하여 Home Assistant에 이 애드온 저장소를 간편하게 추가할 수 있습니다:

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fdugurs%2Fhomeassistant-addons)

1.  저장소 추가가 완료되면 **Settings > Add-ons > Add-on Store** 로 이동합니다.
2.  우측 상단의 점 3개 메뉴를 눌러 **Repositories**를 선택하고, 이 커스텀 애드온의 저장소 URL을 추가합니다.
3.  새로고침 후 목록에서 **"Google Antigravity CLI"** 애드온을 찾아 설치합니다.
4.  **"Start"** 버튼을 눌러 애드온을 실행합니다.
5.  **"Open Web UI"** 버튼을 클릭하면 브라우저에 쾌적한 터미널이 열립니다.
6.  터미널에서 `agy` 가 실행되면 **최초 1회** `ha-mcp` 패키지가 자동으로 다운로드됩니다 (약 10~20초 소요).
7.  다운로드가 완료되면 agy 프롬프트(`>`)에서 아래 명령을 입력해 MCP 연결 상태를 확인합니다:
    ```
    /mcp
    ```
    `home-assistant` 서버가 **✓ connected** 상태로 표시되면 정상적으로 설치된 것입니다.

## 🛠 사용 방법 (Usage)

터미널이 열리면 일반적인 대화형 AI를 쓰듯이 프롬프트(`>`)에 자연어로 명령을 내리시면 됩니다.

**명령어 예시:**
> *"거실 온도 몇 도야?"*
> *"집에 켜져 있는 조명 다 꺼줘"*
> *"최근 1시간 동안 냉장고 전력 사용량 그래프 그려줘"*

### 💡 터미널(Tmux) 스크롤 및 기본 사용법

이 애드온은 백그라운드 세션 유지를 위해 내부적으로 `tmux`를 사용합니다. 터미널의 이전 출력 내용을 (스크롤하여) 확인하려면 다음 단축키를 사용하세요:

*   **스크롤 모드 진입**: `Ctrl + B`를 누른 후 `[` 키를 누릅니다. (또는 마우스 휠을 위로 굴리면 자동으로 진입합니다)
*   **스크롤 이동**: 방향키(위/아래)나 `Page Up` / `Page Down` 키를 사용하여 이전 대화 내용을 확인합니다.
*   **스크롤 모드 종료**: `Esc` 키 또는 `q` 키를 누르면 원래 프롬프트 화면으로 돌아옵니다.

### ⚙️ 설정 (Configuration)

기본적으로 애드온이 Home Assistant의 `SUPERVISOR_TOKEN`을 자동으로 감지하여 모든 권한을 알아서 설정합니다. 사용자가 수동으로 IP나 토큰을 입력할 필요가 없습니다.

*   `ha_sse_url` (선택 사항): [ha-mcp HACS 커스텀 컴포넌트](https://github.com/homeassistant-ai/ha-mcp-integration) 등 외부 MCP 서버의 Streamable HTTP URL을 직접 지정할 때 사용합니다. 비워두면 `uvx ha-mcp@latest`를 `stdio`로 자동 실행합니다.

## 📝 문제 해결 (Troubleshooting)

*   **AI가 기기를 제어하려고 할 때 권한을 묻는다면?**
    최초 1회 실행 시 보안을 위해 도구 접근 권한을 물어봅니다. 선택지에서 **"Yes, and always allow... (Persist to settings.json)"** 항목을 선택하시면 이후부터는 묻지 않고 스스로 제어합니다.

*   **CLI에서 한 번에 ha-mcp의 모든 기능에 대한 권한을 허용하려면?**
    채팅창에 아래와 같이 입력하면 AI가 권한 설정을 수정해 줍니다.
    ```
    ~/.gemini/antigravity-cli/settings.json 파일의 permissions.allow에 "mcp(home-assistant/*)"를 추가해 줘
    ```

*   **`ha-mcp` 첫 실행 시 느리다면?**
    최초 실행 시 `uvx`가 `ha-mcp@latest` 패키지를 다운로드합니다 (약 10~20초). 이후 실행부터는 캐시를 사용하므로 즉시 시작됩니다.

*   **MCP 서버가 `Method Not Allowed` 에러를 낸다면?** (v1.0.2 이하에서 업그레이드 시)
    v1.0.3부터 SSE HTTP 서버 방식을 제거하고 Antigravity CLI의 공식 지원 방식인 `stdio`로 전환했습니다. 애드온을 최신 버전으로 업데이트 후 재시작하면 해결됩니다.

## 🏗 아키텍처 및 내부 구조

*   **ttyd + tmux**: 브라우저와 터미널 환경을 이어줍니다.
*   **uvx + ha-mcp (stdio)**: `agy`가 MCP 서버가 필요할 때 `uvx ha-mcp@latest`를 자식 프로세스(stdio)로 실행합니다. Antigravity CLI는 `stdio` 전송만 지원하므로 이 방식이 공식적으로 올바른 연결 방법입니다.
*   **SUPERVISOR_TOKEN 자동 주입**: 컨테이너 환경에서 토큰을 자동으로 읽어 `ha-mcp`에 환경 변수로 전달하므로 별도의 Long-Lived Access Token 발급이 불필요합니다.
*   **Bash 래퍼 스크립트**: x86_64 및 ARM(QEMU) 환경 모두에서 구동될 수 있도록 동적으로 바이너리 호환성을 맞춰줍니다.
