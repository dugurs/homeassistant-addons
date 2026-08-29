---
name: component-contract-validator
description: "Home Assistant 커스텀 통합구성요소(antigravity_cli)와 애드온 API 서비스 간의 통신 계약(Contract), 데이터 스키마, 센서/버튼 매핑, 에러 처리를 검증하는 스킬. 통합구성요소-애드온 간 통신 인터페이스 검증, API 응답 스키마 대조, 센서 호환성 점검 요청 시 반드시 이 스킬을 사용할 것."
---

# Component Contract Validator

Home Assistant 커스텀 통합구성요소(`custom_components/antigravity_cli`)와 애드온 백그라운드 API 간의 경계면 통신 계약을 검증하는 스킬.

## 1. 통신 계약 스키마 (Communication Contract)

### 1.1 엔드포인트: `GET /api/status`
- **목적**: `AntigravityDataUpdateCoordinator`가 주기적으로 상태를 폴링하여 센서 엔티티를 갱신
- **요청 헤더**:
  - `Authorization: Bearer <API_KEY>` (선택사항, `api_key`가 설정된 경우)
- **필수 응답 JSON 스키마**:
  ```json
  {
    "status": "online | offline | busy",
    "version": "string (예: 1.0.5)",
    "active_sessions": "integer (예: 1)",
    "uptime": "integer (초 단위, 예: 3600)"
  }
  ```

### 1.2 엔드포인트: `POST /api/chat` (어시스턴트 파이프라인 / Conversation)
- **목적**: Home Assistant Assist Pipeline에서 사용자의 질문/명령(Prompt)을 Antigravity CLI로 전달하고 응답 텍스트를 수신
- **요청 헤더**:
  - `Content-Type: application/json`
  - `Authorization: Bearer <API_KEY>` (선택사항)
- **요청 Body**:
  ```json
  {
    "prompt": "거실 불 켜줘",
    "conversation_id": "optional-uuid",
    "language": "ko"
  }
  ```
- **응답 JSON 스키마**:
  ```json
  {
    "response": "거실 조명을 켰습니다.",
    "conversation_id": "optional-uuid"
  }
  ```

### 1.3 엔터티 매핑 검증표
| 센서 Key | 타입 | 단위 / Class | 용도 및 기대값 |
|:---|:---|:---|:---|
| `status` | string | `icon: mdi:robot` | 에이전트 구동 상태 (`online`, `idle`, `running`, `busy`) |
| `active_sessions` | int | `measurement` | 현재 연결/작업 중인 세션 개수 |
| `uptime` | int | `s`, `total_increasing` | 서비스 가동 시간(초) |

| 버튼 Key | 연계 액션 | 기대 동작 |
|:---|:---|:---|
| `sync_status` | `coordinator.async_request_refresh()` | Coordinator 즉시 폴링 트리거 |
| `restart_agent` | `POST /api/restart` 또는 CLI 재시작 | 에이전트 프로세스 재시작 요청 |

| 플랫폼 | 클래스 / 인터페이스 | 기대 동작 |
|:---|:---|:---|
| `conversation` | `ConversationEntity` | `async_process` 호출 시 `/api/chat` 연동 및 `ConversationResult` 반환 |

---

## 2. 검증 절차 (Validation Workflow)

1. **스키마 정합성 검사**:
   - 애드온 API 응답 필드 이름이 Coordinator가 파싱하는 키(`status`, `version`, `active_sessions`, `uptime`)와 정확히 일치하는지 확인
2. **타입 및 단위 검사**:
   - `uptime`이 초(seconds) 단위의 정수/실수인지 검증
   - `active_sessions`가 정수인지 검증
3. **에러 및 타임아웃 복원력**:
   - 애드온 미기동 시 Coordinator의 오프라인 폴백(`status: offline`, `active_sessions: 0`, `uptime: 0`) 정상 작동 여부 점검
   - 10초 타임아웃 처리 로직 확인
4. **인증 검증**:
   - `api_key` 유무에 따른 HTTP 200 / 401 응답 처리 점검
