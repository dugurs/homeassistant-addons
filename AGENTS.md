# Agent Team & Skill Pointer

## 하네스: 애드온-통합구성요소 연동 (Addon Integration)

**목표:** Home Assistant 애드온(`addons/antigravity-cli`)과 커스텀 통합구성요소(`custom_components/antigravity_cli`) 간의 통신/연동 및 애드온 수정 작업을 체계적이고 안전하게 수행.

**핵심 규칙 (필수 준수):**
- **수정 작업 전 원인/개선방향 브리핑 및 사전 승인 의무 (Mandatory Pre-Modification Approval Gate)**: 기능 개선, 버그 수정, UI 변경, API 수정 등 **모든 코드 수정 작업을 진행하기 전**에는 반드시 **(1) 정확한 원인 분석**과 **(2) 구체적인 개선 방향 및 조치 계획**을 사용자에게 먼저 상세히 브리핑하고, **사용자의 명시적인 승인(Approval)을 받은 후**에만 파일 수정을 진행한다.
- **Git 작업 & 파일 동기화 상시 자동 승인 (Git & File Sync Auto-Approval)**: 사용자의 승인을 받아 진행된 수정 작업의 완료 단계에서 실행되는 Git 작업(`git add`, `commit`, `push`), Samba 파일 동기화(`python sync_files.py`), 애드온 Rebuild 및 재시작은 승인 대기 없이 **즉시 자동으로 일괄 실행**한다.

**트리거:** 애드온 수정, 커스텀 통합구성요소 통신 연동, 어시스턴트 파이프라인(Conversation) 연계, 상태 API 추가, 포트 매핑 조정, 에이전트 서비스 연계 작업 요청 시 `addon-integration-orchestrator` 스킬을 사용하라. 단순 질문은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|:---|:---|:---|:---|
| 2026-08-29 | 수정 전 원인 분석/조치 계획 보고 및 사용자 승인 게이트(Approval Gate) 규칙 의무화 | 전체 | 안전하고 통제된 코드 수정을 위해 승인 절차 추가 |
| 2026-08-29 | 어시스턴트 파이프라인(Conversation) 연동 규격 및 엔드포인트 확장 | 전체 | Home Assistant 음성/채팅 어시스턴트 파이프라인 연동 지원 |
| 2026-08-29 | 동적 포트(api_port) 설정 지원 추가 | 전체 | 사용자가 설정 화면에서 포트를 유연하게 변경할 수 있도록 개선 |
| 2026-08-29 | 초기 하네스 구성 및 도메인(`antigravity_cli`) 표준화 | 전체 | 애드온과 통합구성요소 간 통신 연동 하네스 구축 |
