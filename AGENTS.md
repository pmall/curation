# Agent instructions

Drakkar is the curation database of virus–human protein–protein interactions. Claude curates it: each description exactly what its publication shows, every write checked, every decision traceable in its note.

## Where things are

- `docs/`, the source of truth, read before acting: `glossary.md` (one meaning per term, used everywhere), `curation-rules.md` (the biological rules explained for humans: what a right description is, and the evidence for it; their source of truth is the curator's prompt), `database.md` (structure, states, the publication and description notes, versioning, invariants, writes), `tools.md` (the files and the tools that write and read the database, the dry run, the tools that fetch and convert full texts, the release tools), `datasets.md` (what is exported, and what it means for curation).
- `prompts/`: what the agents run. `prompts/skills/` (linked from `.claude/skills/` and `.agents/skills/`): `curate`, a batch of publications curated; `export`, the derived datasets, the generic viral proteins brought in step first. `prompts/agents/` (linked from `.claude/agents/` and `.agents/agents/`): `curator.md`, the subagent that curates one publication.
- `src/drakkar/`: the tools (`tools.md`). `tests/`: their tests.
- `docs/history/`: the record of the move from manual curation to Claude's curation, with its dates, counts and measurements, one file each. Closed: nothing is added to it. The reference docs never point to it.
- `data/`, reports and scratch files are disposable: docs never point to them, what a reader needs is written in the doc itself.

## Docs

- The reference docs are explanations, instructions and rules for the working agent, timeless and right at reading time: they describe the current rules and the current state. Every paragraph is something the agent needs to act correctly now. No account of how things came to be (what changed, was added or removed, and when), no detail a tool or a database constraint already enforces, no dates, no counts, no results of a run, no status tags, no plans. Every rule written is decided.
- `docs/` holds the rules, each written once, in its place; other docs point to it. Each doc keeps to its scope: `curation-rules.md` the biology, `database.md` the data, its notes and its invariants, `tools.md` the commands and their files; no process in a doc.
- The skills and the agent files hold the processes, each self-contained: the whole process it runs, the formats it writes and the tools it uses, condensed, so that an agent spends its context on its job, not on reading docs. It reads no doc; it repeats of a doc only the short parts it needs (the columns of a file, the note lines it writes). Two prompts may give the same instruction.
- Keep the docs and the prompts up to date with every decision: a change of a format or a tool updates the prompts that repeat it.

## Working with the user

- The skills and docs are instructions for an agent that curates publications and manages Drakkar, with the user supervising its results: not a pipeline where every detail is settled end to end. What matters is the instructions, the process, and data that is easy to use and manage. Not every detail or edge case needs a rule, and no error is dramatic: every version is kept, and a publication can always be curated again.
- Use the user's definitions exactly as given (`docs/glossary.md`): never merge, regroup, relabel or extend a problem, term or rule; when one seems incomplete, ask one precise question.
- When the user states a principle, apply it to every case it covers in one pass; ask only about cases it does not decide.
- Be precise and short: say what is counted (descriptions, interactors, proteins, sides) and never mix units; one decision at a time; show the special cases, not the obvious ones; plain words, no invariant codes.
- Every count comes from a fresh query or the latest report, never from memory or arithmetic on earlier numbers; tables add up to their total. A result is reported only once the analysis behind it is complete: each count is given once, final, never revised in a later message.
- When the user says to wait, start nothing. Run exactly the rule the user stated: no extra check, no arbitrary threshold. Keep a check at the level the user named (checking names is not re-checking interactors) and estimate its cost first; anything more than a quick pass needs approval.
- Low-stakes requests (test data, demos): the simplest thing in minutes, one plain query, no enrichment; extras only afterwards.
- Rewriting a skill, a tool or a process starts from its goal: every step of the old version is questioned before it is kept, and the design is agreed before anything is written or run. A tool is built when its job comes, not before.

## Database writes

- Every job that writes (curation batches, versioning passes, a fix) writes nothing to the database before the user's go on its report. The user supervises every commit: the report shows what the commit would write, the user judges it, and the commit writes what the user approved. So no skill or tool holds back part of a job on its own: the report shows it, the user decides. A dry run writes nothing and needs no go.
- The report leaves no open question to the user. After the go, the orchestrator commits in its own context, without asking again.
- Subagents decide and write files, never to the database. A skill writes only where its prompt says; placing and aggregating its output is the orchestrator's job.
- Writes go through the tools of `tools.md`; plain SQL only when the user allows it for that write.
- Recomputed values (alignments, identities, coordinates) are written only if our code first reproduces the stored values on the cases that are right; any discrepancy: stop, show it, write nothing.

## Database queries

- The database is big (millions of protein snapshots, the whole NCBI taxonomy): every query must be fast. Check the indexes (`pg_indexes`) and, when unsure, the plan (`EXPLAIN`); set a `statement_timeout` so a bad plan fails fast; aggregate first, then join the small result; time each step.
- SQL is written for a human reader: plain joins, named columns in `GROUP BY` and `ORDER BY`, clear aliases; a complex form only when speed needs it, with a comment saying so.
- Timestamps are `timestamp(0)`: compare with `now()::timestamp(0)`.

## Python

- uv for environments and dependencies, ruff for linting and formatting, pyright for type checking, pytest for tests (`uv run pytest`: a test database, never Drakkar).
- Parameters go from the most general to the most specific, in a command as in a function: `drakkar-diff <pmid> <file>`, `drakkar-mapping <accession> <sequence>...`.
- Markdown is formatted with `uv run mdformat --wrap no --number --compact-tables docs/ prompts/ generic/ AGENTS.md README.md`.

## Git

- Never commit, amend or push without the user's explicit request for it: write the files, show them, and ask.
