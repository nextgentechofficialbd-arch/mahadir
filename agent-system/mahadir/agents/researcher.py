"""RESEARCHER — gathers the evidence pack a draft must be grounded in.

Receives : subtask  { subtask:{objective, acceptance_criteria}, task_title }
Decides  : what facts matter, which sources are credible, whether evidence
           is strong enough (policy: evidence_min) or a corroborating source
           is needed per fact (learned lesson).
Emits    : evidence  { facts:[{id,claim,detail,source,confidence}], gaps }
"""

from __future__ import annotations

from .base import Agent, ContractViolation, RunContext


class ResearcherAgent(Agent):
    name = "researcher"
    role = ("Collect a sourced, confidence-scored evidence pack for the draft. "
            "Every fact needs an evidence id, a source and a confidence value; "
            "add corroborating sources where trust matters.")
    SCHEMA = {
        "facts": "list",
        "keyword_summary": "list",
        "confidence_floor": "number",
        "gaps": "list",
    }

    def handle(self, msg: dict, ctx: RunContext) -> list[dict]:
        sub = msg["payload"]["subtask"]
        pack = self.ask(ctx, {"input": {"objective": sub["objective"],
                                        "task_title": msg["payload"].get("task_title", "")}})
        facts = pack.get("facts", [])
        if len(facts) < ctx.policies.get("evidence_min", 3):
            raise ContractViolation(
                f"evidence pack too thin: {len(facts)} facts < policy evidence_min="
                f"{ctx.policies.get('evidence_min', 3)}. Return at least that many sourced facts.")
        if any(not f.get("id") or not f.get("source") for f in facts):
            raise ContractViolation("every fact needs an id and a source")
        return [self.out("orchestrator", "evidence",
                         {"evidence": pack, "subtask": sub["id"]})]
