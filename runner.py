#!/usr/bin/env python3
"""Microsecond-precision Real-Time SSE Packet Timing Report for Mode 1, Mode 2, and Mode 3."""

import json
import sys
import time
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def profile_stream(mode: int, prompt: str):
    ha_ip = "192.168.0.14"
    chat_url = f"http://{ha_ip}:8000/api/chat"

    mode_names = {
        1: "Mode 1: AI Deep Brain",
        2: "Mode 2: Fast Dispatcher",
        3: "Mode 3: Google Antigravity Headless CLI"
    }

    print("\n" + "=" * 90)
    print(f"[*] PROFILING [{mode_names.get(mode, mode)}] on {chat_url}")
    print(f"[*] Prompt: '{prompt}'")
    print("-" * 90)

    payload = json.dumps({
        "prompt": prompt,
        "stream_mode": mode
    }).encode("utf-8")

    req = urllib.request.Request(
        chat_url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    t0 = time.perf_counter()
    packet_index = 0
    packets_log = []

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            t_connect = time.perf_counter()
            print(f"[{format_ms_us(t_connect - t0)}] HTTP 200 SSE Stream Initialized")

            last_t = t_connect
            while True:
                line_bytes = resp.readline()
                if not line_bytes:
                    break
                now_t = time.perf_counter()
                line = line_bytes.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                packet_index += 1
                delta_total = now_t - t0
                delta_gap = now_t - last_t
                last_t = now_t

                payload_str = line[5:].strip() if line.startswith("data:") else line
                try:
                    ev_data = json.loads(payload_str)
                    ev_type = ev_data.get("type", "unknown")
                    ev_content = ev_data.get("content", "")
                    tokens = ev_data.get("tokens", None)
                except Exception:
                    ev_type = "raw"
                    ev_content = line[:80]
                    tokens = None

                log_entry = {
                    "index": packet_index,
                    "total_sec": delta_total,
                    "gap_sec": delta_gap,
                    "type": ev_type,
                    "content": ev_content,
                    "tokens": tokens,
                }
                packets_log.append(log_entry)

                if ev_type == "chunk":
                    snippet = f"'{ev_content[:40]}...' ({len(ev_content)} chars)"
                elif ev_type == "tool":
                    snippet = f"{ev_content}"
                elif ev_type == "done":
                    snippet = f"Tokens: {tokens}"
                elif ev_type == "text":
                    snippet = f"[Full Text ({len(ev_content)} chars)]"
                else:
                    snippet = str(ev_content)[:60]

                print(
                    f"  Packet #{packet_index:02d} | "
                    f"Total: +{delta_total*1000:8.2f}ms (+{delta_total*1_000_000:10.0f}µs) | "
                    f"Gap: +{delta_gap*1000:7.2f}ms | "
                    f"[{ev_type.upper():5s}] {snippet}"
                )

                if ev_type == "done":
                    break

    except Exception as e:
        print(f"[!] Error: {e}")

    t_end = time.perf_counter()
    print("-" * 90)
    print(f"[*] Summary: {packet_index} packets received in {(t_end - t0)*1000:.2f}ms ({(t_end - t0):.4f}s)")
    return packets_log


def format_ms_us(sec):
    return f"+{sec*1000:7.2f}ms (+{sec*1_000_000:9.0f}µs)"


if __name__ == "__main__":
    time.sleep(2)
    # Profile Mode 1
    profile_stream(1, "각 방 온도 알려줘")
    time.sleep(1)
    # Profile Mode 3
    profile_stream(3, "What is a git rebase in one sentence?")
