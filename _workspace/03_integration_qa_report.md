# 03. Integration & Contract QA Report

## 1. 검증 대상
- **통합구성요소**: `custom_components/antigravity_cli` (Coordinator, Sensor, Button)
- **애드온**: `addons/antigravity-cli` (`antigravity_api.py`, `config.yaml`, `run.sh`)

## 2. 계약 정합성 교차 비교 (Cross-Comparison)

| 항목 | 통합구성요소 기대 규격 | 애드온 API 구현 규격 | 일치 여부 |
|:---|:---|:---|:---|
| **도메인** | `antigravity_cli` | - | **일치** (통합구성요소 도메인 통일 완료) |
| **상태 엔드포인트** | `GET /api/status` | `GET /api/status` | **일치** |
| **대화 엔드포인트** | `POST /api/chat` (Assist) | `POST /api/chat` (`{"response": ...}`) | **일치** |
| **기본 포트** | `8000` (옵션 동적 변경) | `8000/tcp: 8000` (`api_port` 지원) | **일치** |
| **인증 헤더** | `Authorization: Bearer <token>` | `Bearer <token>` 파싱 및 검증 | **일치** |
| **어시스턴트 플랫폼** | `ConversationEntity` | `AntigravityConversationEntity` 등록 | **일치** |
| **status 필드** | `string` (`online`/`offline`/`busy`) | `"online"` / `"busy"` 반환 | **일치** |
| **version 필드** | `string` | `"1.1.0"` 반환 | **일치** |
| **active_sessions** | `integer` (Measurement 센서) | `tmux list-sessions` 기반 정수 반환 | **일치** |
| **uptime 필드** | `integer` (초 단위, Total Increasing) | `int(time.time() - START_TIME)` 반환 | **일치** |

## 3. 엣지 케이스 및 복원력 검증
1. **서버 오프라인 시나리오**:
   - 애드온 미실행 또는 포트 차단 시 `aiohttp.ClientError` 발생
   - Coordinator가 `{"status": "offline", "version": "unknown", "active_sessions": 0, "uptime": 0}` 기본 폴백 데이터로 안전하게 복구 확인.
2. **타임아웃 시나리오**:
   - `asyncio.timeout(10)`에 의해 10초 초과 시 `UpdateFailed` 발생으로 HA Core 크래시 방지 확인.
3. **상태 동기화 버튼(`sync_status`)**:
   - `coordinator.async_request_refresh()` 호출을 통해 즉시 `GET /api/status` 재호출 및 센서 갱신 정상 지원.

## 4. 종합 평가
- **최종 판정**: **PASS (적합)**
- 통합구성요소와 애드온 간 통신 계약이 100% 충족되었으며 배포 준비가 완료되었습니다.
