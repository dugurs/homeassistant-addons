#!/usr/bin/env python3
"""Antigravity Dual Ingress Server & Fast REST/SSE API Dispatcher.
Refactored Modular Architecture:
- core.web_ui: HTML5/CSS3/JS Web UI
- core.ha_engine: Smart Home States, Weather, Environment, and Log queries
- core.streamer: Non-blocking SSE Real-time Streaming (Modes 1, 2, 3)
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import select
import socket
import sys
import threading
import time

from core.ha_engine import get_resource_usage, get_supervisor_token, handle_agent_chat
from core.streamer import stream_agent_chat
from core.web_ui import HTML_INDEX

TTYD_INTERNAL_PORT = 7682


class AntigravityAPIHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Ingress Dual Web UI, Real-Time Streaming, and REST API."""

    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def _check_auth(self):
        """Check API authentication key."""
        options_path = "/data/options.json"
        expected_key = None
        if os.path.exists(options_path):
            try:
                with open(options_path, "r", encoding="utf-8") as f:
                    options = json.load(f)
                    expected_key = options.get("api_key")
            except Exception:
                pass
        if not expected_key:
            return True

        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            return token == expected_key
        return False

    def _proxy_to_ttyd(self):
        """Proxy HTTP and WebSocket requests to internal ttyd on port 7682."""
        if self.headers.get("Upgrade", "").lower() == "websocket":
            try:
                target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target_sock.connect(("127.0.0.1", TTYD_INTERNAL_PORT))

                req_lines = [f"{self.command} {self.path} {self.request_version}"]
                for k, v in self.headers.items():
                    req_lines.append(f"{k}: {v}")
                req_lines.append("\r\n")
                target_sock.sendall("\r\n".join(req_lines).encode("utf-8"))

                client_sock = self.connection
                client_sock.setblocking(0)
                target_sock.setblocking(0)
                sockets = [client_sock, target_sock]
                while True:
                    r, _, x = select.select(sockets, [], sockets, 30.0)
                    if x or not r:
                        break
                    for s in r:
                        other = target_sock if s is client_sock else client_sock
                        try:
                            data = s.recv(16384)
                            if not data:
                                return
                            other.sendall(data)
                        except Exception:
                            return
            except Exception:
                pass
            return

        import urllib.request
        target_url = f"http://127.0.0.1:{TTYD_INTERNAL_PORT}{self.path}"
        try:
            req_headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
            req = urllib.request.Request(target_url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ("transfer-encoding", "content-length"):
                        self.send_header(k, v)
                body = resp.read()
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:
            self.send_error(502, f"Bad Gateway to ttyd: {e}")

    def do_GET(self):
        """Handle GET requests."""
        clean_path = self.path.split("?")[0].rstrip("/")

        # 1. Forward /terminal traffic to ttyd
        if clean_path.endswith("/terminal") or "/terminal" in self.path:
            self._proxy_to_ttyd()
            return

        # 2. REST Status API
        if clean_path.endswith("/api/status"):
            if not self._check_auth():
                self._set_headers(401)
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return

            resources = get_resource_usage()
            from core.system_info import check_agy_hardware_support
            from core.ui import UI_BUILD_VERSION
            hw_info = check_agy_hardware_support()
            res = {
                "status": "online",
                "version": "1.1.0-beta.17",
                "ui_build_version": UI_BUILD_VERSION,
                "uptime": int(time.time() - SERVER_START_TIME),
                "active_sessions": 1,
                "memory_usage": resources["memory_usage"],
                "addon_memory_mb": resources["addon_memory_mb"],
                "addon_memory_percent": resources["addon_memory_percent"],
                "cpu_usage": resources["cpu_usage"],
                "addon_cpu_usage": resources["addon_cpu_usage"],
                "system_cpu_usage": resources["system_cpu_usage"],
                "total_memory_gb": resources["total_memory_gb"],
                "used_memory_gb": resources["used_memory_gb"],
                "memory_percent": resources["memory_percent"],
                "system_memory_percent": resources["system_memory_percent"],
                "mcp_enabled": True,
                "agy_stream_supported": hw_info.get("supported", False),
                "hw_info": hw_info,
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        # 3. Headless Stream Test API
        if clean_path.endswith("/api/test_stream"):
            from core.streamer import test_headless_cli_execution
            test_res = test_headless_cli_execution()
            self._set_headers(200)
            self.wfile.write(json.dumps(test_res, ensure_ascii=False).encode("utf-8"))
            return

        # 3b. Debug: list a conversation's brain directory tree (diagnostic only)
        if clean_path.endswith("/api/debug_brain_dir"):
            import os as _os
            from core.session_manager import get_brain_base_dir
            qs = self.path.split("?", 1)[1] if "?" in self.path else ""
            import urllib.parse as _up
            cid = _up.parse_qs(qs).get("cid", [""])[0]
            base = get_brain_base_dir()
            target = _os.path.join(base, cid) if cid else base
            tree = []
            if _os.path.exists(target):
                for root, dirs, files in _os.walk(target):
                    for f in files:
                        fp = _os.path.join(root, f)
                        try:
                            tree.append({"path": fp, "size": _os.path.getsize(fp), "mtime": _os.path.getmtime(fp)})
                        except Exception:
                            pass
            self._set_headers(200)
            self.wfile.write(json.dumps({"base": base, "target": target, "exists": _os.path.exists(target), "tree": tree}, ensure_ascii=False).encode("utf-8"))
            return

        # 4. PTY-based agy test (uses script -q -c to force TTY mode)
        if clean_path.endswith("/api/test_pty"):
            import subprocess as _sp
            import os as _os
            import time as _t
            results = {}
            agy_bin = "/root/.local/bin/agy"

            # Check auth files / symlinks
            auth_info = {}
            for p in ["/root/.gemini", "/config/.gemini", "/root/.config"]:
                if _os.path.islink(p):
                    auth_info[p] = f"symlink -> {_os.readlink(p)}"
                elif _os.path.exists(p):
                    try:
                        auth_info[p] = _os.listdir(p)
                    except Exception as ex:
                        auth_info[p] = str(ex)
                else:
                    auth_info[p] = "NOT_FOUND"
            results["auth_info"] = auth_info

            # Look for credential files - exhaustive recursive search
            cred_found = {}
            import os as _os2
            for search_root in ["/root/.gemini", "/config/.gemini", "/root/.config", "/config/.config", "/root/.local/share"]:
                real_root = _os.path.realpath(search_root) if _os.path.islink(search_root) else search_root
                if _os.path.exists(real_root):
                    for dirpath, dirnames, filenames in _os.walk(real_root):
                        for fname in filenames:
                            fpath = _os.path.join(dirpath, fname)
                            cred_found[fpath] = f"size={_os.path.getsize(fpath)}"
            results["all_files"] = cred_found

            env = _os.environ.copy()
            env["HOME"] = "/root"
            env["USER"] = "root"
            env["PATH"] = "/root/.local/bin:/usr/local/bin:/usr/bin:/bin"
            env["TERM"] = "xterm"
            env["FORCE_COLOR"] = "0"

            # Try script -q -c to force pseudo-TTY (Go flushes immediately in TTY mode)
            t0 = _t.time()
            try:
                proc = _sp.Popen(
                    ["script", "-q", "-e", "-c",
                     f"{agy_bin} -p 'Say hi in 3 words' --output-format stream-json --dangerously-skip-permissions",
                     "/dev/null"],
                    stdout=_sp.PIPE, stderr=_sp.PIPE, text=True, env=env,
                )
                try:
                    stdout, stderr = proc.communicate(timeout=20)
                    results["script_pty"] = {
                        "time": round(_t.time() - t0, 2),
                        "ret": proc.returncode,
                        "stdout_raw_lines": [l for l in stdout.splitlines() if l.strip()],
                        "stderr": stderr[:300],
                    }
                except _sp.TimeoutExpired:
                    proc.kill()
                    stdout, stderr = proc.communicate()
                    results["script_pty"] = {
                        "timeout": True,
                        "time": round(_t.time() - t0, 2),
                        "stdout_raw_lines": [l for l in stdout.splitlines() if l.strip()],
                        "stderr": stderr[:300],
                    }
            except Exception as ex:
                results["script_pty"] = {"error": str(ex)}

            self._set_headers(200)
            self.wfile.write(json.dumps(results, ensure_ascii=False).encode("utf-8"))
            return

        # 5. Read agy crash and run logs for diagnosis
        if clean_path.endswith("/api/read_logs"):
            import os as _os
            import glob as _glob
            result = {}

            # Read latest crash log
            crash_dir = "/config/.gemini/antigravity-cli/crashes"
            if _os.path.exists(crash_dir):
                crash_files = sorted(_glob.glob(f"{crash_dir}/*.log"))
                if crash_files:
                    latest_crash = crash_files[-1]
                    try:
                        with open(latest_crash) as f:
                            result["crash_log"] = {"file": latest_crash, "content": f.read(3000)}
                    except Exception as ex:
                        result["crash_log"] = {"error": str(ex)}

            # Read latest agy run log
            log_dir = "/config/.gemini/antigravity-cli/log"
            if _os.path.exists(log_dir):
                log_files = sorted(_glob.glob(f"{log_dir}/cli-*.log"))
                if log_files:
                    latest_log = log_files[-1]
                    try:
                        with open(latest_log) as f:
                            content = f.read()
                            # Show last 3000 chars
                            result["agy_log"] = {"file": latest_log, "content": content[-3000:]}
                    except Exception as ex:
                        result["agy_log"] = {"error": str(ex)}

            # Check token file
            token_path = "/config/.gemini/antigravity-cli/antigravity-oauth-token"
            if _os.path.exists(token_path):
                result["token_exists"] = True
                result["token_size"] = _os.path.getsize(token_path)
            else:
                result["token_exists"] = False

            self._set_headers(200)
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        # Model catalog for the Mode 3 model/effort picker -- queried live from
        # `agy models` (falls back to the bundled static catalog if unavailable)
        # since model lineup and per-model effort support vary by account.
        if clean_path.endswith("/api/models"):
            from core.model_discovery import get_live_model_catalog
            force = "force=1" in self.path
            self._set_headers(200)
            self.wfile.write(json.dumps(get_live_model_catalog(force=force), ensure_ascii=False).encode("utf-8"))
            return

        # Quota (/usage) snapshot for the Mode 3 model picker's usage panel
        if clean_path.endswith("/api/usage"):
            from core.usage_client import get_usage_snapshot
            force = "force=1" in self.path
            self._set_headers(200)
            self.wfile.write(json.dumps(get_usage_snapshot(force=force), ensure_ascii=False).encode("utf-8"))
            return

        # Session Management REST APIs
        if clean_path.endswith("/api/sessions"):
            from core.session_manager import list_all_sessions
            sessions = list_all_sessions(limit=50)
            self._set_headers(200)
            self.wfile.write(json.dumps({"sessions": sessions}, ensure_ascii=False).encode("utf-8"))
            return

        if "/api/sessions/" in clean_path:
            from core.session_manager import get_session_history
            target_cid = clean_path.split("/api/sessions/")[-1].strip()
            history = get_session_history(target_cid)
            self._set_headers(200)
            self.wfile.write(json.dumps({"conversation_id": target_cid, "history": history}, ensure_ascii=False).encode("utf-8"))
            return

        # Serve Web UI
        self._set_headers(200, "text/html; charset=utf-8")
        self.wfile.write(HTML_INDEX.encode("utf-8"))

    def do_POST(self):
        """Handle POST requests."""
        clean_path = self.path.split("?")[0].rstrip("/")

        # 1. Forward /terminal traffic to ttyd
        if clean_path.endswith("/terminal") or "/terminal" in self.path:
            self._proxy_to_ttyd()
            return

        if not self._check_auth():
            self._set_headers(401)
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
            return

        # 2. Real-Time Chat Streaming API
        if clean_path.endswith("/api/chat") or clean_path.endswith("/api/prompt") or "/api/chat" in clean_path or "/api/prompt" in clean_path:
            body = b""
            content_length = self.headers.get("Content-Length")
            if content_length:
                try:
                    body = self.rfile.read(int(content_length))
                except Exception:
                    body = b""
            elif self.headers.get("Transfer-Encoding", "").lower() == "chunked":
                chunks = []
                while True:
                    line = self.rfile.readline().strip()
                    if not line:
                        break
                    try:
                        chunk_len = int(line, 16)
                    except ValueError:
                        break
                    if chunk_len == 0:
                        self.rfile.readline()
                        break
                    chunks.append(self.rfile.read(chunk_len))
                    self.rfile.readline()
                body = b"".join(chunks)

            payload = {}
            if body:
                try:
                    payload = json.loads(body.decode("utf-8"))
                except Exception:
                    try:
                        import urllib.parse
                        payload = dict(urllib.parse.parse_qsl(body.decode("utf-8")))
                    except Exception:
                        pass

            prompt = payload.get("prompt", "").strip()
            if not prompt and "?" in self.path:
                try:
                    import urllib.parse
                    qs = urllib.parse.parse_qs(self.path.split("?", 1)[1])
                    prompt = qs.get("prompt", [""])[0].strip()
                except Exception:
                    pass

            is_direct_llm = payload.get("is_direct_llm", False) or prompt.startswith("ai ") or prompt.startswith("/llm")
            stream_mode = int(payload.get("stream_mode", 1))
            is_mobile = bool(payload.get("is_mobile", False))
            conversation_id = str(payload.get("conversation_id", "")).strip()
            model = str(payload.get("model", "")).strip()

            if not prompt:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Empty prompt"}).encode("utf-8"))
                return

            # Send Server-Sent Events (SSE) Stream Headers
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            try:
                for event_str in stream_agent_chat(
                    prompt,
                    is_direct_llm=is_direct_llm,
                    stream_mode=stream_mode,
                    is_mobile=is_mobile,
                    conversation_id=conversation_id,
                    model=model,
                ):
                    self.wfile.write(event_str.encode("utf-8"))
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        elif clean_path.endswith("/api/restart"):
            self._set_headers(200)
            self.wfile.write(json.dumps({"result": "restarted", "status": "online"}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_DELETE(self):
        """Handle DELETE requests -- session removal.

        Two shapes: DELETE /api/sessions/<cid> (single, id from the path) and
        DELETE /api/sessions with a JSON body {"conversation_ids": [...]}
        (bulk, for the sidebar's multi-select "선택 삭제").
        """
        clean_path = self.path.split("?")[0].rstrip("/")
        from core.session_manager import delete_session

        if "/api/sessions/" in clean_path:
            target_cid = clean_path.split("/api/sessions/")[-1].strip()
            ok = delete_session(target_cid)
            self._set_headers(200 if ok else 404)
            self.wfile.write(json.dumps({"conversation_id": target_cid, "deleted": ok}, ensure_ascii=False).encode("utf-8"))
            return

        if clean_path.endswith("/api/sessions"):
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else b"{}"
                payload = json.loads(body or b"{}")
            except Exception:
                payload = {}
            ids = payload.get("conversation_ids") or []
            results = {cid: delete_session(str(cid)) for cid in ids if isinstance(cid, str)}
            self._set_headers(200)
            self.wfile.write(json.dumps({"results": results}, ensure_ascii=False).encode("utf-8"))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress noisy request logs."""
        pass


class DualThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


SERVER_START_TIME = time.time()


def start_server(port, name="API Server"):
    server_address = ("0.0.0.0", port)
    try:
        httpd = DualThreadingHTTPServer(server_address, AntigravityAPIHandler)
        print(f"[INFO] {name} running on port {port}")
        httpd.serve_forever()
    except Exception as e:
        print(f"[ERR] Failed to start {name} on port {port}: {e}", file=sys.stderr)


def main():
    api_port = 8000
    options_path = "/data/options.json"
    if os.path.exists(options_path):
        try:
            with open(options_path, "r", encoding="utf-8") as f:
                options = json.load(f)
                api_port = int(options.get("api_port", 8000))
        except Exception:
            pass

    ingress_port = 7681

    print(f"[INFO] Starting Antigravity Dual Ingress Server on {ingress_port} and REST API on {api_port}...")
    ingress_thread = threading.Thread(target=start_server, args=(ingress_port, "Dual Ingress Web UI server"), daemon=True)
    ingress_thread.start()

    start_server(api_port, "Antigravity REST API server")


if __name__ == "__main__":
    main()
