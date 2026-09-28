"""ORCHESTRATOR — the engine that makes the pipeline hands-off.

Responsibilities
  * event loop over explicit states (no agent talks to another directly)
  * Writer<->Critic revision loop and Verifier repair loop, bounded by policy
  * error taxonomy: transient -> backoff retry, schema/policy violation ->
    bounce with corrective feedback, fatal -> graceful degradation
  * budgets (steps / wall clock), circuit breaker, dead-letter log
  * checkpoint after every transition => crash-resumable runs
  * always ends with a Postmortem, even on failure, so the system learns
    from crashes too
"""

from __future__ import annotations

import json
import os
import time
import traceback
from typing import Optional

from .agents import build_agents
from .agents.base import ContractViolation, FatalError, RunContext, TransientError
from .bus import Bus, CircuitBreaker, new_id
from .llm import BrainParseError, BrainUnavailable, MockBrain


class ChaosBrain:
    """Deterministic fault injector (demo/test): fails each agent's first call
    with a transient error, and planner/writer additionally once with a parse
    error — so you can watch retries, feedback loops and recovery live."""

    def __init__(self, inner):
        self.inner = inner
        self.calls: dict[str, int] = {}

    @property
    def name(self):
        return f"chaos({getattr(self.inner, 'name', 'brain')})"

    def complete(self, agent, system, request, schema):
        n = self.calls.get(agent, 0)
        self.calls[agent] = n + 1
        if n == 0:
            raise BrainUnavailable(f"[chaos] simulated transient outage on {agent}")
        if agent in ("planner", "writer") and n == 1:
            raise BrainParseError("[chaos] simulated malformed JSON reply")
        return self.inner.complete(agent, system, request, schema)


class Orchestrator:
    STATES = ("PLANNING", "RESEARCHING", "PRODUCING", "REVIEWING",
              "VERIFYING", "POSTMORTEM", "DONE", "FAILED")

    def __init__(self, task: dict, root: str, run_id: Optional[str] = None,
                 brain=None, memory=None, subscribe=None):
        self.root = root
        self.run_id = run_id or new_id("run")
        self.run_dir = os.path.join(root, "runs", self.run_id)
        os.makedirs(self.run_dir, exist_ok=True)
        self.task = task
        self.brain = brain or MockBrain()
        self.memory = memory
        self.agents = build_agents()
        self.bus = Bus(self.run_id, trace_dir=self.run_dir)
        if subscribe:
            self.bus.subscribe(subscribe)
        self.breaker = CircuitBreaker(threshold=3)

        pol = memory.policies if memory else {}
        self.policies = pol
        self.deadline = time.time() + float(pol.get("max_seconds", 600))
        self.max_steps = int(pol.get("max_steps", 120))

        # run state (checkpointed)
        self.state = "PLANNING"
        self.plan = None
        self.stage_index = 0
        self.evidence = None
        self.draft = None
        self.draft_round = 0
        self.repair_attempts = 0
        self.forced = False
        self.verification_failed = False
        self._revision_notes: list = []
        self.incidents: list[dict] = []
        self.dead_letters: list[dict] = []
        self.per_agent: dict[str, dict] = {}
        self.postmortem = None
        self.t0 = time.time()

    # ------------------------------------------------------------------ ctx
    def _ctx(self, parse_feedback=None, contract_feedback=None) -> RunContext:
        return RunContext(brain=self.brain, memory=self.memory, task=self.task,
                          policies=self.policies, parse_feedback=parse_feedback,
                          contract_feedback=contract_feedback)

    # -------------------------------------------------------- agent invoke
    def _invoke(self, agent_name: str, msg: dict) -> None:
        """Call an agent with the full error-handling ladder, then emit whatever
        it produced. Retries: transient->backoff, parse->feedback, policy->bounce."""
        agent = self.agents[agent_name]
        if self.breaker.is_tripped(agent_name):
            raise FatalError(f"circuit breaker open for agent '{agent_name}' "
                             f"({self.breaker.consecutive.get(agent_name, 0)} consecutive failures)")
        stat = self.per_agent.setdefault(
            agent_name, {"calls": 0, "retries": 0, "first_pass_ok": True,
                         "latency_ms": 0, "tokens_est": 0, "errors": []})
        attempts = int(self.policies.get("retry_budget", 2))
        backoff = 0.5
        parse_fb = contract_fb = None
        for attempt in range(attempts + 1):
            self._check_budget()
            stat["calls"] += 1
            t = time.time()
            try:
                outs = agent.handle(msg, self._ctx(parse_feedback=parse_fb,
                                                   contract_feedback=contract_fb))
                latency = int((time.time() - t) * 1000)
                stat["latency_ms"] += latency
                if attempt > 0:
                    stat["first_pass_ok"] = False
                stat["tokens_est"] += (len(json.dumps(msg)) + sum(len(json.dumps(o)) for o in outs)) // 4
                self.breaker.record_success(agent_name)
                for o in outs:
                    o["from"] = agent_name
                    o["meta"]["latency_ms"] = latency
                    o["meta"]["attempt"] = attempt + 1
                    self.bus.emit(o)
                return
            except (BrainUnavailable, TransientError) as e:
                self._incident(agent_name, "transient", str(e), attempt)
                stat["first_pass_ok"] = False
                self.breaker.record_failure(agent_name)
                if self.breaker.is_tripped(agent_name):
                    raise FatalError(f"agent '{agent_name}' tripped the circuit breaker") from e
                if attempt >= attempts:
                    raise FatalError(f"agent '{agent_name}' exhausted retry budget: {e}") from e
                stat["retries"] += 1
                self.bus.event("retry", agent=agent_name, attempt=attempt + 1,
                               wait_s=backoff, reason=str(e)[:200])
                time.sleep(backoff)
                backoff = min(backoff * 2, 5)
            except (BrainParseError, ContractViolation) as e:
                self._incident(agent_name, "schema" if isinstance(e, BrainParseError) else "policy",
                               str(e), attempt)
                stat["first_pass_ok"] = False
                self.breaker.record_failure(agent_name)
                if attempt >= attempts:
                    raise FatalError(f"agent '{agent_name}' could not produce valid output: {e}") from e
                stat["retries"] += 1
                self.bus.event("feedback", agent=agent_name, attempt=attempt + 1,
                               reason=str(e)[:200])
                if isinstance(e, BrainParseError):
                    parse_fb = str(e)
                else:
                    contract_fb = str(e)
            except FatalError:
                raise
            except Exception as e:  # unknown -> treated as transient, then fatal
                self._incident(agent_name, "unexpected", f"{type(e).__name__}: {e}", attempt)
                stat["first_pass_ok"] = False
                stat["retries"] += 1
                self.breaker.record_failure(agent_name)
                if attempt >= attempts:
                    raise FatalError(f"agent '{agent_name}' unexpected failure: {e}") from e

    def _incident(self, agent, kind, detail, attempt):
        self.incidents.append({"agent": agent, "kind": kind, "attempt": attempt,
                               "detail": str(detail)[:400], "ts": time.time()})

    # -------------------------------------------------------------- budget
    def _check_budget(self) -> None:
        if time.time() > self.deadline:
            raise FatalError("wall-clock budget exceeded")
        if len(self.bus.history) > self.max_steps:
            raise FatalError("step budget exceeded (too many messages)")

    # ---------------------------------------------------------- state jump
    def _goto(self, state: str) -> None:
        self.state = state
        self.bus.event("state", state=state)
        self.checkpoint()

    # ------------------------------------------------------------- kickoff
    def start(self, task: Optional[dict] = None) -> dict:
        if task:
            self.task = task
        self.bus.event("run.start", run_id=self.run_id, task=self.task,
                       brain=getattr(self.brain, "name", "?"))
        self.checkpoint()
        return self._step_planning()

    # ------------------------------------------------------------- planner
    def _step_planning(self) -> dict:
        try:
            msg = {"from": "orchestrator", "to": "planner", "type": "task.kickoff", "round": 0,
                   "payload": {"task": self.task}}
            self.bus.emit(msg)
            self._invoke("planner", msg)
        except FatalError as e:
            return self._fail(e)
        return self._on_plan(self.bus.history[-1])

    def _on_plan(self, msg: dict) -> dict:
        if msg.get("type") != "plan":
            return self._fail(FatalError(f"expected plan, got {msg.get('type')}"))
        self.plan = msg["payload"]["plan"]
        self.bus.event("plan.accepted", subtasks=[s["id"] for s in self.plan["subtasks"]],
                       seeded_from_playbook=self.plan.get("seeded_from_playbook"))
        self._goto("RESEARCHING")
        return self._dispatch_stage()

    # ------------------------------------------------------- stage machine
    def _stage(self) -> dict:
        return self.plan["subtasks"][self.stage_index]

    def _draft_stage_index(self) -> int:
        return [i for i, s in enumerate(self.plan["subtasks"]) if s["stage"] == "draft"][0]

    def _dispatch_stage(self) -> dict:
        stage = self._stage()
        task_title = self.plan.get("task_title", self.task["title"])
        try:
            if stage["stage"] == "research":
                msg = {"from": "orchestrator", "to": "researcher", "type": "subtask",
                       "round": 0, "payload": {"subtask": stage, "task_title": task_title}}
                self.bus.emit(msg)
                self._invoke("researcher", msg)
                return self._on_evidence(self.bus.history[-1])
            if stage["stage"] == "draft":
                return self._send_to_writer()
            if stage["stage"] == "review":
                return self._send_to_critic()
            if stage["stage"] == "verify":
                return self._send_to_verifier()
        except FatalError as e:
            return self._fail(e)
        return self._fail(FatalError(f"unknown stage {stage['stage']}"))

    # ------------------------------------------------------------ researcher
    def _on_evidence(self, msg: dict) -> dict:
        if msg.get("type") != "evidence":
            return self._fail(FatalError(f"expected evidence, got {msg.get('type')}"))
        self.evidence = msg["payload"]["evidence"]
        self.bus.event("evidence.accepted", facts=len(self.evidence.get("facts", [])),
                       confidence_floor=self.evidence.get("confidence_floor"))
        self.stage_index += 1
        self._goto("PRODUCING")
        return self._dispatch_stage()

    # --------------------------------------------------------------- writer
    def _send_to_writer(self) -> dict:
        self.draft_round += 1
        msg = {"from": "orchestrator", "to": "writer", "type": "draft_request",
               "round": self.draft_round,
               "payload": {"evidence": self.evidence,
                           "task_title": self.plan.get("task_title", self.task["title"]),
                           "brief": self.task.get("brief", ""),
                           "round": self.draft_round,
                           "revision_notes": self._revision_notes}}
        self.bus.emit(msg)
        try:
            self._invoke("writer", msg)
        except FatalError as e:
            return self._fail(e)
        return self._on_draft(self.bus.history[-1])

    def _on_draft(self, msg: dict) -> dict:
        if msg.get("type") != "draft":
            return self._fail(FatalError(f"expected draft, got {msg.get('type')}"))
        self.draft = msg["payload"]["draft"]
        self._revision_notes = []
        self.stage_index += 1
        self._goto("REVIEWING")
        return self._dispatch_stage()

    # --------------------------------------------------------------- critic
    def _send_to_critic(self) -> dict:
        stage = self._stage()
        msg = {"from": "orchestrator", "to": "critic", "type": "review_request",
               "round": self.draft_round,
               "payload": {"draft": self.draft,
                           "acceptance_criteria": stage.get("acceptance_criteria", []),
                           "round": self.draft_round,
                           "task_title": self.plan.get("task_title", self.task["title"])}}
        self.bus.emit(msg)
        try:
            self._invoke("critic", msg)
        except FatalError as e:
            return self._fail(e)
        return self._on_verdict(self.bus.history[-1])

    def _on_verdict(self, msg: dict) -> dict:
        verdict = msg["payload"]["verdict"]
        cap = int(self.policies.get("critic_rounds", 3))
        if verdict.get("verdict") == "PASS":
            self.bus.event("critic.pass", score=verdict.get("score"), round=self.draft_round,
                           forced=bool(verdict.get("forced")))
            self.stage_index += 1
            self._goto("VERIFYING")
            return self._dispatch_stage()
        self.bus.event("critic.reject", round=self.draft_round, score=verdict.get("score"),
                       issues=[i.get("note", "") for i in verdict.get("issues", [])])
        if self.draft_round >= cap:
            # graceful degradation: ship the best effort, clearly flagged
            self.forced = True
            self.bus.event("critic.force_accept", round=self.draft_round, cap=cap)
            self.stage_index += 1
            self._goto("VERIFYING")
            return self._dispatch_stage()
        self._revision_notes = verdict.get("issues", [])
        self.stage_index = self._draft_stage_index()  # back to the draft stage
        self._goto("PRODUCING")
        return self._dispatch_stage()

    # ------------------------------------------------------------- verifier
    def _send_to_verifier(self) -> dict:
        msg = {"from": "orchestrator", "to": "verifier", "type": "verify_request",
               "round": self.draft_round,
               "payload": {"draft": self.draft, "evidence": self.evidence}}
        self.bus.emit(msg)
        try:
            self._invoke("verifier", msg)
        except FatalError as e:
            return self._fail(e)
        return self._on_verification(self.bus.history[-1])

    def _on_verification(self, msg: dict) -> dict:
        check = msg["payload"]["verification"]
        if check.get("verdict") == "PASS":
            self.bus.event("verify.pass", claims=check.get("checked_claims"))
            return self._finish()
        self.bus.event("verify.fail", unresolved=check.get("unresolved_citations"),
                       uncovered=check.get("uncovered_facts"))
        if self.repair_attempts < int(self.policies.get("verify_attempts", 2)) - 1:
            self.repair_attempts += 1
            self._revision_notes = [
                {"severity": "blocking", "area": "citations",
                 "note": f"Unresolved citations {check.get('unresolved_citations')}; "
                         f"uncovered facts {check.get('uncovered_facts')}",
                 "fix_hint": "Cite every evidence id exactly as in the evidence pack."}]
            # jump back to the draft stage; the critic re-reviews after repair
            self.stage_index = self._draft_stage_index()
            self._goto("PRODUCING")
            return self._dispatch_stage()
        # second failure: finish flagged, never silently ship unverified content
        self.bus.event("verify.give_up", attempts=self.repair_attempts + 1)
        return self._finish(verification_failed=True)

    # ------------------------------------------------------------ postmortem
    def _finalize_agent_stats(self) -> None:
        """first_pass_ok = the agent did its whole job in a single clean call
        (no revision rounds, no retries, no bounces). This is the metric the
        scorecards trend across runs."""
        for s in self.per_agent.values():
            s["first_pass_ok"] = (s["calls"] <= 1 and s["retries"] == 0)

    def _stats(self) -> dict:
        return {"run_id": self.run_id, "messages": len(self.bus.history),
                "retries": sum(s["retries"] for s in self.per_agent.values()),
                "critic_rejections": sum(1 for m in self.bus.history if m["type"] == "verdict"
                                         and m["payload"]["verdict"]["verdict"] == "FAIL"),
                "critic_round_cap": int(self.policies.get("critic_rounds", 3)),
                "retry_budget": int(self.policies.get("retry_budget", 2)),
                "verifier_flags": sum(1 for m in self.bus.history if m["type"] == "verification"
                                      and m["payload"]["verification"]["verdict"] == "FAIL"),
                "wall_s": time.time() - self.t0,
                "completed": self.state != "FAILED",
                "forced": self.forced}

    def _finish(self, verification_failed: bool = False) -> dict:
        self.verification_failed = verification_failed
        if verification_failed:
            banner = ("<!-- WARNING: verifier FAILED on this artifact; "
                      "it is untrusted and must not ship as-is. -->\n\n")
            with open(os.path.join(self.run_dir, "final_output_UNVERIFIED.md"), "w",
                      encoding="utf-8") as f:
                f.write(banner + self.draft["draft_markdown"])
        else:
            with open(os.path.join(self.run_dir, "final_output.md"), "w", encoding="utf-8") as f:
                f.write(self.draft["draft_markdown"])
        self._goto("POSTMORTEM")
        try:
            msg = {"from": "orchestrator", "to": "postmortem", "type": "postmortem_request",
                   "round": 0,
                   "payload": {"stats": self._stats(), "plan": self.plan or {},
                               "run_meta": {"task_title": (self.plan or {}).get(
                                   "task_title", self.task["title"]),
                                   "status": "DONE"}}}
            self.bus.emit(msg)
            self._invoke("postmortem", msg)
            self.postmortem = self.bus.history[-1]["payload"]["postmortem"]
        except FatalError as e:
            self.bus.event("postmortem.failed", error=str(e)[:200])
            self.dead_letters.append({"agent": "postmortem", "reason": str(e)[:200]})
        status = "DONE_WITH_WARNINGS" if verification_failed else "DONE"
        if self.memory:
            quality = (self.postmortem or {}).get("run_quality", {}).get("score", 5.0)
            if verification_failed:
                quality = min(quality, 3.0)
            self._finalize_agent_stats()
            self.memory.record_run(self.per_agent, quality)
            self.memory.set_last_run_quality(self.run_id, quality)
        return self.report(status)

    def _fail(self, err: Exception) -> dict:
        self.bus.event("run.failed", error=str(err)[:300])
        self.dead_letters.append({"agent": self.state, "reason": str(err)[:300]})
        # Learn from crashes too: run postmortem in degraded mode.
        pre_state = self.state
        try:
            msg = {"from": "orchestrator", "to": "postmortem", "type": "postmortem_request",
                   "round": 0,
                   "payload": {"stats": {**self._stats(), "completed": False,
                                         "failed_in": pre_state},
                               "plan": self.plan or {},
                               "run_meta": {"task_title": self.task["title"], "status": "FAILED"}}}
            self.bus.emit(msg)
            self._invoke("postmortem", msg)
            self.postmortem = self.bus.history[-1]["payload"]["postmortem"]
        except Exception as e:
            self.dead_letters.append({"agent": "postmortem", "reason": str(e)[:200]})
        finally:
            self.state = "FAILED"
        if self.memory:
            self._finalize_agent_stats()
            self.memory.record_run(self.per_agent, 2.0)
            self.memory.set_last_run_quality(self.run_id, 2.0)
        return self.report("FAILED")

    # --------------------------------------------------------------- report
    def report(self, status: str) -> dict:
        stats = self._stats()
        rep = {
            "run_id": self.run_id,
            "task": self.task,
            "status": status,
            "quality": (self.postmortem or {}).get("run_quality", {}).get("score"),
            "brain": getattr(self.brain, "name", "?"),
            "states_visited": [m["payload"].get("state") for m in self.bus.history
                               if m["type"] == "event.state"],
            "draft_rounds": self.draft_round,
            "forced_accept": self.forced,
            "verification_failed": self.verification_failed,
            "stats": stats,
            "per_agent": self.per_agent,
            "incidents": self.incidents,
            "dead_letters": self.dead_letters,
            "self_improvement": {
                "lessons_added": (self.postmortem or {}).get("applied", {}).get("lessons_added", []),
                "policies_now": (self.postmortem or {}).get("applied", {}).get("policies_now", {}),
                "playbook_id": (self.postmortem or {}).get("applied", {}).get("playbook_id"),
            },
            "wall_s": round(time.time() - self.t0, 2),
            "messages": len(self.bus.history),
        }
        if self.draft and status in ("DONE", "DONE_WITH_WARNINGS"):
            rep["artifact"] = os.path.join(
                self.run_dir,
                "final_output.md" if status == "DONE" else "final_output_UNVERIFIED.md")
        with open(os.path.join(self.run_dir, "report.json"), "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=1)
        self.checkpoint()
        self.bus.event("run.end", status=status, quality=rep["quality"],
                       wall_s=rep["wall_s"])
        return rep

    # ----------------------------------------------------------- checkpoint
    def checkpoint(self) -> None:
        snap = {
            "run_id": self.run_id, "task": self.task, "state": self.state,
            "stage_index": self.stage_index, "draft_round": self.draft_round,
            "repair_attempts": self.repair_attempts, "forced": self.forced,
            "plan": self.plan, "evidence": self.evidence, "draft": self.draft,
            "per_agent": self.per_agent, "incidents": self.incidents,
            "dead_letters": self.dead_letters, "t0": self.t0,
        }
        tmp = os.path.join(self.run_dir, "state.json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False)
        os.replace(tmp, os.path.join(self.run_dir, "state.json"))

    @classmethod
    def resume(cls, run_id: str, root: str, brain=None, memory=None,
               subscribe=None) -> dict:
        """Rebuild from the last checkpoint and continue the pending step.
        At-least-once semantics: the interrupted agent call is re-executed."""
        with open(os.path.join(root, "runs", run_id, "state.json"), encoding="utf-8") as f:
            snap = json.load(f)
        orch = cls(snap["task"], root, run_id=run_id, brain=brain,
                   memory=memory, subscribe=subscribe)
        orch.state, orch.plan = snap["state"], snap["plan"]
        orch.stage_index, orch.draft_round = snap["stage_index"], snap["draft_round"]
        orch.evidence, orch.draft = snap["evidence"], snap["draft"]
        orch.repair_attempts, orch.forced = snap["repair_attempts"], snap["forced"]
        orch.per_agent, orch.incidents = snap["per_agent"], snap["incidents"]
        orch.dead_letters = snap["dead_letters"]
        orch.t0 = snap["t0"]
        orch.bus.event("run.resume", from_state=orch.state)
        if orch.state in ("DONE", "FAILED", "POSTMORTEM"):
            if orch.state in ("DONE", "FAILED"):
                return orch.report(orch.state)
        if not orch.plan:
            return orch._step_planning()
        try:
            return orch._dispatch_stage()
        except FatalError as e:
            return orch._fail(e)
