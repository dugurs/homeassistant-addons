import json
import urllib.request
import urllib.error
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def generate_spec_doc():
    import os
    spec_content = """# Antigravity CLI 통신 규격 정의서 (Frozen Baseline)

> **상태: 영구 동결 (LOCKED)**  
> **기준 커밋: `1fd3b0123f8532ab419c2aff3f666db116a8fc1c`**  
> **절대 규칙:** 사용자의 명시적인 수정 명령이 없는 한 이 규격 및 `core/streamer.py` 통신 로직은 절대 수정할 수 없습니다.

---

## 1. 개요
Home Assistant 애드온(`addons/antigravity-cli`)의 백엔드와 프론트엔드/통합구성요소 간의 HTTP/SSE 통신 규격을 정의합니다.

---

## 2. API 엔드포인트 규격

### POST `/api/chat` (또는 `/api/prompt`)
- **설명**: 실시간 대화 및 제어 스트리밍 엔드포인트
- **Content-Type**: `application/json`
- **Response Content-Type**: `text/event-stream; charset=utf-8`

#### [Request Payload]
```json
{
  "prompt": "거실 불 켜줘",
  "mode": 1,
  "conversation_id": "optional-uuid",
  "model": "optional-model-name",
  "effort": "high"
}
```
- `mode`:
  - `1`: AI Deep Brain / Smart Home Fast Control (환경 분석 및 고속 기기 제어)
  - `2`: Standard HA Assistant Chat (표준 대화)
  - `3`: Antigravity CLI v2.0 Headless Agent (자율 코딩/심층 에이전트)

#### [SSE Response Stream Events]
모든 이벤트는 `data: <JSON>\\n\\n` 포맷으로 전송됩니다.

1. **`tool` 이벤트** (진행 상황 / 도구 로그):
   ```json
   {"type": "tool", "content": "🧠 [모드 1: AI 딥 브레인] 환경 분석 세션 초기화: '거실 불 켜줘'"}
   ```
2. **`text` / `chunk` 이벤트** (최종 답변 텍스트 조각):
   ```json
   {"type": "text", "content": "🏠 거실 조명을 켰습니다."}
   ```
3. **`done` 이벤트** (스트림 종료 및 메트릭):
   ```json
   {"type": "done", "tokens": {"input": 48, "output": 120, "total": 168, "speed_tps": 450.0, "elapsed": 0.05}}
   ```

---

## 3. 통신 옵션 변경 관리 규칙
1. 옵션 추가가 필요한 경우, 반드시 본 문서의 `[변경 이력]`에 **(1) 변경 전 규격**, **(2) 변경 후 규격**, **(3) 공식 문서 근거**를 명시하여 사용자 사전 승인을 득해야 함.
2. 백엔드와 프론트엔드는 항상 본 규격을 100% 준수해야 함.
"""
    os.makedirs("docs", exist_ok=True)
    with open("docs/COMMUNICATION_SPEC.md", "w", encoding="utf-8") as f:
        f.write(spec_content)
    print("[OK] docs/COMMUNICATION_SPEC.md created successfully.")


def check():
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/status"
    print(f"[*] Checking Antigravity CLI Add-on Status at {url}...")
    try:
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[OK] Add-on Status : {data.get('status')} (v{data.get('version')})")
            print(f"[OK] RAM Usage     : {data.get('addon_memory_mb')} MB (CPU {data.get('cpu_usage')}%)")
            print(f"[OK] Total Host RAM: {data.get('used_memory_gb')} GB / {data.get('total_memory_gb')} GB ({data.get('memory_percent')}%)")
            print(f"[OK] Tmux Sessions : {data.get('active_sessions')}")
            print(f"[OK] Uptime        : {data.get('uptime')}s")
    except Exception as e:
        print(f"[ERR] Failed to connect to add-on: {e}", file=sys.stderr)


GITEA_URL = "http://192.168.0.26:3000"
GITEA_TOKEN = "3661f3216d24db475ad10c43fb2f8a02fdd9d8cd"
GITEA_REPO_OWNER = "lee"
GITEA_REPO_NAME = "homeassistant-addons"


def gitea_api(endpoint, method="GET", data=None):
    url = f"{GITEA_URL}/api/v1/repos/{GITEA_REPO_OWNER}/{GITEA_REPO_NAME}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"token {GITEA_TOKEN}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[ERR] Gitea HTTP {e.code}: {e.read().decode('utf-8')}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[ERR] Gitea API Error ({endpoint}): {e}", file=sys.stderr)
        return None


def list_issues(state="open"):
    issues = gitea_api(f"issues?state={state}")
    if not issues:
        print("[*] No issues found or failed to fetch.")
        return []
    print(f"\n📋 [Gitea Issues - {state.upper()}] Total: {len(issues)}")
    for iss in issues:
        labels = [l.get("name") for l in iss.get("labels", [])]
        label_str = f" [{', '.join(labels)}]" if labels else ""
        print(f"  #{iss['number']}: {iss['title']}{label_str}")
        print(f"     URL: {iss.get('html_url')}")
    print()
    return issues


def create_issue(title, body="", labels=None):
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    res = gitea_api("issues", method="POST", data=payload)
    if res and "number" in res:
        print(f"[OK] Issue #{res['number']} created successfully: {res['title']}")
        print(f"     URL: {res.get('html_url')}")
        return res
    return None


def update_issue(issue_num, title=None, body=None, state=None):
    payload = {}
    if title:
        payload["title"] = title
    if body:
        payload["body"] = body
    if state:
        payload["state"] = state
    res = gitea_api(f"issues/{issue_num}", method="PATCH", data=payload)
    if res:
        print(f"[OK] Issue #{issue_num} updated successfully.")
        return res
    return None


def add_issue_comment(issue_num, comment_body):
    payload = {"body": comment_body}
    res = gitea_api(f"issues/{issue_num}/comments", method="POST", data=payload)
    if res and "id" in res:
        print(f"[OK] Comment added to Issue #{issue_num} successfully (ID: {res['id']})")
        return res
    return None


def register_session_issue():
    title = "[기능] conversation_id 기반 대화 지속(Resume) 및 세션 관리 체계 구축"
    body = """### 🎯 기능 요청 개요
- **목적**: 매 질문마다 새 대화가 생성되는 문제를 해결하고, 모드 전환(모드 1, 2, 3) 시에도 이전 대화 맥락과 도구 실행 내역을 완벽히 기억하여 이어가는 통합 세션 관리 체계 구축
- **통신 규격 원칙**: 검증된 `1fd3b01` 통신 규격(`core/streamer.py`)을 안전하게 준수하며, `docs/COMMUNICATION_SPEC.md`에 정의된 공식 인터페이스 활용
- **핵심 아키텍처 원칙**:
  1. 모드 1, 2의 대화 기록 로직은 `core/session_manager.py` 모듈로 분리하여 독립 관리
  2. 모드 1, 2에서도 모드 3과 동일한 규격(Thinking + Tool Calls + Final Response)으로 `brain/<conversation_id>/transcript.jsonl`에 기록하여 모드 3 전환 시 맥락 100% 동기화

---

### 📚 공식 문서 근거 (Official Reference)
- **Google Antigravity CLI Reference**:
  - URL: `https://antigravity.google/docs/cli/reference#sessions`
  - 세션 지속 명령: `agy -p "<prompt>" --resume <conversation-id>`
  - 세션 데이터 저장소: `<appDataDir>/brain/<conversation-id>/` 디렉토리에 대화 기록(transcript.jsonl) 영구 보존

---

### 📋 단계별 우선순위 작업 리스트 (Prioritized Tasks)

#### 🔹 [우선순위 1단계] 세션 관리 전용 모듈(`core/session_manager.py`) 신설
- [x] `brain/<conversation_id>/` 디렉토리 자동 생성 및 경로 관리
- [x] 모드 1, 2 대화 시 모드 3 표준 규격(`USER_INPUT`, `PLANNER_RESPONSE`, `thinking`, `tool_calls`) 생성 및 `transcript.jsonl` 비동기 기록 함수 구현
- [x] 세션 목록 및 히스토리 파싱/조회 함수 구현
- [x] **1단계 독립 단위 테스트 통과 (PASS)**

#### 🔹 [우선순위 2단계] 모드 1 & 모드 2 세션 로거 연동
- [x] 모드 2(초고속 스마트홈): 기기 제어(`ha_call_service`) 및 조회 도구 호출 내역을 표준 `tool_calls`로 세션에 기록
- [x] 모드 1(AI 딥 브레인): 센서 수집(`ha_get_state`) 및 환경 분석 추론 과정을 세션에 기록
- [x] 다중 스레드 안전성 확보를 위한 `_TRANSCRIPT_LOCK` 적용
- [x] **2단계 독립 단위 테스트 통과 (PASS)**

#### 🔹 [우선순위 3단계] 모드 3(Antigravity CLI) 세션 지속(`--resume`) 연동
- [x] 신규 대화 시 `session_init` SSE 이벤트를 통해 클라이언트에 `conversation_id` 전달
- [x] 클라이언트가 전달한 `conversation_id`를 기반으로 `agy -p "<prompt>" --resume <conversation-id>` 실행 연동
- [x] `antigravity_api.py`와 `streamer.py` 간 `conversation_id` 안전 전달 체계 구축
- [x] **3단계 독립 단위 테스트 통과 (PASS)**

#### 🔹 [우선순위 4단계] 세션 관리 REST API & 통신 규격 문서화
- [x] `GET /api/sessions`: 이전 대화 세션 목록 조회 엔드포인트 구현
- [x] `GET /api/sessions/<id>`: 특정 세션의 대화 내역 조회 엔드포인트 구현
- [x] `docs/COMMUNICATION_SPEC.md`에 세션 인터페이스(SSE 이벤트 및 REST API) 규격 명문화
- [x] **4단계 독립 단위 테스트 통과 (PASS)**

#### 🔹 [우선순위 5단계] 실운영 배포 및 파일 동기화
- [ ] Samba 파일 동기화 (`python sync_files.py`)
- [ ] Gitea Git Push (`python sync_files.py --push`)
"""
    return update_issue(2, title=title, body=body)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-spec":
        generate_spec_doc()
    elif len(sys.argv) > 1 and sys.argv[1] == "--issues":
        state = sys.argv[2] if len(sys.argv) > 2 else "open"
        list_issues(state)
    elif len(sys.argv) > 1 and sys.argv[1] == "--register-session-issue":
        register_session_issue()
    elif len(sys.argv) > 1 and sys.argv[1] == "--create-issue":
        title = sys.argv[2] if len(sys.argv) > 2 else "테스트 이슈"
        body = sys.argv[3] if len(sys.argv) > 3 else ""
        create_issue(title, body)
    elif len(sys.argv) > 1 and sys.argv[1] == "--comment-issue":
        issue_num = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        comment = sys.argv[3] if len(sys.argv) > 3 else ""
        add_issue_comment(issue_num, comment)
    else:
        check()
