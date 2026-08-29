# Home Assistant MCP (ha-mcp) 73개 도구 전체 분석 및 모드별 적용 가이드

Home Assistant MCP(`homeassistant-ai/ha-mcp`)는 Model Context Protocol(MCP) 표준을 준수하여 AI 어시스턴트가 Home Assistant의 모든 기기, 엔티티, 자동화, 스크립트, 대시보드, 시스템 설정을 실시간으로 제어하고 모니터링할 수 있도록 지원하는 프레임워크입니다.

---

## 1. ha-mcp 73개 도구의 모드별 분류 및 적용 아키텍처

모든 도구를 고속모드(단순 키워드)에 무차별적으로 넣으면 **자동화 삭제나 시스템 재부팅 같은 위험한 사고**가 발생할 수 있기 때문에, **[고속모드 직결 25개]**, **[AI 딥 브레인 전용 35개]**, **[특수/배제 13개]**로 최적화 분류하여 적용되어 있습니다.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ha-mcp 73개 도구 적용 아키텍처                                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ⚡ [고속모드(모드 3) 직결 : 25개] ➔ 0.05초 일상 제어 및 상태 조회 (조명, 온습도, 헬스 등)     │
│ 🧠 [AI 딥 브레인(모드 1) 전용 : 35개] ➔ 복합 설정, YAML 수정, 자동화 생성, 안전 제어          │
│ 🔒 [배제 및 특수 하드웨어 : 13개] ➔ 카메라 바이너리, 라디오, 이슈 리포트 등                      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. ⚡ 고속모드(모드 3)에 즉시 적용된 핵심 도구 (25개)
> **적용 목적**: 대기 시간 없이 0.05초 만에 즉각 실행되어야 하는 일상 스마트홈 제어 및 모니터링

| 도구 이름 | 분류 | 고속모드 기능 및 발화 예시 |
| :--- | :--- | :--- |
| `ha_call_service` | 기기 제어 | 조명/환풍기 On/Off, 커튼 열기/닫기 (`"거실 불 켜줘"`, `"환풍기 틀어줘"`) |
| `ha_bulk_control` | 일괄 제어 | 방 전체 조명 켜기/끄기 (`"거실 조명 다 꺼줘"`) |
| `ha_get_state` | 엔티티 상태 | 단일 기기 상태 조회 (`"거실 다운라이트 켜져 있어?"`) |
| `ha_search` | 퍼지 검색 | 스마트홈 엔티티 및 기기 빠른 검색 (`"온도 센서 찾아줘"`) |
| `ha_get_overview` | 종합 요약 | 집안 전체 상태 브리핑 (`"우리집 종합 상황"`) |
| `ha_list_floors_areas` | 구역 관리 | 8개 구역별 기기 통합 조회 (`"안방 상태 알려줘"`, `"거실에 켜진 기기"`) |
| `ha_get_zone` | 위치/재실 | 집/외부 GPS 구역 및 가족 재실 조회 (`"가족들 집에 있어?"`) |
| `ha_config_get_automation` | 자동화 | 활성화된 자동화 목록 및 가동 상태 확인 (`"자동화 목록"`) |
| `ha_config_get_script` | 스크립트 | 스마트홈 스크립트 목록 조회 (`"스크립트 목록 보여줘"`) |
| `ha_get_automation_traces` | 자동화 디버깅 | 자동화 최근 실행 이력 및 트리거 상태 조회 |
| `ha_get_system_health` | 헬스체크 | HA 코어, 메모리, CPU 건전성 점검 (`"시스템 헬스체크"`) |
| `ha_get_logs` | 에러 로그 | 최근 시스템 에러/경고 로그 조회 (`"에러 로그 확인"`) |
| `ha_get_entity` | 엔티티 정보 | 엔티티 속성값 및 단위 확인 |
| `ha_get_device` | 기기 정보 | 연결된 Zigbee/Matter/WiFi 기기 목록 조회 |
| `ha_get_todo` | 할 일 관리 | 투두리스트, 쇼핑 목록 조회 (`"할 일 목록 보여줘"`) |
| `ha_set_todo_item` | 할 일 추가 | 새 할 일 등록 및 완료 처리 (`"우유 사기 할 일에 추가"`) |
| `ha_config_get_calendar_events` | 캘린더 | 오늘/주간 캘린더 일정 조회 (`"오늘 일정 확인"`) |
| `ha_config_get_scene` | 씬(Scene) | 등록된 조명 씬 조회 (`"취침 씬 실행해줘"`) |
| `ha_config_list_helpers` | 가상 헬퍼 | Input Boolean, 타이머 헬퍼 현황 확인 |
| `ha_eval_template` | Jinja2 템플릿 | 템플릿 센서 및 표현식 실시간 연산 |
| `ha_manage_updates` | 업데이트 | Core/OS/애드온 업데이트 알림 확인 |
| `ha_get_history` | 과거 이력 | 온습도 및 조명 변경 이력 조회 |
| `ha_config_get_category` | 카테고리 | 자동화/기기 카테고리 분류 확인 |
| `ha_config_list_groups` | 그룹 | 엔티티 그룹 구성 확인 |
| `ha_get_hacs_info` | HACS 정보 | 설치된 커스텀 컴포넌트 정보 확인 |

---

## 3. 🧠 AI 딥 브레인(모드 1)에서만 신중하게 실행해야 하는 도구 (35개)
> **제외/분리 사유**: 시스템 설정을 변경하거나 삭제할 수 있는 **고위험(Destructive) 도구**로, AI가 맥락과 안전성을 면밀히 검토한 뒤 실행해야 함

### 1) 파괴적 삭제/제거 도구 (고속모드 실행 시 위험)
* `ha_config_remove_automation` : 자동화 영구 삭제
* `ha_config_remove_script` : 스크립트 영구 삭제
* `ha_config_delete_dashboard` : Lovelace 대시보드 UI 전체 삭제
* `ha_remove_entity`, `ha_remove_device`, `ha_remove_area_or_floor` : 기기 및 구역 영구 삭제
* `ha_remove_helpers_integrations` : 통합구성요소 및 헬퍼 영구 삭제
* `ha_config_remove_scene`, `ha_config_remove_calendar_event`, `ha_remove_todo_item`
* `ha_remove_zone`, `ha_config_remove_label`, `ha_config_remove_category`

### 2) 복합 생성/YAML 코드 수정 도구 (AI 추론 필수)
* `ha_config_set_automation` : 새로운 자동화 YAML 코드 생성 및 조건식 설계
* `ha_config_set_script` : 다단계 스크립트 시퀀스 코드 작성
* `ha_config_set_dashboard` : Lovelace 대시보드 카드 레이아웃 YAML 생성
* `ha_config_set_helper` : 가상 스위치/타이머 헬퍼 생성
* `ha_config_set_scene` : 복합 공간 조명 씬 정의
* `ha_import_blueprint`, `ha_manage_hacs` : 블루프린트 및 HACS 통합 설치
* `ha_set_integration`, `ha_set_device`, `ha_set_entity`, `ha_set_zone`

### 3) 시스템 재기동 및 백업 조작
* `ha_restart`, `ha_reload_core` : Home Assistant 시스템 재시작 (오작동 방지)
* `ha_manage_backup` : 전체 백업 생성 및 백업 파일 조작

---

## 4. 🔒 제외되거나 특수 목적 전용 도구 (13개)
> **제외/분리 사유**: 텍스트 채팅 스트림에 부적합하거나 특정 부가 기능 전용

* **바이너리/미디어 전송**: `ha_get_camera_image` (CCTV 이미지 바이너리 - 텍스트 채팅에 부적합)
* **특수 하드웨어/미디어**: `ha_manage_radio` (특정 인터넷 라디오), `ha_manage_energy_prefs` (에너지 대시보드 설정)
* **어시스턴트 내부 관리**: `ha_manage_pipeline`, `ha_get_blueprint`, `ha_report_issue`, `ha_get_skill_guide`
* **라벨/리소스 관리**: `ha_config_get_label`, `ha_config_set_label`, `ha_config_delete_dashboard_resource`, `ha_config_set_dashboard_resource`

---

## 5. 고속모드(모드 3) 기술 아키텍처

고속모드(모드 3)는 LLM 추론 대기 시간을 거치지 않고, Home Assistant Core REST API에 직결되어 **0.05~0.2초** 만에 결과를 반환합니다:

```
[사용자 발화] ──► [자연어 인텐트 분석기 (ha_engine.py)] ──► [HA Core REST API / Supervisor] ──► [초고속 실시간 응답 (0.05초)]
                   ├── 기기 제어  : POST /api/services/{domain}/{service}
                   ├── 구역 상태  : GET /api/states (Area/Floor 매핑)
                   ├── 자동화/투두: GET /api/states (automation.* / todo.*)
                   └── 시스템 헬스: GET /api/logs / /api/states
```
