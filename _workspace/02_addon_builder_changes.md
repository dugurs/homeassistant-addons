# 02. Add-on Builder Implementation & Change Log

## 1. 구현 개요

`_workspace/01_addon_architect_spec.md` 명세에 따라 Home Assistant 애드온(`antigravity-cli`)의 환경 센서 수집 계층(`core/sensors.py`), 마크다운 뷰 렌더링 엔진(`core/renderers.py`), 자연어 인텐트 디스패처(`core/ha_engine.py`)를 고도화하였습니다.

단순 온습도 위주의 기존 구조에서 벗어나 **CO2, TVOC, 초미세먼지(PM2.5), 미세먼지(PM10), 조도(Illuminance), 기압(Pressure)**을 포함하는 8대 다차원 환경 지표를 공간(Room)별로 자동 식별 및 파싱하고, 활성화된 지표 열을 동적으로 렌더링하는 반응형 테이블과 실시간 AI 맞춤 권고 합성 엔진을 완벽히 구축하였습니다.

---

## 2. 파일별 주요 수정 내역

### 2.1 `addons/antigravity-cli/core/sensors.py`
- **표준 환경 지표 구성 맵(`ENV_METRIC_CONFIGS`) 정의**:
  - `temperature`, `humidity`, `co2`, `tvoc`, `pm25`, `pm10`, `illuminance`, `pressure` 8대 지표 규격화.
  - HA 표준 `device_class`, 식별 패턴(`patterns`), 단위 후보군(`uom`), 기본 단위(`default_unit`) 정의.
- **노이즈 센서 필터링(`EXCLUDE_KEYWORDS`) 최적화**:
  - `배터리`, `battery`, `전압`, `voltage`, `cpu`, `최고`, `최저`, `power`, `energy`, `linkquality`, `rssi` 등 무관 센서 배제.
  - 조도(`illuminance`, `lux`) 센서가 오배제되지 않도록 필터 항목 재조정.
- **다차원 센서 분류기(`classify_sensor`) 구현**:
  - `device_class`, 엔티티 ID, `friendly_name`, 측정 단위를 종합 분석하여 8대 메트릭 중 하나로 정밀 분류 (PM2.5 vs PM10, 온습도 충돌 방지 로직 적용).
- **공간별 다차원 환경 매트릭스 추출(`get_room_env_matrix`) 구현**:
  - 발견된 방 목록(`rooms`)과 각 방에 존재하는 8대 지표 데이터를 딕셔너리 매트릭스로 집계.
  - 1개 이상의 방에서 실제 감지된 지표 목록(`active_metrics`) 동적 추출.
- **다목적 환경 요약기(`get_room_env_summary`) 리팩터링**:
  - `kind` 파라미터로 `temperature`, `humidity` 외 `co2`, `tvoc`, `pm25`, `pm10`, `illuminance`, `pressure`, `air_quality`를 모두 지원하도록 확장.
- **방 통합 상태 리포트(`get_room_full_state`) 확장**:
  - 온습도뿐만 아니라 CO2, TVOC, PM2.5, 조도 등 감지된 공기질 지표를 융합 표기.

---

### 2.2 `addons/antigravity-cli/core/renderers.py`
- **단일 방 환경 건전성 진단기(`evaluate_room_env_health`) 구현**:
  - CO2(>=1500: 🔴 즉시 환기 요망, >=1000: 🟡 환기 필요)
  - TVOC(>=660 µg/m³: 🔴 유해가스 경고, >=250 µg/m³: 🟡 공기질 주의)
  - PM2.5(>=75 µg/m³: 🔴 초미세먼지 경고, >=35 µg/m³: 🟠 공기질 주의)
  - 온도/습도 열 쾌적성 평가(과열, 저온, 다습, 건조, 🟢 쾌적) 복합 진단 산출.
- **실시간 AI 맞춤 조언 합성 엔진(`generate_dynamic_ai_recommendations`) 고도화**:
  - CO2 농도 기반 환기 및 집중력 조언 (1500ppm 이상 시 창문 개방 + 환풍기 최대 풍량 경고).
  - TVOC 유해가스 농도 기반 주방 후드/환풍기 가동 및 원인 점검 조언.
  - 실내외 PM2.5 융합 비교 기반 (실외 깨끗 시 맞바람 환기 / 실외 오염 시 창문 차단 및 공기청정기 내부 순환 모드) 지능형 조언.
  - 온습도 밸런스 및 다수 점등 조명 에너지 절약 제안 결합.
- **Mode 1 (AI 딥 브레인 환경 분석 - `get_ai_deep_environment_analysis`)**:
  - 데스크톱: `| 구역 (Zone) | 현재 온도 | 현재 습도 | [활성 지표들...] | 종합 환경 진단 |` 동적 마크다운 테이블 렌더링.
  - 모바일: 방별 활성 지표 리스트와 종합 환경 진단 뱃지 렌더링.
- **Mode 3 (실시간 환경 대시보드 - `get_weather_env_summary`)**:
  - 데스크톱: 동적 컬럼 마크다운 테이블 생성.
  - 모바일: `• **거실**: 온도 25.4°C | 습도 55.0% | CO2 1580ppm` 반응형 카드 리스트 출력.
- **Mode 2 (PTY 터미널 CLI 뷰 - `get_terminal_cli_environment_view`)**:
  - CO2 등 핵심 활성 지표가 포함된 고품질 ASCII 박스 터미널 모니터 표 렌더링.
- **종합 브리핑(`get_comprehensive_home_summary`)**:
  - 방별 주요 환경 요약에 CO2/PM2.5 등 다차원 공기질 지표 자동 반영.

---

### 2.3 `addons/antigravity-cli/core/ha_engine.py`
- **자연어 질의 인텐트 확장**:
  - 특정 방 지표 질의: "거실 CO2 농도", "안방 조도", "거실 TVOC", "작은방 미세먼지", "거실 공기질 어때" 등 개별/종합 센서 질의 직접 매칭.
  - 전체 방 지표 질의: "방별 공기질", "CO2 현황", "미세먼지", "조도 확인", "기압" 등 자동 디스패치.
- **기능 소개 및 헬프 메시지 갱신**:
  - 다차원 실내 공기질 모니터링(CO2, TVOC, PM2.5, PM10, 조도, 기압 정밀 분석 및 환기 AI 조언) 안내 추가.

---

## 3. 검증 결과 (Verification Results)

단위 테스트 스크립트(`test_multi_sensors.py`)를 통해 가상 다차원 센서 데이터셋 기반 검증을 성공적으로 완료하였습니다.

1. **동적 공간 및 센서 식별**: `거실`, `안방` 인식 및 `temperature`, `humidity`, `co2`, `tvoc`, `pm25`, `illuminance`, `pressure` 7개 활성 메트릭 추출 확인.
2. **배터리/CPU 노이즈 센서 배제**: `sensor.living_room_battery`, `sensor.cpu_temperature` 자동 제외 확인.
3. **동적 테이블 마크다운 렌더링**: 데스크톱 및 모바일 반응형 헤더/셀 자동 정렬 확인.
4. **AI 맞춤 조언 합성**: 거실 CO2(1580ppm) 감지에 따른 즉시 창문 개방 및 환풍기 가동 경고, 안방 PM2.5(42µg/m³) 자연 환기 조언 합성 확인.
5. **자연어 대화 디스패칭**: 거실 공기질, 안방 CO2, 기능 소개 인텐트 정확 응답 확인.
