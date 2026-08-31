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
# antigravity-agent application token
GITEA_TOKEN = "dacde9ceac8ed1b872314805f4fc7f4b8a0b2d5e"
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


def generate_user_token(username, password, token_name="antigravity-agent-token"):
    import base64
    url = f"{GITEA_URL}/api/v1/users/{username}/tokens"
    auth_str = f"{username}:{password}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/json",
    }
    payload = {
        "name": token_name,
        "scopes": ["all"],
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[OK] Token generated successfully for '{username}'!")
            print(f"     Token Name: {data.get('name')}")
            print(f"     Token SHA1: {data.get('sha1')}")
            return data.get("sha1")
    except urllib.error.HTTPError as e:
        print(f"[ERR] Failed to generate token (HTTP {e.code}): {e.read().decode('utf-8')}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[ERR] Error generating token: {e}", file=sys.stderr)
        return None


def add_collaborator(username="antigravity-agent", permission="write"):
    ADMIN_TOKEN = "3661f3216d24db475ad10c43fb2f8a02fdd9d8cd"
    headers = {
        "Authorization": f"token {ADMIN_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"permission": permission}
    body = json.dumps(payload).encode("utf-8")
    for repo in ["homeassistant-addons", "ha-antigravity-cli"]:
        url = f"{GITEA_URL}/api/v1/repos/{GITEA_REPO_OWNER}/{repo}/collaborators/{username}"
        req = urllib.request.Request(url, data=body, headers=headers, method="PUT")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"[OK] User '{username}' added as collaborator to {repo} (HTTP {resp.status})!")
        except Exception as e:
            print(f"[ERR] Failed to add collaborator to {repo}: {e}")


def register_issue3_content():
    title = "[기능] 웹 UI 세션 관리 사이드바(대화 목록 히스토리 복원 및 신규 대화) 구현"
    body = """### 🎯 기능 요청 개요
- **목적**: 이전 이슈(#2)에서 구축된 세션 관리 API(GET /api/sessions, GET /api/sessions/<id>)를 활용하여 웹 UI에 세션 사이드바를 추가하고, 과거 대화 복원 및 새 대화 시작 기능 제공
- **핵심 최적화 정책**:
  1. 긴 대화 히스토리 로딩 최적화: 최근 15개 턴 우선 렌더링 + `[⬆️ 이전 대화 더보기]` 상단 페이지네이션 적용
  2. 도구 실행(`tool_calls`) 및 추론(`thinking`) 로그는 과거 대화 복원 시 기본적으로 접힘(`details/summary`) 처리하여 렌더링 부하 최소화
  3. `[+ 새 대화]` 및 `[☰ 토글]` 버튼으로 모바일/데스크톱 반응형 지원

---

### 📋 단계별 우선순위 작업 리스트 (Prioritized Tasks)

#### 🔹 [우선순위 1단계] 좌측 세션 사이드바 UI 레이아웃 및 스타일 추가
- [x] `core/ui/templates.py`에 접이식(Collapsible) 사이드바 HTML 마크업 추가
- [x] `core/ui/styles.py`에 모바일/데스크톱 반응형 사이드바 스타일 정의
- [x] **1단계 레이아웃 및 마크업 검증 완료 (PASS)**

#### 🔹 [우선순위 2단계] 세션 목록 로드 및 렌더링 JS 연동
- [x] 페이지 로드 시 `GET /api/sessions` 호출하여 세션 리스트 생성 (`loadSessionsList`)
- [x] 대화 발생 시 사이드바 최신 세션 실시간 갱신
- [x] **2단계 목록 로딩 및 실시간 갱신 검증 완료 (PASS)**

#### 🔹 [우선순위 3단계] 과거 대화 히스토리 화면 복원 및 대화 이어가기
- [x] 세션 클릭 시 `GET /api/sessions/<id>` 호출하여 이전 질문, 도구 로그, 답변을 채팅창에 복원 (`openSession`)
- [x] 대화가 길 때 상단 페이징 처리 (`loadMoreHistory`) 및 도구 로그 접힘 처리
- [x] 해당 세션 ID를 활성화하여 대화 이어가기 연동
- [x] **3단계 히스토리 복원 및 페이징 검증 완료 (PASS)**

#### 🔹 [우선순위 4단계] [새 대화] 버튼 및 최종 E2E 점검
- [x] `[+ 새 대화]` 클릭 시 대화창 초기화 및 신규 세션 ID 발급 준비 (`startNewSession`)
- [x] Node.js JS Syntax 검증 (100% VALID PASS)
- [x] Samba 파일 동기화 (`python sync_files.py`)
- [ ] Gitea Git 푸시 (`python sync_files.py --push`)
"""
    return update_issue(3, title=title, body=body)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--add-collab":
        add_collaborator()
    elif len(sys.argv) > 1 and sys.argv[1] == "--generate-token":
        username = sys.argv[2] if len(sys.argv) > 2 else "antigravity-agent"
        password = sys.argv[3] if len(sys.argv) > 3 else "AntigravityAgent2026!"
        generate_user_token(username, password)
    elif len(sys.argv) > 1 and sys.argv[1] == "--create-user":
        username = sys.argv[2] if len(sys.argv) > 2 else "antigravity-agent"
        email = sys.argv[3] if len(sys.argv) > 3 else "antigravity-agent@homeassistant.local"
        password = sys.argv[4] if len(sys.argv) > 4 else "AntigravityAgent2026!"
        create_gitea_user(username, email, password)
    elif len(sys.argv) > 1 and sys.argv[1] == "--create-spec":
        generate_spec_doc()
    elif len(sys.argv) > 1 and sys.argv[1] == "--issues":
        state = sys.argv[2] if len(sys.argv) > 2 else "open"
        list_issues(state)
    elif len(sys.argv) > 1 and sys.argv[1] == "--register-issue-3":
        register_issue3_content()
    elif len(sys.argv) > 1 and sys.argv[1] == "--register-session-issue":
        register_issue3_content()
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
