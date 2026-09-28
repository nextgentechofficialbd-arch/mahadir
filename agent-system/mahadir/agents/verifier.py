"""VERIFIER — fact-check gate before anything is called 'done'.

Receives : verify_request  { draft, evidence }
Decides  : does every citation resolve to the evidence pack, is every fact
           covered and cited inline; PASS / FAIL with the exact defects.
Emits    : verification  { verdict, unresolved_citations, uncovered_facts, ... }
           (FAIL sends the draft back to Writer once for a citation repair
            cycle; a second FAIL finishes the run flagged `verification_failed`
            so the artifact is clearly marked untrusted, never silently shipped.)
"""

from __future__ import annotations

from .base import Agent, ContractViolation, RunContext


class VerifierAgent(Agent):
    name = "verifier"
    role = ("Fact-check the draft against the evidence pack. Be mechanical: "
            "resolve every [F#] citation, require full coverage, flag anything "
            "that cannot be traced to a source.")
    SCHEMA = {"verdict": "str",
              "unresolved_citations": "list",
              "uncovered_facts": "list",
              "hallucination_risk": "str"}

    def handle(self, msg: dict, ctx: RunContext) -> list[dict]:
        p = msg["payload"]
        check = self.ask(ctx, {"input": {"draft": p["draft"], "evidence": p["evidence"]}})
        v = str(check.get("verdict", "")).upper()
        if v not in ("PASS", "FAIL"):
            raise ContractViolation(f"verdict must be PASS or FAIL, got {v!r}")
        check["verdict"] = v
        return [self.out("orchestrator", "verification", {"verification": check})]
