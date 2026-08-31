# Antigravity CLI 통신 규격 정의서 (Session-Aware Baseline v2.3)

> **상태: 영구 관리 (LOCKED)**
> **기준 커밋: `1fd3b01` 기반 세션 지속(Resume) 규격 재구현 (`feature/session-resume-v2`)**
> **절대 규칙:** 본 규격 및 통신 인터페이스는 공식 문서 및 사용자 사전 승인 없이 임의 수정할 수 없습니다.
> **공식 문서**: https://antigravity.google/docs/cli/conversations , https://antigravity.google/docs/cli/headless (2026-08-31 확인). `agy --help`(설치된 바이너리, v1.1.22)가 flag 이름의 최종 근거.

---

## 1. 개요
Home Assistant 애드온(`addons/antigravity-cli`)의 백엔드와 프론트엔드/통합구성요소 간의 HTTP/SSE 통신 및 세션 지속(Resume) 규격을 정의합니다.

이 문서는 이전 버전(v2.1, `feature/integrate-react-webui`)이 Mode 3(Antigravity CLI headless)의 실시간 stream-json 통신을 깨뜨린 뒤 폐기되고, `main`(1fd3b01)을 기준으로 재구현된 버전을 반영합니다. 재구현 시 반드시 지켜야 하는 제약은 [3. 재구현 시 지켜야 할 제약](#3-재구현-시-지켜야-할-제약)을 참고하세요.

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

`result.status`가 `"SUCCESS"`가 아닌 경우(공식 문서 기준 가능한 값: `SUCCESS`, `ERROR`, `CANCELED`, `INTERRUPTED`, `INVALID`, `WAITING`, `RUNNING` — 예: `agy` API 할당량 초과 시 `ERROR`)에도 스트림은 정상 종료되지만, `chunk` 이벤트로 에러 메시지가 먼저 전달된 뒤 `done`이 옵니다. 절대 빈 답변으로 `done`만 오지 않습니다.

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
- **설명**: 특정 세션의 전체 대화 히스토리 및 도구 호출 내역 조회
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

## 3. 재구현 시 지켜야 할 제약

`core/session_manager.py` / `core/streamer.py`를 다시 손댈 때는 아래 두 가지가 **Mode 3 실시간 통신을 깨뜨린 실제 원인**이었으므로 반드시 지킬 것:

1. **재개 시 넘길 flag는 `--conversation <id>`다. `--resume`이라는 flag는 존재하지 않는다.**
   `agy --help`(v1.1.22)에 나열된 관련 flag는 `--conversation`("Resume a previous conversation by ID")과 `--continue`/`-c`("Continue the most recent conversation") 뿐이다. 과거 코드와 Gitea 이슈 #2 원문이 전부 `--resume <conversation-id>`라고 적어놨던 건 잘못된 전제였다(공식 문서 어디에도 없음). 실측상 `--resume`을 보내도 예외 없이 같은 id로 이어지는 것처럼 보였지만, 이는 문서화되지 않은 우연한 동작에 의존하는 것이라 위험하다 — 반드시 `--conversation`을 써야 한다.
2. **세션 재개 시 기존 transcript 파일을 처음부터 tailing하지 말 것.**
   `stream_headless_cli()`의 `tail_transcript()`는 재개 세션일 경우 파일을 연 직후 `file_obj.seek(0, os.SEEK_END)`로 끝으로 이동한 뒤 tailing을 시작해야 한다. 그렇지 않으면 이전 대화의 모든 단계가 "방금 발생한 것"처럼 실시간 스트림에 재방송되어 화면이 과거 로그로 도배된다.
3. **한글 디코딩은 실제 `\uXXXX` 리터럴만 정규식으로 치환할 것.**
   `session_manager.decode_unicode_text()`가 문자열 전체를 `.encode("utf-8").decode("unicode_escape")` 하면, 이미 정상인 UTF-8 한글까지 깨진다. 반드시 `\uXXXX` 패턴만 매칭하는 정규식(`re.sub(r"\\u[0-9a-fA-F]{4}", ...)`)으로 국소 치환해야 한다.
4. **`transcript.jsonl`(`.system_generated/logs/transcript.jsonl`)이 유일한 정본(cumulative) 로그다.**
   Modes 1/2는 `session_manager`가 직접 이 파일에 기록하고, Mode 3(`agy`)도 재개되는 모든 턴에 걸쳐 이 파일에 누적 기록한다(실측 확인). 반면 `.system_generated/logs/chunks/transcript_full/00000000.jsonl`은 **agy의 자체 스냅샷으로, 대화의 첫 번째 턴 내용만 담고 이후 재개 턴에서는 갱신되지 않는다** — 세션 목록/히스토리 조회의 주 소스로 쓰면 안 되고, `transcript.jsonl`이 아직 없는 극초반 순간의 폴백으로만 사용한다. `get_readable_transcript_path()`가 이 우선순위를 지킨다.
   (미확인 사항: `transcript.jsonl`이 한 턴 "안에서" 생각/도구 단계별로 점진적으로 append되는지, 아니면 턴 종료 시 한 번에 flush되는지는 할당량 문제로 아직 실측 못함. 후자라면 `tail_transcript()`의 재개 턴 실시간 내레이션이 약간 늦게 몰아서 나올 수 있음 — 최종 답변 스트리밍 자체는 `agy` stdout을 직접 파싱하므로 영향 없음.)
5. **`agy`의 `result.status`가 `"SUCCESS"`가 아니면 무시하지 말 것.**
   `result.response`가 비어 있어도 실패로 간주하지 않고 "완료"로 처리하면 안 된다. 공식 문서 기준 `status`는 `SUCCESS/ERROR/CANCELED/INTERRUPTED/INVALID/WAITING/RUNNING` 중 하나이며, `SUCCESS`가 아닌 모든 경우(그리고 `error` 필드가 없는 경우까지 포함해) `chunk`/`live_log`로 스트리밍해 사용자에게 보여준다.
6. **클라이언트가 conversation_id를 자체 생성해서 agy에게 넘기지 말 것.**
   Mode 3의 conversation_id는 **agy 자신이 발급**한다 (`init` 이벤트의 `conversation_id` 필드). 새 대화의 경우 `session_init` SSE는 agy의 `init` 이벤트를 받은 뒤에 그 id로 발급해야 한다 — 미리 자체 생성한 id를 `session_init`으로 먼저 알리고 그걸 `--conversation`에 넘기면, agy는 모르는 id이므로 조용히 새 대화를 또 시작하고 서로 다른 두 개의 분리된 id가 생긴다. Modes 1/2는 agy 프로세스가 없으므로 자체 생성한 id를 그대로 써도 무방하다(`stream_ai_deep_brain`/`stream_fast_dashboard` 참고).

---

## 4. 변경 이력
| 날짜 | 버전 | 변경 내용 | 사유 및 근거 |
|:---|:---|:---|:---|
| 2026-08-31 | v2.3 | 공식 문서(`/docs/cli/conversations`, `/docs/cli/headless`) 및 `agy --help` 대조 확인. `--resume`→`--conversation`으로 flag 수정(존재하지 않는 flag였음), conversation_id를 agy의 `init` 이벤트에서 받아오도록 수정(클라이언트 자체 생성 id를 쓰면 agy가 인식 못 해 재개가 조용히 실패), `result.status` 체크를 `"ERROR"` 단일값에서 `!= "SUCCESS"` 전체로 확장 | Gitea 이슈 #2 원문이 애초에 `--resume`을 문서화된 flag로 잘못 전제하고 있었고, "클라이언트가 전달한 conversation_id"를 쓰라고 되어 있어 원인이 됨 — 라이브 2턴 테스트로 재발견 |
| 2026-08-31 | v2.2 | `feature/session-resume-v2`에서 재구현. 재개 세션 seek-to-end, 정규식 기반 유니코드 디코딩, Mode 3/Modes 1·2 이원 transcript 경로 지원, `result.status=="ERROR"` 처리 추가 | `feature/integrate-react-webui`(v2.1)가 위 항목들의 부재로 Mode 3 실시간 통신을 깨뜨려 롤백 후 재작업 |
| 2026-08-31 | v2.1 (폐기) | 세션 관리 REST API(`GET /api/sessions`, `GET /api/sessions/<id>`) 및 `session_init` SSE 이벤트 추가 — Mode 3 실시간 통신 손상으로 병합되지 않고 폐기됨 | 대화 지속(Resume) 및 다중 모드 통합 맥락 지원 (Gitea Issue #2) |
| 2026-08-30 | v2.0 | Mode 1, 2, 3 스트리밍 규격 정립 및 동결 | 검증 커밋 `1fd3b01` 기준 규격 동결 |
