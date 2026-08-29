# Agent Team & Skill Pointer

## 하네스: 애드온-통합구성요소 연동 (Addon Integration)

**목표:** Home Assistant 애드온(`addons/antigravity-cli`)과 커스텀 통합구성요소(`custom_components/antigravity_cli`) 간의 통신/연동 및 애드온 수정 작업을 체계적이고 안전하게 수행.

**핵심 규칙 (필수 준수):**
- **최신 공식 문서 기반 사전 검증 및 브리핑 의무 (Mandatory Official Documentation & Pre-Modification Gate)**:
  1. **공식 문서 사전 검증 (Official Docs Verification)**: 모든 아키텍처 설계, CLI/API 연동, 버그 수정 시 단편적 추측을 엄격히 금지하고, 반드시 최신 공식 문서(Antigravity CLI 공식 문서 `https://antigravity.google/docs/cli/reference`, Home Assistant 개발자 문서, MCP 공식 규격 등)를 웹 검색 및 레퍼런스로 대조·검증하여 기술적 사실 관계를 입증한다.
  2. **사전 승인 의무 (Approval Gate)**: 검증된 공식 문서 근거와 함께 **(1) 정확한 원인 분석**과 **(2) 구체적인 개선 방향 및 조치 계획**을 사용자에게 먼저 상세히 브리핑하고, **사용자의 명시적인 승인(Approval)을 받은 후**에만 파일 수정을 진행한다.
  3. **중간 진행 상황 및 단계별 보고 의무 (Iterative Step-by-Step Progress Reporting)**: 작업 도중 중간중간 (1) 어떤 작업을 진행했고, (2) 그 결과가 어떠하며, (3) 다음 작업은 어떤 것을 진행할지 명확히 브리핑하며 단계별로 작업을 수행한다.
  4. **E2E 실측 데이터 완전 검증 (E2E Stream Verification)**: 수정 후에는 단순 실행 여부가 아닌, 실제 터미널/스트림 패킷 원문 및 로그를 끝까지 추적·검증한 후 결과를 보고한다.
- **파일 동기화 및 Gitea 푸시 분리 규칙 (Samba Sync & Gitea Push Gate)**: 
  1. **Samba 파일 동기화 & 애드온 Rebuild**: 수정된 코드의 신속한 HA 환경 적용을 위해 `python sync_files.py` (삼바 파일 복사) 및 애드온 재빌드는 자동으로 실행한다.
  2. **Gitea Git Push 선택 승인 의무 (Gitea Push Confirmation)**: Gitea 원격 저장소 커밋/푸시(`git push gitea`)는 수정 후 매번 자동 실행하지 않고, **반드시 사용자에게 버튼(`ask_question`)으로 동기화 여부를 질의하여 명시적 승인을 얻은 경우에만 실행**(`python sync_files.py --push`)한다.

**트리거:** 애드온 수정, 커스텀 통합구성요소 통신 연동, 어시스턴트 파이프라인(Conversation) 연계, 상태 API 추가, 포트 매핑 조정, 에이전트 서비스 연계 작업 요청 시 `addon-integration-orchestrator` 스킬을 사용하라. 단순 질문은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|:---|:---|:---|:---|
| 2026-08-30 | Gitea Git Push 자동 실행 중단 및 버튼 선택 승인 게이트 의무화 | 전체 | 불필요한 빈번한 원격 커밋 방지 및 사용자 통제권 강화 |
| 2026-08-30 | 중간 작업 내용, 결과 및 다음 작업 계획 단계별 보고 규칙(Iterative Reporting) 의무화 | 전체 | 투명하고 명확한 작업 진행 상태 공유를 위해 추가 |
| 2026-08-29 | 수정 전 원인 분석/조치 계획 보고 및 사용자 승인 게이트(Approval Gate) 규칙 의무화 | 전체 | 안전하고 통제된 코드 수정을 위해 승인 절차 추가 |
| 2026-08-29 | 어시스턴트 파이프라인(Conversation) 연동 규격 및 엔드포인트 확장 | 전체 | Home Assistant 음성/채팅 어시스턴트 파이프라인 연동 지원 |
| 2026-08-29 | 동적 포트(api_port) 설정 지원 추가 | 전체 | 사용자가 설정 화면에서 포트를 유연하게 변경할 수 있도록 개선 |
| 2026-08-29 | 초기 하네스 구성 및 도메인(`antigravity_cli`) 표준화 | 전체 | 애드온과 통합구성요소 간 통신 연동 하네스 구축 |
