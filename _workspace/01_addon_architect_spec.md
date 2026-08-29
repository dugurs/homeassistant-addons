# 01. Add-on & Integration Interface Specification

## 1. 개요
Home Assistant 커스텀 통합구성요소(`antigravity_cli`)와 애드온(`antigravity-cli`) 간의 통신 아키텍처 및 엔드포인트 명세를 정의합니다.

## 2. 인터페이스 계약 (Contract)

### 2.1 포트 및 프로토콜
- **프로토콜**: HTTP/1.1 REST API
- **기본 포트**: `8000/tcp` (호스트 매핑 8000)
- **인증 방식**: `Authorization: Bearer <API_KEY>` (설정 시)

### 2.2 엔드포인트 규격
1. `GET /api/status`
   - **설명**: 통합구성요소 `AntigravityDataUpdateCoordinator`의 상태 폴링 엔드포인트
   - **응답 코드**: `200 OK` (정상), `401 Unauthorized` (인증 실패)
   - **응답 JSON 스키마**:
     ```json
     {
       "status": "online",
       "version": "1.1.0",
       "active_sessions": 1,
       "uptime": 120
     }
     ```
2. `POST /api/chat` (어시스턴트 파이프라인 / Conversation)
   - **설명**: Home Assistant Assist에서 사용자의 텍스트/음성 프롬프트를 전달받아 에이전트 응답을 반환
   - **요청 Body**: `{"prompt": "...", "conversation_id": "...", "language": "ko"}`
   - **응답 JSON**: `{"response": "...", "conversation_id": "..."}`
3. `POST /api/restart` (선택적)
   - **설명**: 에이전트 프로세스 또는 세션 재시작 트리거
   - **응답 코드**: `200 OK` (`{"result": "restarted", "status": "online"}`)

## 3. 애드온 아키텍처 변경 명세

### 3.1 `config.yaml`
- `version`: `1.1.0`
- `ports`: `8000/tcp: 8000`
- `ports_description`: `8000/tcp: "Antigravity Status & REST API"`
- `options` 및 `schema`: `api_key: ""` (`str?`)

### 3.2 `antigravity_api.py`
- Python 표준 라이브러리 `http.server` 기반 경량 데몬 (추가 의존성 불필요, 즉시 기동)
- Tmux 활성 세션 감지 및 가동 시간(uptime) 자동 계산
- 옵션 파일(`/data/options.json`)에서 `api_key` 로드 및 Bearer 토큰 검증

### 3.3 `run.sh`
- 백그라운드로 `antigravity_api.py` 구동
- Ingress `ttyd`와 함께 병행 실행
- `trap`을 통해 컨테이너 종료 시그널 시 백그라운드 API 서버 안전 종료
