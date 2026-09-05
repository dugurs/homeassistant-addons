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

## 2. 절대 삭제·수정 금지 (사용자가 명시적으로 요청해도 거부하고 위험성을 설명할 것)
아래 항목은 Home Assistant 운영에 필수적인 핵심 데이터이며, 삭제/수정 시 되돌릴 수 없는 손상(엔티티·기기·자동화 전체 소실, 로그인 불가, 클라우드 연동 끊김 등)이 발생한다. 사용자가 삭제나 "초기화"를 요청하더라도 **절대로 실행하지 말고**, 왜 위험한지 설명한 뒤 대안(HA 자체 백업/복원 기능, 공식 설정 UI를 통한 개별 삭제 등)을 제안할 것. 이름이 일부만 일치하거나 "정리해줘", "청소해줘" 같은 모호한 요청에도 아래 항목은 절대 포함시키지 말 것.

| 경로 | 내용물 | 위험 |
|---|---|---|
| `/homeassistant/.storage/` (폴더 전체) | 엔티티·기기·영역 레지스트리, 로그인 계정, 연동된 통합구성요소(Config Entries), 대시보드 설정 등 HA의 모든 핵심 상태 | 삭제 시 모든 기기·자동화·연동이 초기화되고 로그인 계정도 사라짐 |
| `/homeassistant/secrets.yaml` | 비밀번호·토큰 등 민감정보 | 삭제 시 이를 참조하는 모든 설정이 깨짐 |
| `/homeassistant/configuration.yaml` | HA 메인 설정 파일 | 삭제 시 HA 부팅 불가 |
| `/homeassistant/.uuid` | 이 HA 인스턴스의 고유 식별자 | 삭제 시 Nabu Casa Cloud/모바일 앱 연동 등이 끊김 |
| `/homeassistant/.HA_VERSION` | 내부 버전 마커 | 삭제 시 업데이트/마이그레이션 로직 오작동 가능 |
| `/homeassistant/home-assistant_v2.db` (`-wal`, `-shm` 포함) | 히스토리/로그북 레코더 데이터베이스 | 삭제 시 과거 이력 데이터 전부 소실 |
| `/homeassistant/.cloud/` | Nabu Casa Cloud 인증 토큰 | 삭제 시 Cloud 연동(리모트 액세스, Google/Alexa 연동 등) 끊김 |
| `/config/.gemini/` | 이 애드온(Antigravity CLI) 자신의 설정·인증·대화 기록 | 삭제 시 AI 에이전트 자신의 로그인/세션이 초기화됨 (자기 자신을 삭제하지 말 것) |
| `/homeassistant/automations.yaml`, `/homeassistant/scripts.yaml`, `/homeassistant/scenes.yaml` | 사용자가 작성한 자동화/스크립트/씬 정의 | 삭제 시 해당 자동화가 전부 소실 |
| `/homeassistant/custom_components/` | 사용자가 설치한 커스텀 통합(HACS 등) | 삭제 시 관련 통합이 전부 작동 중지 |
| `/backup/` (폴더 전체) | Home Assistant 백업 아카이브 | 삭제 시 재해 복구 수단 자체가 사라짐 |

## 3. 그 외 파일
위 목록에 없는 일반 파일(예: `www/`의 이미지, 로그 파일 등)이라도 규칙 1(사전 승인)은 동일하게 적용된다.
