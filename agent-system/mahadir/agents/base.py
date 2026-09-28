"""Agent base: every agent is a pure message->messages function with a strict
output schema, plus a role prompt that carries its learned lessons."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


class ContractViolation(Exception):
    """Deterministic post-check failed (e.g. evidence pack too thin).
    Bounces back to the same agent once with corrective feedback."""


class TransientError(Exception):
    """Retryable failure (network, rate limit, provider 5xx)."""


class FatalError(Exception):
    """Unrecoverable failure — abort the run gracefully."""


@dataclass
class RunContext:
    """Everything an agent may touch during a run. Agents never talk to each
    other directly — they only see their inbox and emit to the orchestrator."""
    brain: Any
    memory: Any                    # Memory
    task: dict
    policies: dict
    parse_feedback: Optional[str] = None       # corrective feedback after a schema violation
    contract_feedback: Optional[str] = None    # corrective feedback after a policy violation


class Agent:
    name: str = "agent"
    role: str = ""
    SCHEMA: dict = {}              # JSON-schema-lite for the brain's reply

    # ------------------------------------------------------------------ prompt
    def system_prompt(self, ctx: RunContext) -> str:
        lessons = ctx.memory.lessons_for(self.name) if ctx.memory else []
        lines = [
            f"You are the {self.name.upper()} agent in a multi-agent pipeline.",
            f"ROLE: {self.role}",
            "OUTPUT: reply with a single JSON object and nothing else. It must satisfy this schema:",
            f"{self.SCHEMA}",
        ]
        if ctx.parse_feedback:
            lines.append(f"Your previous reply was rejected. Fix it: {ctx.parse_feedback}")
        if ctx.contract_feedback:
            lines.append(f"Policy violation to fix: {ctx.contract_feedback}")
        if lessons:
            lines.append("KNOWN PITFALLS learned from previous runs (apply proactively):")
            lines += [f"- [{l['id']}] {l['condition']}: {l['guidance']}" for l in lessons]
        return "\n".join(lines)

    # ------------------------------------------------------------------- brain
    def ask(self, ctx: RunContext, request: dict) -> dict:
        request = {**request, "lessons": ctx.memory.lessons_for(self.name) if ctx.memory else [],
                   "policies": ctx.policies}
        return ctx.brain.complete(self.name, self.system_prompt(ctx), request, self.SCHEMA)

    # ------------------------------------------------------------------ handle
    def handle(self, msg: dict, ctx: RunContext) -> list[dict]:
        """Receive one inbox message, decide, emit 0..n messages."""
        raise NotImplementedError

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def out(to: str, mtype: str, payload: dict, round_no: int = 0, **meta) -> dict:
        return {"from": "agent", "to": to, "type": mtype,
                "payload": payload, "round": round_no, "meta": meta}
