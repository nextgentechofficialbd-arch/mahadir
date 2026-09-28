"""WRITER — produces the artifact (draft) from brief + evidence.

Receives : draft_request  { evidence, task_title, brief, round, revision_notes? }
Decides  : structure, tone, which evidence to cite where; on a revision, how
           to answer each of the critic's issues; on later runs, proactively
           applies lessons it owns in memory.
Emits    : draft  { draft_markdown, citations, applied_lessons, revision_of_round }
"""

from __future__ import annotations

from .base import Agent, ContractViolation, RunContext


class WriterAgent(Agent):
    name = "writer"
    role = ("Write the publish-ready markdown artifact. Cite every evidence id "
            "inline with [F#], include Sources & Citations and an SEO meta "
            "description, keep headings in consistent Title Case, end with a CTA.")
    SCHEMA = {
        "draft_markdown": "str",
        "citations": "list",
        "applied_lessons": "list",
        "revision_of_round": "number",
    }

    def handle(self, msg: dict, ctx: RunContext) -> list[dict]:
        p = msg["payload"]
        draft = self.ask(ctx, {"input": {
            "evidence": p["evidence"],
            "task_title": p.get("task_title", ""),
            "brief": p.get("brief", ""),
            "round": p.get("round", 1),
            "revision_notes": p.get("revision_notes", []),
        }})
        if not draft.get("draft_markdown", "").strip():
            raise ContractViolation("draft_markdown is empty")
        cited = set(draft.get("citations", []))
        available = {f["id"] for f in p["evidence"].get("facts", [])}
        if not available <= cited:
            raise ContractViolation(
                f"citations missing evidence ids: {sorted(available - cited)}")
        return [self.out("orchestrator", "draft", {"draft": draft}, p.get("round", 1))]
