# Drakkar curation

Drakkar is the curation database of virus–human protein–protein interactions. This repository is the harness in which an AI agent curates Drakkar under the user's supervision: the instructions it follows, the tools it works through, and the orchestration that turns a list of publications into checked writes.

This README is an overview. What makes a description right, what the database holds and how it is versioned are explained in `docs/`:

- [`docs/glossary.md`](docs/glossary.md): the terms, one meaning each, used everywhere;
- [`docs/curation-rules.md`](docs/curation-rules.md): the biological rules explained in full (the acceptance criteria, how each value of a description is identified, the mappings), which the curator's prompt holds in condensed form;
- [`docs/database.md`](docs/database.md): the tables, the states of a publication, the publication and description notes, versioning, UniProt releases, invariants;
- [`docs/datasets.md`](docs/datasets.md): what is exported from Drakkar;
- [`docs/tools.md`](docs/tools.md): the file formats and every tool.

## The idea

The agent curates; the user supervises. The agent reads each publication, decides its descriptions and writes them into files. The tools check those files against the whole database, and nothing reaches Drakkar before the user's go on a report. Every version of every description is kept, so no write is irreversible and a publication can always be curated again.

The harness has three layers:

| Layer | Where | What it holds |
| -- | -- | -- |
| Instructions | [`AGENTS.md`](AGENTS.md), [`docs/`](docs/) | How the agent works with the user, writes to and queries the database; the curation rules, the database, the tools. |
| Tools | [`src/drakkar/`](src/drakkar/), [`tests/`](tests/) | Python commands that fetch, convert, read, diff, check and write; the only way to write to Drakkar. |
| Processes | [`prompts/`](prompts/) | The `curate` skill, which orchestrates a batch ([`SKILL.md`](prompts/skills/curate/SKILL.md)), and the `curator` agent, which curates each publication ([`curator.md`](prompts/agents/curator.md)); the `export` skill, which brings the generic viral proteins in step, then exports the derived datasets ([`SKILL.md`](prompts/skills/export/SKILL.md)). |

Each rule is written once, in `docs/`, except the curation rules: the curator's prompt holds them, and `docs/curation-rules.md` explains them. Each skill and each agent is self-contained: it holds its whole process, start to end, and reads no doc, so its context goes to its job.

## The tools

They are all project commands, run with `uv run <command>` and described in [`docs/tools.md`](docs/tools.md).

| Purpose | Commands | What they do |
| -- | -- | -- |
| Full texts | `drakkar-fetch`, `drakkar-download`, `drakkar-parse` | Download a full text with its supplementary files, convert them and list them in a manifest; download and convert one file from a URL; convert files (XML, HTML, PDF, Word, spreadsheets) to texts named by their format. |
| Reading | `drakkar-read`, `drakkar-genbank` | Look up methods, taxa, entries (by accession, name or sequence), sequences and the generic names in use; run any read-only SQL query; search NCBI protein sequences. |
| Mapping | `drakkar-mapping` | Compute mapping sequences on an identified entry exactly as the write does, to check them. |
| Diffing | `drakkar-diff` | Compare a publication's curated descriptions with its live ones, and write the differences as files to add, revise and remove. |
| Writing | `drakkar-add`, `drakkar-revise`, `drakkar-publications`, `drakkar-notes`, `drakkar-batch` | Write descriptions, revisions and removals, publication states and notes; build a batch's publications file from its notes; write a whole batch in one transaction. |
| Checking | `drakkar-check` | Check every invariant on the whole database, read-only. |
| Releases | `drakkar-taxonomy`, `drakkar-uniprot` | Load the NCBI taxonomy and a UniProt release. |
| Generic viral proteins | `drakkar-generic` | Keep the species and the generic viral proteins of the vh descriptions dataset (`generic/`) in step with Drakkar. |
| Derived datasets | `drakkar-export` | Export the vh and hh descriptions, the sequences of the viral interactors and the mappings, as files for other applications. |

Every write follows the same path ([`docs/database.md` §2](docs/database.md#2-descriptions-and-versioning)). Each row is checked against what it builds on (the publication, the snapshots, the method, the coordinates, the mappings), never against its note; then every invariant is checked on the whole database, inside the same transaction. Without `--commit`, the transaction is rolled back: a dry run runs the same code as a commit, writes nothing and needs no go. With `--commit`, it commits only when no row is refused and no error is found. What is derived (human names, full-length coordinates, mapping occurrences) is computed by the tools, never given by the agent.

## A batch

A batch is a curation of publications, orchestrated by the [`curate`](prompts/skills/curate/SKILL.md) skill. Its work directory, by default `data/sessions/run<run>/batch<n>/` (`data/sessions/batch<n>/` when its publications come from several runs), holds one directory per publication and the merged files.

```
orchestrator (curate skill)
  1. publications   from the prompt
  2. full texts     drakkar-fetch, unless done        ── no subagent yet; the orchestrator never reads them
  3. curate         one curator agent per publication (curator.md)
                      reads the converted full text and the UniProt entries
                      writes its descriptions and curation notes
  4. merge          batch files: descriptions.jsonl (cat), publications.jsonl (drakkar-notes)
  5. dry run        drakkar-batch: the whole batch checked in one transaction, rolled back
  6. report         to the user, with the errors of the dry run       ── nothing written yet
     ── go ──
  7. commit         drakkar-batch --commit: descriptions, publications
```

- **Full texts first.** Before any subagent starts, the orchestrator fetches every full text with its supplementary files and converts them to text. It tries PMC (its open access files, Europe PMC, NCBI, the PMC article page), then the publisher's page, then the PDFs of free copies (OpenAlex, Unpaywall). A free article that could not be downloaded is fetched once more; a publication still without its article gets no subagent. A subagent never downloads the article: it downloads a missing supplementary file it needs from the URL the text gives (`drakkar-download`), and any file it needs to identify an interactor, its coordinates or a mapping (a sequence, an entry, a taxon) from a public database. When no route works, the user can provide the files: they are set up as the fetch would set them up, with their manifest.
- **One subagent per publication**: the `curator` agent, with its own context, the shell, a tool to read files and web search. It reads the publication, decides each description by the rules and writes files; it never writes to the database.
- **Every description is written.** Each value comes from the first tier that gives it, from the most direct to the most inferred ([`docs/curation-rules.md`](docs/curation-rules.md)); a publication stays `selected` only when the subagent could not get a relevant file.
- **A dry run before the report.** `drakkar-batch` applies the merged files in one transaction, checks every invariant on the result and rolls back. Its refused rows and errors, including inconsistencies between publications, go into the report as they are, unfixed.
- **The report leaves no open question**: it says what each file holds, which publications have no full text or were not curated, and why.
- **The go.** The orchestrator then commits the batch files. The publications the agent could not curate fully (a relevant file missing: the full text or a supplementary file) stay `selected` with a date. When the user asks, they are moved to the open special run, where their manual pass happens, so that the run they came from can be complete.

Batches are independent: each takes its own publications, works in its own directory and writes only those. Several batches could run in parallel on distinct publications; the default pick, the next publications of the oldest run, is made for one batch at a time.

## What is tracked

A publication in a run carries its state, its note and the date of the agent's last pass (`docs/database.md`, [states](docs/database.md#states) and [notes](docs/database.md#notes)): `selected` without a date waits for the agent, `curated` is done, `selected` with a date waits for a manual pass in a special run. Each pass and each move puts its note at the top of the publication's note, so that note keeps their whole history; each description version has its own note. Together, they make every decision traceable without the conversation that made it.

## Running it

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), PostgreSQL with Drakkar, and Claude Code (or another agent that reads [`.agents/skills/`](.agents/skills/)).

```sh
uv sync
cp .env.example .env    # database connection, the address Unpaywall asks for, the NCBI API key
```

In Claude Code, run from the repository, `/curate` starts a batch: alone, it takes the next publications into the default work directory; a prompt can name the publications, the work directory, or both. The agent ends with its report and waits for the go.

The skills are linked from [`.claude/skills/`](.claude/skills/) and [`.agents/skills/`](.agents/skills/), the agent from [`.claude/agents/`](.claude/agents/) and [`.agents/agents/`](.agents/agents/); [`AGENTS.md`](AGENTS.md) is read by the agent at the start of every conversation.

## Development

```sh
uv run pytest                    # on a test database built from sql/schema.sql and tests/fixture.sql, never Drakkar
uv run ruff check && uv run ruff format
uv run pyright
uv run mdformat --wrap no --number --compact-tables docs/ prompts/ generic/ AGENTS.md README.md
```

## Layout

```
AGENTS.md            instructions for the agent
docs/                rules, database, tools, derived datasets
  history/           the move from manual curation to the agent's curation (closed)
prompts/skills/      curate (a batch), export (the derived datasets, the generic viral proteins first)
prompts/agents/      curator.md (one publication)
generic/             the species and generic viral proteins of the vh descriptions dataset
src/drakkar/         the tools
sql/schema.sql       the database structure (written by tests/build_fixture.py)
tests/               tests and their fixture
data/                releases, reports, batch directories (not versioned)
```
