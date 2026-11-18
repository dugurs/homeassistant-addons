---
name: ha-file-safety
description: Require explicit user approval before deleting or overwriting any file, and never touch Home Assistant's critical config data under any circumstance
trigger: always_on
---

# Home Assistant 파일 안전 수칙 (반드시 준수)

## 1. 파일 삭제/덮어쓰기 전 사전 승인 필수
사용자의 요청을 처리하다가 파일이나 폴더를 **삭제(rm, unlink 등)하거나 기존 내용을 되돌릴 수 없게 덮어써야 하는 경우**, 절대로 먼저 실행하지 말 것. 반드시 다음 순서를 따를 것:
1. 삭제/변경하려는 파일의 **정확한 전체 경로 목록**을 나열한다.
2. 대상 파일이 **총 몇 개**인지 명시한다.
3. **왜** 삭제/변경이 필요한지 이유를 설명한다.
4. 위 내용을 답변으로 제시하고, 실제 삭제/덮어쓰기 명령은 실행하지 않은 채 답변을 마치고 **사용자의 다음 메시지에서 명확한 승인**("네", "삭제해줘", "진행해", "확인" 등)이 올 때까지 기다린다.
5. 사용자가 승인하기 전에는 `rm`, 파일을 덮어쓰는 이동/치환 등 되돌리기 어려운 작업을 절대 먼저 수행하지 않는다.
6. 대상이 단 1개 파일이어도 이 규칙은 동일하게 적용된다. "간단한 작업이니 그냥 진행"하지 않는다.
7. **폴더(디렉터리) 자체를 삭제하려는 경우는 예외 없이 항상 경고하고 명확한 승인을 받은 뒤에만 진행한다.** 폴더 삭제(`rm -rf`, `rmdir` 등)는 그 안의 파일이 몇 개든 한 번에 전부 사라지는 작업이므로, 폴더가 비어있어 보이거나 안에 든 파일이 사소해 보여도, 그리고 2절의 보호 목록에 없는 폴더여도 절대 예외를 두지 않는다. 경고 시 해당 폴더의 전체 경로와 그 안에 들어있는 파일/하위폴더 목록(또는 개수)을 반드시 함께 제시한다.

## 2. 파일 및 폴더 안전 보호 3단계 기준 (/homeassistant 하위 1단계)

### 2.1. [삭제 금지 & 수정 금지] (시스템 코어, 인증, 바이너리 DB)
아래 항목은 Home Assistant 운영에 필수적인 핵심 데이터이며, 삭제/수정 시 되돌릴 수 없는 손상(엔티티·기기·자동화 전체 소실, 로그인 불가, 클라우드 연동 끊김 등)이 발생한다.
사용자가 삭제나 "초기화"를 요청하더라도 **절대로 실행하지 말고**, 왜 위험한지 설명한 뒤 대안(HA 자체 백업/복원 기능, 공식 설정 UI를 통한 개별 작업 등)을 제안할 것.
- `/homeassistant/.storage/` (폴더 전체 - 엔티티·기기·영역 레지스트리, auth 등 핵심 상태)
- `/homeassistant/.cloud/` (폴더 전체 - Nabu Casa Cloud 인증 토큰)
- `/homeassistant/.HA_VERSION` (내부 코어 버전 식별 마커)
- `/homeassistant/.ha_run.lock` (HA 코어 프로세스 실행 락 파일)
- `/homeassistant/home-assistant_v2.db` (`-wal`, `-shm` 포함 - SQLite 히스토리 데이터베이스)
- `/homeassistant/config` (`/config` 심볼릭 링크 자체)
- `/backup/` (폴더 전체 - Home Assistant 백업 아카이브)

### 2.2. [삭제 금지 & 수정 가능] (설정, 자동화, 컴포넌트, 대시보드 리소스)
아래 항목은 스마트홈 제어 규칙 및 커스텀 기능이 정의된 핵심 리소스이다.
1. **최상위 파일 및 컨테이너 폴더 자체를 `rm`으로 통째 삭제하는 것은 엄격히 금지**한다.
2. 자동화 추가, 설정 편집, 신규 파일 생성을 위한 **내용 수정(`edit_file`, `write_file`)은 전면 허용**한다.
3. 폴더 내부의 **특정 하위 개별 항목(예: `custom_components/aaa/`, `packages/my_package.yaml`, `www/my_card.js`) 삭제**는 **규칙 1(사전 승인 필수: 경로 목록, 개수, 이유 명시 후 승인 대기)**을 준수하여 수행할 수 있다. (단, 이 애드온의 연동 컴포넌트인 `custom_components/antigravity_cli/`는 삭제 보호)

- `/config/.gemini/` (폴더 통째 삭제 ❌ / 내부 `settings.json`, `rules/`, `hooks/` 등 설정·규칙 추가·수정 ⭕)
- `secrets.yaml` (파일 자체 삭제 ❌ / 비밀번호·API 토큰 추가·수정 ⭕)
- `configuration.yaml` (파일 자체 삭제 ❌ / 센서, include, 통합 설정 추가·수정 ⭕)
- `automations.yaml` (파일 자체 삭제 ❌ / 내부 자동화 추가·수정·부분삭제 ⭕)
- `scripts.yaml`, `scenes.yaml` (파일 자체 삭제 ❌ / 스크립트·씬 추가·수정·부분삭제 ⭕)
- `customize.yaml`, `customize_glob.yaml` (파일 자체 삭제 ❌ / 커스터마이징 수정 ⭕)
- `/homeassistant/www/` (폴더 통째 삭제 ❌ / 대시보드 커스텀 카드 JS, 이미지 추가·수정 및 개별 파일 삭제(규칙 1 승인) ⭕)
- `/homeassistant/custom_components/` (폴더 통째 삭제 ❌ / 컴포넌트 개발·수정 및 개별 컴포넌트 폴더 삭제(규칙 1 승인) ⭕)
- `/homeassistant/packages/` (폴더 통째 삭제 ❌ / 패키지 yaml 추가·수정 및 개별 파일 삭제(규칙 1 승인) ⭕)
- `/homeassistant/blueprints/` (폴더 통째 삭제 ❌ / 블루프린트 템플릿 추가·수정 ⭕)
- `/homeassistant/themes/` (폴더 통째 삭제 ❌ / 대시보드 테마 추가·수정 ⭕)
- `/homeassistant/custom_sentences/` (폴더 통째 삭제 ❌ / 음성 대화 문장 추가·수정 ⭕)
- `/homeassistant/esphome/` (폴더 통째 삭제 ❌ / ESPHome 기기 yaml 추가·수정 및 개별 파일 삭제 ⭕)
- `/homeassistant/espresense/`, `/homeassistant/node-red/`, `/homeassistant/pyscript/` (폴더 통째 삭제 ❌ / 하위 작업 스크립트·설정 수정 ⭕)
- 분할 설정 YAML: `recorder.yaml`, `logger.yaml`, `logbook.yaml`, `rest_commands.yaml`, `frigate.yaml`, `go2rtc.yaml` 등 (내용 수정 ⭕ / 파일 자체 삭제 ❌)
- `known_devices.yaml`, `ip_bans.yaml` (내용 수정 ⭕ / 파일 자체 삭제 ❌)

### 2.3. [그 외: 삭제 가능 & 수정 가능] (사용자 리소스, 캐시, 임시 파일)
아래 항목은 수정이 자유로우며, 삭제 시에는 반드시 **규칙 1(사전 승인 의무)**을 준수하여 사용자 확인 후 정리한다.
- `/homeassistant/adbkey`, `/homeassistant/adbkey.pub` (안드로이드 ADB 디버깅 인증 키)
- `core` (178MB 과거 크래시 덤프 파일 - 용량 확보를 위해 삭제 권장)
- `home-assistant.log.*` (`home-assistant.log.1`, `.fault`, `.old` 등 이전 로그 파일)
- `/homeassistant/tts/` (TTS 음성 캐시 파일)
- `/homeassistant/image/` (임시 이미지 캐시)
- `/homeassistant/projects/` (사용자 개발 프로젝트 워크스페이스)
- `/homeassistant/workspaces/`, `work/` (개발 및 작업 워크스페이스)
- 임시/작업 디렉터리: `notebooks/`, `logs/`, `deps/`, `glances/`, `tensorflow/`, `file_sensor/`, `nest/`, `custom_recorder/`, `hamh-backup/`
- 에디터/도구 캐시: `.history/`, `.cache/`, `.vscode/`, `.agents/`, `.ha_mcp/`

## 3. 그 외 파일
위 목록에 없는 일반 파일(예: `www/`의 이미지, 로그 파일 등)이라도 규칙 1(사전 승인)은 동일하게 적용된다.
