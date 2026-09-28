# Mahadir MAS — a self-improving multi-agent system

A hands-off pipeline where specialist agents hand work to each other under an
orchestrator that enforces budgets, recovers from errors, and **writes what it
learned into persistent memory** so the next run is measurably better.

Runs fully offline with a deterministic mock brain (no API key), or point it at
OpenAI / Anthropic / any OpenAI-compatible endpoint with one env var.

```bash
python3 run.py                     # demo task, end to end, ~1s
python3 run.py "your task here" --chaos   # same, with injected faults -> watch retries
python3 run.py --resume run-xxxx   # continue a run from its last checkpoint
python3 dashboard.py               # http://localhost:8000 — control room UI
python3 -m unittest discover -s tests
```

Use a real LLM (agents and prompts are unchanged):

```bash
MAHADIR_PROVIDER=openai     MAHADIR_API_KEY=sk-...  python3 run.py "..."
MAHADIR_PROVIDER=anthropic  MAHADIR_API_KEY=sk-...  python3 run.py "..."
MAHADIR_PROVIDER=compatible MAHADIR_BASE_URL=http://localhost:11434/v1 MAHADIR_MODEL=llama3.1 python3 run.py "..."
```

---

## 1. Architecture

No agent ever talks to another agent directly. Every exchange is a message
envelope routed by the Orchestrator, recorded in an append-only trace
(`runs/<run_id>/trace.jsonl`) — that is what makes handoffs auditable, runs
resumable, and the dashboard live.

```
                         ┌─────────────────────────────────────────────┐
                         │                 ORCHESTRATOR                │
                         │  state machine · budgets · retries · DLQ    │
                         │  circuit breaker · checkpoints · memory     │
                         └─────────────────────────────────────────────┘
                            │ kickoff            ▲ plan/evidence/draft/
                            ▼                    │ verdict/verification/report
 ┌──────────┐  subtask  ┌──────────┐  evidence ┌────────┐  draft   ┌────────┐
 │ PLANNER  │──────────▶│RESEARCHER│──────────▶│ WRITER │─────────▶│ CRITIC │──┐
 └──────────┘           └──────────┘           └────────┘          └────────┘  │
      ▲                     │                        ▲                        │ FAIL
      │ playbook            │                        │ revision notes         │ (round < cap)
      │ (memory)            │                        └────────────────────────┘
      │                     ▼                                                 │ PASS
      │               (facts, ids, sources)                                   ▼
 ┌────────────┐  report  ┌────────────┐   verify    ┌──────────┐◀──────────────┘
 │ POSTMORTEM │◀─────────│ ORCHESTR.  │◀────────────│ VERIFIER │   draft+evidence
 └────────────┘          └────────────┘             └──────────┘
      │ writes lessons, scorecards, playbook, tuned policies
      ▼
   memory/  (lessons.json · scorecards.json · playbooks.json · policies.json)
```

Pipeline states: `PLANNING → RESEARCHING → PRODUCING ⇄ REVIEWING → VERIFYING → POSTMORTEM → DONE`
(`FAILED` at any point, still via POSTMORTEM — crashes are learning input too).

---

## 2. Agent contracts — receives / decides / emits

Each agent is a pure `inbox message → outbox messages` function with a strict
output schema. The Orchestrator validates structure and enforces policy before
anything moves forward.

### Planner — *"what does done look like?"*
| | |
|---|---|
| **Receives** | `task.kickoff`: `{task:{title, brief, constraints}}` + all stored playbooks |
| **Decides** | how to decompose the task into the 4 staged subtasks (research→draft→review→verify), measurable acceptance criteria per stage, the definition-of-done, and whether a past playbook is close enough to seed the plan |
| **Emits** | `plan`: `{subtasks[4] with objective+acceptance_criteria, definition_of_done, risk_notes, seeded_from_playbook}` |
| **Gate** | orchestrator rejects plans whose stages aren't exactly the canonical 4 — bounces back with corrective feedback |

### Researcher — *"what is true?"*
| | |
|---|---|
| **Receives** | `subtask`: the research objective + acceptance criteria |
| **Decides** | which facts matter, which sources are credible, confidence per fact, whether a corroborating source is needed (a lesson it owns tells it when) |
| **Emits** | `evidence`: `{facts:[{id F1..Fn, claim, detail, source, confidence}], keyword_summary, confidence_floor, gaps}` |
| **Gate** | pack must contain ≥ `policies.evidence_min` sourced facts, every fact needs id+source — else bounced once with feedback |

### Writer — *"produce the artifact"*
| | |
|---|---|
| **Receives** | `draft_request`: `{evidence, task_title, brief, round, revision_notes[]}` |
| **Decides** | structure, tone, where each `[F#]` citation goes; on a revision, how to answer each of the critic's issues; on later runs, **pre-applies the lessons it owns** so v1 is already right |
| **Emits** | `draft`: `{draft_markdown, citations, applied_lessons, revision_of_round}` |
| **Gate** | citations must cover every evidence id; markdown may not be empty |

### Critic — the quality gate
| | |
|---|---|
| **Receives** | `review_request`: `{draft, acceptance_criteria, round, task_title}` |
| **Decides** | PASS/FAIL against the planner's criteria, a 0–10 score, and on FAIL the exact severity-ranked issues with fix hints |
| **Emits** | `verdict`: `{verdict, score, issues[], forced}` |
| **Loop** | FAIL → orchestrator routes issues back to Writer (round+1) until `policies.critic_rounds`; at the cap it **force-accepts, flagged** — the run degrades, it never deadlocks |

### Verifier — the fact-check gate
| | |
|---|---|
| **Receives** | `verify_request`: `{draft, evidence}` |
| **Decides** | does every citation resolve, is every fact covered and cited inline; hallucination risk |
| **Emits** | `verification`: `{verdict, unresolved_citations, uncovered_facts, checked_claims}` |
| **Loop** | FAIL → one citation-repair cycle back through Writer→Critic; second FAIL → run ends `DONE_WITH_WARNINGS`, artifact saved as `final_output_UNVERIFIED.md` — **unverified content is never silently shipped** |

### Postmortem — the self-improvement agent
| | |
|---|---|
| **Receives** | `postmortem_request`: real run statistics — messages, retries, critic rejections, verifier flags, wall time, completion status |
| **Decides** | which failure patterns deserve a durable lesson, which policies to tune, whether the successful plan becomes a reusable playbook |
| **Writes** | `memory/lessons.json`, `memory/policies.json` (clamped), `memory/playbooks.json`, `memory/scorecards.json` |
| **Emits** | `postmortem_report`: exactly what changed — shown in the run report and dashboard |

### Orchestrator — the engine (not an LLM agent)
Receives the task; decides execution order, when to retry/bounce/force-accept/abort, when budgets are exhausted; owns routing, the checkpoint, the dead-letter log, and the final `report.json`. Guarantees: bounded work, auditable handoffs, resumability, and *a postmortem after every run*.

---

## 3. Error handling

Four failure classes, each with its own ladder — the goal is that a broken
model call, a thin evidence pack, or a dead network degrade the run gracefully
instead of killing it or looping forever.

| Failure class | Example | Response |
|---|---|---|
| **Transient** (`BrainUnavailable`) | network down, provider 5xx, rate limit | exponential backoff retry `0.5s→1s→2s→…` (cap 5s), up to `policies.retry_budget`, then escalate |
| **Schema** (`BrainParseError`) | model returned prose instead of JSON, missing fields | immediate retry **with the parse error injected into the agent's prompt** ("your previous reply was rejected, fix it"), up to budget |
| **Policy** (`ContractViolation`) | evidence pack below `evidence_min`, missing citations | deterministic post-check; bounce to the same agent once with the violation spelled out |
| **Fatal** (`FatalError`) | budget exhausted, retry budget burned, breaker tripped | graceful stop: dead-letter entry, **postmortem still runs**, report says exactly where and why |

Additional protections:

- **Budgets** — hard caps on wall-clock (`max_seconds`), message steps (`max_steps`); enforced before every agent call.
- **Circuit breaker** — 3 consecutive failures trips an agent; the run stops instead of burning budget on a dead agent.
- **Force-accept with flags** — if the Critic rejects up to the round cap, the best draft ships *clearly marked* (`forced: true`, warning in the report/dashboard), and the postmortem raises the round cap for next time.
- **Unverified ≠ shipped** — a Verifier FAIL after the repair cycle produces `final_output_UNVERIFIED.md` and status `DONE_WITH_WARNINGS`.
- **Dead-letter log** — every abandoned message lands in `report.json: dead_letters` with its reason.
- **Checkpoints** — `state.json` is rewritten after every transition; `--resume <run_id>` rebuilds and continues (at-least-once: the interrupted agent call is re-executed).
- **Chaos testing** — `run.py --chaos` wraps the brain in a deterministic fault injector (transient outage on every agent + malformed JSON on planner/writer) so you can watch the whole ladder recover live. A chaos run completed with **8 incidents, 0 failures** in the demo.

---

## 4. Self-improvement over time

Every run reads `memory/` at kickoff and the Postmortem writes it back after
the run — success **or** crash. Concretely, four feedback loops:

1. **Lessons → prompts.** Failure patterns become lessons
   `{id, target_agent, condition, guidance, evidence, times_seen}`. On the next
   run, each agent's system prompt ends with *"KNOWN PITFALLS learned from
   previous runs"* — its own lessons only. Demo run 1: the Critic rejected the
   first draft (no Sources section, no meta description); the Postmortem wrote
   lesson `L-writer-firstpass-style`. Demo run 2: the Writer **pre-applied it
   and passed on round 1** (quality 8.5 → 10.0, messages 29 → 22).
2. **Scorecards → trend.** Per-agent `first_pass_yield` (did the agent do its
   whole job in one clean call?), latency, tokens — rolling 20-run history,
   visualized in the dashboard.
3. **Playbooks → faster planning.** Successful plans are stored with a keyword
   fingerprint; the next Planner retrieves the most similar playbook and seeds
   from it (`seeded_from_playbook: PB-xxx`).
4. **Policy tuning → bounded.** The Postmortem may adjust `critic_rounds`,
   `retry_budget`, `evidence_min`, `verify_attempts` — every knob is **clamped
   to hard bounds** (`BOUNDS` in `memory.py`), unknown keys rejected, so the
   system can never tune itself into instability. Demo: after a chaos run with
   8 incidents it raised `retry_budget` 2 → 3.

```
run N:  agents read memory ─▶ run ─▶ trace ─▶ postmortem ─▶ memory'
run N+1: agents read memory' ─▶ fewer rejections, fewer retries, higher quality
```

Nothing is tuned by hand: quality pressure (critic/verifier verdicts, retries)
is the only input, and clamps are the only guardrails.

---

## 5. Layout

```
agent-system/
├── run.py                 CLI: live colored trace + run report
├── dashboard.py           stdlib web server: /api/overview /api/run/<id> /api/memory
├── dashboard.html         control-room UI (pipeline, trace, scorecards, lessons)
├── mahadir/
│   ├── llm.py             MockBrain + RemoteBrain (openai/anthropic/compatible) + chaos
│   ├── memory.py          persistent memory, bounded policy tuning
│   ├── bus.py             message envelopes, trace JSONL, circuit breaker
│   ├── orchestrator.py    state machine, error ladder, budgets, checkpoints, report
│   └── agents/            base + planner, researcher, writer, critic, verifier, postmortem
├── tests/test_core.py     8 tests: full run, improvement across runs, graceful
│                          budget failure, retry recovery, resume, schema, bounds
├── runs/<run_id>/         trace.jsonl · state.json · report.json · final_output.md
└── memory/                lessons · playbooks · scorecards · policies   (runtime)
```

### Extending
- **New agent**: subclass `Agent` (name, role, SCHEMA, `handle`), register in
  `agents/__init__.py`, add a stage handling it in the orchestrator. Lessons
  start flowing to it automatically via `lessons_for(name)`.
- **New topology**: the orchestrator executes whatever staged plan the Planner
  emits, as long as it declares stage kinds the orchestrator knows how to route
  (`research/draft/review/verify` today — add routing for more).
- **Real model**: set provider env vars; every agent's prompt already carries
  its contract + schema + lessons, and malformed replies trigger the
  feedback-retry ladder automatically.
