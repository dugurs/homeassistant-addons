---
name: addon-integration-orchestrator
description: "Home Assistant 애드온과 커스텀 통합구성요소(antigravity_cli) 간의 통신/연동, 어시스턴트 파이프라인(Conversation) 연계, 애드온 수정 작업을 총괄 조율하는 오케스트레이터. 애드온 수정, 통합구성요소 연동, 대화 API(/api/chat) 추가, 상태 API 추가, 포트 설정, 통신 인터페이스 개발 작업 요청 시 반드시 이 스킬을 사용. 후속 작업: 애드온 통신 수정, 부분 재실행, 업데이트, 보완, 다시 실행, 이전 결과 개선 요청 시에도 반드시 이 스킬을 사용할 것."
---

# Addon Integration Orchestrator

Home Assistant 애드온(`addons/antigravity-cli`)과 커스텀 통합구성요소(`custom_components/antigravity_cli`) 간의 양방향 통신 구현, 어시스턴트 파이프라인(Conversation) 연동, 애드온 수정 작업을 전담 조율하는 오케스트레이터 스킬.

## 실행 모드: 서브에이전트 (순차 협업)

## 팀 구성

| 에이전트 TypeName | 역할 | 주요 산출물 |
|:---|:---|:---|
| `addon-architect` | 통신 규격 및 애드온 아키텍처 설계 | `_workspace/01_addon_architect_spec.md` |
| `addon-builder` | 애드온 코드(`run.sh`, `config.yaml`, API 데몬) 구현/수정 | `_workspace/02_addon_builder_changes.md` |
| `integration-qa` | 경계면 교차 검증 및 계약 호환성 QA | `_workspace/03_integration_qa_report.md` |

---

## 워크플로우

### Phase 0: 컨텍스트 확인 (후속 작업 및 부분 재실행 지원)

1. 작업 디렉토리 내 `_workspace/` 존재 여부 확인:
   - **`_workspace/` 미존재** → 초기 실행. Phase 1로 진행.
   - **`_workspace/` 존재 + 사용자 부분 수정/보완 요청** → 부분 재실행. 이전 산출물 경로를 프롬프트에 제공하고 필요한 서브에이전트만 선별 호출.
   - **`_workspace/` 존재 + 새로운 전체 작업 요청** → 기존 `_workspace/`를 `_workspace_{YYYYMMDD_HHMMSS}/`로 백업한 뒤 Phase 1 진행.

### Phase 1: 원인 분석 및 아키텍처/조치 설계 (`addon-architect`)

1. `invoke_subagent` 도구 호출로 `addon-architect` 구동:
   - **TypeName**: `addon-architect`
   - **Role**: `Add-on & Integration Interface Architect`
   - **Prompt**: "문제 현상 또는 요청 사항을 분석하여 (1) 원인 분석 (Root Cause), (2) 아키텍처 수정 명세, (3) 구체적인 조치 예정 내역(Action Plan)을 `_workspace/01_addon_architect_spec.md`에 작성하세요."

### Phase 2: 원인 분석 및 조치 계획 보고 ➔ 사용자 승인 (User Approval Gate) **[필수]**

2. 오케스트레이터(메인 에이전트)는 `_workspace/01_addon_architect_spec.md`를 기반으로 사용자에게 보고:
   - **원인 분석**: 무엇이 문제였는지 또는 변경이 왜 필요한지 설명
   - **조치 예정 내역**: 어떤 파일(`run.sh`, `config.yaml`, `conversation.py` 등)을 어떻게 수정할 것인지 명시
   - **승인 대기**: **사용자의 명시적 승인("진행해", "승인", "수정해" 등)을 받기 전까지는 절대 코드를 수정하거나 `addon-builder`를 호출하지 않고 대기한다.**

### Phase 3: 승인 후 애드온 코드 및 서비스 구현 (`addon-builder`)

3. 사용자의 승인을 확인한 후 `invoke_subagent` 도구 호출로 `addon-builder` 구동:
   - **TypeName**: `addon-builder`
   - **Role**: `Add-on Code & Service Builder`
   - **Prompt**: "`_workspace/01_addon_architect_spec.md` 명세에 따라 승인된 조치 계획을 충실히 구현하고, 수정 내역을 `_workspace/02_addon_builder_changes.md`에 기록하세요."

### Phase 4: 경계면 교차 검증 (`integration-qa`)

4. `invoke_subagent` 도구 호출로 `integration-qa` 구동:
   - **TypeName**: `integration-qa`
   - **Role**: `Integration Contract QA Specialist`
   - **Prompt**: "`_workspace/01_addon_architect_spec.md` 및 `_workspace/02_addon_builder_changes.md`를 바탕으로, 수정된 코드의 스키마 정합성, 포트/인증 매핑, 예외 처리를 교차 검증하여 `_workspace/03_integration_qa_report.md`에 작성하세요."

### Phase 5: 통합 및 보고

1. 모든 서브에이전트의 산출물 파일(`_workspace/` 내 파일들) 확인
2. 사용자에게 최종 수정 완료 내역 및 검증 결과 요약 보고

### Phase 6: 정리

1. `_workspace/` 디렉토리 보존 (사후 검증 및 변경 추적용)

---

## 데이터 흐름

```
[오케스트레이터 (addon-integration-orchestrator)]
       │
       ├── invoke_subagent("addon-architect") ──→ _workspace/01_addon_architect_spec.md
       │                                                 │
       │                                                 ↓ (참조)
       ├── invoke_subagent("addon-builder")   ──→ _workspace/02_addon_builder_changes.md
       │                                                 │
       │                                                 ↓ (교차 비교)
       ├── invoke_subagent("integration-qa")  ──→ _workspace/03_integration_qa_report.md
       │
       └── 최종 통합 보고 및 산출물 보존
```

---

## 에러 핸들링

| 상황 | 대응 전략 |
|:---|:---|
| 서브에이전트 실패 | 1회 재시도 후 재실패 시 실패 로그와 함께 사용자 확인 요청 |
| 스키마 불일치 발견 | `integration-qa`의 권장사항을 바탕으로 `addon-builder` 재호출하여 스키마 일치 보정 |
| 포트 충돌 또는 권한 누락 | `config.yaml`의 `ports` 및 Supervisor API 역할 재설정 지침 전달 |

---

## 테스트 시나리오

### 정상 흐름 (Happy Path)
1. 사용자가 "애드온에서 통합구성요소와 통신할 수 있게 수정해줘" 요청
2. `addon-architect`가 `antigravity_cli`의 `/api/status` 계약 및 8000 포트 구조 설계
3. `addon-builder`가 `config.yaml`에 8000 포트 추가, `run.sh`에 상태 API 서버 스크립트 연결
4. `integration-qa`가 스키마(`status`, `active_sessions`, `uptime`) 정합성 검증 완료
5. 정상 완료 보고

### 에러 흐름 (Contract Drift)
1. `addon-builder`가 생성한 응답 필드 이름이 Coordinator의 기대 필드와 상이할 경우
2. `integration-qa`가 불일치를 감지하여 `_workspace/03_integration_qa_report.md`에 기록
3. `addon-builder` 재호출을 통해 필드명을 즉시 보정
