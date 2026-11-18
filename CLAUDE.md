# Athar: notes for Claude Code

Athar is the working title of the school product built on Meska Brain (the challenge entry). The Python
package is still `meska_brain` and the command is still `meska`. The product name shown on the page is one
setting: `MESKA_PRODUCT_NAME`.

Read this first, then `README.md`, `ARCHITECTURE.md` and `EVALS.md`. `docs/meska-brain-readme.md` is the
README of the challenge entry, kept for reference.

What this folder adds to Meska Brain:

| Path | What |
|---|---|
| `packs/egypt-maths`, `egypt-science`, `egypt-english`, `egypt-arabic`, `egypt-social` | Egypt, grades 4 to 8, one pack per subject: topics with grade, term and source. ALL DRAFT: the prerequisite links are not reviewed by a teacher, and most topic lists come from secondary sources |
| `packs/egypt-school/pack.yaml` | The five subjects joined, plus three cross-subject links. This is what `meska demo` and `meska seed` build |
| `src/meska_brain/synth_school.py` | A synthetic school built from any pack's own graph (`generator: school` in the pack): several subjects, two teachers per subject, one class per grade |
| `src/meska_brain/accounts.py` | Sign-in: accounts, scrypt password hashes, sessions, admin and teacher roles |
| `src/meska_brain/classes.py` | Classes. Once sign-in is on, a teacher sees only the learners of their own classes. `web/app.py` enforces it in the middleware and in every list |
| `src/meska_brain/privacy.py` | Backup and restore, one learner's record as a file, deleting one learner, withdrawing one wrong record. Admin jobs, never MCP tools |
| `src/meska_brain/imports.py` | Marks sheet template and upload, new learner records, documents for the agent |
| `tests/test_accounts_upload.py`, `tests/test_classes_privacy.py`, `tests/test_synth_school.py` | Their tests |

`uv run meska demo` and `uv run meska seed` build the five-subject Egyptian school. `meska story` works on it.
The original cohort is `uv run meska seed --pack generic-maths`, and `meska eval` still expects that cohort.
Seeding wipes everything, accounts and classes included. No account is ever seeded: the admin is created on the
School page.

Arabic:

- The page (`index.html`) is written in English. In Arabic, `tr()` in the page looks every piece of visible text up in
  `static/ar.json` and `static/ar-server.json` (exact match, then whole-string patterns, then fragments). A
  MutationObserver applies it to everything added to the page, so new English text shows up translated only if it has
  an entry. Add the entry when you add text. Data (a finding, a teacher's words, a name) must be marked `dir="auto"`
  or `lang`, which keeps it out of the dictionary.
- Server side, `curriculum.current_lang` is set per request from the `athar_lang` cookie, and `pack.label(id)` follows
  it. `i18n.tr()` is the same lookup in Python, used by `report.py` with `static/ar-report.json`.
- `MESKA_LANGUAGE` (default `ar`) decides the language of seeded data and of the agent's findings. Tests set it to
  `en` in `tests/conftest.py`; `meska eval` forces `en`.
- Wording rules and fixed terms are in `docs/arabic-glossary.md`. Follow them.

Things that bite:

- A label in a pack with a comma must be in quotes (`{en: "Ratio, proportion and percent"}`). The loader refuses
  a cut label.
- Concept and strand ids must be unique across the packs that `egypt-school` includes. Each subject uses a prefix
  (`sci-`, `eng-`, `ara-`, `soc-`; maths uses `g4-` and so on).
- A topic may only need topics taught earlier (an earlier grade, or the same grade no later in the year). A test
  checks every Egyptian pack.
- A new route that returns learner data must filter with `_mine(request, ...)` or check with `classes.check`.
  Routes under `/api/learners/{id}/` are checked by the middleware.
- `data/backups/` and `exports/` hold names. They are ignored by git. Keep it that way.
- In this setup a bash heredoc that contains an apostrophe fails. Write a patch script to a file and run it instead.

## What this is

An entry for the Education track ("The Long View") of the African Agentic AI Design Challenge.
Meska Brain follows one learner across years and builds a cited profile for a teacher.

Three maps laid over each other:

- **Curriculum map**: concepts and their prerequisites, loaded from a pack (`packs/generic-maths/pack.yaml`).
  We graph the school's curriculum. We never change it.
- **Learner map**: evidence rows (quiz items, observations, attendance) attached to concepts over time.
- **Teacher map**: what was taught, when, and with which approach.

Who does what:

- The **graph engine** (`graph.py`) reaches the conclusions, in plain code: patterns held over terms,
  tracing a struggle back to where it began, which approaches were followed by improvement.
- The **model** only reads documents, chooses which analyses to run, and words text.
- A **named teacher** approves every finding and every note. Approving is not an MCP tool, so the
  agent cannot approve anything.

## Layout

| Path | What |
|---|---|
| `src/meska_brain/server.py`, `tools.py` | Our MCP server: 12 tools, 4 that write |
| `src/meska_brain/graph.py` | The deterministic graph engine |
| `src/meska_brain/guard.py` | Refuses statements that label, rank or track a child |
| `src/meska_brain/review.py` | Teacher decisions (not reachable by the agent) |
| `src/meska_brain/audit.py` | Every tool call is logged |
| `src/meska_brain/agent/workflow.py` | The LangGraph agent: the ask-for-a-record loop and two teacher gates |
| `src/meska_brain/agent/runner.py` | Starts, pauses and resumes runs |
| `src/meska_brain/agent/llm.py` | Model access (any OpenAI-compatible endpoint) |
| `src/meska_brain/explain.py` | Why a finding says what it says: plain facts and chart data, computed from its records |
| `src/meska_brain/report.py` | Printable learner report, built from approved findings only |
| `src/meska_brain/school.py` | Whole-school map by topic (never ranks learners) and its GraphML export |
| `src/meska_brain/web/` | Teacher web app (FastAPI and one HTML file) |
| `src/meska_brain/synth.py` | Synthetic cohort and sample documents |
| `src/meska_brain/evals.py` | The evaluation set that writes `EVALS.md` |
| `packaging/windows/` | The offline Windows package: `build.py`, `launch.py`, model download, start files |
| `tests/` | 316 tests, no model needed |

## Commands

```
uv sync --extra dev          # install
uv run meska demo            # seed if needed, open the teacher app at http://127.0.0.1:8765
uv run pytest -q             # tests (no model needed)
uv run ruff check src tests  # lint
uv run meska seed --pack generic-school   # all four subjects (default seed is maths only)
uv run meska seed --school   # a whole school: four subjects, 36 learners, ten subject teachers with profiles
uv run meska story           # a ready state for presenting, no model used
uv run meska learners        # list learners
uv run meska run A-17 --file data/inbox/quiz_sheet_A17_2025-T1.md
uv run meska pending         # what is waiting for a teacher
uv run meska answer <request_id> --teacher <id> --text "..."   # answer the agent's question, then `meska resume`
uv run meska report A-17     # printable report, approved findings only (--all for every learner)
uv run meska export-graph    # school graph as GraphML, for Gephi or Neo4j
uv run meska eval --skip-model   # engine tasks only (this rewrites the table in EVALS.md)
uv run meska eval --repeats 1    # full evaluation, needs a model
```

## Using an API instead of a local model

The model is any OpenAI-compatible endpoint. Settings are read from the process environment.
The project does not load a `.env` file, so set them in the shell that runs the command:

```
MESKA_LLM_BASE_URL   the provider's OpenAI-compatible base URL (ends in /v1)
MESKA_LLM_API_KEY    the key
MESKA_LLM_MODEL      the model id as the provider names it
MESKA_LLM_REASONING  set to "default" for hosted APIs
```

`MESKA_LLM_REASONING=default` matters: by default the code sends `reasoning_effort: "none"`, which
LM Studio accepts and some hosted APIs reject.

The Agent page can also use OpenAI or Claude for a run, as a comparison. A key is read from `OPENAI_API_KEY` or
`ANTHROPIC_API_KEY`, or typed on the page, where it is kept in memory only. See `SECURITY.md`.

Prefer an open-weights model (Qwen, Llama, Gemma, Mistral) from a host such as OpenRouter, Groq or
Together. The challenge requires a full task on open weights, so numbers that go into `EVALS.md`
must come from an open-weights model. A closed model is fine for exploring, but say which model
produced any result you report.

## Rules that must not be broken

These come from the challenge. Breaking one disqualifies the entry.

1. **Never commit a key.** No `.env` file, no key in code, docs, tests or commit messages. The repo is public.
2. **Synthetic data only.** No real learner data, ever. A learner's record code is the alias (A-17). The names in
   the teacher app and the report are invented, and no tool result and no model prompt ever carries a name.
3. **The agent never labels a child or assigns a track.** Do not weaken `guard.py` or the two teacher gates.
4. **No unsourced claim.** Every finding cites evidence ids, and those ids come from the tools, never from the model.
5. **Every tool call is logged.** New tools must use `@audited`.
6. **Report results as they are.** Do not edit the generated table in `EVALS.md` by hand. If something fails, write it down.
7. **Keep the one-command run working.** `uv run meska demo` must work on a fresh clone.

## Working here

- Work on a branch and open a pull request. Do not push to `main`.
- Before every commit: `uv run pytest -q` and `uv run ruff check src tests` must both pass. CI runs both on
  every push and pull request (`.github/workflows/ci.yml`).
- `meska seed` rewrites the tracked files in `data/`. Restore them with `git checkout -- data/` before committing.
- `SECURITY.md` lists what the code enforces. If you change one of those rules, change the page and its test.
- Add a test with every fix.
- Docs are written in plain English with no em dashes or en dashes.
- Known weak spots are listed at the end of `EVALS.md`. Start there.
