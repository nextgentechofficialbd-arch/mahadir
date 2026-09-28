#!/usr/bin/env python3
"""Run the Mahadir multi-agent pipeline end-to-end from the terminal.

Examples
    python run.py                                          # demo task, mock brain
    python run.py "Write a launch post for our GPU rental service" --chaos
    MAHADIR_PROVIDER=openai MAHADIR_API_KEY=sk-... python run.py "..."
    python run.py --resume run-1a2b3c4d
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mahadir.llm import make_brain                           # noqa: E402
from mahadir.memory import Memory                            # noqa: E402
from mahadir.orchestrator import ChaosBrain, Orchestrator    # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))

DEFAULT_TASK = {
    "title": "Global Computer & Technology: on-site PC repair and build service in Dhaka",
    "brief": ("Publish-ready blog post announcing our on-site PC repair and custom "
              "build service. Professional-friendly tone for home users and small "
              "businesses in Dhaka. Must be factual and citation-backed."),
    "constraints": ["cite every claim", "no unverifiable pricing promises"],
}

C = {"dim": "\033[2m", "b": "\033[1m", "r": "\033[31m", "g": "\033[32m",
     "y": "\033[33m", "bl": "\033[34m", "m": "\033[35m", "c": "\033[36m", "x": "\033[0m"}
AGENT_COLOR = {"planner": "m", "researcher": "bl", "writer": "c",
               "critic": "y", "verifier": "g", "postmortem": "r", "orchestrator": "dim"}
TYPE_GLYPH = {"task.kickoff": "▶", "plan": "🗺", "subtask": "▶", "evidence": "📚",
              "draft_request": "▶", "draft": "✍", "review_request": "▶",
              "verdict": "⚖", "verify_request": "▶", "verification": "🔍",
              "postmortem_request": "▶", "postmortem_report": "🧠"}


def printer(msg: dict) -> None:
    color = C[AGENT_COLOR.get(msg["from"], "dim")]
    glyph = TYPE_GLYPH.get(msg["type"], "·")
    head = f"{C['dim']}{msg['ts'][11:19]}{C['x']} {color}{msg['from']:>11}{C['x']} {glyph} {msg['type']}"
    if msg.get("round"):
        head += f" (r{msg['round']})"
    tail = ""
    p = msg.get("payload", {})
    if msg["type"] == "event.state":
        head = f"{C['dim']}{msg['ts'][11:19]}{C['x']} {C['b']}━━ {p.get('state','')}{C['x']}"
    elif msg["type"] == "event.retry":
        tail = f" {C['r']}retrying in {p.get('wait_s')}s — {p.get('reason','')[:90]}{C['x']}"
    elif msg["type"] == "event.feedback":
        tail = f" {C['y']}feedback bounce — {p.get('reason','')[:90]}{C['x']}"
    elif msg["type"] == "plan":
        tail = f" {C['dim']}stages={[s['stage'] for s in p['plan']['subtasks']]} seeded={p['plan'].get('seeded_from_playbook')}{C['x']}"
    elif msg["type"] == "evidence":
        tail = f" {C['dim']}facts={len(p['evidence']['facts'])} floor={p['evidence'].get('confidence_floor')}{C['x']}"
    elif msg["type"] == "draft":
        tail = f" {C['dim']}{len(p['draft']['draft_markdown'])} chars, cites={p['draft']['citations']}{C['x']}"
    elif msg["type"] == "verdict":
        v = p["verdict"]
        vc = C["g"] if v["verdict"] == "PASS" else C["r"]
        tail = f" {vc}{v['verdict']} score={v.get('score')}{C['x']} {C['dim']}{len(v.get('issues', []))} issue(s){C['x']}"
    elif msg["type"] == "verification":
        v = p["verification"]
        vc = C["g"] if v["verdict"] == "PASS" else C["r"]
        tail = f" {vc}{v['verdict']}{C['x']} {C['dim']}claims={v.get('checked_claims')}{C['x']}"
    elif msg["type"] == "postmortem_report":
        ap = p["postmortem"].get("applied", {})
        tail = (f" {C['dim']}lessons+{len(ap.get('lessons_added', []))} "
                f"playbook={ap.get('playbook_id')}{C['x']}")
    print(head + tail, flush=True)


def summary(rep: dict) -> None:
    line = "─" * 78
    status = rep["status"]
    sc = C["g"] if status == "DONE" else (C["y"] if "WARN" in status else C["r"])
    print(f"\n{line}\n{C['b']}RUN {rep['run_id']}{C['x']}  status: {sc}{status}{C['x']}  "
          f"quality: {rep['quality']}  wall: {rep['wall_s']}s  messages: {rep['messages']}")
    pa = rep["per_agent"]
    if pa:
        print(f"{C['b']}agent scorecard{C['x']}")
        for a, s in pa.items():
            fp = C["g"] + "clean" + C["x"] if s["first_pass_ok"] else C["y"] + f"{s['retries']} retry/bounce" + C["x"]
            print(f"  {a:<11} calls={s['calls']:<3} {fp:<20} latency={s['latency_ms']}ms")
    if rep["incidents"]:
        print(f"{C['y']}incidents handled: {len(rep['incidents'])}{C['x']}")
        for i in rep["incidents"][:6]:
            print(f"  [{i['kind']}] {i['agent']}: {i['detail'][:100]}")
    si = rep["self_improvement"]
    print(f"{C['b']}self-improvement{C['x']}  lessons+{len(si['lessons_added'])} "
          f"playbook={si['playbook_id']}")
    if si.get("policies_now"):
        print(f"  policies now: {si['policies_now']}")
    if rep.get("artifact"):
        print(f"{C['b']}artifact:{C['x']} {rep['artifact']}")
    print(f"{C['b']}dashboard:{C['x']} python dashboard.py  → http://localhost:8000\n{line}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Mahadir multi-agent pipeline")
    ap.add_argument("task", nargs="?", default=None, help="task title")
    ap.add_argument("--task-file", default=None, help="JSON file with {title, brief, constraints}")
    ap.add_argument("--resume", default=None, help="run id to resume")
    ap.add_argument("--chaos", action="store_true", help="inject deterministic faults (see retries live)")
    ap.add_argument("--provider", default=None, help="mock|openai|anthropic|compatible")
    ap.add_argument("--max-steps", type=int, default=None)
    args = ap.parse_args()

    memory = Memory(os.path.join(ROOT, "memory"))
    brain = make_brain(args.provider)
    if args.chaos:
        brain = ChaosBrain(brain)
    if args.max_steps:
        memory.update_policies({"max_steps": args.max_steps})

    if args.resume:
        print(f"{C['b']}resuming {args.resume}{C['x']}", flush=True)
        rep = Orchestrator.resume(args.resume, ROOT, brain=brain, memory=memory,
                                  subscribe=printer)
        summary(rep)
        return 0 if rep["status"] == "DONE" else 1

    if args.task_file:
        with open(args.task_file, encoding="utf-8") as f:
            task = json.load(f)
    else:
        task = dict(DEFAULT_TASK)
        if args.task:
            task["title"] = args.task

    print(f"{C['b']}Mahadir MAS{C['x']} brain={getattr(brain, 'name', '?')}  "
          f"task={task['title']!r}\n", flush=True)
    orch = Orchestrator(task, ROOT, brain=brain, memory=memory, subscribe=printer)
    rep = orch.start()
    summary(rep)
    return 0 if rep["status"] == "DONE" else 1


if __name__ == "__main__":
    time.sleep(0)
    sys.exit(main())
