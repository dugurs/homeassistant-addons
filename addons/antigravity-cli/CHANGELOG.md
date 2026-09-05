## 1.1.0-beta.67

### 수정 (Fix) — 추론/도구 로그 UI를 Antigravity 데스크톱 앱 스타일로 개편
- **추론 로그가 응답 말풍선(`.bubble`) 안에 다시 한 번 박스로 갇혀 있던 문제 수정**: `.term-box`(추론/도구 타임라인)를 `.bubble` 내부에서 꺼내 `.bubble-wrap`의 형제 요소로 이동(`buildBotBubbleDOM()`, `core/ui/scripts.py`) — 기존엔 어두운 터미널 패널(`.term-box`)이 다시 카드 스타일 말풍선(`.bubble`) 안에 중첩되어 이중으로 갇혀 보였음
- **어두운 "터미널 콘솔" 룩 제거, 페이지와 같은 배경에 자연스럽게 흐르는 스타일로 전환**(`core/ui/styles.py`): `.term-box`/`.term-header`/`.term-body`의 고정 다크 배경(#0d1117 등)·테두리·모노스페이스 폰트·가로 스크롤을 제거하고 앱 테마 변수(`var(--text-muted)` 등)로 교체 — 라이트 모드에서도 자연스럽게 보임(기존엔 "터미널은 항상 다크"라는 전제였는데, 더 이상 독립된 박스가 아니라 페이지에 녹아드는 요소가 되면서 그 전제가 깨짐)
- 상단 요약 뱃지("● LIVE"/"🕐 N초 동안 작업함")를 알약(pill) 모양에서 일반 텍스트 토글로 변경, 끝에 항상 접기/펼치기 화살표(▾/▸)가 따라붙도록 신설 `setTermBadgeText()`/`toggleTermBody()`로 통일(3곳에 흩어져 있던 중복 로직 정리)
- **MCP 도구 호출("HA 도구") 표시를 Antigravity 참고화면과 동일하게 "MCP Tool: {서버} / {도구}" + 펼치면 "Tool arguments"/"Tool Output" JSON 블록**으로 변경(`_classify_tool_call()`의 `call_mcp_tool` 분기, `core/streamer.py`/`core/ui/scripts.py` 양쪽 미러 + 신설 `toolIoDetailHTML()`) — 이전엔 인자를 한 줄에 다 욱여넣었음. "Tool Output"은 `find_by_name`/`run_command`/`search_web`와 동일한 GENERIC 결과 버퍼링에 의존하는데, agy가 MCP 호출에도 동일하게 결과 스텝을 남기는지는 아직 실측 전 — 없으면 "Tool arguments"만 보임(정상 동작, 추정으로 지어내지 않음)
- 그룹 요약 "파일 N개 탐색, 검색 M회"의 숫자를 굵게 표시, 파일 경로류 텍스트(`view_file`/`write_to_file`/`replace_file_content`의 대상)를 코드체(모노스페이스)로 표시 — 참고 화면의 "Analyzed {} ha_search.json" 스타일과 동일
- 접기/펼치기 화살표를 항상 줄 끝에 오도록 변경(CSS `order` 사용, 마크업 순서는 그대로 두고 시각적 위치만 이동) — 참고 화면과 동일하게 왼쪽이 아니라 오른쪽에 표시
- "Explored N files, M searches" 그룹은 기본적으로 펼쳐진 채로 시작(개별 도구 결과/추론 블록은 여전히 기본 접힘) — 참고 화면과 동일한 기본 상태

## 1.1.0-beta.66

### 수정 (Fix) — 모바일 UI 정리
- **CPU/RAM 그래프 패널 제목/범례 텍스트가 좁은 화면에서 단어 중간(예: "애드\n온")까지 줄바꿈되던 문제 수정**: 제목을 "CPU 사용률 추이 (듀얼)"/"RAM 점유율 추이 (듀얼)" → "CPU"/"RAM"으로, 범례를 "애드온:"/"시스템 전체:" → "애드온"/"전체"로 축약(`core/ui/templates.py`), `.lg-item`/`.chart-title`에 `white-space: nowrap` 추가하고 안 맞으면 개별 항목이 아니라 범례 전체가 다음 줄로 내려가도록 `.chart-top`에 `flex-wrap` 적용(`core/ui/styles.py`)
- **모바일에서 좌측 세션 사이드바를 열면 CPU/RAM 그래프 패널이 그 위에 떠 있는 것처럼 보이던 문제 수정**: `.top-resource-panel`이 `position` 없이 `z-index: 50`만 있어 사실상 아무 효과가 없었던 것(포지션 없는 요소의 z-index는 무시됨 -- 반면 모바일의 `.session-sidebar`는 `position: fixed`라 항상 위에 그려짐)이 근본 원인은 아니었지만, 상태 동기화가 어긋나 두 패널이 동시에 열려 있는 경우 자체가 혼란의 원인이었음 — `toggleResourcePanel()`/`toggleSessionSidebar()`가 모바일(`window.innerWidth <= 768`)에서 서로를 상호 배타적으로 닫도록 수정(`core/ui/scripts.py`), `.top-resource-panel`에도 `position: relative`와 사이드바(z-index 40)보다 낮은 `z-index: 10`을 명시해 상태가 어긋나도 항상 사이드바가 위에 그려지도록 이중 방어(`core/ui/styles.py`)
- **헤더의 누적 토큰 표시(🪙) 제거**: `resetTokens()`/`session-tokens` 갱신 로직은 이미 전부 `if (element)` 가드가 있어 요소를 지워도 안전 — 턴별 토큰 수치는 각 답변 말풍선 하단(`⚡ N초 완료` 옆 토큰 배지)에 여전히 표시됨(`core/ui/templates.py`)
- **모바일에서 실행모드/모델/에이전트 선택 버튼 3개가 한 줄에 다 안 들어가 마지막(에이전트) 버튼이 화면 밖으로 잘려 나가던 문제 수정**: `.composer-toolbar-left`에 가로 스크롤(`overflow-x: auto`, 스크롤바 숨김) 적용, `.composer-toolbar-right`(마이크/전송 버튼)는 `flex-shrink: 0`으로 항상 고정(`core/ui/styles.py`) — 에이전트 선택을 모델 선택 드롭다운 안으로 합치는 대신 이 방법을 택함(아래 참고)

## 1.1.0-beta.65

### 추가 (Add) — HA 파일 보호를 실제 강제 차단으로 승격 (PreToolUse 훅)
- beta.47의 HA 파일 보호는 (a) `ha-file-safety.md` 규칙 주입(모델이 원칙적으로 따르길 기대하는 지시일 뿐)과 (b) `settings.json`의 `permissions.deny`(Mode 3가 항상 쓰는 `--dangerously-skip-permissions`가 permissions 엔진 자체를 우회해버려서 실제로는 강제되지 않음) 두 가지뿐이었음 — 이번에 공식 문서(antigravity.google/docs/hooks/)를 확인해 **PreToolUse 훅**을 추가로 도입: 훅은 사람의 승인 프롬프트가 전혀 필요 없는 "스크립트를 동기 실행하고 그 결과(JSON)로 허용/차단을 결정"하는 별개의 메커니즘이라, `--dangerously-skip-permissions`가 우회하는 permissions 엔진과도, 헤드리스에서 영구 행(hang)하는 상위 버그가 있는 인터랙티브 승인 UI와도 무관하게 동작할 것으로 판단(문서상 인터랙티브 CLI에서는 매 도구 호출마다 실제로 발동해 차단이 동작한다는 실사용자 확인까지는 찾았으나, 헤드리스(`-p`) 모드에서도 그런지는 아직 실측 전 — 배포 후 실제 삭제 시도로 반드시 확인 필요)
  - 신설 `run.sh` → `/root/.gemini/hooks/ha_file_guard.py`: `run_command`(쉘 명령어에 `rm`/`unlink`/`shred`/`truncate`/`mv`/`>`(단순 리다이렉트, `>>`는 제외) 같은 파괴적 동작 + 보호 대상 경로 문자열이 함께 있을 때만 차단 — `cat`/`ls`/`grep` 같은 단순 조회는 걸리지 않음)와 `write_to_file`/`replace_file_content`(대상 경로가 보호 목록과 일치/그 하위일 때 차단)를 매처로 지정. beta.59에서 발견된 "일부 도구 인자 문자열이 이중 JSON 인코딩되어 있다"는 특성을 이 훅의 자체 stdin 페이로드에도 방어적으로 동일 적용(`_unwrap()`)
  - 차단 대상 목록은 `ha-file-safety.md`와 동일(`.storage`/`secrets.yaml`/`configuration.yaml`/`.uuid`/`.HA_VERSION`/`home-assistant_v2.db`/`.cloud`/이 애드온 자신의 `.gemini`/`automations·scripts·scenes.yaml`/`custom_components`/`/backup`) — 로컬에서 13개 케이스(보호 경로+파괴적 동작 조합 차단, 무관한 rm/조회/mv/append 허용, mcp 도구 통과, 이중 인코딩 경로 차단 등)로 훅 스크립트 자체의 판정 로직만 별도 검증 완료(agy가 실제로 이 훅을 호출하는지는 별개로 미검증)
  - 훅 등록 위치가 문서상 명확하지 않아(워크스페이스 `.agents/hooks.json` vs `settings.json`의 `hooks` 키, 기존 `core/hooks_discovery.py`는 후자를 전제로 작성돼 있었음) 두 곳 모두에 동일하게 등록(중복 실행은 되어도 무해함) — 실제로 어느 쪽이 유효한지는 라이브 테스트로 확인 예정

## 1.1.0-beta.64

### 추가 (Feature) — Mode 3 추론/도구 로그 전면 개편 (그룹핑 + 접기/펼치기 + 실제 결과 표시)
- 기존엔 추론(💭)/도구 호출(🔧)이 전부 완성된 문자열 한 줄씩으로 쌓이기만 하고, 접기/펼치기도 없이 180px 고정 높이 박스에 계속 쌓여 답답했던 것을 Antigravity IDE 자체의 액션 타임라인(연속 탐색/검색 묶기 + "Thought for Xs" + "Edited +N -M") 형태로 개편
- **`transcript.jsonl`에 `write_to_file`/`replace_file_content` 외의 도구(`find_by_name`/`grep_search`/`run_command`/`search_web`)는 호출 인자만 있고 실제 결과(검색 결과 개수, 커맨드 출력, 웹검색 요약)가 안 보이던 문제를 실측으로 해결**: agy가 도구 호출 바로 다음 줄에 `type:"GENERIC"`인 결과 스텝을 별도로 남긴다는 것을 실제 대화로 확인(예: `find_by_name` 다음 줄에 `"Found 2 results\nautomations.yaml\n..."`) — 신설 버퍼링 로직(`core/streamer.py` `tail_transcript()`)이 결과가 필요한 도구 호출을 한 줄 보류했다가, 바로 다음 줄이 매칭되는 GENERIC 결과면 접어서 하나의 항목으로 합침(결과가 없으면 한 줄 지연 후 그대로 흘려보냄, 무한 대기 없음)
- 신설 `_classify_tool_call()`이 도구별로 그룹(탐색/웹검색/편집/명령어/HA 도구)·동사·대상·통계·펼치기용 상세내용을 한 곳에서 결정 — `write_to_file`/`replace_file_content`는 beta.59에서 만든 diff에서 바로 `+N -M` 통계를 계산하고, `find_by_name`/`grep_search`/`run_command`는 GENERIC 결과에서 "N개 결과"/"N줄 출력" 요약을 정규식으로 뽑아냄(`_result_stat()`)
- SSE에 신설 `reasoning_step` 이벤트 타입 추가(`make_sse()`에 구조화 `data` 페이로드 지원 추가) — 기존 `live_log`(세션 시작/오류 배너 등 일회성 메시지)는 그대로 두고, 추론/도구 로그만 구조화 데이터로 분리 전송
- 프론트(`core/ui/scripts.py` 신설 `createReasoningTimeline()`): 연속된 파일 확인/파일명 검색/grep/웹검색은 자동으로 "파일 N개 탐색, 검색 M회" 하나의 접힌 그룹으로 묶이고, 편집/명령어/HA 도구 호출은 각각 독립된 줄로 표시. 각 줄(추론/그룹/개별 항목)은 클릭으로 개별 펼치기 가능 — 펼치면 diff, 커맨드 출력, 검색 결과 요약 등 실제 내용이 보임(6000자 캡, `_cap_detail()`)
- 말풍선 상단 뱃지(`.term-badge`, 기존 "● LIVE"/"● COMPLETED")를 전체 접기/펼치기 토글로 재활용 — 스트리밍 중엔 "⏳ N초 작업 중"으로 틱, 답변이 끝나면 "🕐 N초 동안 작업함"으로 고정되며 자동으로 접힘(사용자가 이미 수동으로 펼쳤다면 그 상태 유지)
- 복원된(과거) 대화도 동일하게 보이도록 신설 `buildStepsFromResponses()`가 `core/streamer.py`의 버퍼링 로직을 JS로 그대로 미러링 — `get_session_history()`가 이미 GENERIC 결과 스텝을 포함해서 반환하고 있었다는 것을 확인했기 때문에(rewind가 의존하는 `transcript.jsonl`/`step_index` 체계는 전혀 건드리지 않음) 서버 쪽 변경 없이 프론트만으로 라이브와 동일한 타임라인을 재구성. 다만 복원된 대화는 처음부터 접힌 상태로 시작(라이브는 완료 시점에 자동으로 접힘)
- `core/ui/styles.py`에 `.step-row`/`.step-child`/`.step-detail`/`.step-children` 등 신설 — 기존 `.term-box`와 동일한 고정 다크 콘솔 팔레트 사용

## 1.1.0-beta.63

### 개선 (Improve) — 도움말 패널 스크롤 + 스킬 설명 팝오버
- **도움말/피드백 패널(`.help-box`)에 `max-height`/`overflow-y:auto`가 없어 스킬·훅이 많아지면 화면 밖으로 넘칠 수 있던 문제 수정**: MCP/스킬/훅 목록이 전부 늘어나는 패널인데 세로 크기 제한이 없었음 (`core/ui/styles.py`)
- **스킬 목록에서 긴 `description`을 줄에 그대로 늘어놓지 않고, 이름 옆 (i) 아이콘 클릭 시 팝오버로 보여주도록 변경** (`core/ui/scripts.py` `toggleSkillInfo()`/`closeSkillInfoPopover()`, `core/ui/styles.py` `.skill-info-btn`/`.info-popover`): 특히 이번에 기본 탑재한 `home-assistant-best-practices` skill처럼 설명이 여러 문장인 경우 목록이 옆으로 한참 길어지던 문제 해결. 아이콘 클릭 시 버튼 위치 기준으로 팝오버를 띄우고(화면 밖으로 나가면 반대쪽으로 뒤집음), 같은 버튼 재클릭·바깥 클릭·패널 닫기 시 닫힘 — 이미지 라이트박스(beta.19 이전)와 동일하게 delegated click 리스너로 구현해 목록이 새로고침돼도 계속 동작

## 1.1.0-beta.62

### 추가 (Feature) — Home Assistant 모범사례 Agent Skill 기본 탑재
- `homeassistant-ai/skills` 저장소의 `home-assistant-best-practices` skill(SKILL.md + `references/` 참고파일 14개, 총 15개 파일)을 이미지 빌드 시 구워서 기본 탑재(`Dockerfile`). Agent Skills 표준의 progressive-disclosure 구조 그대로 유지 — SKILL.md만 컨텍스트에 상시 로드되고 나머지 참고파일은 에이전트가 필요할 때만 읽음
- **`/skills` 목록 기능(`core/skills_discovery.py`)이 애초에 실제 skill을 하나도 못 찾던 버그를 이번에 발견해 같이 수정**: 이 모듈은 공식 웹 문서(antigravity.google/docs/cli/plugins/)를 근거로 "skill은 `{skill}.md` 형태의 flat 파일이고 글로벌 경로는 `~/.gemini/antigravity-cli/skills/`"라고 가정하고 있었는데, 실제 설치된 Antigravity 제품 자체의 내장 문서(`agy-customizations` skill의 `docs/skills.md`)와 실제 파일시스템(`~/.gemini/config/skills/<name>/SKILL.md`에 이미 존재하던 사용자 생성 skill 2개, 그리고 `antigravity_guide`/`agy-customizations` 등 내장 skill들이 전부 `references/`·`docs/` 하위 폴더를 쓰는 디렉토리 구조)을 직접 확인한 결과 공식 웹 문서가 stale함을 실측으로 확인:
  - 진짜 글로벌 경로는 `~/.gemini/antigravity-cli/skills/`가 아니라 `~/.gemini/config/skills/`(`~/.gemini/antigravity-cli/`는 `settings.json`이 있는 곳이지 skill이 있는 곳이 아니었음)
  - 진짜 포맷은 skill 하나당 flat `.md` 파일이 아니라 `<skill>/SKILL.md` 디렉토리(+선택적 `scripts/`/`examples/`/`resources/`/`references/`)
  - `_skill_search_dirs()`의 global 경로와 `list_available_skills()`의 스캔 로직(디렉토리 목록 → 각 하위 디렉토리의 `SKILL.md` 탐색)을 이 실측 결과에 맞게 수정
- 새로 구운 skill은 `run.sh`가 `/root/.gemini/config/skills/`(=`/config/.gemini/config/skills/`, addon_config에 영구 보존)에 최초 1회만 복사 — `ha-guidelines.md`/`ha-file-safety.md`와 동일하게 이미 존재하면 건드리지 않아 사용자가 삭제/수정해도 다음 재시작에 되살아나지 않음. `Dockerfile`에서 바로 `~/.gemini/`에 굽지 않은 이유: `run.sh`가 매 시작마다 `/root/.gemini`를 통째로 지우고 `/config/.gemini`로 심볼릭 링크하기 때문에, 이미지에 구운 파일은 그 시점에 사라짐
- **실제 addon을 재빌드해 `/api/skills`로 실측하는 과정에서 두 번째 버그를 발견해 같이 수정**: 위 경로/포맷 수정 후 skill 자체는 잡혔지만 `description`이 `">"` 한 글자만 나옴 — `home-assistant-best-practices/SKILL.md`가 `description: >`(YAML 접힘 블록 스칼라)로 여러 줄에 걸쳐 설명을 적어두는데(같은 이유로 antigravity 자체 내장 예시 `agy-customizations/docs/skills.md`도 `description: >-`를 씀 — skill 설명은 에이전트가 언제 이 skill을 쓸지 판단하는 핵심 필드라 길게 쓰는 게 일반적인 관례), `_parse_frontmatter()`가 한 줄짜리 `key: value`만 읽던 기존 로직(`agent_discovery.py`와 공유하던 접근)이 `>` 마커 자체만 값으로 잘라먹고 있었음. 블록 스칼라(`>`/`|`, 폴딩 여부 구분)를 뒤따르는 들여쓰기 줄까지 이어붙이도록 `_parse_frontmatter()`를 확장(`core/skills_discovery.py`) — `agent_discovery.py`의 동일 파서는 지금까지 실제로 여러 줄 description을 만난 적이 없어 그대로 둠(범위 밖)

## 1.1.0-beta.60

### 수정 (Fix) — 화면 전체 먹통(세션 목록/모드/모델 선택 불가) 긴급수정
- **beta.59에서 추가한 diff 표시 기능이 프론트엔드 JS 전체를 문법 오류로 깨뜨려 화면이 통째로 먹통이 되던 버그 수정**: `core/ui/scripts.py`의 `JS_SCRIPTS`는 raw 문자열이 아닌 일반 Python 삼중따옴표 문자열이라, 소스에 `'\n'`(줄바꿈 이스케이프 2글자)라고 적어도 Python이 이를 실제 개행 문자로 미리 해석해버림 — 결과적으로 `formatTermLineHTML()`/`diffLogLines()`에 있던 `split('\n')`/`join('\n')`이 작은따옴표 문자열 안에 실제 줄바꿈이 낀 채로 브라우저에 전달되어 JS 파서가 그 지점에서 전체 스크립트 파싱을 실패시킴. 이 스크립트가 페이지의 모든 초기화 로직(세션 목록 로드, 모드/모델 선택 등)을 담당하고 있어서, 이 한 군데 문법 오류로 "세션 목록 불러오는 중..."에서 멈추고 모드/모델 선택도 전혀 반응하지 않는 전면 장애로 이어졌음
  - `node --check`로 추출한 JS를 실제 파싱해 정확한 실패 지점을 특정 후 확인 — 파일 내 같은 패턴(정규식 리터럴의 `\\`)은 이미 올바르게 이중 이스케이프되어 있었는데, 이번에 새로 추가된 5곳(`split`/`join` 3쌍)만 단일 이스케이프로 작성되어 있었음
  - `'\n'` → `'\\n'`로 수정해 Python 해석 후에도 JS에는 리터럴 2글자 `\n`이 그대로 전달되도록 함(`core/ui/scripts.py` `formatTermLineHTML()`, `diffLogLines()`). 템플릿 리터럴(백틱) 안의 `\n` 2곳은 Python이 실제 개행으로 바꿔도 백틱 문자열은 실제 개행을 허용하므로 문법상 문제 없어 그대로 둠

## 1.1.0-beta.59

### 추가 (Feature) — Mode 3 파일 편집 diff 표시
- Mode 3(`agy`)가 파일을 쓰거나 수정할 때 실시간 로그에 실제 변경 내용(diff)을 표시하도록 개선. 이전에는 `write_to_file`/`replace_file_content` 같은 파일 편집 도구 호출이 전부 "🔧 [도구 실행] write_to_file ..."처럼 일반 도구 호출과 동일하게만 표시되고 실제로 어떤 내용이 바뀌었는지는 전혀 안 보였음
  - 실측(`_agy_diff_test.txt` 생성 → 수정 시나리오로 실제 transcript.jsonl 캡처)으로 agy의 파일 편집 도구가 `write_to_file`(신규 생성/전체 덮어쓰기, `CodeContent`에 새 전체 내용)과 `replace_file_content`(부분 수정, `TargetContent`=기존 내용 / `ReplacementContent`=새 내용을 `StartLine`/`EndLine` 범위로 모두 제공)로 나뉜다는 것을 확인
  - **agy의 tool_call args 값이 이중 JSON 인코딩되어 있음을 실측으로 발견**: `CodeContent`/`TargetContent`/`AbsolutePath` 등 내용성 필드는 바깥쪽 JSON 파싱 후에도 `"hello world\n"`처럼 따옴표가 문자열 안에 그대로 남아있어(예: `\"CodeContent\":\"\\\"hello world\\\\n\\\"\"`), 실제 값을 얻으려면 한 번 더 파싱해야 함(반면 `Overwrite`/`StartLine` 같은 스칼라성 필드는 이렇게 감싸여 있지 않음) — 신설 `_agy_str()`(`core/streamer.py`)/`agyStr()`(`core/ui/scripts.py`)로 양쪽에서 동일하게 언랩. 기존에 이 언랩 없이 `AbsolutePath`/`toolSummary` 등을 그대로 쓰던 곳들도 전부 적용해 파일명 끝에 낀 따옴표 등 기존의 사소한 표시 오염도 같이 정리됨
  - `replace_file_content`는 `TargetContent`/`ReplacementContent`가 이미 정확히 바뀐 범위만 담고 있어 별도 diff 알고리즘 없이 `- 기존줄` / `+ 새줄` 블록으로 바로 표시(신설 `_diff_log_lines()`/`diffLogLines()`). `write_to_file`은 이전 내용이 args에 없어 diff 자체는 불가능 — 새 파일 생성(`Overwrite:false`)이면 전체를 `+`로, 기존 파일 덮어쓰기(`Overwrite:true`)면 "파일 덮어쓰기"로 구분 표시하고 새 내용만 보여줌(추정으로 이전 내용을 지어내지 않음)
  - 라이브 스트리밍 경로(`core/streamer.py` `tail_transcript()`)와 복원된 과거 대화 경로(`core/ui/scripts.py` `formatToolCallLogStr()`)가 동일한 로직을 각각 미러링하도록 구현 — 기존 "실시간 로그 = 복원 로그" 관례(beta.19 이전 정리) 유지. `+`/`-`로 시작하는 줄은 `formatTermLineHTML()`에서 초록/빨강으로 색칠(`core/ui/styles.py`의 `.diff-add`/`.diff-del`)
  - 스키마 실측 없이 설계하는 대신, 사용자가 실제 Mode 3 대화로 파일 생성→수정을 실행해 받은 실제 transcript.jsonl을 근거로 구현

## 1.1.0-beta.50

### 수정 (Fix)
- **되돌리기(rewind)가 기존(구버전에서 만들어진) 대화에서 400 에러로 실패하던 버그 수정**: `rewind_session()`이 항상 `get_session_transcript_path()`(캐노니컬 `logs/transcript.jsonl`) 경로만 보고 있었는데, 이 파일은 이 애드온의 "캐노니컬 트랜스크립트" 관례가 생기기 전에 만들어졌거나 agy가 아직 플러시하지 않은 대화에는 존재하지 않음(그런 대화는 agy의 레거시 첫 턴 스냅샷 `chunks/transcript_full/00000000.jsonl`만 가지고 있고, 화면에는 `get_readable_transcript_path()`로 그 파일을 읽어서 정상적으로 보여주고 있었음) — 되돌리기는 존재하지도 않는 캐노니컬 파일을 찾다가 매번 실패. `get_readable_transcript_path()`로 교체해 실제 화면에 보이는 파일을 그대로 잘라내도록 수정
- 되돌릴 지점을 찾을 때 "파일의 N번째 줄 = step_index N"이라고 가정하던 것도 함께 제거 — 이 가정은 이 애드온 자신이 쓰는 파일(`get_next_step_index()`가 항상 줄 수+1로 매김)에서만 보장되고, agy가 직접 쓰는 Mode 3 트랜스크립트의 실제 번호 매김 방식은 문서화돼 있지 않음. 각 줄을 파싱해서 `step_index` 필드값이 실제로 일치하는 줄을 찾아 그 위치에서 자르도록 변경(`core/session_manager.py` `rewind_session()`)

## 1.1.0-beta.49

### 추가 (Feature) — 대화 되돌리기 (/rewind 대응)
- 세션 히스토리의 각 사용자 메시지 옆에 "이 메시지로 되돌리기" 버튼 추가 — 클릭하면 해당 메시지부터 이후 대화가 전부 삭제되고, 되돌아간 시점에서 새 메시지를 이어보낼 수 있음(`core/ui/scripts.py` `rewindToStep()`/`buildUserRow()`, `POST /api/sessions/<cid>/rewind`, `core/session_manager.py` `rewind_session()`)
- **agy는 헤드리스에 `--rewind` 플래그가 없고, "삭제된" 대화도 agy 자신의 내부 메모리에는 그대로 남는다는 제약을 실측이 아니라 설계로 먼저 인지하고 우회**: 되돌리기는 이 애드온이 표시/추적하는 `transcript.jsonl`만 자를 뿐이므로, 되돌린 뒤 같은 `conversation_id`로 `--conversation`을 계속 보내면 agy 입장에서는 "삭제됐던" 내용이 여전히 살아있어 사용자를 속이는 셈이 됨. 따라서:
  - 신설 `mark_rewound()`/`is_rewound()`/`clear_rewound()`(`core/session_manager.py`)로 "되돌려짐" 상태를 마킹하고, `core/streamer.py`의 재개 판단 로직(`resume_this_session`)이 이를 확인해 되돌린 직후의 다음 Mode 3 턴에는 `--conversation`을 보내지 않도록 함 — 이미 존재하던 "모드 1/2 전용 대화 → 모드 3 최초 전환" 시 agy가 자체 id를 새로 발급하고 `link_conversation_continuation()`으로 연결하던 경로(beta.20)를 그대로 재사용
  - 새 agy id가 과거 맥락을 전혀 모르는 상태로 시작하는 문제를 막기 위해, 신설 `build_rewind_context_preamble()`이 남겨진(잘리지 않은) 대화의 질문/답변만 텍스트로 압축해 다음 프롬프트 앞에 삽입 — 4000~6000자 캡을 두는 `/usage` raw_text 등 기존 방어적 캡핑 관례와 동일하게 6000자로 제한
  - 되돌리기는 "클릭한 메시지 자체는 남기고 답변만 지우기"가 아니라 "클릭한 메시지부터 포함해서 전부 삭제"로 구현 — 전자는 답변 없는 질문이 히스토리 중간에 붕 뜨는 형태가 되어 후자로 결정
- 모드 1/2 → 모드 3 핸드오프로 대화가 여러 물리 파일(체인)에 걸쳐 있는 경우, `step_index`는 파일마다 독립적으로 매겨지므로 다른 파일의 `step_index`를 잘못 적용해 엉뚱한 줄을 자르는 사고를 막기 위해 `get_session_history()`가 각 항목에 `source_cid`(실제 그 메시지가 들어있는 물리 파일의 id)를 태깅하도록 변경 — 프론트는 `source_cid`가 현재 열려있는 대화와 다른(=체인의 이전 세그먼트) 메시지에는 되돌리기 버튼을 아예 숨김

## 1.1.0-beta.47

### 추가 (Add) — HA 파일 안전장치
- **파일 삭제/덮어쓰기 전 사전 승인 + HA 핵심 폴더 보호 규칙 도입** (`run.sh`): Mode 3(`agy -p ... --dangerously-skip-permissions`)는 모든 도구 호출을 자동 승인하는 헤드리스 실행이라 인터랙티브 권한 프롬프트 자체가 없다는 것을 `agy` 공식 문서/이슈 트래커로 실측 확인(`--dangerously-skip-permissions` 자체가 permissions 엔진을 완전히 우회하며, 이 플래그 없이 헤드리스로 돌리면 승인이 필요한 도구 호출에서 타임아웃도 안 먹고 영구 행(hang)하는 상위 버그가 별도로 존재 — 헤드리스 스트리밍이 동작하려면 이 플래그가 사실상 필수). 따라서 실제 강제 차단은 모드와 무관하게 항상 컨텍스트로 주입되는 always-on 규칙 파일로 구현:
  - 신설 `/root/.gemini/config/rules/ha-file-safety.md` (기존 `ha-guidelines.md`와 동일한 주입 방식): "삭제/덮어쓰기 전 대상 파일 경로·개수·사유를 먼저 알리고 사용자의 다음 메시지에서 명시적 승인을 받기 전에는 절대 실행하지 않는다"는 절차 규칙 + `/config/.storage/`, `secrets.yaml`, `configuration.yaml`, `.uuid`, `.HA_VERSION`, `home-assistant_v2.db`, `.cloud/`, 이 애드온 자신의 `.gemini/`, `automations/scripts/scenes.yaml`, `custom_components/`, `/backup/` 등 HA 운영에 필수적인 절대 삭제·수정 금지 목록을 표로 명시(사용자가 명시적으로 요청해도 거부하고 위험성을 설명하도록 지시)
  - `settings.json`의 `permissions.deny`에 `command(rm -rf)`/`command(sudo)` 및 위 핵심 경로들에 대한 `write_file(...)` 항목 추가(기존 `allow` 병합 로직과 동일하게 `jq`로 멱등 병합). `--dangerously-skip-permissions`가 걸린 Mode 3 헤드리스 경로에서는 이 목록이 강제되지 않지만(위 이유), `--dangerously-skip-permissions` 없이 `agy`를 직접 띄우는 웹 터미널(ttyd/tmux) 경로에서는 실제 하드 차단으로 동작 — 두 메커니즘을 함께 적용해 방어를 이중화

## 1.1.0-beta.46

### 수정 (Fix) — 안전 긴급수정
- **기기 상태 질문이 기기 제어 명령으로 오작동하던 심각한 버그 수정**: "안방 스탠드 등 켜져있어?" 같은 상태 질문이 "켜"라는 글자가 포함되어 있다는 이유만으로 "켜줘" 명령과 동일하게 처리되어 실제로 안방 조명이 전부 켜지는 사고 발생 — 실사용 중 발견 및 즉시 수정
  - 신설 `is_status_query()`(`core/ha_client.py`): "켜져있", "꺼져있", "열려있", "닫혀있", "작동중" 등 상태 표현이나, 명령 어미("줘"/"주세요"/"줄래" 등) 없이 "?"로 끝나는 문장을 감지 — `execute_device_control_intent`/`toggle_automation_intent`/`run_script_or_scene_intent` 진입 전 최우선 검사로 적용(방어적 이중 체크: `ha_engine.py` 디스패치 단계 + 각 제어 함수 내부)
  - 신설 `get_device_status_answer()`: 상태 질문으로 판별되면 어떤 기기를 실행하지 않고, 해당 방/도메인에 속한 기기들의 현재 상태를 개별적으로 나열해서 응답(예: "안방 조명 상태 - 안방 등: 꺼짐 / 안방 화장실 등: 꺼짐 / 안방 스탠드 램프: 꺼짐") — 방 안에 이름이 비슷한 기기가 여러 개일 때 어떤 것을 뜻하는지 추측하지 않고 전부 보여주는 방식으로 안전하게 답변
  - "커튼 열어줄래?"처럼 명령 어미가 있는 의문형 명령문은 기존대로 정상 실행됨을 회귀 테스트로 확인

## 1.1.0-beta.43

### 수정 (Fix)
- **첨부 업로드가 파일 크기와 무관하게 매번 실패하던 진짜 원인 발견**: `/api/chat`는 `Content-Length`와 `Transfer-Encoding: chunked` 둘 다 처리하는데, `/api/upload`는 `Content-Length`만 보고 없으면 곧바로 빈 본문(`{}`)으로 취급하고 있었음 — HA Ingress 프록시가 POST 본문을 청크 전송으로 릴레이하면 `Content-Length` 헤더 자체가 없어서, 파일 하나 없이도 매번 `files: []`로 조용히 끝났던 것(서버 로그도 안 남고, HTTP 200이라 에러 코드도 안 뜨고, 프런트는 "업로드 실패"만 표시). 작은 텍스트 파일도 실패한다는 실측으로 크기 문제가 아님을 확인 후 발견. `_read_request_body()` 공통 헬퍼로 청크 처리 로직을 추출해 `/api/chat`과 `/api/upload` 둘 다 사용하도록 수정
- `/api/upload`에 요청 진입 시점 로그(`body_len`, `files_in_payload`)를 추가해 앞으로 같은 종류의 문제를 로그만으로 바로 구분 가능하도록 함

## 1.1.0-beta.42

### 수정 (Fix)
- 서버 사이드 확장자 화이트리스트(`ALLOWED_EXTENSIONS`)와 MIME 기반 복구 로직(`_recover_allowed_extension`)을 `core/uploads.py`에서 완전히 제거 — beta.36부터 계속 재현되던 업로드 실패의 근본 원인이었고, 실기기가 브라우저에 넘기는 파일명/MIME 조합이 예상과 달라 계속 오탐이 나왔음. 이제 필터는 파일 선택창의 `accept` 속성(`core/ui/templates.py`)뿐이고, 서버는 확장자와 무관하게 통과된 파일을 그대로 저장

## 1.1.0-beta.41

### 수정 (Fix)
- `core/uploads.py`의 `save_uploaded_files()`가 모든 첨부 시도(수신한 파일명/MIME 타입/base64 길이, 거부 사유, 저장 성공 경로)를 `[Upload]` 접두어로 stderr(HA 애드온 로그)에 기록하도록 변경 — 이전엔 진짜 예외(크래시)만 로그에 남고 확장자 거부/빈 파일/크기 초과 같은 "정상적인 거부"는 응답 JSON에만 담겨 로그로는 원인을 알 수 없었음

## 1.1.0-beta.40

### 수정 (Fix)
- **첨부 업로드 실패 원인 확정 및 수정**: beta.35(확장자 검사 없음)에서는 되고 beta.36(확장자 화이트리스트 추가) 이후 안 됐던 게 결정적 단서 — 모바일 카메라 촬영/클립보드 붙여넣기로 온 파일은 `3d3a9dc0-53d0-...`처럼 확장자 없는 UUID 파일명으로 넘어오는 경우가 있어, 확장자 검사에서 전부 걸러지고 있었음. `core/uploads.py`에 `_recover_allowed_extension()` 추가 — 파일명에 허용된 확장자가 없으면 브라우저가 함께 보내주는 MIME 타입(`file.type`)으로 유추해서 구제(예: `image/jpeg` → `.jpg` 자동 부여), 그래도 못 찾으면 그때 거부. 프론트(`core/ui/scripts.py`)는 업로드 요청에 `content_type` 필드를 추가로 실어 보내도록 수정

## 1.1.0-beta.39

### 수정 (Fix)
- 첨부 파일 업로드 시점을 "파일 선택 즉시"에서 "메시지 전송 시"로 변경 — 파일 선택은 로컬 미리보기만 만들고(네트워크 요청 없음), 실제 `/api/upload` 호출은 전송 버튼을 누른 시점에 한 번에 처리되도록 `uploadAttachment()`로 분리(`core/ui/scripts.py`). "첨부 → 입력 → 전송"이 한 동작처럼 느껴지도록 함
- **CPU 듀얼 차트에서 애드온 사용량이 시스템 전체보다 높게 그려지던 버그 수정**: `core/system_info.py`의 `get_addon_cpu_percent()`가 cgroup `usage_usec`(컨테이너가 사용한 모든 코어의 CPU 시간 합)를 코어 개수로 나누지 않고 그대로 0~100%로 환산하고 있었음 — 멀티코어 호스트에서 애드온이 코어 1개를 거의 다 쓰면(코어 1개 기준 100%) 전체 시스템 사용률(전체 코어 평균, 예: 25%)보다 높게 표시되는 물리적으로 불가능한 그래프가 나왔음. `os.cpu_count()`로 나눠 시스템 전체와 동일한 척도(전체 호스트 용량 대비 %)로 정규화
- 리소스 모니터 차트가 너무 빨리 스크롤되는 문제 — 히스토리 버퍼를 24개(3초 간격 기준 72초)에서 60개(3분)로 확대

## 1.1.0-beta.38

### 수정 (Fix)
- 첨부 시 파일 박스가 빨간 테두리(업로드 실패)로 표시되던 문제 진단을 위해 오류 메시지를 hover 툴팁이 아니라 칩 안에 바로 보이는 텍스트로 변경, 실패 사유도 더 구체적으로(`HTTP 상태 코드` 또는 실제 예외 메시지) 표시
- `POST /api/upload` 핸들러 전체를 try/except로 감싸 처리되지 않은 예외가 응답 자체를 끊어버리는 경우(클라이언트에서 원인 불명의 "업로드 실패"로만 보이던 상황)를 방지 — 실패 시에도 항상 원인이 담긴 JSON 오류 응답을 반환하고 서버 stderr에도 기록
- `base64.b64decode`를 엄격 검증(`validate=True`)에서 기본 동작(`validate=False`)으로 완화 — 일부 브라우저 인코딩 경로가 섞어 보낼 수 있는 공백/개행 문자를 관대하게 허용(빈 파일/크기 초과 검사는 그대로 유지되어 실제로 깨진 데이터는 계속 걸러짐)

## 1.1.0-beta.37

### 수정 (Fix)
- 첨부 파일을 agy가 인식 못 하던 문제 수정 — 기존 "다음 첨부 파일을 참고해서 답변해줘: - <경로>" 식 한국어 안내문 대신, 첨부 파일을 프롬프트 맨 앞에 마크다운으로 직접 삽입(이미지는 `![파일명](경로)`, 그 외 파일은 `📄 **파일명**`)하도록 변경. agy에게 보내는 텍스트에는 컨테이너 절대경로를, 사용자 말풍선 렌더링에는 새로 만든 `GET /api/uploads/<batch>/<파일명>`(신설, `core/uploads.py`의 `resolve_upload_path`로 경로 검증) URL을 사용 — 브라우저는 컨테이너 파일시스템 경로를 직접 로드할 수 없어서 서빙 라우트가 필요했음
- 사용자 말풍선을 AI 응답과 동일한 `formatMarkdown()` 파이프라인으로 렌더링하도록 통일 — 별도 썸네일 스트립 마크업 없이 마크다운 하나로 첨부(이미지/파일)와 본문 텍스트가 자연스럽게 분리되어 보임(요청하신 "지금과 동일한 UI 유지")
- 채팅 버블 내 이미지 클릭 시 확대 보기(라이트박스) 추가 — 첨부 이미지뿐 아니라 AI 응답에 이미지가 포함되는 경우에도 동일하게 적용되는 위임 클릭 핸들러

## 1.1.0-beta.36

### 수정 (Fix)
- 첨부 파일 허용 확장자를 Google Antigravity가 실제 지원하는 형식(사용자 제공 목록)으로 제한 — 소스코드(`.py/.js/.ts/.java/.c/.cpp/.go/.rs/.sh/.bat/.ps1`), 구조화 데이터(`.json/.yaml/.yml/.xml/.toml/.ini/.env/.csv/.tsv`), 문서(`.txt/.md/.pdf/.docx`), 이미지(`.png/.jpg/.jpeg/.webp/.gif`). 파일 선택창(`accept`)뿐 아니라 `core/uploads.py`(`ALLOWED_EXTENSIONS`)에서 서버 사이드로도 검증 — `accept`는 우회 가능한 UI 힌트일 뿐이라 서버 쪽 확인이 실제 방어선

## 1.1.0-beta.35

### 추가 (Feature)
- Mode 3(CLI 추론 모드) 전용 파일/이미지 첨부 기능 추가. 실측 확인: agy 자체 내장 `view_file` 도구가 헤드리스 `-p` 프롬프트에 절대경로만 참조해도 이미지를 실제로 "보고" 정확히 이해함(별도 멀티모달 API 연동 불필요) — 신설 `core/uploads.py`가 업로드 바이트를 저장하고 절대경로만 반환, `POST /api/upload` 신설. 프론트는 여러 파일 동시 첨부 + 이미지 썸네일 미리보기 지원, 전송 시 파일 경로들을 프롬프트 앞에 자동으로 엮어 넣고 실제 유저 말풍선에는 원문 텍스트 + 썸네일만 표시
  - Mode 1/2는 agy를 호출하지 않아 `view_file` 자체가 없으므로, 첨부 버튼은 Mode 3가 아닐 때 비활성화(회색 처리)되고, 혹시 모를 상태 불일치에 대비해 첨부파일이 있으면 전송 시점에 강제로 Mode 3로 실행
- 채팅 입력창을 최대 3줄까지 자동으로 늘어나도록 변경(`autoResizeTextarea`) — 그 이상은 내부 스크롤

## 1.1.0-beta.34

### 추가 (Feature)
- Mode 3(CLI 추론 모드)에 커스텀 에이전트(`agy --agent <id>`) 선택 기능 추가. 신설 `core/agent_discovery.py`가 `{workspace}/.agents/agents/*/agent.md`(워크스페이스, `/homeassistant` 우선)와 `~/.gemini/config/agents/*/agent.md`(전역)를 직접 읽어 YAML 프런트매터(name/description)를 파싱 — `agy agents` 서브커맨드는 쓰지 않음(실측 확인: `--output-format` 자체를 지원 안 하고, 커스텀 에이전트가 하나도 없으면 성공/실패 구분 없이 그냥 빈 출력만 냄). `GET /api/agents` 신설, 컴포저 툴바에 에이전트 피커 추가 — 발견된 에이전트가 0개면(설치 초기 기본 상태) 피커 자체를 숨겨서 빈 목록이 노출되지 않도록 처리
- `docs/cli/commands/agents` 공식 문서로 에이전트 정의 형식 확인: `---\\nname: ...\\ndescription: ...\\n---` 프런트매터 + 본문 시스템 프롬프트

## 1.1.0-beta.33

### 수정 (Fix)
- 복합모드(Mode 2, `stream_ai_deep_brain`)가 날씨/환경 관련 단어가 없는 일반 상태 질의("우리집 종합 상황 알려줘" 등)에서는 고속모드와 완전히 동일한 `handle_agent_chat()` 결과를 그대로 반환하던 문제 수정 — "상태/상황/현황/요약/브리핑/종합/집안/우리집/어때" 등 일반 상태 키워드도 AI 딥 브레인 리포트(`get_ai_deep_environment_analysis`)로 라우팅되도록 트리거 키워드 확장. 이제 같은 질문에도 고속모드는 짧은 요약을, 복합모드는 표+진단+AI 제안이 포함된 리포트를 반환

## 1.1.0-beta.32

### 수정 (Fix)
- 대화 제목 변경을 `prompt()` 팝업 대신 인라인 편집으로 변경 — 연필 아이콘 클릭 시 제목 텍스트가 바로 입력창으로 바뀌어 그 자리에서 수정(Enter 확정/Esc 취소/포커스 아웃 시 저장), `PATCH /api/sessions/<cid>` 연동은 beta.30과 동일
- "최근 대화 이어가기" 버튼 제거 — 최근 대화 목록 맨 위 항목을 클릭하는 것과 동일한 기능이라 중복으로 판단되어 되돌림

### 조사 (Investigation)
- 대화를 이어가면 최근 대화 목록에서 해당 항목이 맨 위로 재정렬되는지 코드 검토: `list_all_sessions()`의 정렬 기준(`mtime`)은 매 호출마다 transcript.jsonl의 실제 파일 mtime을 다시 읽어 계산하고, 메시지 전송 시작(`session_init`)과 완료(`done`) 시점마다 프론트에서 `loadSessionsList()`를 다시 호출하므로 별도 코드 변경 없이 이미 정상 동작해야 함 — 실사용 테스트로 최종 확인 필요

## 1.1.0-beta.31

### 추가 (Feature)
- 고속모드(Mode 1)/복합모드(Mode 2)가 다루는 HA 도메인 확장 (`core/ha_client.py`, `core/ha_engine.py`, `core/sensors.py`)
  - 신규 제어: 가습기/제습기(`humidifier.`, 없으면 큐레이션 switch로 폴백), 보일러/히터/온열기/전기스토브/콘센트/플러그(큐레이션 switch), 에어컨(`climate.`), TV(기존 IR 스크립트 우선, 없으면 `media_player.`)/스피커(`media_player.`) — on/off만 지원
  - 신규: 자동화 켜기/끄기(`toggle_automation_intent`), 스크립트/씬 실행(`run_script_or_scene_intent`) — 이름 부분일치, 애매하면 후보 제시
  - 신규 조회: 문/창문 열림 및 카메라 상태, 가족 재실 현황 및 특정 가족 위치, 전력/가스 사용량(현재 값 기준), 가족 생일·기념일 D-day, 배터리 부족/업데이트 대기 기기(기존 시스템 헬스체크에 통합)
- 오작동 방지 안전장치
  - 방 이름 오인식 수정: "안방 화장실"처럼 두 단어가 붙어 하나의 실제 구역을 이루는 경우를 인접 토큰 합성으로 발견하고, 매칭 시 더 구체적인(긴) 후보를 우선하도록 변경(`get_dynamic_rooms`/신설 `match_room`) — 예: "안방화장실 온도"가 안방 온도로 잘못 나오던 문제 수정
  - 기기 제어(조명/커튼/팬/가습기/스위치/에어컨/미디어) 전체에 안전 게이트 적용(신설 `resolve_control_scope`): 방을 인식 못 하면 조용히 전체 기기를 대상으로 삼던 기존 동작을 제거하고, "전체/모두/다같이" 같은 명시적 전체 키워드가 없으면 실행 대신 "어느 방을 말씀하시는 걸까요?" 재질문으로 응답
  - 스위치 도메인은 도메인 전체가 아니라 큐레이션된 가전 키워드로만 진입(차일드락/마이크뮤트/리부트 등 설정용 스위치는 명시적으로 제외), "냉장고"는 허용 키워드에서 의도적으로 제외
  - 동적으로 삽입되는 기기/방 이름에 맞춰 을/를, 이/가 조사를 배치문자 유무로 자동 선택(신설 `_particle`)

## 1.1.0-beta.30

### 추가 (Feature)
- 세션 사이드바에 대화 제목 변경(연필 아이콘) 기능 추가 — `core/session_manager.py`에 `set_session_title`/`get_custom_title` 추가(대화 폴더에 `custom_title.txt` 마커 저장), `PATCH /api/sessions/<cid>` 엔드포인트 신설, `list_all_sessions()`가 커스텀 제목을 첫 프롬프트 자동 제목보다 우선 사용
- 사이드바 "새 대화 시작" 버튼 옆에 "최근 대화 이어가기" 버튼 추가 — 별도 agy 플래그 없이 이미 있는 `conversation_id` 재개 흐름으로 가장 최근 세션을 바로 염
- 헤더에 도움말/피드백(ℹ️) 버튼 추가 — 실행 모드 설명, 단축키, GitHub Issues 링크를 담은 정적 모달 패널
- 애드온 설정에 `print_timeout`(기본 `5m`, agy 자체 기본값과 동일)·`enable_sandbox`(기본 꺼짐) 옵션 추가 — Mode 3(`agy` headless) 실행 시 `--print-timeout`/`--sandbox`로 전달. 실측 `agy --help`(설치 바이너리)로 두 플래그 존재 확인 후 반영. `print_timeout`은 Go duration 형식(`5m`, `90s`, `1h30m` 등)만 허용하고, 형식이 맞지 않으면 플래그 자체를 생략해 agy 자체 기본값(5m0s)으로 안전하게 폴백(쉘 문자열에 그대로 삽입되므로 임의 값 통과 방지)

### 조사 (Investigation)
- 실측 `agy --help`(v1.1.22+)에서 `--effort low|medium|high` 플래그가 실제로 존재함을 확인 — `core/streamer.py`/`core/model_discovery.py`의 기존 전제("별도 --effort 플래그 없음, effort는 모델 slug에 baked-in")와 모순됨. 현재 코드는 여전히 slug 기반 방식으로 동작 중이며 이번 변경에서는 건드리지 않음 — effort 처리 방식을 바꾸려면 모델 피커/카탈로그 전체에 영향이 있어 별도 검토 필요
- `/logout`: `agy --help` 서브커맨드 목록(`agent/agents/changelog/help/install/mcp/mic-serve/models/plugin/plugins/update`)에 auth/logout류가 없고, `~/.gemini` 하위에서 token/credential/auth 이름의 파일도 발견되지 않음 — 안전하게 구현할 공식 메커니즘이 확인되지 않아 보류
- `--output-format`: `text`/`json`/`stream-json` 중 `stream-json`만 이 애드온의 실시간 SSE 파싱과 호환되므로, 채팅 UI에 선택 옵션으로 노출하지 않음(다른 값 선택 시 실시간 스트리밍이 깨짐)

## 1.1.0-beta.29

### 수정 (Fix)
- 고속모드(Mode 1)/복합모드(Mode 2) 자연어 응답의 한국어 표현 개선
  - 기기 제어 확인 문구에서 번역투 "성공적으로" 제거 (예: "조명을 성공적으로 켰습니다" → "조명을 켰습니다")
  - 온도/습도/CO2/TVOC/PM2.5 단일 지표 질의에 쾌적도 코멘트 추가 (기존 `evaluate_room_env_health` 임계값 재사용)
  - "찾을 수 없습니다"/"수집하지 못했습니다" 등으로 흩어져 있던 데이터 없음 안내를 "찾지 못했습니다"로 통일
  - AI 추천 문구 라벨 자연화: "온열 환경 케어"→"온도 관리", "에너지 케어"→"에너지 관리 안내", "환기 제어"→"환기 안내"

## 1.1.0-beta.28

### 수정 (Fix)
- 터미널 agy 실행 확인 문구 "agy를 실행하시겠습니까?" → "agy(Antigravity CLI)를 실행할까요?"

## 1.1.0-beta.27

### 추가 (Feature)
- 터미널 탭 진입 시 곧바로 bash 커서로 떨어지는 대신 "agy를 실행하시겠습니까?" Yes/No 확인창 표시. Yes 선택 시 서버가 ttyd와 동일한 tmux 세션(`main`)에 `agy` + Enter를 직접 입력(`tmux send-keys`)해 실제로 타이핑한 것처럼 실행 — 새 `POST /api/run_agy` 엔드포인트 추가(`/api/terminal/*`로 만들면 `do_POST`의 ttyd 프록시 분기가 경로에 "/terminal"이 포함된 모든 요청을 가로채므로 의도적으로 `/api/run_agy`로 명명). No 선택 시 확인창만 닫고 그대로 bash 프롬프트 유지

## 1.1.0-beta.26

### 수정 (Fix)
- 사이드바 내비게이션에서 "웹 터미널" 탭을 선택하면 왼쪽 세션 사이드바가 자동으로 닫히도록 변경(데스크톱은 collapsed, 모바일은 slide-out 닫힘) — 터미널 화면을 최대한 넓게 사용

## 1.1.0-beta.25

### 수정 (Fix)
- 모델 선택 버튼의 사용량 링 게이지 크기를 20% 축소(11px → 8.8px), 링 두께 비율이 유지되도록 안쪽 여백도 비례 조정

## 1.1.0-beta.24

### 수정 (Fix)
- 모델 선택의 Effort(추론강도) 드롭다운 순서를 High→Medium→Low에서 Low→Medium→High로 변경 — 실측 `agy models` 출력 순서(high/medium/low)를 그대로 쓰던 것을 고정된 표시 순서로 정렬(`core/model_discovery.py`의 `_sort_efforts`), 내장 폴백 카탈로그(`core/models_catalog.py`)도 동일하게 수정. 기본 선택값(High)은 그대로 유지 — 순서만 바뀜

## 1.1.0-beta.23

### 수정 (Fix)
- 직전 beta.22의 "입력창 아래 사용량 게이지 블록"을 요청대로 되돌리고, 모델 선택 버튼의 이펙트 태그("Low") 바로 오른쪽에 링 게이지 하나만 인라인으로 표시하도록 변경 — 라벨/퍼센트 텍스트 없이 링만. 주간 잔여율을 우선 표시하고, 없으면 5시간 잔여율로 대체, 둘 다 없으면 표시 안 함

## 1.1.0-beta.22

### 수정 (Fix)
- 상단 리소스 모니터 패널을 3줄(제목바 / CPU·RAM 차트 / 통계 4칸)에서 차트 1줄만 남기고 나머지 2줄 제거 — 모바일에서도 차트 2개가 세로로 쌓이지 않고 항상 1줄로 유지되도록 하고, 대신 좁은 화면에서는 패딩/폰트/캔버스 높이만 축소
- 모델 선택 창의 실행 모드 이름 변경: "스마트홈 고속 제어"→"고속 제어 모드", "AI 딥 브레인"→"고속 제어 & 스마트 모드", "Antigravity CLI"→"CLI 추론 모드"
- 응답 말풍선 헤더 재구성: 추론/도구 로그 박스를 답변보다 위, 답변 헤더(렌더링·원문 토글)보다도 위로 이동해 시각적으로 분리. 로그 헤더의 빨강/노랑/초록 터미널 점 장식 제거, 그 자리에 모드 태그를 배치해 `[고속]`/`[복합]`/`[CLI]`로 표시 — `모델 선택 창`과 동일한 짧은 이름을 재사용하므로 두 곳의 표기가 어긋날 일이 없음
- 응답 본문 텍스트 크기를 0.935rem → 0.875rem로 한 단계 축소

### 추가 (Feature)
- 대화 입력창 아래에 현재 선택된 모델의 사용량 게이지 추가 — 주간/5시간 한도 중 실제 값이 있는 항목만 표시(N/A인 창은 표시하지 않음)

## 1.1.0-beta.21

### 수정 (Fix)
- 히스토리 복원 시 페이지네이션이 원문 JSONL 줄 수(15줄) 단위로 슬라이스되어, 모드3(agy)처럼 도구 호출 하나마다 여러 줄을 남기는 턴의 중간을 잘라버리는 문제 수정 — 질문 하나가 "답변만 있고 질문이 없는 말풍선"과 "질문 뒤에 가짜 '작업이 완료되었습니다' 답변이 붙는 말풍선"으로 쪼개져 여러 대화처럼 보였음. 이제 원문을 USER_INPUT 기준 턴 단위로 먼저 그룹화한 뒤 턴 단위로만 페이지네이션(`buildSessionTurns`) — 턴 중간이 잘리는 경우가 구조적으로 불가능해짐
- 히스토리 복원 말풍선과 실시간 스트리밍 말풍선의 디자인이 서로 달랐던 문제 수정 — 헤더(모드 배지/렌더링·원문 토글/복사 버튼), 도구 실행 로그 박스, 메타 영역까지 완전히 동일한 마크업(`buildBotBubbleDOM`)을 공유하도록 통일. 복원된 턴은 저장된 `thinking` 텍스트 접두어로 모드 배지를 추정 표시
- "이전 대화 더보기" 버튼을 없애고, 채팅창 위로 스크롤하면 자동으로 이전 턴을 더 불러오도록 변경(IntersectionObserver) — 더 불러올 대화가 없으면 "🏁 더 이상 이전 대화가 없습니다" 표시. 한 번에 불러오는 단위도 15줄 → 10턴으로 확대

## 1.1.0-beta.20

### 수정 (Fix)
- 한 채팅에서 모드1/2로 대화를 시작한 뒤 모드3(Antigravity CLI)으로 전환하면, 프론트가 들고 있던 자체 생성 id로 `agy --conversation`을 호출하게 되어 agy가 이를 인식 못 하고 조용히 별개의 새 id로 대화를 시작 → 세션이 두 조각으로 쪼개져 나중에 목록에서 열면 일부 내용이 복원되지 않던 문제 수정
  - `is_agy_native_session()` 추가: agy 자신의 첫 턴 스냅샷 존재 여부로 "agy가 이 id를 실제로 발급했는지" 판별
  - `resume_this_session`이 `is_agy_native_session()`까지 확인하도록 강화 — 모드1/2 전용 히스토리는 모드3 입장에서 신규 대화로 취급(agy가 자체 id 발급하도록 둠)
  - 전환으로 새로 생긴 id는 `link_conversation_continuation()`으로 원래 id와 연결(`continued_as.txt`/`continued_from.txt` 마커), `get_session_history()`/`list_all_sessions()`/`delete_session()`이 이 체인을 따라가 하나의 병합된 세션으로 표시·삭제
  - 상세: `docs/COMMUNICATION_SPEC.md` v2.4 (제약 #7) 참고

## 1.1.0-beta.19

### 수정 (Fix)
- "새 대화 시작" 버튼이 사이드바 폭을 꽉 채우도록 수정(부모 래퍼가 flex가 아니어서 flex:1이 적용되지 않던 문제)
- "새 대화 시작" 버튼 래퍼의 위/아래 여백을 8px로 동일하게 맞춤

## 1.1.0-beta.18

### 수정 (Fix)
- 사이드바 내비게이션(AI 채팅/웹 터미널 탭)과 "새 대화 시작" 버튼 사이에 구분선 추가

## 1.1.0-beta.17

### 수정 (Fix)
- 사이드바 순서를 내비게이션 → 새 대화 시작 → 최근 대화 기록 순으로 변경(사용자 요청, 원본 소스와는 다른 배치)
- "전체선택/선택삭제" 툴바를 최근 대화 목록 상단이 아니라, "총 N개 세션" 푸터와 같은 자리(목록 하단)에 표시되도록 이동
- 채팅 입력창 위 구분선 제거
- 모바일 대응: 모델 선택 → 특정 모델 탭 시 effort 플라이아웃이 화면 밖으로 나가 안 보이던 문제 수정(좁은 화면에서는 오른쪽이 아니라 아래로 펼침) + 모델 행을 탭하면 즉시 선택되며 닫혀버리던 것을, effort가 있는 모델은 항상 먼저 effort 선택지를 펼치도록 변경(호버가 없는 터치 환경 대응)
- 모바일 대응: View Usage 패널이 화면 오른쪽으로 잘려 보이던 문제 수정(좁은 화면에서는 화면 하단에 고정 표시)

## 1.1.0-beta.16

> git reflog에서 롤백된 React(@assistant-ui/react + Tailwind) 소스를 복구해서, 스크린샷 눈대중이 아니라 실제 색상 값·아이콘·여백·폰트 크기를 그대로 포팅. "100%"의 실제 의미(색·아이콘·여백·시간포맷·폰트크기·레이아웃 전부)에 맞춘 전면 재작업.

### 추가 (Feature)
- 세션 삭제 기능 추가 — 개별 삭제(호버 시 휴지통 아이콘, 확인창) + 다중 선택 삭제("전체 선택"/"선택 삭제 (N)", 확인창). `core/session_manager.delete_session()` + `DELETE /api/sessions/<cid>`, `DELETE /api/sessions`(bulk) 신설
- 실제 음성 입력 구현(Web Speech API, 브라우저 내장 STT) — 첨부 파일과 달리 백엔드 없이 클라이언트만으로 가능해서 실제로 동작하도록 구현
- 세션 목록 날짜를 서버에서 "MM/DD HH:MM" 형식으로 미리 포맷(`date_str`) — 브라우저 로케일에 따라 "오후 2:37"처럼 바뀌던 문제 원천 차단

### 수정 (Fix)
- 색상 토큰을 실제 소스값으로 교체: `#09090b`/`#121215`/`#18181b`(surface 단계), `#38bdf8`(accent-blue), `#2563eb`(사용자 말풍선) 등 — 지난 버전의 "M3 톤" 추정값 전부 폐기
- 이모지 아이콘(☰🌙🪙🎤 등)을 전부 Lucide 동등 SVG 아이콘으로 교체(헤더, 사이드바, 컴포저, 모델/모드 피커). 단, 퀵액션 카드는 원본처럼 이모지+텍스트 버튼 그대로 유지(색상 아이콘 사각형은 저희가 잘못 추가했던 것— 제거)
- 채팅 입력창을 원본과 동일한 단일 보더 박스(rounded-[22px], 배경 #18181b)로: 첨부 24px 원형 버튼, 모드/모델 피커는 필이 아닌 rounded-lg(8px) 버튼, 마이크·전송 28px 원형, 전송 버튼은 텍스트 입력 시 흰 배경으로 전환
- 모드 선택 강조색을 파랑에서 호박색(amber)으로, 모델 사용량 패널을 클릭이 아닌 호버로 여는 방식으로 변경(원본과 동일)
- 모드 번호 체계를 원본 기준(1=고속, 2=복합, 3=CLI)으로 백엔드 라우팅까지 맞춤(이전엔 프런트 라벨만 바꾸고 백엔드 라우팅은 그대로였음)
- 사이드바 새 대화 버튼을 채워진 파란 필에서 원본과 동일한 테두리 버튼으로, 세션 카드 라운딩 축소(16px→8px)
- 폰트를 Pretendard에서 원본과 동일한 시스템 폰트 스택으로 변경

## 1.1.0-beta.15

> "텔레그램 같다, 디자인 감각이 구식이다 — Material 3로 해달라" 피드백. 특정 스크린샷 재현이 아니라 실제 디자인 시스템(M3) 컬러/셰이프 언어로 전면 개편.

### 수정 (Fix)
- 컬러 토큰을 M3 톤 팔레트로 전면 교체 — surface/surface-container/surface-container-high 3단 톤(그림자 대신 색조로 표현하는 M3식 elevation), primary는 다크모드에서 밝은 톤(텍스트/보더용), 필드 채우기는 별도의 진한 primary-container 톤(`--bg-bubble-user`)으로 분리해 명암비 확보
- 셰이프 스케일을 M3식으로 확대 — 새 대화 버튼/사이드바 네비 활성 표시/모드·모델 피커 버튼을 필(pill, 999px)로, 세션 카드/퀵액션 카드/드롭다운/사용량 패널을 16~20px로, 메시지 버블을 20px로 확대
- `--accent-blue`가 다크모드에서 밝은 톤으로 바뀌면서 흰 텍스트와 대비가 깨지던 채움 배경(새 대화 버튼, 로고 배지, 뷰탭 활성)을 진한 톤(`--bg-bubble-user`)으로 교체해 대비 확보

## 1.1.0-beta.14

> 사용자가 하단 입력창 확대 스크린샷을 다시 짚어줌 — 레퍼런스는 텍스트영역+툴바(첨부/모드/모델/마이크/전송)가 전부 하나의 보더 박스 안에 있는데, 지금까지는 두 개의 분리된 행(모드바 위 / 인풋바 아래)이었음. 구조적으로 다시 맞춤.

### 수정 (Fix)
- 하단 입력 영역을 텍스트영역 + 툴바가 한 박스 안에 있는 통합 컴포저(`.composer`)로 재구성 — 기존엔 모드/모델 피커 행과 입력창 행이 별도 박스였음
- 입력창 placeholder를 레퍼런스와 동일하게 영문 "Ask anything, @ to mention, / for actions"로 변경
- 헤더 로고를 이모지 🤖 대신 그라디언트 배지 + SVG 아이콘으로 교체
- 버전 배지를 "v1.1.0-beta.14"(김) 대신 "b14"(짧음)로 축소, 전체 버전은 툴팁에 유지
- 데스크탑 화면에서 사이드바 ✕ 닫기 버튼 숨김(레퍼런스에 없음, 모바일에서는 유지)

## 1.1.0-beta.13

### 수정 (Fix)
- 채팅 입력창에 "+"(파일 첨부) / 🎤(음성 입력) 아이콘 추가 — 실제 기능은 아직 없어 클릭 시 "아직 지원되지 않습니다" 토스트만 표시
- 대화 목록 항목의 메타 정보를 스크린샷과 동일하게 "날짜 · N단계" 한 줄로 변경(기존엔 "💬 N턴"과 날짜가 좌우로 나뉘어 있었음)
- 퀵액션 카드 아이콘을 이모지+반투명 배경에서 실제 스크린샷처럼 단색 배경 + 심플한 흰색 라인 아이콘(SVG)으로 교체
- "선택" 클릭 시 "전체선택 / N개 선택됨 / 지우기" 툴바가 뜨도록 추가(지우기는 선택 해제이며, 세션 삭제 API 자체가 없어 실제 삭제 기능은 아직 없음)

## 1.1.0-beta.12

### 수정 (Fix)
- 전체 UI를 참고 스크린샷 기준으로 재정비:
  - 헤더: 버전 배지를 "v{버전}" 하나로 통합(빌드 번호는 툴팁으로 유지), CPU/RAM 텍스트를 "● 0.1% · 51MB" 형태로 압축, AI Chat/Terminal 헤더 탭 버튼 제거
  - 사이드바: "내비게이션" 섹션 추가(💬 AI 채팅 대화창 / 🖥️ 웹 터미널) — 탭 전환을 헤더 대신 사이드바에서 처리. "새 대화 시작" 버튼에 Ctrl+K 힌트 배지 추가 및 실제 단축키로 동작. "최근 대화 기록 (N)"에 "선택" 버튼 추가(체크박스로 다중 선택 가능, 삭제 API가 없어 삭제 기능은 아직 없음)
  - 빈 대화 화면: 카드형 히어로를 중앙 정렬 웰컴 화면으로 변경("Google Antigravity Engine" 배지 + "무엇을 도와드릴까요?"), 퀵액션을 pill 칩에서 색상 아이콘이 있는 2x3 카드 그리드로 교체

## 1.1.0-beta.11

### 수정 (Fix)
- Engine Mode(모드 1/2/3) 선택 UI를 네이티브 `<select>`에서 모델 피커와 동일한 커스텀 드롭다운으로 교체 — 평소엔 아이콘+짧은 이름만 보이고(예: "🧠 복합"), 클릭해서 열면 각 모드의 전체 설명이 보임. 현재 선택된 모드엔 체크(✓) 표시, CLI 모드는 AVX 미지원 시 비활성화 표시로 회색 처리

## 1.1.0-beta.10

### 수정 (Fix)
- 모드 번호/이름 재정렬 — 모드 1(고속 모드, 구 초고속 스마트홈) / 모드 2(복합 모드, 구 AI 딥 브레인) / 모드 3(CLI 모드, 명칭만 단순화). 드롭다운 표시 순서만 바뀌었고 내부 stream_mode 값과 라우팅은 그대로라 동작 변경 없음. 채팅창에 뜨는 도구 로그 문구도 새 번호/이름에 맞게 함께 수정

## 1.1.0-beta.8

> 5시간 한도가 "N/A"인 이유를 검색으로 확인: Google Antigravity는 무료 티어에 5시간 스프린트 한도 자체가 없고 주간 리셋만 적용됨(Pro/Ultra부터 5시간 갱신 주기 제공) — 파싱 문제가 아니라 실제로 이 계정(무료 추정)에 해당 버킷이 없는 것.

### 추가 (Feature)
- `raw_json`에 있던 agy 자체 설명 텍스트(정책 설명 + 그룹별 설명 + 버킷별 "N일 M시간 후 초기화" 문구)를 그동안 버리고 있었는데, 이제 파싱해서 사용량 패널의 각 항목 문구로 우선 사용(직접 생성한 문구는 값이 없을 때만 폴백)
- 모델 드롭다운의 "View Usage" 옆에 ⓘ 버튼 추가 — 클릭하면 agy가 알려주는 전체 사용량 정책 설명을 토스트 팝업으로 표시

## 1.1.0-beta.7

> `GET /api/models?force=1`을 실제 서버(192.168.0.14:8000)에 직접 호출해 `agy models`의 진짜 응답을 확보 — effort는 별도 `--effort` 플래그가 아니라 모델 슬러그 자체에 포함되어 있었음(`gemini-3.7-flash-high`/`-medium`/`-low`는 서로 다른 슬러그). 슬러그도 점 표기(`gemini-3.7-flash`)이고 이 계정엔 `gemini-3.5-flash`가 아예 없음 — 둘 다 기존 정적 카탈로그의 잘못된 가정이었음.

### 수정 (Fix)
- `--effort` 플래그를 완전히 제거 — 이펙트 선택은 이제 그룹 내 variant 슬러그 전환으로 처리(`core/model_discovery.py`가 `agy models`의 `slug\tlabel` 출력을 파싱해 `...-high/-medium/-low` 접미사로 그룹화, 프런트가 선택된 이펙트에 맞는 실제 슬러그를 골라 `--model`로만 전달)
- effort-not-supported 자동 재시도 로직 제거(더 이상 필요 없음 —애초에 `--effort`를 안 보내므로)
- 정적 폴백 카탈로그(`core/models_catalog.py`)를 실제 확인된 슬러그/구조로 교체

## 1.1.0-beta.6

### 수정 (Fix)
- 사용량 패널을 열 때마다 새로 fetch하던 것을 없애고, 백그라운드 프리페치(`prefetchUsage`)가 패널 내용까지 미리 렌더링해두도록 변경 — 페이지 로드 직후 바로 열지만 않으면 클릭 시 즉시 표시됨
- `GET /api/usage`·`GET /api/models`에 락 추가 — 프리페치와 클릭이 겹칠 때 `agy` 서브프로세스가 중복 실행되던 것 방지(먼저 시작한 호출의 결과를 공유)
- 사용량 게이지에서 데이터가 아예 없는 경우("-")와 실제 0%를 구분하기 어렵던 것을 "N/A" 표기 + 별도 안내 문구로 명확화

## 1.1.0-beta.5

> 실제 사용 중 `--model "gemini-3-7-flash" --effort "low"` 조합이 "invalid model selection ... --effort is not supported for model" 오류로 거부됨 — 공식 문서 기준 정적 카탈로그(모든 Gemini Flash가 Low/Medium/High 지원)가 실제 계정과 어긋난다는 게 실기로 확인됨.

### 수정 (Fix)
- 모델/이펙트 유효성 검증을 정적 카탈로그(`core/models_catalog.py`) 대신 `agy models`로 실시간 조회(`core/model_discovery.py`, 5분 캐시)한 결과 기준으로 변경 — 신규 모델 출시나 계정별 차이를 정적 목록이 못 따라가는 문제 해결. `agy models` 조회 실패 시에만 정적 카탈로그로 폴백
- `--effort ... not supported` 오류를 agy가 반환하면 해당 모델에 `--effort` 없이 자동으로 1회 재시도 — 실시간 조회가 아직 정확하지 않거나 갱신 전이어도 사용자에게 오류 대신 정상 응답이 가도록 하는 안전망
- `GET /api/models`가 이제 `core/model_discovery.get_live_model_catalog()`를 그대로 반환(`available`/`reason`/`raw_json`/`raw_text` 포함) — `/usage`처럼 `?force=1`로 강제 새로고침 및 원본 응답 진단 가능

## 1.1.0-beta.4

> 실제 Antigravity PC 앱의 모델/사용량 UI를 참고해 맞춤. 사용량 게이지는 다시 "남은 양" 기준으로 되돌림(beta.3에서 "사용한 양"으로 바꿨던 것을 취소) — 실제 앱도 remaining 기준이었음.

### 추가 (Feature)
- 주간 할당량이 0%인 모델은 모델 목록에 ⚠️ 아이콘 표시, 현재 선택된 모델에는 체크(✓) 표시
- 현재 선택한 모델의 주간 할당량이 소진되면 입력창 위에 안내 배너 표시(초기화 시각 포함, 닫기 가능) — 실제 앱의 "Baseline model quota reached" 배너에 대응. 다만 Antigravity 자체 결제/오버리지 기능은 이 애드온에서 제어할 수 없어 "Enable Overages"/"See Plans" 버튼은 넣지 않음(눌러도 아무 동작 안 하는 가짜 버튼을 만들지 않기 위함)
- `agy` 응답의 `reset_time`을 파싱해 사용량 패널·배너에 초기화 시각 표시

### 수정 (Fix)
- 사용량 게이지 표기를 "사용한 양"에서 실제 앱과 동일한 "남은 양"으로 되돌림
- 게이지 표시 방식을 큰 링 안에 숫자 → 숫자 옆에 작은 링 아이콘으로 변경(실제 앱 레이아웃에 맞춤)

## 1.1.0-beta.3

### 수정 (Fix)
- 사용량 게이지를 "남은 양"이 아닌 "사용한 양"으로 표시하도록 변경 — 링/숫자가 100-remaining을 보여주고, 색상 기준도 반전(사용량 85%+ 빨강, 60%+ 노랑)
- 페이지 로드 시 및 55초 주기로 `/api/usage`를 백그라운드에서 미리 호출해 캐시를 데워둠(서버 캐시 TTL도 20s→60s) — `View Usage`를 열 때마다 10초 이상 기다리던 문제 완화
- Effort 서브메뉴가 `›` 클릭 후에만 보이던 것을 모델 행에 마우스를 올리면 바로 보이도록 변경(클릭으로 여는 것도 계속 지원)

## 1.1.0-beta.2

### 수정 (Fix)
- `GET /api/usage`의 JSON 파싱 경로가 실제 `agy -p "/usage" --output-format json` 응답 구조(`command.data.groups[].buckets[]`, `remaining_fraction` 0~1, `window` 필드)와 맞지 않아 매번 조용히 실패하고 텍스트 정규식 폴백으로만 동작하던 문제 수정 — 실제 응답으로 검증 완료(Gemini 96%, Claude/GPT 100% 정확히 파싱). 5시간(Five Hour) 한도가 "-"로 표시되는 것은 파싱 실패가 아니라 해당 계정 응답에 5시간 버킷 자체가 없기 때문으로 확인됨

## 1.1.0-beta.1

> 실제 운영 중인 인스턴스의 마지막 배포 버전이 1.0.5여서, 커밋 히스토리상의 1.1.0/1.2.0-beta.1/1.3.0(실배포된 적 없음)과는 별개로 1.0.5 다음 베타 빌드로 번호를 다시 잡음. 이후 Samba 배포 중 수정이 생길 때마다 베타 번호를 올림(beta.2, beta.3, ...).

### 추가 (Feature)
- 모드 3(Antigravity CLI) 전용 모델/추론강도(Effort) 선택 UI 추가 — 공식 문서(`antigravity.google/docs/models/`, `/docs/cli/headless/`) 기준 Gemini 3.7/3.6/3.5 Flash(Low/Medium/High), Gemini 3.1 Pro(Low/High), Claude Sonnet/Opus 4.6(Thinking), GPT-OSS 120B 카탈로그를 반영
  - `GET /api/models` 모델 카탈로그 API 추가
  - 선택한 모델/이펙트는 `agy` 실행 시 문서화된 `--model`/`--effort` 헤드리스 플래그로 전달 (알려진 슬러그로 화이트리스트 검증 후 전달)
- 모델 피커에 Gemini / Claude·GPT 계열별 5시간·주간 한도 잔량을 보여주는 사용량(View Usage) 패널 추가
  - `GET /api/usage` — agy v1.1.11의 헤드리스 `/usage` 프린트 모드(`agy -p "/usage"`, 에이전트 턴/쿼터 소모 없이 응답)를 파싱. 정확한 컬럼 스키마가 공식 문서에 없어 family/시간창/퍼센트 키워드 기반으로 방어적으로 파싱하며, 실패 시 원본 응답(`raw_json`/`raw_text`)을 함께 반환해 실제 컨테이너에서 검증 가능

### 참고
- 모델/이펙트 카탈로그(`core/models_catalog.py`)와 사용량 파서(`core/usage_client.py`)는 서드파티 정리글이 아닌 공식 문서를 기준으로 작성했으나, `/usage` 프린트 모드의 정확한 필드 스키마는 비공개라 실제 배포 환경에서 `GET /api/usage?force=1`의 `raw_text`/`raw_json`을 보고 파서 보정이 필요할 수 있음

## 1.3.0

### 추가 (Feature)
- 대화 세션 지속(Resume) 및 통합 관리 체계 구축 (Gitea #2)
  - Mode 1/2/3 전 모드가 `conversation_id` 기준으로 동일한 대화를 이어갈 수 있음
  - `GET /api/sessions`, `GET /api/sessions/<id>` 세션 목록/히스토리 REST API 추가
- 웹 UI 세션 사이드바 — 과거 대화 목록, 히스토리 복원, 새 대화 시작, 페이지네이션 (Gitea #3)

### 수정 (Fix)
- 이전 대화 목록 한글 유니코드 이스케이프(`\uXXXX`) 노출 결함 수정 (Gitea #4)
- 과거 대화 복원 시 다중 도구 실행이 여러 말풍선으로 쪼개지던 결함 수정 — 하나의 통합 답변으로 그룹화 (Gitea #5)
- 헤더 AI Chat / Terminal 탭 전환 및 다크·라이트 테마 버튼 미동작 수정 (Gitea #6)
- "이전 대화 더보기" 클릭 시 스크롤 위치가 튀던 결함 수정 (Gitea #6)
- Mode 3 대화 재개 시 `--resume`이 아닌 존재하지 않는 flag를 사용하고 있던 문제 수정 → 공식 문서 기준 `--conversation <id>`로 교체
- Mode 3 실시간 통신이 재개 세션에서 과거 로그 전체를 다시 재생하며 깨지던 근본 원인(파일 seek 누락) 수정
- `result.status`가 `ERROR`가 아닌 다른 실패 상태(`CANCELED`/`INTERRUPTED`/`INVALID` 등)일 때도 무응답으로 완료 처리되던 문제 수정

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
