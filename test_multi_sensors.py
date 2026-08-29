"""Unit tests and verification for multi-dimensional sensor parsing, dynamic rendering, and AI synthesis."""

import sys
import os

# Set UTF-8 encoding for Windows console output
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Add add-on directory to sys.path
sys.path.insert(0, os.path.abspath("addons/antigravity-cli"))

from core.sensors import (
    get_dynamic_rooms,
    get_room_env_matrix,
    get_room_env_summary,
    get_room_full_state,
    classify_sensor,
    ENV_METRIC_CONFIGS,
)
from core.renderers import (
    evaluate_room_env_health,
    generate_dynamic_ai_recommendations,
    get_ai_deep_environment_analysis,
    get_weather_env_summary,
    get_terminal_cli_environment_view,
    get_comprehensive_home_summary,
)
from core.ha_engine import handle_agent_chat

def mock_states():
    return [
        # Weather
        {
            "entity_id": "weather.home",
            "state": "sunny",
            "attributes": {"friendly_name": "우리집 날씨", "temperature": 28.5, "humidity": 50, "pm25": 18}
        },
        # Living room sensors (Temp, Hum, CO2, TVOC, Illuminance)
        {
            "entity_id": "sensor.living_room_temperature",
            "state": "25.4",
            "attributes": {"friendly_name": "거실 온도", "device_class": "temperature", "unit_of_measurement": "°C"}
        },
        {
            "entity_id": "sensor.living_room_humidity",
            "state": "55.0",
            "attributes": {"friendly_name": "거실 습도", "device_class": "humidity", "unit_of_measurement": "%"}
        },
        {
            "entity_id": "sensor.living_room_co2",
            "state": "1580",
            "attributes": {"friendly_name": "거실 CO2 농도", "device_class": "carbon_dioxide", "unit_of_measurement": "ppm"}
        },
        {
            "entity_id": "sensor.living_room_tvoc",
            "state": "310",
            "attributes": {"friendly_name": "거실 TVOC", "device_class": "volatile_organic_compounds", "unit_of_measurement": "µg/m³"}
        },
        {
            "entity_id": "sensor.living_room_illuminance",
            "state": "450",
            "attributes": {"friendly_name": "거실 조도", "device_class": "illuminance", "unit_of_measurement": "lx"}
        },
        # Master bedroom sensors (Temp, Hum, PM2.5, Pressure)
        {
            "entity_id": "sensor.bedroom_temp",
            "state": "23.8",
            "attributes": {"friendly_name": "안방 온도", "unit_of_measurement": "°C"}
        },
        {
            "entity_id": "sensor.bedroom_humidity",
            "state": "62.0",
            "attributes": {"friendly_name": "안방 습도", "unit_of_measurement": "%"}
        },
        {
            "entity_id": "sensor.bedroom_pm25",
            "state": "42.0",
            "attributes": {"friendly_name": "안방 초미세먼지", "device_class": "pm25", "unit_of_measurement": "µg/m³"}
        },
        {
            "entity_id": "sensor.bedroom_pressure",
            "state": "1013.2",
            "attributes": {"friendly_name": "안방 기압", "device_class": "atmospheric_pressure", "unit_of_measurement": "hPa"}
        },
        # Noise / Excluded Sensors
        {
            "entity_id": "sensor.living_room_battery",
            "state": "98",
            "attributes": {"friendly_name": "거실 센서 배터리", "unit_of_measurement": "%"}
        },
        {
            "entity_id": "sensor.cpu_temperature",
            "state": "45.0",
            "attributes": {"friendly_name": "CPU 온도", "unit_of_measurement": "°C"}
        },
        # Devices
        {
            "entity_id": "light.living_room_main",
            "state": "on",
            "attributes": {"friendly_name": "거실 메인등"}
        },
        {
            "entity_id": "fan.living_room_vent",
            "state": "off",
            "attributes": {"friendly_name": "거실 환풍기"}
        },
        {
            "entity_id": "cover.living_room_curtain",
            "state": "open",
            "attributes": {"friendly_name": "거실 커튼"}
        },
        {
            "entity_id": "person.father",
            "state": "home",
            "attributes": {"friendly_name": "아빠"}
        }
    ]

def run_tests():
    states = mock_states()
    print("=== 1. Test Dynamic Rooms ===")
    rooms = get_dynamic_rooms(states)
    print("Rooms:", rooms)
    assert "거실" in rooms
    assert "안방" in rooms

    print("\n=== 2. Test Room Env Matrix ===")
    env_data = get_room_env_matrix(states)
    print("Active Metrics:", env_data["active_metrics"])
    print("Matrix Living Room:", env_data["matrix"]["거실"])
    print("Matrix Bedroom:", env_data["matrix"]["안방"])
    assert "co2" in env_data["active_metrics"]
    assert "tvoc" in env_data["active_metrics"]
    assert "pm25" in env_data["active_metrics"]
    assert "illuminance" in env_data["active_metrics"]
    assert "pressure" in env_data["active_metrics"]
    assert env_data["matrix"]["거실"]["co2"]["value"] == 1580.0
    assert env_data["matrix"]["안방"]["pm25"]["value"] == 42.0

    print("\n=== 3. Test Room Env Summary by Kind ===")
    co2_summary = get_room_env_summary(states, "co2")
    print(co2_summary)
    assert "거실: 1580ppm" in co2_summary

    air_summary = get_room_env_summary(states, "air_quality")
    print(air_summary)
    assert "CO2 1580ppm" in air_summary

    print("\n=== 4. Test Room Full State ===")
    full_state = get_room_full_state(states, "거실")
    print(full_state)
    assert "CO2 1580ppm" in full_state
    assert "거실 메인등" in full_state

    print("\n=== 5. Test AI Deep Environmental Analysis (Mode 1) ===")
    mode1_desktop = get_ai_deep_environment_analysis(states, "분석해줘", is_mobile=False)
    print(mode1_desktop)
    assert "실내 이산화탄소 경고" in mode1_desktop
    assert "🔴 즉시 환기 요망(CO2)" in mode1_desktop
    assert "| 구역 (Zone) |" in mode1_desktop

    mode1_mobile = get_ai_deep_environment_analysis(states, "분석해줘", is_mobile=True)
    print("\n[Mode 1 Mobile]:\n", mode1_mobile)
    assert "CO2 `1580ppm`" in mode1_mobile

    print("\n=== 6. Test Weather Env Summary (Mode 3) ===")
    mode3_desktop = get_weather_env_summary(states, is_mobile=False)
    print(mode3_desktop)
    assert "CO2" in mode3_desktop
    assert "PM2.5" in mode3_desktop

    mode3_mobile = get_weather_env_summary(states, is_mobile=True)
    print("\n[Mode 3 Mobile]:\n", mode3_mobile)
    assert "CO2 `1580ppm`" in mode3_mobile

    print("\n=== 7. Test Terminal CLI View (Mode 2) ===")
    mode2_view = get_terminal_cli_environment_view(states, is_mobile=False)
    print(mode2_view)
    assert "CO2" in mode2_view

    print("\n=== 8. Test Natural Language Dispatching in ha_engine ===")
    import core.ha_engine
    core.ha_engine.get_ha_states = lambda: states

    chat1 = handle_agent_chat("거실 공기질 어때")
    print("[Chat 1]:", chat1)
    assert "거실" in chat1 and "CO2" in chat1

    chat2 = handle_agent_chat("안방 CO2 농도")
    print("[Chat 2]:", chat2)

    chat3 = handle_agent_chat("거실 CO2 농도 알려줘")
    print("[Chat 3]:", chat3)
    assert "1580ppm" in chat3

    chat4 = handle_agent_chat("방별 공기질")
    print("[Chat 4]:", chat4)
    assert "CO2 1580ppm" in chat4

    chat5 = handle_agent_chat("기능 소개")
    print("[Chat 5]:", chat5)
    assert "다차원 실내 공기질" in chat5

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
