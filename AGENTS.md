# Agent instructions

## Git

- Never add co-authorship or attribution to commits or pull requests: no `Co-Authored-By` trailer, no "Generated with" line.

## Python

- Use uv for environments and dependencies, ruff for linting and formatting, pyright for type checking.
- Format Markdown with mdformat (`uv run mdformat --wrap no docs/`).

## Documentation

- Project knowledge lives in `docs/`: `curation-rules.md` (biological curation rules), `database.md` (structure, versioning, invariants).
