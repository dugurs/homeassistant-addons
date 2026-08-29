#!/usr/bin/env python3
"""[대화/스트리밍 테스트] 애드온 Chat API 및 SSE 실시간 스트리밍 기능 검증 스크립트.
chat.txt 파일의 내용을 읽어 고정 명령어 'python test_chat_api.py' 로 실행합니다.
"""

import json
import os
import sys
import urllib.request


def test_chat(prompt: str = "", stream_mode: int = 3):
    if not prompt:
        chat_file = os.path.join(os.path.dirname(__file__), "chat.txt")
        if os.path.exists(chat_file):
            with open(chat_file, "r", encoding="utf-8") as f:
                prompt = f.read().strip()
        if not prompt:
            prompt = "우리집 종합 상황 알려줘"

    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"
    print(f"[*] Testing Chat API with prompt: '{prompt}' (Mode {stream_mode})...")

    is_direct_llm = prompt.startswith("ai ") or prompt.startswith("/llm")
    payload = json.dumps({"prompt": prompt, "is_direct_llm": is_direct_llm, "stream_mode": stream_mode}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_type = resp.headers.get("Content-Type", "")
            print(f"[OK] Response HTTP {resp.status} ({content_type})")
            print("--- [Stream Output] ---")
            for line in resp:
                l = line.decode("utf-8", errors="replace").strip()
                if l.startswith("data:"):
                    try:
                        ev = json.loads(l[5:].strip())
                        ev_type = ev.get("type")
                        if ev_type in ("text", "chunk"):
                            sys.stdout.buffer.write(ev.get("content", "").encode("utf-8"))
                            sys.stdout.buffer.flush()
                        elif ev_type == "tool":
                            sys.stdout.buffer.write(f"\n[TOOL] {ev.get('content')}\n".encode("utf-8"))
                            sys.stdout.buffer.flush()
                        elif ev_type == "done":
                            print("\n[DONE] Stream finished successfully.")
                    except Exception:
                        pass
    except Exception as e:
        print(f"[ERR] Chat test error: {e}", file=sys.stderr)


if __name__ == "__main__":
    test_chat()
