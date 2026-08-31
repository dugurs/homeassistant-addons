#!/usr/bin/env python3
"""[실서버 검증] Home Assistant 애드온 재기동 및 실서버 /api/sessions 엔드포인트 검증."""
import json
import os
import sys
import urllib.request
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def test_live_backend():
    ha_ip = "192.168.0.14"
    
    # 1. 애드온 재기동 API 호출 (새로 복사된 session_manager.py 및 변경된 antigravity_api.py 로드)
    print("1. 실서버 애드온 재기동 요청 (POST http://192.168.0.14:8000/api/restart)...")
    try:
        req = urllib.request.Request(f"http://{ha_ip}:8000/api/restart", data=b"{}", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"   -> 응답: {r.read().decode('utf-8')}")
    except Exception as e:
        print(f"   -> 재기동 요청 결과: {e}")

    print("2. 백엔드 서버 로딩 대기 (3초)...")
    time.sleep(3)

    # 2. 실서버 GET /api/sessions 엔드포인트 호출
    print("3. 실서버 GET /api/sessions 호출...")
    req = urllib.request.Request(f"http://{ha_ip}:8000/api/sessions")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            res_text = r.read().decode("utf-8")
            data = json.loads(res_text)
            print(f"   -> [성공] HTTP {r.status} 응답 수신!")
            print(f"   -> 서버에 저장된 세션 수: {len(data.get('sessions', []))}개")
            for s in data.get("sessions", [])[:3]:
                print(f"      • [{s['conversation_id'][:8]}] {s['title']} ({s['turns']} steps)")
    except Exception as e:
        print(f"   -> [오류] {e}")

if __name__ == "__main__":
    test_live_backend()

