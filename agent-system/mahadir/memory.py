"""Persistent memory — the substrate of self-improvement.

Files under memory/:
    lessons.json     learned pitfalls, injected into the owning agent's prompts
    playbooks.json   successful plans, retrieved by fingerprint similarity
    scorecards.json  per-agent running performance history
    policies.json    tuned control knobs (critic rounds, retry budgets, ...)

Every run reads this memory at kickoff and the Postmortem agent writes back
after completion, so run N+1 is measurably better than run N.
"""

from __future__ import annotations

import copy
import json
import os
import threading
import time
from typing import Any, Optional

DEFAULT_POLICIES = {
    "critic_rounds": 3,      # max writer<->critic revision loops per run
    "verify_attempts": 2,    # max fact-check repair cycles
    "retry_budget": 2,       # transient-error retries per agent step
    "max_steps": 120,        # hard stop on processed messages
    "max_seconds": 600,      # hard stop on wall clock
    "evidence_min": 3,       # minimum acceptable facts in an evidence pack
}
BOUNDS = {  # self-tuning is clamped so the system can never destabilise itself
    "critic_rounds": (1, 5),
    "verify_attempts": (1, 4),
    "retry_budget": (1, 5),
    "evidence_min": (2, 8),
}


class Memory:
    def __init__(self, root: str):
        self.root = root
        self.lock = threading.RLock()
        os.makedirs(root, exist_ok=True)
        self._policies = self._load("policies.json", DEFAULT_POLICIES)
        self._lessons = self._load("lessons.json", [])
        self._playbooks = self._load("playbooks.json", [])
        self._scorecards = self._load("scorecards.json", {})

    # ------------------------------------------------------------------ io
    def _path(self, name: str) -> str:
        return os.path.join(self.root, name)

    def _load(self, name: str, default: Any) -> Any:
        try:
            with open(self._path(name), encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return copy.deepcopy(default)

    def _save(self, name: str, data: Any) -> None:
        tmp = self._path(name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self._path(name))

    # ------------------------------------------------------------- policies
    @property
    def policies(self) -> dict:
        with self.lock:
            return dict(self._policies)

    def update_policies(self, updates: dict) -> dict:
        """Apply bounded self-tuning. Tunable keys are clamped to BOUNDS so
        improvement can never destabilise the pipeline; ops knobs (budgets)
        pass through with sanity clamps; unknown keys are rejected."""
        passthrough = {"max_steps": (5, 100000), "max_seconds": (10, 86400)}
        with self.lock:
            for k, v in updates.items():
                if k in BOUNDS:
                    lo, hi = BOUNDS[k]
                    self._policies[k] = max(lo, min(hi, int(v)))
                elif k in passthrough:
                    lo, hi = passthrough[k]
                    self._policies[k] = max(lo, min(hi, int(v)))
            self._save("policies.json", self._policies)
            return dict(self._policies)

    # -------------------------------------------------------------- lessons
    @property
    def lessons(self) -> list[dict]:
        with self.lock:
            return copy.deepcopy(self._lessons)

    def lessons_for(self, agent: str) -> list[dict]:
        with self.lock:
            return [dict(l) for l in self._lessons if l.get("target") == agent]

    def add_lessons(self, lessons: list[dict]) -> list[str]:
        """Dedup by id; refresh evidence line when re-observed."""
        added = []
        with self.lock:
            known = {l.get("id"): l for l in self._lessons}
            for l in lessons:
                lid = l.get("id") or f"L-{int(time.time())}"
                if lid in known:
                    known[lid]["times_seen"] = known[lid].get("times_seen", 1) + 1
                    known[lid]["last_seen_run"] = l.get("evidence", "")
                else:
                    entry = {**l, "id": lid, "times_seen": 1,
                             "created_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
                    known[lid] = entry
                    added.append(lid)
            self._lessons = list(known.values())
            self._save("lessons.json", self._lessons)
        return added

    # ------------------------------------------------------------ playbooks
    @property
    def playbooks(self) -> list[dict]:
        with self.lock:
            return copy.deepcopy(self._playbooks)

    def add_playbook(self, fingerprint: list[str], plan: dict, run_id: str) -> str:
        with self.lock:
            pid = f"PB-{len(self._playbooks) + 1:03d}"
            self._playbooks.append({"id": pid, "fingerprint": fingerprint,
                                    "plan": plan, "run_id": run_id,
                                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
            self._save("playbooks.json", self._playbooks)
            return pid

    # ----------------------------------------------------------- scorecards
    @property
    def scorecards(self) -> dict:
        with self.lock:
            return copy.deepcopy(self._scorecards)

    def record_run(self, agent_stats: dict, run_quality: float) -> None:
        """agent_stats: {agent: {first_pass_ok: bool, latency_ms: int, tokens: int}}"""
        with self.lock:
            for agent, s in agent_stats.items():
                card = self._scorecards.setdefault(
                    agent, {"runs": 0, "first_pass_yields": [], "avg_latency_ms": 0, "avg_tokens": 0})
                card["runs"] += 1
                card.setdefault("first_pass_yields", []).append(1 if s.get("first_pass_ok") else 0)
                card["first_pass_yields"] = card["first_pass_yields"][-20:]
                n = card["runs"]
                card["avg_latency_ms"] = round(
                    (card["avg_latency_ms"] * (n - 1) + s.get("latency_ms", 0)) / n, 1)
                card["avg_tokens"] = round(
                    (card["avg_tokens"] * (n - 1) + s.get("tokens", 0)) / n)
            self._scorecards.setdefault("_run_quality", []).append(
                {"run_id": "", "score": run_quality, "ts": time.time()})
            self._scorecards["_run_quality"] = self._scorecards["_run_quality"][-30:]
            self._save("scorecards.json", self._scorecards)

    def set_last_run_quality(self, run_id: str, score: float) -> None:
        with self.lock:
            q = self._scorecards.setdefault("_run_quality", [])
            if q:
                q[-1]["run_id"] = run_id
                q[-1]["score"] = score
                self._save("scorecards.json", self._scorecards)

    # -------------------------------------------------------------- summary
    def summary(self) -> dict:
        with self.lock:
            yield_trend = {
                a: round(sum(c.get("first_pass_yields", [])) / max(1, len(c.get("first_pass_yields", [1]))), 2)
                for a, c in self._scorecards.items() if a != "_run_quality"
            }
            return {
                "lessons": len(self._lessons),
                "playbooks": len(self._playbooks),
                "policies": dict(self._policies),
                "first_pass_yield": yield_trend,
                "runs_scored": len(self._scorecards.get("_run_quality", [])),
            }

    def snapshot(self) -> dict:
        return {"policies": self.policies, "lessons": self.lessons,
                "playbooks": self.playbooks, "scorecards": self.scorecards}
