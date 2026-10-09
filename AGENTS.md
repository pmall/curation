# Agent instructions

## Documentation

- Project knowledge lives in `docs/`: `glossary.md` (the meaning of every term, to use everywhere), `curation-rules.md` (biological curation rules), `database.md` (structure, versioning, invariants), `derived-datasets.md` (what is exported from Drakkar, and what it means for curation).
- `docs/history/` records the passes done on the database (exploration, fixing pass, versioning pass): what was done, when, with counts and reports. Reference docs hold the rules and point to the history; a rule found in a history file belongs in the reference docs.

## Python

- Use uv for environments and dependencies, ruff for linting and formatting, pyright for type checking.
- Format Markdown with mdformat (`uv run mdformat --wrap no docs/`).

## Git

- Never add co-authorship or attribution to commits or pull requests: no `Co-Authored-By` trailer, no "Generated with" line.
