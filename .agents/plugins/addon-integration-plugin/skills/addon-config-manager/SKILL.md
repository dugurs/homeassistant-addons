---
name: addon-config-manager
description: "Home Assistant 애드온의 설정 파일(config.yaml), Dockerfile, Ingress/포트 매핑, run.sh 실행 스크립트 작성 및 수정 스킬. 애드온 설정 변경, 포트 추가, 백그라운드 서비스 등록, Supervisor API 권한 조정, 환경변수 설정 요청 시 반드시 이 스킬을 사용할 것."
---

# Addon Config Manager

Home Assistant 애드온의 설정 및 런타임 스크립트를 표준 규격에 맞게 안전하게 수정·관리하는 스킬.

## 1. 애드온 설정 핵심 구성요소 (`config.yaml`)

### 1.1 포트 매핑 (Ports)
애드온 내부에서 실행되는 백그라운드 API 서버(예: 8000/tcp)를 외부 또는 내부 네트워크에 노출하기 위해 `ports` 섹션을 구성한다:

```yaml
ports:
  8000/tcp: 8000 # 통합구성요소(antigravity_cli)와의 통신용 포트
ports_description:
  8000/tcp: "API & Status Server"
```

### 1.2 옵션 및 스키마 (Options & Schema)
동적 설정(예: API 키, 포트 커스텀 등)을 위한 스키마 정의:

```yaml
options:
  api_key: ""
  api_port: 8000
schema:
  api_key: "str?"
  api_port: "int?"
```

### 1.3 Supervisor API 권한 (API Roles)
- `homeassistant_api: true` : Home Assistant Core API 접근 권한 부여 (`SUPERVISOR_TOKEN` 발급)
- `hassio_api: true` : Hass.io Supervisor API 접근 권한 부여
- `hassio_role: manager` : Supervisor 관리자 권한 (애드온 제어 등)

---

## 2. 런타임 스크립트 패턴 (`run.sh`)

### 2.1 백그라운드 서비스 구동 및 PID 관리
메인 Ingress 프로세스(예: `ttyd`)를 차단하지 않고 API 데몬을 백그라운드로 실행하는 패턴:

```bash
# 1. API 서버 스크립트 또는 모듈 백그라운드 구동
echo "[INFO] Starting Antigravity Status API server on port ${API_PORT:-8000}..."
python3 /usr/local/bin/antigravity_api_server.py &
API_PID=$!

# 2. 종료 시그널 핸들링
trap "kill -TERM $API_PID 2>/dev/null; exit 0" SIGTERM SIGINT

# 3. 메인 프로세스(ttyd/ingress) 실행
exec /usr/local/bin/ttyd ...
```

---

## 3. 변경 시 체크리스트
1. `config.yaml` 구문(YAML) 유효성 검사
2. `ports` 및 Ingress 포트 간 충돌 방지
3. 컨테이너 재시작 시 데이터 보존 경로(`/config` / `addon_config`) 연계 확인
4. 환경변수(`SUPERVISOR_TOKEN`, `HASS_SERVER`) 유효성 검증
