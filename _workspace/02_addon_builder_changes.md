# 02. Add-on Builder Changes Summary

## 1. 구현 개요
`_workspace/01_addon_architect_spec.md` 명세에 따라 애드온에 상태 API 데몬을 추가하고 설정/빌드/실행 스크립트를 갱신했습니다.

## 2. 변경된 파일 목록 및 상세
1. **`addons/antigravity-cli/antigravity_api.py`** [MODIFY]
   - `POST /api/chat`, `POST /api/prompt` 엔드포인트 및 `handle_agent_chat` 디스패처 구현
   - `GET /api/status`, `GET /api/health`, `POST /api/restart` 엔드포인트
   - Bearer 토큰 인증 및 동적 포트 바인딩
2. **`custom_components/antigravity_cli/conversation.py`** [NEW]
   - `ConversationEntity` 구현 (`AntigravityConversationEntity`)
   - Assist Pipeline에서 프롬프트 수신 시 `/api/chat` 연동 및 `ConversationResult` 반환
3. **`custom_components/antigravity_cli/const.py`** [MODIFY]
   - `PLATFORMS`에 `"conversation"` 플랫폼 추가
4. **`addons/antigravity-cli/config.yaml` & `run.sh`** [MODIFY]
   - `api_port: "port?"` 설정 지원 및 백그라운드 API 서버 자동 구동
4. **`custom_components/antigravity_cli/config_flow.py` & `coordinator.py`** [MODIFY]
   - 통합구성요소 Options Flow 및 Coordinator에서 동적 포트(`port`) 및 API 키 변경 지원
5. **`addons/antigravity-cli/CHANGELOG.md`** [MODIFY]
   - v1.1.0 릴리즈 노트 추가
