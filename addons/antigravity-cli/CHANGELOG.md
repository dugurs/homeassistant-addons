## 1.2.0-beta.1

### 수정 (Fix)
- 모드 3(Antigravity CLI) 실행 중 `agy`가 API 할당량 초과 등으로 `result.status: "ERROR"`를 반환할 때, 답변 없이 조용히 "완료" 처리되던 문제 수정 — 이제 오류 메시지가 채팅창에 그대로 표시됨

### 추가 (Feature)
- 웹 UI 헤더와 `GET /api/status`(`ui_build_version`)에 빌드 번호 표시 — 배포/리빌드가 실제로 반영됐는지 눈으로 바로 확인 가능

---

## 1.1.0

### 추가 (Feature)
- Home Assistant 커스텀 통합구성요소(`antigravity_cli`)와의 통신을 위한 백그라운드 REST/Status API 서버(포트 8000) 추가
- `GET /api/status`, `GET /api/health`, `POST /api/restart` 엔드포인트 지원
- 활성 tmux 세션 수 및 가동 시간(uptime) 상태 모니터링 연동
- 포트 8000 매핑 및 API 키 인증 옵션 추가

---

## 1.0.5

### 수정 (Fix)
- v1.0.4의 ha-mcp 사전 다운로드 로직이 타임아웃 없이 무한 블록되어 애드온/HA가 멈추는 심각한 버그 수정
  - `uvx --with ha-mcp python` 방식을 백그라운드 실행 + 45초 타임아웃 방식으로 교체
  - run.sh가 절대 멈추지 않도록 안전 처리

---

## 1.0.4


### 수정 (Fix)
- 첫 설치 후 agy 실행 시 `home-assistant` MCP 서버가 "No MCP servers configured"로 표시되는 문제 수정
  - agy 시작 전 `ha-mcp` 패키지를 미리 다운로드(캐시 워밍업)하도록 개선
  - 기존에는 uvx가 ha-mcp를 백그라운드에서 다운로드하는 동안 agy가 MCP 연결 타임아웃 발생

---

## 1.0.3

### 수정 (Fix)
- MCP 연동 방식을 SSE HTTP 서버 프록시에서 **`stdio` (`uvx ha-mcp@latest`)** 방식으로 전환
  - Antigravity CLI는 `stdio` 전송만 지원하므로 기존 `serverUrl` 방식은 `Method Not Allowed` 에러 유발
  - 커스텀 ASGI SSE 프록시 스크립트 제거

### 개선 (Improve)
- uv 패키지 캐시를 `/config/.uv_cache`(영구 저장소)에 저장하여 애드온 업데이트 후에도 재다운로드 불필요
- `SUPERVISOR_TOKEN` 읽기 로직을 MCP 설정 생성보다 먼저 수행하도록 순서 개선
- 포트 7123 HTTP 서버 대기 루프 제거로 즉시 `agy` 실행
