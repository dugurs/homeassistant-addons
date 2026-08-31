#!/usr/bin/env python3
"""[단위 검증] CLI 포맷 Envelopes 저장/정제 및 Web UI JS 문법 검증."""
import os
import re
import subprocess
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "addons", "antigravity-cli"))

from core.session_manager import decode_unicode_text, clean_user_prompt, format_cli_user_input
from core.web_ui import HTML_INDEX

def run_all_tests():
    print("=== [CLI Envelope 포맷 및 정제 단위 검증] 시작 ===")
    
    # 1. format_cli_user_input 검증
    raw_prompt = "오늘 날씨 어때?"
    formatted = format_cli_user_input(raw_prompt)
    print(f"1. CLI Envelope 생성 테스트:\n{formatted}")
    assert "<USER_REQUEST>" in formatted and "오늘 날씨 어때?" in formatted, "Envelope format failed"
    print("   -> [PASS] CLI Envelope 생성 정상")

    # 2. clean_user_prompt 정제 검증 (CLI 원본 메타데이터 포함된 문자열)
    cli_saved_raw = """<USER_REQUEST> \\uc624\\ub298 \\ub0a0\\uc528 </USER_REQUEST> <ADDITIONAL_METADATA> The current local time is: 2026-08-31T12:54:45+09:00. </ADDITIONAL_METADATA> <USER_SETTINGS_CHANGE> The user changed setting `Model Selection` </USER_SETTINGS_CHANGE>"""
    cleaned = clean_user_prompt(cli_saved_raw)
    print(f"\n2. CLI 원본 정제 테스트:\n   입력: {cli_saved_raw}\n   결과: '{cleaned}'")
    assert cleaned == "오늘 날씨", f"Expected '오늘 날씨', got '{cleaned}'"
    print("   -> [PASS] 시스템 태그 완전 제거 및 유니코드 복원 100% 정상")

    # 3. 프론트엔드 JS 구문 검증
    print("\n=== [Web UI 프론트엔드 JS 검증] ===")
    scripts = re.findall(r"<script>(.*?)</script>", HTML_INDEX, flags=re.DOTALL)
    for i, s in enumerate(scripts):
        tmp_file = "temp_check.js"
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(s)
        res = subprocess.run(["node", "--check", tmp_file], capture_output=True, text=True, check=False)
        try:
            os.remove(tmp_file)
        except Exception:
            pass
        assert res.returncode == 0, f"JS Syntax Error in block {i}:\n{res.stderr}"
        print(f"   -> [PASS] Script Block {i}: JS SYNTAX 100% VALID")

    print("\n🎉 모든 단위 검증을 완벽히 통과하였습니다!")

if __name__ == "__main__":
    run_all_tests()

