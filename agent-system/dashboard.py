#!/usr/bin/env python3
"""Mahadir MAS dashboard — observe runs, handoffs, incidents and
self-improvement in the browser. Stdlib only:  python dashboard.py [port]"""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(ROOT, "runs")
MEM = os.path.join(ROOT, "memory")


def jload(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def overview():
    runs = []
    if os.path.isdir(RUNS):
        for rid in sorted(os.listdir(RUNS)):
            rep = jload(os.path.join(RUNS, rid, "report.json"), None)
            if rep:
                runs.append({k: rep.get(k) for k in
                             ("run_id", "status", "quality", "wall_s", "messages",
                              "draft_rounds", "brain", "task", "forced_accept",
                              "verification_failed")})
                runs[-1]["task_title"] = rep.get("task", {}).get("title", "")[:90]
                runs[-1]["ts"] = rid
    runs.sort(key=lambda r: r.get("ts", ""), reverse=True)
    mem = jload(os.path.join(MEM, "policies.json"), {})
    lessons = jload(os.path.join(MEM, "lessons.json"), [])
    cards = jload(os.path.join(MEM, "scorecards.json"), {})
    return {"runs": runs, "policies": mem,
            "lessons": lessons,
            "scorecards": {k: v for k, v in cards.items() if k != "_run_quality"},
            "quality_history": cards.get("_run_quality", [])}


def run_detail(rid):
    base = os.path.join(RUNS, rid)
    rep = jload(os.path.join(base, "report.json"), None)
    if rep is None:
        return {"error": "unknown run"}
    trace = []
    tp = os.path.join(base, "trace.jsonl")
    if os.path.exists(tp):
        with open(tp, encoding="utf-8") as f:
            trace = [json.loads(line) for line in f if line.strip()]
    return {"report": rep, "trace": trace, "state": jload(os.path.join(base, "state.json"), {})}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(ROOT, "dashboard.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        try:
            if self.path == "/api/overview":
                return self._send(200, overview())
            if self.path.startswith("/api/run/"):
                return self._send(200, run_detail(self.path.rsplit("/", 1)[-1]))
            if self.path == "/api/memory":
                return self._send(200, {
                    "lessons": jload(os.path.join(MEM, "lessons.json"), []),
                    "playbooks": jload(os.path.join(MEM, "playbooks.json"), []),
                    "policies": jload(os.path.join(MEM, "policies.json"), {}),
                    "scorecards": jload(os.path.join(MEM, "scorecards.json"), {})})
            return self._send(404, {"error": "not found"})
        except Exception as e:  # noqa: BLE001
            return self._send(500, {"error": str(e)})

    def log_message(self, *a):  # silence request spam
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Mahadir dashboard → http://0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
