"""FocusFlow server: Python stdlib only. Run: python3 src/server.py -> http://localhost:8003/

Persistence: local JSON file only (data/focusflow.json, next to the project
root). No cloud, no account, no external API, no keys. The file is gitignored
so a user's real tasks are never committed to a public repo.
"""
import json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(__file__))
from planner import Planner

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.environ.get("FOCUSFLOW_DATA",
                           os.path.join(ROOT, "data", "focusflow.json"))
PLANNER = Planner.load(DATA_PATH)
PUBLIC = os.path.join(ROOT, "public")
PORT = int(os.environ.get("PORT", "8003"))


def _persist():
    PLANNER.save(DATA_PATH)


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/api/health":
            self._send(200, json.dumps({"status": "ok", "mode": "local"}))
        elif p == "/api/summary":
            self._send(200, json.dumps(PLANNER.summary()))
        elif p == "/api/focus":
            self._send(200, json.dumps(PLANNER.focus.status()))
        elif p in ("/", "/index.html"):
            with open(os.path.join(PUBLIC, "index.html"), "rb") as fh:
                self._send(200, fh.read(), "text/html")
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        p = urlparse(self.path).path
        try:
            if p == "/api/tasks":
                body = self._read_json()
                t = PLANNER.add(body["title"], body["minutes"])
                _persist()
                self._send(200, json.dumps({"ok": True, "task": t.to_dict(),
                                            "summary": PLANNER.summary()}))
            elif p.startswith("/api/tasks/") and p.endswith("/complete"):
                task_id = p.split("/")[3]
                t = PLANNER.complete_by_id(task_id)
                _persist()
                self._send(200, json.dumps({"ok": True, "task": t.to_dict(),
                                            "summary": PLANNER.summary()}))
            elif p == "/api/focus/start":
                status = PLANNER.focus.start()
                self._send(200, json.dumps(status))
            elif p == "/api/focus/pause":
                status = PLANNER.focus.pause()
                _persist()
                self._send(200, json.dumps(status))
            elif p == "/api/focus/reset":
                status = PLANNER.focus.reset()
                _persist()
                self._send(200, json.dumps(status))
            else:
                self._send(404, json.dumps({"error": "not found"}))
        except KeyError as e:
            self._send(404, json.dumps({"error": str(e)}))
        except Exception as e:
            self._send(400, json.dumps({"error": str(e)}))

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
