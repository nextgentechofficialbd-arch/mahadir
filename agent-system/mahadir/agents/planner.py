"""PLANNER — turns a raw task into an executable plan.

Receives : task.kickoff  { task:{title, brief, constraints}, playbooks:[...] }
Decides  : how to decompose the task into staged subtasks, acceptance
           criteria, definition of done; whether to seed from a past playbook.
Emits    : plan  { subtasks[4], definition_of_done, risk_notes }
"""

from __future__ import annotations

from .base import Agent, ContractViolation, RunContext


class PlannerAgent(Agent):
    name = "planner"
    role = ("Decompose the user task into a staged plan (research -> draft -> "
            "review -> verify) with measurable acceptance criteria. Reuse the "
            "closest past playbook when one matches.")
    SCHEMA = {
        "task_title": "str",
        "subtasks": "list",
        "definition_of_done": "list",
        "seeded_from_playbook": "any",
        "risk_notes": "list",
    }
    VALID_STAGES = ("research", "draft", "review", "verify")

    def handle(self, msg: dict, ctx: RunContext) -> list[dict]:
        plan = self.ask(ctx, {
            "input": {"task": ctx.task},
            "playbooks": ctx.memory.playbooks if ctx.memory else [],
        })
        # Deterministic gate: the orchestrator only accepts executable plans.
        stages = [s.get("stage") for s in plan.get("subtasks", [])]
        if stages != list(self.VALID_STAGES):
            raise ContractViolation(
                f"plan stages must be exactly {list(self.VALID_STAGES)}, got {stages}")
        for s in plan["subtasks"]:
            if not s.get("objective") or not s.get("acceptance_criteria"):
                raise ContractViolation(f"subtask {s.get('id')} missing objective/criteria")
        return [self.out("orchestrator", "plan", {"plan": plan})]
