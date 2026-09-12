# Google Antigravity CLI - Home Assistant Add-on

[![Current Version](https://img.shields.io/badge/version-1.3.1--beta.1-blue.svg)](config.yaml)

이 애드온은 Home Assistant 내부에서 **Google Antigravity CLI (`agy`)**를 구동하고, Home Assistant의 모든 기기와 상태를 AI 요원이 직접 제어할 수 있도록 완벽하게 연동해 주는 커스텀 애드온입니다.

## ✨ 주요 기능 (Features)

*   **웹 기반 터미널 (Web Terminal):** Home Assistant 대시보드 내에서 곧바로 Antigravity CLI에 접속할 수 있습니다.
*   **완벽한 MCP(Model Context Protocol) 연동:**
    *   초고속 Python 패키지 매니저 `uv`를 통해 공식 **`ha-mcp`**를 **`stdio` 프로세스**로 실행하여 88개 이상의 Home Assistant 전용 도구(조명 제어, 센서 읽기, 자동화 관리 등)를 AI에게 즉시 제공합니다.
    *   Antigravity CLI의 공식 MCP 전송 방식인 `stdio`를 올바르게 활용하므로 `Method Not Allowed` 에러 없이 안정적으로 연결됩니다.
*   **백그라운드 세션 유지 (Tmux):** 브라우저 창을 닫아도 AI의 작업과 채팅 세션이 백그라운드(`tmux`)에서 그대로 유지됩니다.
*   **영구 저장소 (Persistence):** AI의 설정, 인증 정보, 사용자가 만든 스킬 등은 Home Assistant의 `/config/.gemini` 폴더에 안전하게 영구 저장되어 애드온을 재시작하거나 업데이트해도 날아가지 않습니다.

## 📖 관련 문서

*   **[고속 제어 모드 명령어 가이드](https://dugurs.github.io/homeassistant-addons/fast-control-guide/)** — 자연어로 쓸 수 있는 전체 명령어와 활용법 정리
*   **[CLI 추론 모드 가이드](https://dugurs.github.io/homeassistant-addons/cli-reasoning-guide/)** — agy 기반 심층 에이전트의 로그인, 모델·에이전트 선택, 파일 첨부, MCP 연동 정리

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

| 옵션명 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `auto_start_remote_control` | bool | `false` | 애드온 부팅 시 백그라운드로 `agy remote-control serve` 데몬을 자동 시작합니다. 웹 대시보드나 리모트 세션을 주로 쓸 때 추천합니다. |
| `enable_terminal` | bool | `true` | 인그레스 웹 터미널(`ttyd` 및 `tmux`)을 띄울지 여부입니다. 최초 로그인 후 터미널을 안 쓸 때 `false`로 끄면 메모리를 절약할 수 있습니다. |
| `enable_chat_ui` | bool | `true` | 웹 UI AI 채팅 및 대화창을 띄울지 여부입니다. 리모트 데몬만 쓸 때 `false`로 끄면 웹 UI가 모니터링 전용 대시보드로 전환되어 메모리 피크 스파이크(200~300MB)를 원천 차단합니다. |
| `dangerous_mode` | bool | `true` | 채팅(CLI 추론 모드)과 리모트 데몬에 `--dangerously-skip-permissions`를 붙입니다. 끄면 agy가 무한 대기(hang)할 수 있으므로 `true` 권장. |
| `api_port` | port | `8000` | 애드온의 REST/SSE 및 상태 API 포트 번호입니다. |
| `api_key` | string | `""` (비움) | 외부 클라이언트 접근용 인증 토큰입니다. 비워두면 로컬 네트워크에서 인증 없이 접근 가능합니다. |
| `print_timeout` | string | `"5m"` | CLI 헤드리스 실행 최대 타임아웃 시간입니다. |
| `ha_sse_url` | string | `""` (비움) | 외부 MCP 서버(HACS 컴포넌트 등)의 HTTP/SSE URL을 직접 지정할 때 사용합니다. 비워두면 로컬 stdio(`uvx ha-mcp@latest`)로 자동 실행됩니다. |
| `enable_sandbox` | bool | `false` | CLI 실행 시 샌드박스 컨테이너 격리를 적용할지 여부입니다. |


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

## 🧩 기본 제공 구성 요소 (MCP · 스킬 · 에이전트 · 훅 · 규칙)

애드온을 설치하면 아래 항목들이 자동으로 세팅됩니다. 대부분 CLI 추론 모드(agy)에서 의미가 있는 구성이며, 매 부팅마다 3-way 병합 방식으로 배포되므로 애드온이 업데이트돼도 사용자가 직접 수정해둔 내용은 보존됩니다.

*   **MCP 서버 — `ha-mcp`**
    공식 Home Assistant MCP 서버를 `uvx ha-mcp@latest`로 `stdio` 실행해 자동 연결합니다. 조명/스위치 제어, 센서 조회, 자동화·스크립트·씬 생성/수정, 백업 관리 등 **88개 이상의 도구**를 제공하며, `SUPERVISOR_TOKEN`을 자동 주입하므로 별도 토큰 발급이 필요 없습니다.
    출처: [homeassistant-ai/ha-mcp](https://github.com/homeassistant-ai/ha-mcp) (MIT License, PyPI `ha-mcp` 패키지)

*   **에이전트 스킬 — `home-assistant-best-practices`**
    자동화/헬퍼/스크립트/대시보드/블루프린트 작성 시 자동으로 참고하는 베스트 프랙티스 모음입니다. Jinja2 템플릿 대신 네이티브 옵션을 쓸지, 헬퍼를 어떻게 고를지, 카드 종류나 도메인 문서를 어디서 찾을지 등을 CLI 모드가 상황에 맞게 자동으로 불러와 적용합니다.
    출처: [homeassistant-ai/skills](https://github.com/homeassistant-ai/skills/tree/main/skills/home-assistant-best-practices) — 이미지 빌드 시 최신 버전을 자동으로 가져오고, 네트워크 실패 시에만 이 저장소에 내장된 스냅샷([bundled/skills/home-assistant-best-practices](bundled/skills/home-assistant-best-practices))으로 대체됩니다.

*   **커스텀 에이전트 (CLI 모드 입력창의 "에이전트 선택"에서 전환 가능)**

    | 에이전트 | 전문 분야 |
    |---|---|
    | HA Antigravity Orchestrator (기본) | 자동화/대시보드/진단/실시간 제어 중 어떤 영역인지 스스로 판단해 직접 처리하는 총괄 에이전트 |
    | HA Automation Engineer | 자동화·스크립트·씬 설계, YAML 검증, 트레이스(Trace) 디버깅 |
    | HA Dashboard Designer | Lovelace 대시보드 뷰/카드 디자인, 리소스 등록, 반응형 레이아웃 |
    | HA Diagnostics Operator | HA/애드온 로그 분석, 오프라인 기기 탐지, 시스템 헬스체크 |
    | HA Smart Controller | 조명/스위치/냉난방 실시간 제어, 모드 일괄 제어, 상태 브리핑 |

*   **훅(Hook) — `ha-file-guard`**
    파일 삭제/덮어쓰기 도구가 호출되기 직전(PreToolUse)에 가로채, `/homeassistant/.storage`, `secrets.yaml`, `configuration.yaml`, `automations.yaml`, `home-assistant_v2.db`, `/backup` 등 HA 핵심 데이터를 대상으로 한 `rm`/`mv`/덮어쓰기 시도를 스크립트 레벨에서 무조건 차단합니다. 사용자 승인 여부와 무관하게 항상 거부되는 최후 방어선이며, **`--dangerously-skip-permissions`가 걸린 CLI 추론 모드와 리모트 데몬(`agy remote-control serve`) 양쪽 모두에서 그대로 작동합니다** — 이 플래그가 우회하는 건 아래 `permissions.allow/deny` 목록뿐, 훅은 별개 메커니즘입니다.

*   **`permissions.deny` 목록 (`bundled/hooks/deny_rules.json`)**
    위 훅과는 별도로, `settings.json`의 `permissions.deny`에도 같은 취지의 차단 목록이 등록됩니다. 다만 이건 **`--dangerously-skip-permissions`가 걸리면 완전히 우회되는** agy 자체의 권한 엔진이라, CLI 추론 모드와 리모트 데몬 양쪽 다 이 목록의 보호를 받지 못합니다(실측 확인 — 위 `ha-file-guard` 훅이 이 두 경로의 실질적인 방어선). 이 목록이 실제로 적용되는 건 `--dangerously-skip-permissions` 없이 뜨는 웹 터미널(ttyd/tmux) 경로뿐입니다.

*   **하네스 규칙 (always-on rule, 모든 대화에 항상 적용)**
    *   `ha-guidelines` — 기기 제어/조회 시 직접 `curl` 대신 `ha-mcp` 도구를 우선 사용하도록 지시
    *   `ha-file-safety` — 파일 삭제·덮어쓰기 전에는 항상 대상 경로와 개수, 이유를 먼저 제시하고 사용자의 명시적 승인을 받은 뒤에만 실행하도록 지시하며, 위 훅이 보호하는 HA 핵심 데이터는 사용자가 승인해도 거부하고 위험성을 설명하도록 지시. CLI 모드/리모트 데몬의 headless 실행 경로(`--dangerously-skip-permissions`)에서는 승인 절차 자체가 우회되므로, 이 규칙이 실질적인 최종 안전장치 역할을 합니다.

*   **웹 UI 오픈소스 라이브러리 — `jsdiff`**
    CLI 추론 모드의 파일 수정 내역을 실제 줄 단위(line-matching)로 비교해 보여주는 diff 뷰어에 사용됩니다. CDN이 아니라 `core/ui/vendor_diff.py`에 직접 내장(vendoring)되어 있어 외부 네트워크 접근 없이 동작합니다.
    출처: [kpdecker/jsdiff](https://github.com/kpdecker/jsdiff) (`diff` 9.0.0, BSD-3-Clause)

## 🏗 아키텍처 및 내부 구조

*   **ttyd + tmux**: 브라우저와 터미널 환경을 이어줍니다.
*   **uvx + ha-mcp (stdio)**: `agy`가 MCP 서버가 필요할 때 `uvx ha-mcp@latest`를 자식 프로세스(stdio)로 실행합니다. Antigravity CLI는 `stdio` 전송만 지원하므로 이 방식이 공식적으로 올바른 연결 방법입니다.
*   **SUPERVISOR_TOKEN 자동 주입**: 컨테이너 환경에서 토큰을 자동으로 읽어 `ha-mcp`에 환경 변수로 전달하므로 별도의 Long-Lived Access Token 발급이 불필요합니다.
*   **Bash 래퍼 스크립트**: x86_64 및 ARM(QEMU) 환경 모두에서 구동될 수 있도록 동적으로 바이너리 호환성을 맞춰줍니다.
