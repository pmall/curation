# Agent instructions

Drakkar is the curation database of virus–human protein–protein interactions. Claude curates it: each description exactly what its publication shows, every write checked, every decision traceable in its note.

## Where things are

- `docs/`, the source of truth, read before acting: `glossary.md` (one meaning per term, used everywhere), `curation-rules.md` (what a right description is, and the evidence for it), `database.md` (structure, versioning, invariants, writes), `process.md` (how a curation or re-curation session runs: files, tools, dry run, commit), `derived-datasets.md` (what is exported, and what it means for curation), `todo.md` (the next steps).
- `skills/`: the `curate` and `recurate` sessions (linked from `.claude/skills/` and `.agents/skills/`). A skill holds only what is specific to its session; the rules are in `docs/`.
- `src/drakkar/`: the tools (`process.md` § Tools; the release tools in `database.md` §3). `tests/`: their tests.
- `docs/history/`: the history of the project: what was done and when, with its dates, counts and measurements, one file each. The reference docs never point to it.
- `data/`, reports and scratch files are disposable: docs never point to them, what a reader needs is written in the doc itself.

## Docs

- The reference docs are explanations, instructions and rules for the working agent, timeless and right at reading time: they describe the current state and the current process. Every paragraph is something the agent needs to act correctly now. No account of how things came to be (what changed, was added or removed, and when), no detail a tool or a database constraint already enforces, no dates, no counts, no results of a run, no status tags, no plans (`todo.md`). Every rule written is decided.
- Each rule is written once, in its place; other places point to it. A rule found in a history file, a skill or a conversation goes into the reference docs; a fact about the past goes into `docs/history/`.
- Keep the docs up to date with every decision. Project knowledge goes in the project, never in Claude's local memory.

## Working with the user

- Use the user's definitions exactly as given (`docs/glossary.md`): never merge, regroup, relabel or extend a problem, term or rule; when one seems incomplete, ask one precise question.
- When the user states a principle, apply it to every case it covers in one pass; ask only about cases it does not decide.
- Be precise and short: say what is counted (descriptions, interactors, proteins, sides) and never mix units; one decision at a time; show the special cases, not the obvious ones; plain words, no invariant codes.
- Every count comes from a fresh query or the latest report, never from memory or arithmetic on earlier numbers; tables add up to their total. A result is reported only once the analysis behind it is complete: each count is given once, final, never revised in a later message.
- Before any analysis, even read-only, agree its plan: method, tools, thresholds, what is counted, helper agents. When the user says to wait, start nothing. Run exactly the rule the user stated: no extra check, no arbitrary threshold. Keep a check at the level the user named (checking names is not re-checking interactors) and estimate its cost first; anything more than a quick pass needs approval.
- Low-stakes requests (test data, demos): the simplest thing in minutes, one plain query, no enrichment; extras only afterwards.
- Rewriting a skill, a tool or a process starts from its goal: every step of the old version is questioned before it is kept, and the design is agreed before anything is written or run. A tool is built when its job comes, not before.

## Database writes

- Every job that writes (curation and re-curation sessions, versioning passes, a fix) writes nothing to the database before the user's go on its report. A dry run writes nothing and needs no go.
- The report leaves no open question to the user: what cannot be settled is unsettled, with why. After the go, the orchestrator commits in its own context, without asking again.
- Subagents decide and write files, never to the database. A skill writes only where its prompt says; placing and aggregating its output is the orchestrator's job.
- Writes go through the tools of `process.md`; plain SQL only when the user allows it for that write.
- Recomputed values (alignments, identities, coordinates) are written only if our code first reproduces the stored values on the cases that are right; any discrepancy: stop, show it, write nothing.

## Database queries

- The database is big (millions of protein snapshots, the whole NCBI taxonomy): every query must be fast. Check the indexes (`pg_indexes`) and, when unsure, the plan (`EXPLAIN`); set a `statement_timeout` so a bad plan fails fast; aggregate first, then join the small result; time each step.
- SQL is written for a human reader: plain joins, named columns in `GROUP BY` and `ORDER BY`, clear aliases; a complex form only when speed needs it, with a comment saying so.
- Timestamps are `timestamp(0)`: compare with `now()::timestamp(0)`.
- Taxonomy: never a per-row nested-set lookup (`left_value`/`right_value`) in a big query; collect the distinct taxa, then walk their lineage once by `parent_taxon_id`.

## Python

- uv for environments and dependencies, ruff for linting and formatting, pyright for type checking, pytest for tests (`uv run pytest`: a test database, never Drakkar).
- Markdown is formatted with `uv run mdformat --wrap no docs/ skills/ AGENTS.md`.

## Git

- Never commit or amend without the user's explicit request for that commit: write the files, show them, and ask.
- No co-authorship or attribution in commits: no `Co-Authored-By` trailer, no "Generated with" line. A verification result goes in the commit message.
- Fold follow-ups into the commit being finished (amend, when asked). The user works alone on this repository: diverging from origin is fine; never push unless asked.
