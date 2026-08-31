# Antigravity CLI 통신 규격 정의서 (Session-Aware Baseline v2.1)

> **상태: 영구 관리 (LOCKED)**  
> **기준 커밋: `1fd3b01` 기반 세션 지속(Resume) 규격 확장**  
> **절대 규칙:** 본 규격 및 통신 인터페이스는 공식 문서 및 사용자 사전 승인 없이 임의 수정할 수 없습니다.

---

## 1. 개요
Home Assistant 애드온(`addons/antigravity-cli`)의 백엔드와 프론트엔드/통합구성요소 간의 HTTP/SSE 통신 및 세션 지속(Resume) 규격을 정의합니다.

---

## 2. API 엔드포인트 규격

### 1) POST `/api/chat` (또는 `/api/prompt`)
- **설명**: 실시간 대화 및 제어 스트리밍 엔드포인트
- **Content-Type**: `application/json`
- **Response Content-Type**: `text/event-stream; charset=utf-8`

#### [Request Payload]
```json
{
  "prompt": "거실 불 켜줘",
  "stream_mode": 1,
  "conversation_id": "optional-uuid",
  "is_direct_llm": false,
  "is_mobile": false
}
```
- `stream_mode`:
  - `1`: AI Deep Brain / Environmental Analysis (환경 분석 및 조언 합성)
  - `2`: Ultra-Fast Smart Home Control (0.05s 고속 기기 제어)
  - `3`: Antigravity CLI v2.0 Headless Agent (자율 코딩/심층 에이전트)
- `conversation_id`: (선택) 이전 대화 세션을 이어갈 경우 전달. 생략 시 신규 발급.

#### [SSE Response Stream Events]
모든 이벤트는 `data: <JSON>\n\n` 포맷으로 전송됩니다.

1. **`session_init` 이벤트** (스트림 첫 줄 세션 ID 통지):
   ```json
   {"type": "session_init", "content": "2938460a-218d-48ad-9e24-6d95217e87f9"}
   ```
2. **`tool` / `live_log` 이벤트** (진행 상황 / 도구 로그):
   ```json
   {"type": "tool", "content": "⚡ [모드 2: 초고속 스마트홈] 실시간 기기 및 엔티티 상태 고속 탐색"}
   ```
3. **`chunk` / `text` 이벤트** (최종 답변 텍스트 스트리밍):
   ```json
   {"type": "text", "content": "🏠 거실 조명을 켰습니다."}
   ```
4. **`done` 이벤트** (스트림 종료 및 메트릭):
   ```json
   {"type": "done", "tokens": {"input": 48, "output": 120, "total": 168, "speed_tps": 450.0, "elapsed": 0.05}}
   ```

---

### 2) GET `/api/sessions`
- **설명**: 이전 대화 세션 목록 조회
- **Response**: `application/json`
```json
{
  "sessions": [
    {
      "conversation_id": "2938460a-218d-48ad-9e24-6d95217e87f9",
      "title": "거실 조명 켜줘",
      "turns": 6,
      "last_message": "📊 [AI 환경 분석] 거실 CO2는 650ppm이며...",
      "updated_at": "2026-08-31T12:07:56+09:00",
      "timestamp": 1788145676.0
    }
  ]
}
```

---

### 3) GET `/api/sessions/<conversation_id>`
- **설명**: 특정 세션의 전체 `transcript.jsonl` 대화 히스토리 및 도구 호출 내역 조회
- **Response**: `application/json`
```json
{
  "conversation_id": "2938460a-218d-48ad-9e24-6d95217e87f9",
  "history": [
    {"step_index": 1, "type": "USER_INPUT", "content": "거실 조명 켜줘"},
    {"step_index": 2, "type": "PLANNER_RESPONSE", "thinking": "...", "tool_calls": [...]},
    {"step_index": 3, "type": "PLANNER_RESPONSE", "content": "💡 거실 조명을 성공적으로 켰습니다."}
  ]
}
```

---

## 3. 변경 이력
| 날짜 | 버전 | 변경 내용 | 사유 및 근거 |
|:---|:---|:---|:---|
| 2026-08-31 | v2.1 | 세션 관리 REST API(`GET /api/sessions`, `GET /api/sessions/<id>`) 및 `session_init` SSE 이벤트 추가 | 대화 지속(Resume) 및 다중 모드 통합 맥락 지원 (Gitea Issue #2) |
| 2026-08-30 | v2.0 | Mode 1, 2, 3 스트리밍 규격 정립 및 동결 | 검증 커밋 `1fd3b01` 기준 규격 동결 |
