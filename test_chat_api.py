#!/usr/bin/env python3
"""[대화/스트리밍 테스트] 애드온 Chat API 및 SSE 실시간 스트리밍 기능 검증 스크립트."""

import json
import sys
import urllib.request


def test_chat(prompt: str = "우리집 종합 상황 알려줘", is_direct_llm: bool = False):
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"
    print(f"[*] Testing Chat API with prompt: '{prompt}'...")

    payload = json.dumps({"prompt": prompt, "is_direct_llm": is_direct_llm}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
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
                        elif ev_type == "tool":
                            sys.stdout.buffer.write(f"\n[TOOL] {ev.get('content')}\n".encode("utf-8"))
                        elif ev_type == "done":
                            print("\n[DONE] Stream finished successfully.")
                    except Exception:
                        pass
    except Exception as e:
        print(f"[ERR] Chat test error: {e}", file=sys.stderr)


if __name__ == "__main__":
    prompt_arg = sys.argv[1] if len(sys.argv) > 1 else "우리집 종합 상황 알려줘"
    is_llm = "--llm" in sys.argv or prompt_arg.startswith("ai ")
    test_chat(prompt_arg, is_llm)
