"""POSTMORTEM — the self-improvement agent. Runs after every run, success or
crash, and writes what it learned back into memory.

Receives : postmortem_request  { stats, plan, run_meta }
Decides  : which failure patterns are worth a lesson, which policies to tune
           (bounded!), whether the successful plan deserves a reusable playbook.
Writes   : memory.lessons / memory.policies / memory.playbooks / scorecards
Emits    : postmortem_report (what changed, so the run report can show it)
"""

from __future__ import annotations

from .base import Agent, RunContext


class PostmortemAgent(Agent):
    name = "postmortem"
    role = ("Analyse the run trace statistics. Extract durable lessons (id, "
            "target agent, condition, guidance) from recurring failures. "
            "Propose small bounded policy updates. If the plan succeeded, keep "
            "it as a playbook for future similar tasks.")
    SCHEMA = {"lessons_to_write": "list", "policy_updates": "dict",
              "run_quality": "dict", "observations": "list"}

    def handle(self, msg: dict, ctx: RunContext) -> list[dict]:
        p = msg["payload"]
        report = self.ask(ctx, {"input": {"stats": p["stats"], "plan": p.get("plan", {}),
                                          "run_meta": p.get("run_meta", {})}})
        # Apply what it decided — postmortem is the only agent with write
        # access to memory; policy updates are clamped by Memory.update_policies.
        added = ctx.memory.add_lessons(report.get("lessons_to_write", []))
        new_policies = ctx.memory.update_policies(report.get("policy_updates", {}))
        playbook_id = None
        if p["stats"].get("completed") and p.get("plan"):
            import re
            title = p.get("run_meta", {}).get("task_title", "")
            fingerprint = [w for w in re.findall(r"[a-zA-Z][a-zA-Z&\-]+", title.lower()) if len(w) > 3][:6]
            playbook_id = ctx.memory.add_playbook(fingerprint, p["plan"], p["stats"]["run_id"])
        report["applied"] = {"lessons_added": added,
                             "policies_now": new_policies,
                             "playbook_id": playbook_id}
        return [self.out("orchestrator", "postmortem_report", {"postmortem": report})]
