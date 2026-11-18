#!/usr/bin/env python3
"""PreToolUse hook: hard-block deletion/overwrite of Home Assistant's
critical config data (see run.sh's ha-file-safety.md for the same list in
rule-instruction form -- this is the enforced counterpart, matched on
run_command's shell command line and on write_to_file/replace_file_content's
target path).

Payload shape and decision contract per antigravity.google/docs/hooks/:
    stdin:  {"toolCall": {"name": ..., "args": {...}}, ...}
    stdout: {"decision": "allow"} | {"decision": "deny", "reason": "..."}
"""
import json
import re
import sys

# 1. [삭제 금지 & 수정 금지] (시스템 코어, 인증, 바이너리 DB)
STRICT_PROTECTED = [
    ("/homeassistant/.storage", ".storage 레지스트리(엔티티/기기/로그인 계정 등 HA 핵심 상태)"),
    ("/homeassistant/.cloud", "Nabu Casa Cloud 인증 토큰"),
    ("/homeassistant/.HA_VERSION", "내부 코어 버전 식별 마커"),
    ("/homeassistant/.ha_run.lock", "HA 코어 실행 락 파일"),
    ("/homeassistant/.uuid", "이 HA 인스턴스의 고유 식별자"),
    ("/homeassistant/home-assistant_v2.db", "히스토리/로그북 레코더 데이터베이스"),
    ("/homeassistant/config", "/config 시스템 심볼릭 링크"),
    ("/backup", "Home Assistant 백업 아카이브"),
]

# 2. [삭제 금지 & 수정 가능] 개별 파일 자체 삭제 금지 (내용 편집/추가는 허용)
CONTAINER_FILES_NO_DELETE = [
    ("/homeassistant/secrets.yaml", "민감정보(비밀번호/토큰) 파일"),
    ("/homeassistant/configuration.yaml", "HA 메인 설정 파일"),
    ("/homeassistant/automations.yaml", "사용자 자동화 정의"),
    ("/homeassistant/scripts.yaml", "사용자 스크립트 정의"),
    ("/homeassistant/scenes.yaml", "사용자 씬 정의"),
    ("/homeassistant/customize.yaml", "엔티티 커스터마이징 파일"),
    ("/homeassistant/customize_glob.yaml", "엔티티 커스터마이징 파일"),
    ("/homeassistant/custom_components/antigravity_cli", "애드온 연동 핵심 컴포넌트"),
]

# 3. [삭제 금지 & 수정 가능] 루트 컨테이너 폴더 자체 삭제 금지 (하위 개별 항목 삭제/수정은 허용)
ROOT_CONTAINERS_NO_DELETE = [
    ("/config/.gemini", "애드온 설정/기록 루트 폴더"),
    ("/homeassistant/.gemini", "애드온 설정/기록 루트 폴더"),
    ("/homeassistant/custom_components", "커스텀 통합구성요소 루트 폴더"),
    ("/homeassistant/www", "대시보드 www 웹 리소스 루트 폴더"),
    ("/homeassistant/packages", "패키지 설정 루트 폴더"),
    ("/homeassistant/blueprints", "블루프린트 템플릿 루트 폴더"),
    ("/homeassistant/themes", "대시보드 테마 루트 폴더"),
    ("/homeassistant/custom_sentences", "음성 대화 문장 루트 폴더"),
    ("/homeassistant/esphome", "ESPHome 기기 설정 루트 폴더"),
    ("/homeassistant/espresense", "ESPresense 설정 루트 폴더"),
    ("/homeassistant/node-red", "Node-RED 플로우 루트 폴더"),
    ("/homeassistant/pyscript", "Pyscript 파이썬 스크립트 루트 폴더"),
]

# A protected path substring alone isn't enough (plain `cat`/`ls`/`grep` must
# stay unblocked) -- only deny when a destructive verb/redirect is also
# present. `>` (but not `>>`, which only appends) covers truncate-by-redirect.
_DESTRUCTIVE_RE = re.compile(r"(?:^|[\s;&|])(rm|unlink|shred|truncate|mv)\b|(?<!>)>(?!>)")


def _unwrap(value):
    """agy has been observed double-JSON-encoding string tool-call args for
    some fields (confirmed for AbsolutePath/CodeContent/TargetContent in
    transcript.jsonl -- see core/streamer.py _agy_str()). This hook gets its
    payload from a separate, first-class stdin contract that may or may not
    share the quirk, so unwrap defensively either way -- a plain unquoted
    path string just fails json.loads and falls through unchanged."""
    if not isinstance(value, str):
        return value
    try:
        unwrapped = json.loads(value)
        if isinstance(unwrapped, str):
            return unwrapped
    except Exception:
        pass
    return value


def _deny(path, why):
    print(json.dumps({
        "decision": "deny",
        "reason": (
            f"[HA 파일 보호] '{path}' 는 Home Assistant 운영에 필수적인 핵심 데이터({why})로, "
            "이 애드온의 안전 정책상 어떤 요청에도 삭제/덮어쓰기가 차단됩니다. "
            "사용자에게 이 사실과 위험성을 알리고, 정말 필요하다면 HA 자체 백업/복원 기능이나 "
            "공식 설정 화면을 통한 개별 작업을 안내하세요."
        ),
    }, ensure_ascii=False))


def _allow():
    print(json.dumps({"decision": "allow"}))


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        _allow()
        return

    tool_call = payload.get("toolCall") or {}
    name = tool_call.get("name", "")
    args = tool_call.get("args")
    if isinstance(args, str):
        args = _unwrap(args)
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
    if not isinstance(args, dict):
        args = {}

    if name == "run_command":
        cmd = _unwrap(args.get("CommandLine", "")) or ""
        if _DESTRUCTIVE_RE.search(cmd):
            # 1. [삭제 금지 & 수정 금지] 대상 경로 검사
            for path, why in STRICT_PROTECTED:
                if path in cmd:
                    _deny(path, why)
                    return

            # 2. [삭제 금지 & 수정 가능] 개별 파일 자체 삭제 검사
            for path, why in CONTAINER_FILES_NO_DELETE:
                if path in cmd:
                    _deny(path, why)
                    return

            # 3. [삭제 금지 & 수정 가능] 루트 컨테이너 폴더 자체/전체 삭제 검사
            # (하위 개별 항목, 예: custom_components/aaa/ 삭제는 허용)
            for path, why in ROOT_CONTAINERS_NO_DELETE:
                pat = re.compile(r'(?:^|[\s"\'])\s*' + re.escape(path) + r'(?:/(?:\*|\.)?)?(?=\s|["\']|$)')
                if pat.search(cmd):
                    _deny(path, why)
                    return
        _allow()
        return

    if name in ("write_to_file", "replace_file_content"):
        target = _unwrap(args.get("AbsolutePath", "")) or ""
        # 1번 그룹(STRICT_PROTECTED)만 쓰기/수정 차단 (2번 그룹은 내용 편집 전면 허용)
        for path, why in STRICT_PROTECTED:
            if target == path or target.startswith(path.rstrip("/") + "/"):
                _deny(path, why)
                return
        _allow()
        return

    _allow()


if __name__ == "__main__":
    main()
