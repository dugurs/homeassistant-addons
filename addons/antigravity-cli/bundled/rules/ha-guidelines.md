---
name: ha-guidelines
description: Always prioritize using ha-mcp tools over direct curl API calls when controlling or querying Home Assistant
trigger: always_on
---

# Home Assistant Guidelines

## Tools & Integrations
- Always prioritize using `ha-mcp` tools (`control_activate`, `get_entity_state`, `search_entities`, etc.) when interacting with Home Assistant entities, devices, and states.
- Avoid using direct shell `curl` commands to the Home Assistant REST API unless explicitly requested or when MCP tools are unavailable for the specific task.
- When a task requires specialized skills (e.g., `addon-config-manager`, `home-assistant-best-practices`), activate, reference, and execute the skill's instructions directly without prompting the user for repetitive confirmation.

## Development Tools & Custom Environment Persistence
- Home Assistant 애드온 컨테이너는 재빌드나 업데이트 시 내부 기본 파일시스템(`/root/`, `/tmp/`, `/usr/local/bin` 등)이 초기화됩니다.
- 사용자가 외부 개발 도구(CLI 유틸리티, SDK, 컴파일러, 대용량 패키지)나 프로젝트 설치/생성을 요청할 때:
  1. **설치 위치 및 영구 보존 안내 의무**:
     - 애드온 재빌드 후에도 보존되는 공식 영구 디렉터리 경로를 명시하고 사용자에게 안내합니다:
       - **사용자 정의 CLI 실행 바이너리**: `/config/.local_bin/` (부팅 시 자동 `/root/.local/bin` 링크 및 PATH 주입)
       - **외부 개발 SDK / 캐시**: `/config/Android/` (Android SDK), `/config/.gradle/` 등 (부팅 시 조건부 자동 심볼릭 링크 및 환경변수 주입)
       - **사용자 개발 프로젝트 코드**: `/homeassistant/projects/` 또는 사용자가 지정한 영구 워크스페이스
  2. **용량 및 변경 내역 고지**:
     - 예상 소요 디스크 용량과 설치 방식을 간략히 안내한 뒤 안전하게 설치를 진행합니다.
