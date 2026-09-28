# A-to-Z Guide — run the Mahadir multi-agent system

Zero dependencies. If you have Python 3.10 or newer, you can run everything
below. Total time from nothing to your first run: **about 3 minutes**.

---

## WINDOWS 10/11 QUICK START (start here if you're on Windows)

On Windows the command is `python`, **never** `python3`, and you don't need Git.

1. **Install Python** — go to https://www.python.org/downloads/ , click the big
   yellow **Download Python** button, run the installer, and **tick the box
   "Add python.exe to PATH"** at the bottom of the first screen. Install, then
   close ALL Command Prompt windows.
2. **Download the project ZIP** — paste this in your browser:
   `https://github.com/nextgentechofficialbd-arch/mahadir/archive/refs/heads/arena/01a0e893-mahadir.zip`
   Right-click the downloaded ZIP → **Extract All** → extract to `C:\Users\rahma\`.
   You get a folder like `C:\Users\rahma\mahadir-arena-01a0e893-mahadir\`.
3. **Open a NEW Command Prompt** and type:
   ```bat
   cd C:\Users\rahma\mahadir-arena-01a0e893-mahadir\agent-system
   python --version
   python run.py
   ```
4. **Dashboard**: `python dashboard.py` → open http://localhost:8000 in the browser.
5. If `python --version` still says "Python was not found": Windows Settings →
   Apps → Advanced app settings → **App execution aliases** → turn OFF both
   `python.exe` and `python3.exe`, open a fresh Command Prompt, try again.

Paste commands as plain text — if a URL pastes as `[text](url)` markdown,
cmd cannot read it; type browser URLs in the browser's address bar instead.

---

## STEP 1 — Install Python (skip if you have it)

Check: open a terminal (Windows: PowerShell; Mac/Linux: Terminal) and type:

```bash
python3 --version     # Mac/Linux      (or: python --version on Windows)
```

- If you see `Python 3.10+` → done.
- If not: install from https://www.python.org/downloads/
  (Windows: tick **"Add Python to PATH"** during install).

## STEP 2 — Get the code

```bash
git clone -b arena/01a0e893-mahadir https://github.com/nextgentechofficialbd-arch/mahadir.git
cd mahadir/agent-system
```

(Once the pull request is merged to `main`, plain `git clone https://github.com/nextgentechofficialbd-arch/mahadir.git` is enough.)

No Git? Download the ZIP on GitHub → green **Code** button → **Download ZIP**,
unzip, then `cd` into `mahadir/agent-system`.

Everything now happens inside `mahadir/agent-system/`.

## STEP 3 — First run (offline, no API key, nothing to pay)

```bash
python3 run.py
```

You will see a live colored trace, something like:

```
Mahadir MAS brain=mock  task='Global Computer & Technology: ...'
15:21:34 orchestrator  · event.run.start
15:21:34     planner  🗺 plan  stages=['research','draft','review','verify']
15:21:34 researcher  📚 evidence  facts=5 floor=0.82
15:21:34      writer  ✍ draft (r1)
15:21:35      critic  ⚖ verdict (r1)  FAIL score=6.4  3 issue(s)
15:21:35      writer  ✍ draft (r2)            <- revised after the rejection
15:21:35      critic  ⚖ verdict (r2)  PASS score=8.8
15:21:35   verifier  🔍 verification PASS  claims=5
15:21:35 postmortem  🧠 postmortem_report  lessons+1 playbook=PB-001
```

That's the whole pipeline completing hands-off: plan → research → draft →
rejected → revised → verified → lessons saved. ~1 second.

**Where is my output?**

```
runs/<run_id>/final_output.md     <- the finished artifact (open it!)
runs/<run_id>/report.json         <- full run report: stats, incidents, lessons
runs/<run_id>/trace.jsonl         <- every message between agents
memory/                           <- what the system learned (persists)
```

## STEP 4 — Run it again and watch it improve

```bash
python3 run.py "Global Computer & Technology: custom gaming PC builds"
```

Notice: this time the writer **passes on round 1** — it remembered the
critic's rejection from Step 3 (stored in `memory/lessons.json`) and applied
it before writing. Fewer messages, quality 10/10.

Each new run gets smarter: lessons accumulate, successful plans are kept as
reusable playbooks, and per-agent scorecards build up.

## STEP 5 — Watch error handling (chaos mode)

```bash
python3 run.py "Announce our laptop screen replacement service" --chaos
```

`--chaos` injects faults: a network outage on every agent + malformed AI
replies. You'll see `retrying in 0.5s` and `feedback bounce` events, then the
run completes anyway — and afterwards the system **raises its own retry
budget** for next time (check `memory/policies.json`).

## STEP 6 — Open the dashboard (visual control room)

Open a **second terminal**, same folder:

```bash
python3 dashboard.py
```

Open http://localhost:8000 in your browser. You get:
- run list with status + quality
- click a run → pipeline strip, every handoff in the message trace
- agent scorecards, lessons learned, self-tuned policies, quality trend
- the page refreshes itself every 2 s; start a run in the first terminal and
  watch it appear live.

Stop the dashboard with `Ctrl+C` when done.

## STEP 7 — Use your own task (three ways)

```bash
# 1. one-liner
python3 run.py "Write a service page for our CCTV installation package"

# 2. custom title + brief baked in (edit DEFAULT_TASK at the top of run.py)

# 3. full control via a JSON file
echo '{
  "title": "Annual IT maintenance contract for offices in Dhaka",
  "brief": "Landing page copy. Professional tone. Emphasize 24/7 support.",
  "constraints": ["cite every claim", "no unverifiable uptime promises"]
}' > mytask.json
python3 run.py --task-file mytask.json
```

Rules of thumb: keep the title specific; the brief is where tone/audience go;
put hard rules in constraints.

## STEP 8 — Switch on a real AI brain (optional but recommended)

The offline `mock` brain is a deterministic simulator so you can test the
plumbing for free. For genuinely written content, connect a real model —
**no code changes, one environment variable**:

**Mac / Linux:**
```bash
export MAHADIR_PROVIDER=openai
export MAHADIR_API_KEY="sk-..."          # from platform.openai.com
python3 run.py "your task"
```

**Windows PowerShell:**
```powershell
$env:MAHADIR_PROVIDER="openai"
$env:MAHADIR_API_KEY="sk-..."
python3 run.py "your task"
```

Other brains — same idea:

| Provider | Variables |
|---|---|
| OpenAI (GPT-4o-mini default) | `MAHADIR_PROVIDER=openai` + `MAHADIR_API_KEY` |
| Anthropic (Claude) | `MAHADIR_PROVIDER=anthropic` + `MAHADIR_API_KEY` |
| Local, free (Ollama) | install Ollama → `ollama pull llama3.1` → `MAHADIR_PROVIDER=compatible MAHADIR_BASE_URL=http://localhost:11434/v1 MAHADIR_MODEL=llama3.1` |
| Any OpenAI-compatible API (Groq, DeepSeek, OpenRouter…) | `MAHADIR_PROVIDER=compatible` + `MAHADIR_BASE_URL=...` + `MAHADIR_API_KEY=...` + `MAHADIR_MODEL=...` |

Keys are read from the environment only — never hardcoded, never stored in
the repo. Real-API failures (rate limits, timeouts, malformed JSON) flow
through the same retry/feedback ladder you saw in chaos mode.

## STEP 9 — Interrupted run? Resume it

Every run checkpoints after every step into `runs/<run_id>/state.json`:

```bash
python3 run.py --resume run-4c7683d4     # use your own run id from runs/
```

It rebuilds to the exact point of interruption and continues — a crashed
laptop, `Ctrl+C`, or an API outage never wastes the work already done.

## STEP 10 — Run the test suite (whenever you change code)

```bash
python3 -m unittest discover -s tests
```

8 tests: full pipeline, cross-run improvement, graceful budget failure,
retry recovery, resume, schema validation, policy bounds. All should pass.

---

## Daily usage cheat sheet

```bash
cd mahadir/agent-system
python3 run.py "task..."              # do a task
python3 dashboard.py                  # watch visually (2nd terminal)
python3 run.py --resume run-xxxx      # recover an interrupted run
cat runs/<id>/final_output.md         # read the artifact
cat memory/lessons.json               # what the system has learned
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python3: command not found` (Windows) | use `python` instead of `python3` |
| `No module named mahadir` | you must run commands from inside `mahadir/agent-system/` |
| Dashboard port busy | `python3 dashboard.py 8080` then open http://localhost:8080 |
| `Unknown provider` | `MAHADIR_PROVIDER` must be `mock`, `openai`, `anthropic` or `compatible` |
| OpenAI `401` | API key wrong/expired — re-set `MAHADIR_API_KEY` in the **same** terminal you run from |
| Status `DONE_WITH_WARNINGS` | the verifier could not fully verify — read the note in `report.json`; artifact saved as `final_output_UNVERIFIED.md` on purpose |
| Status `FAILED` | read `report.json` → `dead_letters` + `incidents` for the exact reason; the postmortem still learned from it — just run again |
| Want a clean slate | delete `memory/` (forgets lessons) and `runs/` (deletes history) |

## What "self-improving" means here (30-second version)

After every run — success or crash — the **Postmortem** agent writes into
`memory/`: lessons ("critic rejects drafts without a Sources section"),
playbooks (successful plans for reuse), scorecards (per-agent first-pass
yield), and policy tuning (retry budgets, review-round caps — always clamped
to safe bounds). The next run reads all of it at kickoff. That's why Step 4
passed on round 1 while Step 3 needed round 2.
