"""Message bus + trace recorder.

Every inter-agent message is an explicit, serialisable envelope — this is what
makes handoffs auditable, replays possible, and the dashboard live.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from typing import Callable, Optional


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z"


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class Bus:
    """In-process bus: messages emitted by agents are fanned out to
    subscribers (trace file, live CLI printer, dashboard SSE feed)."""

    def __init__(self, run_id: str, trace_dir: Optional[str] = None):
        self.run_id = run_id
        self.subs: list[Callable[[dict], None]] = []
        self.history: list[dict] = []
        self.lock = threading.Lock()
        self.trace_path = None
        if trace_dir:
            os.makedirs(trace_dir, exist_ok=True)
            self.trace_path = os.path.join(trace_dir, "trace.jsonl")

    def subscribe(self, fn: Callable[[dict], None]) -> None:
        self.subs.append(fn)

    def emit(self, msg: dict) -> dict:
        envelope = {
            "id": msg.get("id") or new_id("msg"),
            "run_id": self.run_id,
            "ts": now_iso(),
            "from": msg.get("from", "?"),
            "to": msg.get("to", "?"),
            "type": msg.get("type", "?"),
            "round": msg.get("round", 0),
            "payload": msg.get("payload", {}),
            "meta": msg.get("meta", {}),
        }
        with self.lock:
            self.history.append(envelope)
        if self.trace_path:
            with open(self.trace_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
        for fn in self.subs:
            try:
                fn(envelope)
            except Exception:  # a broken subscriber must never break the run
                pass
        return envelope

    def event(self, kind: str, **data) -> dict:
        """System-level events (state transitions, retries, budget stops)."""
        return self.emit({"from": "orchestrator", "to": "log", "type": f"event.{kind}",
                          "payload": data})

    def since(self, index: int) -> tuple[list[dict], int]:
        with self.lock:
            return self.history[index:], len(self.history)


class CircuitBreaker:
    """Trips after `threshold` consecutive failures for one agent; a tripped
    agent is skipped (run degrades gracefully instead of burning budget)."""

    def __init__(self, threshold: int = 3):
        self.threshold = threshold
        self.consecutive: dict[str, int] = {}
        self.tripped: dict[str, bool] = {}

    def record_success(self, agent: str) -> None:
        self.consecutive[agent] = 0
        self.tripped[agent] = False

    def record_failure(self, agent: str) -> bool:
        self.consecutive[agent] = self.consecutive.get(agent, 0) + 1
        if self.consecutive[agent] >= self.threshold:
            self.tripped[agent] = True
        return self.tripped.get(agent, False)

    def is_tripped(self, agent: str) -> bool:
        return self.tripped.get(agent, False)
