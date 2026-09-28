"""Pluggable LLM brain.

Providers (env vars):
    MAHADIR_PROVIDER = mock | openai | anthropic | compatible   (default: mock)
    MAHADIR_MODEL    = model name                               (default per provider)
    MAHADIR_BASE_URL = API base URL (for openai/compatible/anthropic)
    MAHADIR_API_KEY  = API key

`mock` is a deterministic offline brain: it implements each agent's contract
with real template logic grounded in the actual data flowing through the run,
so the whole system completes hands-off with no API key. Swap providers with
one env var — agents never change.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Optional


class BrainError(Exception):
    """Base class for brain failures."""


class BrainUnavailable(BrainError):
    """Network / auth / provider outage. Transient — worth retrying."""


class BrainParseError(BrainError):
    """Provider answered but output did not satisfy the agent's schema."""


class MockBrain:
    """Deterministic offline brain. Implements each agent's contract with
    template logic that consumes the *actual* request payload, so artifacts
    are grounded in real inputs (task text, evidence ids, lessons learned)."""

    name = "mock"

    def complete(self, agent: str, system: str, request: dict, schema: dict) -> dict:
        time.sleep(0.12)  # simulate latency so traces look realistic
        handler: dict[str, Callable[[dict], dict]] = {
            "planner": self._plan,
            "researcher": self._research,
            "writer": self._write,
            "critic": self._critique,
            "verifier": self._verify,
            "postmortem": self._postmortem,
        }
        if agent not in handler:
            raise BrainParseError(f"mock brain has no contract for agent '{agent}'")
        out = handler[agent](request)
        errors = validate_schema(out, schema)
        if errors:  # never happens by construction; guards future edits
            raise BrainParseError(f"mock output invalid: {errors}")
        return out

    # ------------------------------------------------------------------ utils
    @staticmethod
    def _keywords(text: str, n: int = 6) -> list[str]:
        stop = {
            "a", "an", "the", "for", "and", "or", "of", "in", "on", "to", "with",
            "write", "create", "make", "about", "our", "my", "please", "that",
            "publish", "ready", "post", "blog", "article", "new", "best",
        }
        words = re.findall(r"[a-zA-Z][a-zA-Z&\-]+", text.lower())
        seen, out = set(), []
        for w in sorted(words, key=len, reverse=True):
            if w not in stop and w not in seen and len(w) > 3:
                seen.add(w)
                out.append(w)
            if len(out) >= n:
                break
        return out or ["technology", "service", "dhaka"]

    # --------------------------------------------------------------- planner
    def _plan(self, req: dict) -> dict:
        task = req["input"]["task"]
        title = task["title"]
        kws = self._keywords(title + " " + task.get("brief", ""))
        seeded_from = None
        playbooks = req.get("playbooks") or []
        if playbooks:
            best = max(
                playbooks,
                key=lambda p: len(set(p["fingerprint"]) & set(kws)),
            )
            if len(set(best["fingerprint"]) & set(kws)) >= 2:
                seeded_from = best["id"]
        return {
            "task_title": title,
            "target_agent_pipeline": ["researcher", "writer", "critic", "verifier"],
            "subtasks": [
                {
                    "id": "S1",
                    "stage": "research",
                    "agent": "researcher",
                    "objective": f"Gather verified facts, pricing and differentiators about: {title}",
                    "acceptance_criteria": [
                        ">=5 facts with sources and confidence",
                        "every fact has an evidence id",
                    ],
                },
                {
                    "id": "S2",
                    "stage": "draft",
                    "agent": "writer",
                    "objective": f"Produce a publish-ready markdown article: {title}",
                    "acceptance_criteria": [
                        "cites every evidence id at least once",
                        "has Sources section and SEO meta description",
                        "consistent Title Case headings",
                    ],
                },
                {
                    "id": "S3",
                    "stage": "review",
                    "agent": "critic",
                    "objective": "Score draft against acceptance criteria; reject with fixable issues if needed",
                    "acceptance_criteria": ["score >= 8.5", "no blocking issues"],
                },
                {
                    "id": "S4",
                    "stage": "verify",
                    "agent": "verifier",
                    "objective": "Fact-check draft citations against the evidence pack",
                    "acceptance_criteria": ["all citations resolve", "full evidence coverage"],
                },
            ],
            "definition_of_done": [
                "critic verdict PASS with score >= 8.5",
                "verifier verdict PASS",
                "artifact saved as final_output.md",
            ],
            "seeded_from_playbook": seeded_from,
            "risk_notes": [
                "evidence pack may be thin -> researcher must pad with corroborating sources",
                "first draft historically fails style checks -> pre-apply style lessons",
            ],
        }

    # ------------------------------------------------------------- researcher
    def _research(self, req: dict) -> dict:
        objective = req["input"]["objective"]
        kws = self._keywords(objective, 5)
        topic = " ".join(w.capitalize() for w in kws[:3])
        boost = any("corroborating" in l.get("guidance", "") for l in req.get("lessons", []))
        raw = [
            ("Local demand is rising", f"Search interest for {kws[0]} services in Dhaka grew steadily over the last 12 months.", 0.82),
            ("Certified technicians", "The service team holds vendor certifications for major PC and laptop brands.", 0.90),
            ("On-site turnaround", "Standard on-site diagnostics complete within one business day in the Dhaka metro area.", 0.85),
            ("Transparent pricing", "Published flat-rate pricing covers diagnostics, parts are quoted before replacement.", 0.88),
            ("Warranty backing", "Repairs carry a 30-day service warranty on parts and labour.", 0.86),
        ]
        facts = []
        for i, (claim, detail, conf) in enumerate(raw, 1):
            fact = {
                "id": f"F{i}",
                "claim": claim,
                "detail": detail,
                "source": {"title": f"{topic} — field notes {i}", "url": f"https://example.com/src/{kws[0]}/{i}"},
                "confidence": conf,
            }
            if boost:
                fact["corroborating"] = {"title": f"Independent review set {i}", "url": f"https://example.com/corro/{kws[0]}/{i}"}
            facts.append(fact)
        return {
            "facts": facts,
            "keyword_summary": kws,
            "confidence_floor": round(min(f["confidence"] for f in facts), 2),
            "gaps": ["No long-term reliability dataset — phrased conservatively in draft brief"],
        }

    # ----------------------------------------------------------------- writer
    def _write(self, req: dict) -> dict:
        evidence = req["input"]["evidence"]
        task_title = req["input"].get("task_title", "Our Service")
        brief = req["input"].get("brief", "")
        round_no = req["input"].get("round", 1)
        lessons = req.get("lessons", [])
        facts = evidence["facts"]
        applied: list[str] = []

        # v2 of a revision: apply the critic's specific fix notes.
        revision_notes = req["input"].get("revision_notes") or []
        # v1 of a *later run*: apply lessons learned from previous runs.
        for l in lessons:
            if l.get("target") == "writer":
                applied.append(l["id"])

        lines = [f"# {task_title}", ""]
        lines += [f"Looking for dependable {', '.join(evidence['keyword_summary'][:2])} support? "
                  f"Here is what sets this team apart, with the receipts. [F1]", ""]
        lines += ["## Why Customers Choose Us", ""]
        for f in facts[1:4]:
            lines += [f"- **{f['claim']}** — {f['detail']} [F{facts.index(f) + 1}]", ""]
        lines += ["## Transparent Pricing", "",
                  "| Item | Detail |", "| --- | --- |",
                  f"| Diagnostics | Flat rate, deducted from repair [F4] |",
                  f"| Parts | Quoted before replacement [F4] |",
                  f"| Warranty | 30-day cover on parts and labour [F5] |", ""]
        lines += ["## What Happens Next", "",
                  f"Book an assessment and a certified technician handles the rest — "
                  f"most diagnostics finish within one business day. [F3]", ""]
        if round_no > 1 or revision_notes or applied:
            lines += ["## Sources & Citations", ""]
            for f in facts:
                lines.append(f"- [F{facts.index(f) + 1}] {f['source']['title']} — {f['source']['url']}")
            lines.append("")
        if round_no > 1 or revision_notes or applied:
            lines += ["*Meta description:* " + f"{task_title} — certified technicians, flat-rate pricing and a 30-day warranty. Book on-site service in Dhaka today." , ""]

        draft_md = "\n".join(lines)
        if brief:
            draft_md = draft_md.replace(task_title, task_title, 1)
        return {
            "draft_markdown": draft_md,
            "citations": [f["id"] for f in facts],
            "style": {"tone": "professional-friendly", "audience": "SME and home users in Dhaka"},
            "applied_lessons": applied,
            "revision_of_round": round_no,
        }

    # ----------------------------------------------------------------- critic
    def _critique(self, req: dict) -> dict:
        draft = req["input"]["draft"]
        criteria = req["input"].get("acceptance_criteria", [])
        applied = draft.get("applied_lessons") or []
        relevant = [l for l in req.get("lessons", []) if l.get("target") == "writer"]

        # A draft is acceptable when it carries the sources section + meta
        # description (i.e. the writer pre-applied lessons, or already revised).
        md = draft.get("draft_markdown", "")
        has_sources = "## Sources & Citations" in md
        has_meta = "Meta description" in md
        if relevant and all(l["id"] in applied for l in relevant) and has_sources and has_meta:
            return {"verdict": "PASS", "score": 9.1, "issues": [], "forced": False,
                    "note": "First-pass acceptance: draft pre-applied all known style lessons."}
        if has_sources and has_meta:
            return {"verdict": "PASS", "score": 8.8, "issues": [], "forced": False,
                    "note": "Revised draft meets all acceptance criteria."}
        return {
            "verdict": "FAIL",
            "score": 6.4,
            "forced": False,
            "issues": [
                {"severity": "blocking", "area": "citations",
                 "note": "No 'Sources & Citations' section though facts cite [F#] ids.",
                 "fix_hint": "Append a Sources & Citations section listing every cited evidence id."},
                {"severity": "major", "area": "seo",
                 "note": "Missing SEO meta description.",
                 "fix_hint": "Add a <=160 char meta description line at the end."},
                {"severity": "minor", "area": "structure",
                 "note": "Close with an explicit next-step CTA paragraph.",
                 "fix_hint": "End with booking/contact call to action."},
            ],
            "unmet_criteria": [c for c in criteria[:2]],
        }

    # --------------------------------------------------------------- verifier
    def _verify(self, req: dict) -> dict:
        draft = req["input"]["draft"]
        evidence = req["input"]["evidence"]
        cited = set(draft.get("citations", []))
        available = {f["id"] for f in evidence["facts"]}
        unresolved = sorted(cited - available)
        uncovered = sorted(available - cited)
        md = draft.get("draft_markdown", "")
        missing_inline = [fid for fid in available if f"[{fid}]" not in md]
        ok = not unresolved and not uncovered and not missing_inline
        return {
            "verdict": "PASS" if ok else "FAIL",
            "checked_claims": len(available),
            "unresolved_citations": unresolved,
            "uncovered_facts": uncovered,
            "missing_inline_citations": missing_inline,
            "hallucination_risk": "low" if ok else "high",
            "note": "Every claim resolves to a sourced evidence id." if ok else "Draft cites facts the evidence pack does not contain.",
        }

    # ------------------------------------------------------------- postmortem
    def _postmortem(self, req: dict) -> dict:
        stats = req["input"]["stats"]
        lessons_out: list[dict] = []
        policy_updates: dict = {}

        if stats["critic_rejections"] > 0:
            lessons_out.append({
                "id": "L-writer-firstpass-style",
                "target": "writer",
                "condition": "First draft of any article",
                "guidance": "Always include in v1: a 'Sources & Citations' section listing every cited [F#], "
                            "an SEO meta description line, consistent Title Case headings, and a closing CTA. "
                            "The critic rejects drafts missing these.",
                "evidence": f"{stats['critic_rejections']} first-pass rejection(s) in run {stats['run_id']}",
            })
        if stats["verifier_flags"] > 0:
            lessons_out.append({
                "id": "L-researcher-corroboration",
                "target": "researcher",
                "condition": "Any evidence pack",
                "guidance": "Attach a corroborating source to every fact; verifier flagged unresolved citations before.",
                "evidence": f"{stats['verifier_flags']} verifier flag(s) in run {stats['run_id']}",
            })
        if stats["critic_rejections"] >= stats.get("critic_round_cap", 3):
            policy_updates["critic_rounds"] = stats.get("critic_round_cap", 3) + 1
        if stats["retries"] >= 2:
            policy_updates["retry_budget"] = stats.get("retry_budget", 2) + 1

        return {
            "lessons_to_write": lessons_out,
            "policy_updates": policy_updates,
            "run_quality": {
                "score": max(4.0, 10.0 - 1.5 * stats["critic_rejections"] - 2.0 * stats["verifier_flags"] - stats["retries"]),
                "completed": stats.get("completed", True),
                "forced_accept": stats.get("forced", False),
            },
            "observations": [
                f"messages={stats['messages']}, retries={stats['retries']}, "
                f"critic_rejections={stats['critic_rejections']}, wall={round(stats['wall_s'], 1)}s",
            ],
        }


class RemoteBrain:
    """Real LLM provider (OpenAI / Anthropic / any OpenAI-compatible endpoint).
    Speaks strict JSON: each agent's request carries its output schema; a
    malformed reply raises BrainParseError which the Orchestrator retries with
    corrective feedback."""

    def __init__(self, provider: str, model: str, base_url: str, api_key: str):
        self.provider = provider
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    # ------------------------------------------------------------------ HTTP
    def _post(self, url: str, headers: dict, body: dict, timeout: int = 90) -> dict:
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, headers={**headers, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise BrainUnavailable(f"{self.provider} HTTP {e.code}: {e.read().decode()[:300]}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise BrainUnavailable(f"{self.provider} unreachable: {e}") from e

    def _chat(self, system: str, user: str) -> str:
        if self.provider in ("openai", "compatible"):
            base = self.base_url or "https://api.openai.com/v1"
            out = self._post(
                f"{base}/chat/completions",
                {"Authorization": f"Bearer {self.api_key}"},
                {"model": self.model,
                 "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                 "temperature": 0.2},
            )
            return out["choices"][0]["message"]["content"]
        if self.provider == "anthropic":
            base = self.base_url or "https://api.anthropic.com"
            out = self._post(
                f"{base}/v1/messages",
                {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                {"model": self.model, "max_tokens": 2048, "temperature": 0.2,
                 "system": system, "messages": [{"role": "user", "content": user}]},
            )
            return "".join(b.get("text", "") for b in out.get("content", []))
        raise BrainUnavailable(f"unknown provider '{self.provider}'")

    # --------------------------------------------------------------- contract
    def complete(self, agent: str, system: str, request: dict, schema: dict) -> dict:
        raw = self._chat(system, json.dumps(request, ensure_ascii=False, indent=1))
        try:
            out = extract_json(raw)
        except ValueError as e:
            raise BrainParseError(f"could not parse JSON from {self.provider}: {e}; raw[:400]={raw[:400]!r}") from e
        errors = validate_schema(out, schema)
        if errors:
            raise BrainParseError(f"{agent} output failed schema: {errors}")
        return out


def extract_json(text: str) -> dict:
    """Pull the first top-level JSON object out of an LLM reply."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fence:
        return json.loads(fence.group(1))
    depth, start = 0, None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                return json.loads(text[start:i + 1])
    raise ValueError("no JSON object found")


def validate_schema(obj: Any, schema: dict, path: str = "") -> list[str]:
    """schema: {key: 'dict'|'list'|'str'|'number'|'bool'|'any'|{...nested}}"""
    errs: list[str] = []
    if not isinstance(obj, dict):
        return [f"{path or 'root'}: expected object, got {type(obj).__name__}"]
    for key, kind in schema.items():
        full = f"{path}.{key}" if path else key
        if key not in obj:
            errs.append(f"{full}: missing")
            continue
        v = obj[key]
        if kind == "any":
            continue
        if isinstance(kind, dict):
            errs += validate_schema(v, kind, full)
            continue
        want = {"dict": dict, "list": list, "str": str, "number": (int, float), "bool": bool}[kind]
        if kind == "bool" and not isinstance(v, bool):
            errs.append(f"{full}: expected bool")
        elif kind != "bool" and not isinstance(v, want):
            errs.append(f"{full}: expected {kind}, got {type(v).__name__}")
    return errs


def make_brain(provider: Optional[str] = None, **overrides) -> MockBrain | RemoteBrain:
    p = (provider or os.environ.get("MAHADIR_PROVIDER", "mock")).lower()
    if p == "mock":
        return MockBrain()
    defaults = {"openai": ("gpt-4o-mini", "https://api.openai.com/v1"),
                "anthropic": ("claude-3-5-sonnet-latest", "https://api.anthropic.com"),
                "compatible": ("llama3.1", "http://localhost:11434/v1")}
    model = overrides.get("model") or os.environ.get("MAHADIR_MODEL") or defaults[p][0]
    base = overrides.get("base_url") or os.environ.get("MAHADIR_BASE_URL") or defaults[p][1]
    key = overrides.get("api_key") or os.environ.get("MAHADIR_API_KEY", "")
    return RemoteBrain(p, model, base, key)
