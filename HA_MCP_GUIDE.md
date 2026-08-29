# Home Assistant MCP (ha-mcp) 전체 기능 분석 및 고속모드 연동 매뉴얼

Home Assistant MCP(`homeassistant-ai/ha-mcp`)는 Model Context Protocol(MCP) 표준을 준수하여 AI 어시스턴트가 Home Assistant의 모든 기기, 엔티티, 자동화, 스크립트, 대시보드, 시스템 설정을 실시간으로 제어하고 모니터링할 수 있도록 지원하는 프레임워크입니다.

---

## 1. ha-mcp 7대 핵심 기능 영역 및 도구 목록 (Tool Catalog)

### 1) 기기 제어 및 상태 모니터링 (Device & Entity Control)
| 도구 이름 | 설명 | 지원 파라미터 / 예시 |
| :--- | :--- | :--- |
| `ha_call_service` | HA 서비스(조명 On/Off, 커튼 열기/닫기, 팬 가동 등) 실행 | `domain`, `service`, `service_data`, `target` |
| `ha_bulk_control` | 여러 기기 일괄 동시 제어 | `entity_ids`, `service`, `service_data` |
| `ha_get_state` | 특정 엔티티의 실시간 상태 및 속성값 조회 | `entity_id` (예: `light.living_room`) |
| `ha_search` | 엔티티, 기기, 영역(Area), 자동화 퍼지 검색 | `query`, `search_types`, `limit` |

### 2) 공간 및 구역 관리 (Floors & Areas)
| 도구 이름 | 설명 | 지원 파라미터 / 예시 |
| :--- | :--- | :--- |
| `ha_list_floors_areas` | 등록된 모든 층(Floor) 및 구역(Area: 거실, 안방 등) 목록 조회 | N/A |
| `ha_set_area_or_floor` | 신규 구역/층 생성 또는 기존 구역 속성 변경 | `name`, `floor_id`, `aliases` |
| `ha_get_zone` | GPS 기반 위치 구역(집, 회사, 학교 등) 조회 | `zone_id` |

### 3) 자동화 및 스크립트 관리 (Automations & Scripts)
| 도구 이름 | 설명 | 지원 파라미터 / 예시 |
| :--- | :--- | :--- |
| `ha_config_get_automation` | 특정 자동화의 YAML 설정 및 트리거 조건 조회 | `automation_id` |
| `ha_config_set_automation` | 자동화 신규 생성 또는 YAML 수정 | `automation_id`, `config` |
| `ha_config_get_script` | 스크립트 시퀀스 및 액션 조회 | `script_id` |
| `ha_get_automation_traces` | 자동화 최근 실행 추적(Trace) 및 디버깅 로그 조회 | `automation_id` |

### 4) 스마트홈 씬 및 헬퍼 관리 (Scenes & Helpers)
| 도구 이름 | 설명 | 지원 파라미터 / 예시 |
| :--- | :--- | :--- |
| `ha_config_get_scene` | 씬(Scene) 엔티티 목록 및 상태 조회 | `scene_id` |
| `ha_config_set_scene` | 공간별 조명/스위치 씬 생성 및 저장 | `scene_id`, `entities` |
| `ha_config_list_helpers` | Input Boolean, Timer, Schedule 등 헬퍼 목록 조회 | N/A |
| `ha_config_set_helper` | 새로운 가상 스위치나 타이머 헬퍼 생성 | `helper_type`, `config` |

### 5) 시스템 헬스 및 백업 진단 (System Diagnostics)
| 도구 이름 | 설명 | 지원 파라미터 / 예시 |
| :--- | :--- | :--- |
| `ha_get_system_health` | HA 코어, 운영체제, 네트워크 및 DB 건전성 점검 | N/A |
| `ha_get_logs` | HA Supervisor 및 Core 에러 로그 실시간 조회 | `lines`, `filter` |
| `ha_get_overview` | 시스템 전체 대시보드 개요 및 주요 기기 통계 | N/A |
| `ha_manage_backup` | 시스템 전체 백업 생성 및 백업 목록 조회 | `action`, `backup_name` |
| `ha_manage_updates` | OS, 코어, 애드온, HACS 업데이트 항목 확인 | N/A |

### 6) 할 일 및 캘린더 (To-Do & Calendar)
| 도구 이름 | 설명 | 지원 파라미터 / 예시 |
| :--- | :--- | :--- |
| `ha_get_todo` | 쇼핑 목록, 스마트홈 투두리스트 항목 조회 | `entity_id` (예: `todo.shopping_list`) |
| `ha_set_todo_item` | 새 할 일 등록, 완료 처리 또는 항목 삭제 | `entity_id`, `item`, `status` |
| `ha_config_get_calendar_events`| 캘린더 등록 일정 및 알림 조회 | `entity_id`, `start_time`, `end_time` |

### 7) 대시보드 및 리소스 (Dashboards & Themes)
| 도구 이름 | 설명 | 지원 파라미터 / 예시 |
| :--- | :--- | :--- |
| `ha_config_get_dashboard` | Lovelace 대시보드 구성 YAML 조회 | `dashboard_id` |
| `ha_config_set_dashboard` | 대시보드 카드 추가 및 레이아웃 수정 | `dashboard_id`, `config` |
| `ha_manage_theme` | 테마(다크모드/라이트모드/커스텀) 변경 및 조회 | `theme_name` |

---

## 2. 고속모드(모드 3) 직결 엔진 (Native Ultra-Fast Execution)

고속모드(모드 3)는 LLM 추론 대기 시간을 거치지 않고, Home Assistant REST API에 직결되어 **0.05초** 만에 결과를 반환합니다:

```
[사용자 발화] ──► [자연어 인텐트 분석기] ──► [HA Core REST API / Supervisor] ──► [실시간 응답 (0.05초)]
                   ├── 기기 제어  : POST /api/services/{domain}/{service}
                   ├── 구역 상태  : GET /api/states (Area/Floor 매핑)
                   ├── 자동화/투두: GET /api/states (automation.* / todo.*)
                   └── 시스템 헬스: GET /api/logs / /api/states
```

### 지원 발화 예시:
* **기기 제어**: `"거실 불 켜줘"`, `"안방 조명 꺼줘"`, `"화장실 환풍기 틀어줘"`, `"거실 커튼 열어줘"`
* **구역별 상세**: `"거실 상태 알려줘"`, `"안방에 켜진 기기 목록"`, `"작은방 환경 어때?"`
* **자동화 확인**: `"자동화 목록"`, `"가동 중인 자동화"`, `"자동화 에러 확인"`
* **할 일/투두**: `"할 일 목록 보여줘"`, `"투두리스트 확인"`
* **시스템 헬스**: `"시스템 헬스체크"`, `"스마트홈 건전성 점검"`, `"에러 로그 확인"`
