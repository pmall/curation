# Agent instructions

## Documentation

- Project knowledge lives in `docs/`: `glossary.md` (the meaning of every term, to use everywhere), `curation-rules.md` (biological curation rules), `database.md` (structure, versioning, invariants), `derived-datasets.md` (what is exported from Drakkar, and what it means for curation), `viruses.md` and `viruses/` (the generic name of each viral protein, decided once, one file per virus family).
- **Only what is committed in `docs/` is kept.** `data/`, reports and scratch files are disposable: any result needed later (a reference, a decision, a list) goes into `docs/` and is committed. Work from `docs/`, and keep it up to date.
- `docs/history/` records the passes done on the database (exploration, fixing pass, versioning pass): what was done, when, with counts and reports. Reference docs hold the rules and point to the history; a rule found in a history file belongs in the reference docs.

## Working with the user

- Use the user's definitions exactly as given (terms in `docs/glossary.md`): never merge, regroup, relabel or extend a problem, term or rule; when one seems incomplete, ask one precise question.
- Be precise and short: say what is counted (descriptions, interactors, proteins, sides) and never mix units; one decision at a time; show the special cases, not the obvious ones; plain words, no invariant codes.
- Every count comes from a fresh query or the latest report, never from memory or arithmetic on earlier numbers; tables add up to their total.
- Database writes: nothing is written before the user approves that specific fix, explained in plain words with examples and a count (`docs/database.md` §2). Dry runs and read-only analysis are fine. A small fix on a few rows is plain SQL, never a new function.
- Recomputed values (alignments, identities, coordinates) are written only if our code first reproduces the stored values on the cases that are right; any discrepancy: stop, show it, write nothing.
- Low-stakes requests (test data, demos): the simplest thing in minutes, one plain query, no enrichment; extras only afterwards.

## Database

- The database is big (millions of protein snapshots, the whole NCBI taxonomy): every query must be fast. Check the indexes (`pg_indexes`) and, when unsure, the plan (`EXPLAIN`); set a `statement_timeout` (e.g. 30 s) so a bad plan fails fast; aggregate first, then join the small result; time each step.
- Timestamps are `timestamp(0)`: compare with `now()::timestamp(0)`.
- Taxonomy queries are slow: never a per-row nested-set lookup (`left_value`/`right_value` ranges) in a big query. Collect the distinct taxa first, then walk their lineage once by `parent_taxon_id` (indexed).

## Python

- Use uv for environments and dependencies, ruff for linting and formatting, pyright for type checking.
- Format Markdown with mdformat (`uv run mdformat --wrap no docs/`).

## Git

- Never add co-authorship or attribution to commits or pull requests: no `Co-Authored-By` trailer, no "Generated with" line.
- Don't make a commit for every slight doc change: fold follow-ups into the commit being finished (amend). The user works alone on this repository: diverging from origin is fine; never push unless asked.
