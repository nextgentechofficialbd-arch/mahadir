"""CRITIC — quality gate between Writer and Verifier.

Receives : review_request  { draft, acceptance_criteria, round, task_title }
Decides  : PASS / FAIL against the planner's acceptance criteria; on FAIL,
           the exact severity-ranked issues + fix hints to send back.
Emits    : verdict  { verdict, score, issues[], forced }
           (orchestrator loops Writer<->Critic up to policy critic_rounds;
            at the cap it force-accepts the best draft and marks it `forced`
            so the run degrades instead of deadlocking — and the postmortem
            raises the cap for next time.)
"""

from __future__ import annotations

from .base import Agent, ContractViolation, RunContext


class CriticAgent(Agent):
    name = "critic"
    role = ("Act as a strict editor. Score the draft 0-10 against the "
            "acceptance criteria. PASS only if no blocking/major issues remain. "
            "On FAIL, give concrete, fixable issues with fix hints.")
    SCHEMA = {"verdict": "str", "score": "number", "issues": "list", "forced": "bool"}

    def handle(self, msg: dict, ctx: RunContext) -> list[dict]:
        p = msg["payload"]
        verdict = self.ask(ctx, {"input": {
            "draft": p["draft"],
            "acceptance_criteria": p.get("acceptance_criteria", []),
            "round": p.get("round", 1),
            "task_title": p.get("task_title", ""),
        }})
        v = str(verdict.get("verdict", "")).upper()
        if v not in ("PASS", "FAIL"):
            raise ContractViolation(f"verdict must be PASS or FAIL, got {v!r}")
        verdict["verdict"] = v
        return [self.out("orchestrator", "verdict", {"verdict": verdict}, p.get("round", 1))]
