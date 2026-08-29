#!/usr/bin/env python3
"""Comprehensive E2E Stream Verifier across Mode 1, Mode 2, and Mode 3."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def p(msg: str):
    print(msg, flush=True)


def test_mode(mode_num: int, prompt: str):
    ha_ip = "192.168.0.14"
    url = f"http://{ha_ip}:8000/api/chat"
    p(f"\n========================================================")
    p(f"[*] Running E2E Test on [Mode {mode_num}] with: '{prompt}'")
    p(f"========================================================")

    payload = json.dumps({"prompt": prompt, "is_direct_llm": False, "stream_mode": mode_num}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    t0 = time.time()
    tools_received = []
    chunks_received = []
    done_received = False

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            p(f"[HTTP {resp.status}] Content-Type: {resp.headers.get('Content-Type')}")
            for line in resp:
                l = line.decode("utf-8", errors="replace").strip()
                if not l.startswith("data:"):
                    continue
                try:
                    ev = json.loads(l[5:].strip())
                    etype = ev.get("type")
                    if etype == "tool":
                        content = ev.get("content", "")
                        tools_received.append(content)
                        p(f"  [TOOL EVENT] {content}")
                    elif etype in ("text", "chunk"):
                        content = ev.get("content", "")
                        chunks_received.append(content)
                        p(f"  [CHUNK] {content[:60]}..." if len(content) > 60 else f"  [CHUNK] {content}")
                    elif etype == "done":
                        done_received = True
                        p(f"  [DONE EVENT] Stream successfully terminated.")
                        break
                except Exception as ex:
                    p(f"  [PARSE ERR] {ex}")
    except Exception as e:
        p(f"[ERR] Failed on Mode {mode_num}: {e}")
        return False

    elapsed = round(time.time() - t0, 3)
    p(f"\n--- [Mode {mode_num} Test Summary] ---")
    p(f"• Tool Events Count : {len(tools_received)}")
    p(f"• Chunk/Text Count  : {len(chunks_received)}")
    p(f"• Finished with Done: {done_received}")
    p(f"• Total Latency     : {elapsed}s")

    success = len(tools_received) > 0 and len(chunks_received) > 0 and done_received
    p(f"• Status            : {'[PASS]' if success else '[FAIL]'}")
    return success


def main():
    p("[E2E Verification Suite Starting] Testing all 3 Modes against Home Assistant Add-on...")
    results = {}
    results["Mode 1 (Step/Transcript Tracking)"] = test_mode(1, "오늘 날씨와 환경 분석해줘")
    results["Mode 2 (PTY Virtual Terminal)"] = test_mode(2, "거실온도")
    results["Mode 3 (Hybrid Fast)"] = test_mode(3, "우리집 종합 상황 알려줘")

    p("\n" + "=" * 56)
    p("           FINAL E2E VERIFICATION REPORT           ")
    p("=" * 56)
    all_pass = True
    for mode_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        p(f"• {mode_name:38} : [{status}]")
        if not passed:
            all_pass = False

    if all_pass:
        p("\nALL 3 MODES PASSED COMPLETE E2E VERIFICATION!")
    else:
        p("\nSOME TESTS FAILED - REQUIRES INVESTIGATION")
        sys.exit(1)


if __name__ == "__main__":
    main()
