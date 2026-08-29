"""Main Home Assistant Engine Facade and High-Speed Natural Language Dispatcher."""

# Re-export all sub-module functions for 100% backwards compatibility
from core.ha_client import (
    execute_device_control_intent,
    get_ha_states,
    ha_call_service_api,
)
from core.renderers import (
    get_ai_deep_environment_analysis,
    get_comprehensive_home_summary,
    get_terminal_cli_environment_view,
    get_weather_env_summary,
)
from core.sensors import (
    get_automations_summary,
    get_room_env_summary,
    get_room_full_state,
    get_room_lights_summary,
    get_system_health_summary,
    get_todo_summary,
)
from core.system_info import (
    get_all_addons_memory,
    get_ha_error_logs,
    get_resource_usage,
    get_supervisor_token,
)


def handle_agent_chat(
    prompt: str,
    conversation_id: str = "",
    home_summary: str = "",
    is_direct_llm: bool = False,
    is_mobile: bool = False,
) -> str:
    """Dispatches prompt to Antigravity CLI or autonomously resolves intents with responsive markdown."""
    clean_prompt = prompt.strip()
    lower = clean_prompt.lower()
    no_space = clean_prompt.replace(" ", "")

    states = get_ha_states()

    # 1. Direct Device Control (ha_call_service)
    if any(ctrl in no_space for ctrl in ["켜", "꺼", "틀어", "시작", "정지", "닫아", "열어", "작동", "돌려"]):
        ctrl_result = execute_device_control_intent(clean_prompt, states)
        if ctrl_result:
            return ctrl_result

    # 2. Specific Room Query (ha_list_floors_areas)
    rooms = ["거실", "안방", "작은방", "옷방", "주방", "화장실", "세탁실", "현관", "베란다"]
    matched_room = next((r for r in rooms if r in no_space), None)
    if matched_room:
        if any(w in no_space for w in ["온도", "기온"]):
            if states:
                summary = get_room_env_summary(states, "temperature")
                for line in summary.split("\n"):
                    if matched_room in line:
                        val = line.split(":", 1)[1].strip() if ":" in line else line
                        return f"현재 {matched_room}의 온도는 {val} 입니다."
        if "습도" in no_space:
            if states:
                summary = get_room_env_summary(states, "humidity")
                for line in summary.split("\n"):
                    if matched_room in line:
                        val = line.split(":", 1)[1].strip() if ":" in line else line
                        return f"현재 {matched_room}의 습도는 {val} 입니다."
        if any(w in no_space for w in ["상태", "상황", "기기", "모습", "어때"]):
            if states:
                return get_room_full_state(states, matched_room)

    # 3. Automations & Scripts (ha_config_get_automation)
    if any(w in lower for w in ["자동화", "오토메이션", "automation"]):
        if states:
            return get_automations_summary(states)

    # 4. To-Do & Tasks (ha_get_todo)
    if any(w in lower for w in ["할 일", "할일", "투두", "todo", "쇼핑 목록", "장보기"]):
        if states:
            return get_todo_summary(states)

    # 5. System Health & Diagnostics (ha_get_system_health)
    if any(w in lower for w in ["헬스", "건전성", "진단", "health", "점검"]):
        if states:
            return get_system_health_summary(states)

    # 6. Weather & Environment
    if any(w in lower for w in ["날씨", "환경", "기상", "일기예보", "온습도"]):
        if states:
            return get_weather_env_summary(states, is_mobile=is_mobile)

    # 7. System Logs (ha_get_logs)
    if any(w in lower for w in ["에러 로그", "오류 로그", "에러 확인", "오류 확인", "시스템 로그", "최근 에러", "로그 확인"]):
        return get_ha_error_logs()

    # 8. Room-by-room Summary
    if any(w in lower for w in ["방별", "방마다", "공간별", "구역별", "각 방", "각방"]):
        if states:
            if any(w in lower for w in ["온도", "기온", "온습도"]):
                return get_room_env_summary(states, "temperature")
            if "습도" in lower:
                return get_room_env_summary(states, "humidity")
            if any(w in lower for w in ["등", "조명", "불", "전등", "램프"]):
                return get_room_lights_summary(states)

    # 9. Resource Usage
    if any(w in lower for w in ["메모리", "램", "ram", "리소스", "cpu", "사양"]):
        if any(w in lower for w in ["애드온", "addon", "앱"]):
            return get_all_addons_memory()
        usage = get_resource_usage()
        return (
            f"현재 Antigravity CLI 애드온의 메모리 사용량은 {usage['memory_usage']} MB 이며, "
            f"시스템 전체 메모리는 {usage['used_memory_gb']} GB / {usage['total_memory_gb']} GB ({usage['memory_percent']}%) 사용 중입니다."
        )

    # 10. Introduction / Greetings
    if "뭐" in clean_prompt and ("할 수" in clean_prompt or "할수" in clean_prompt or "가능" in clean_prompt):
        return (
            "저는 Google Antigravity CLI 기반 Home Assistant 스마트홈 어시스턴트입니다.\n\n"
            "다음과 같은 작업을 도와드릴 수 있습니다:\n"
            "• 조명, 스위치, 커튼, 환풍기, 냉난방 등 스마트홈 기기 제어\n"
            "• 시스템 에러 로그 및 진단 브리핑\n"
            "• 방별 조명 및 온습도 상태 요약 브리핑\n"
            "• 애드온별 메모리/CPU 사용량 및 시스템 리소스 모니터링\n"
            "• 외출/취침 모드 및 스마트 자동화 실행"
        )

    if any(greet in clean_prompt for greet in ["안녕", "반가워", "hello", "hi", "누구"]):
        return "안녕하세요! Google Antigravity CLI 어시스턴트입니다. 무엇을 도와드릴까요?"

    # 11. Broad Home Status Intent
    if any(w in lower for w in ["상태", "상황", "현황", "요약", "브리핑", "분위기", "어때", "어떠", "어떻", "집안", "우리집", "모습"]):
        if home_summary:
            return home_summary
        if states:
            return get_comprehensive_home_summary(states, is_mobile=is_mobile)

    # Fallback
    if states:
        return get_comprehensive_home_summary(states, is_mobile=is_mobile)

    return "스마트홈 상태 정보를 수집하지 못했습니다."
