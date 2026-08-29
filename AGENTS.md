# Agent Team & Skill Pointer

## 하네스: 애드온-통합구성요소 연동 (Addon Integration)

**목표:** Home Assistant 애드온(`addons/antigravity-cli`)과 커스텀 통합구성요소(`custom_components/antigravity_cli`) 간의 통신/연동 및 애드온 수정 작업을 체계적이고 안전하게 수행.

**핵심 규칙 (필수 준수):**
- **사전 승인 원칙**: 코드 수정, 버그 해결, 파일 변경 작업을 진행하기 전에 반드시 **(1) 원인 분석 (Root Cause)**과 **(2) 구체적인 조치 예정 내역 (Action Plan)**을 사용자에게 먼저 보고하고, **사용자의 명시적 승인을 받은 후** 실제 수정을 착수한다.
- **파일 동기화 상시 승인 (File Sync Auto-Approval)**: 승인된 작업의 일환으로 로컬 작업 공간의 변경 파일을 Home Assistant Samba 공유 경로(`\\HOMEASSISTANT\config\...`, `\\HOMEASSISTANT\local_apps\...`)로 복사/동기화하거나 Rebuild/Restart를 수행하는 작업은 사용자의 사전 지시에 따라 **항상 승인된 것으로 간주하고 즉시 자동 실행**한다.

**트리거:** 애드온 수정, 커스텀 통합구성요소 통신 연동, 어시스턴트 파이프라인(Conversation) 연계, 상태 API 추가, 포트 매핑 조정, 에이전트 서비스 연계 작업 요청 시 `addon-integration-orchestrator` 스킬을 사용하라. 단순 질문은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|:---|:---|:---|:---|
| 2026-08-29 | 수정 전 원인 분석/조치 계획 보고 및 사용자 승인 게이트(Approval Gate) 규칙 의무화 | 전체 | 안전하고 통제된 코드 수정을 위해 승인 절차 추가 |
| 2026-08-29 | 어시스턴트 파이프라인(Conversation) 연동 규격 및 엔드포인트 확장 | 전체 | Home Assistant 음성/채팅 어시스턴트 파이프라인 연동 지원 |
| 2026-08-29 | 동적 포트(api_port) 설정 지원 추가 | 전체 | 사용자가 설정 화면에서 포트를 유연하게 변경할 수 있도록 개선 |
| 2026-08-29 | 초기 하네스 구성 및 도메인(`antigravity_cli`) 표준화 | 전체 | 애드온과 통합구성요소 간 통신 연동 하네스 구축 |
