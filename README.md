# Drakkar curation

Drakkar is the curation database of virus–human protein–protein interactions. This repository is the harness in which an AI agent curates it: the instructions it follows, the tools it works through, and the orchestration that turns a list of publications into checked writes, under the supervision of a curator.

What a right description is, what the database holds and how it is versioned are not explained here:

- [`docs/glossary.md`](docs/glossary.md): the terms, one meaning each, used everywhere;
- [`docs/curation-rules.md`](docs/curation-rules.md): the biological rules, the acceptance criteria, how each value of a description is identified, the mappings;
- [`docs/notes.md`](docs/notes.md): the publication and description notes;
- [`docs/database.md`](docs/database.md): the tables, the states of a publication, versioning, UniProt releases, invariants;
- [`docs/derived-datasets.md`](docs/derived-datasets.md): what is exported from Drakkar;
- [`docs/tools.md`](docs/tools.md): the file formats and every tool.

## The idea

The agent curates; the curator supervises. The agent reads each publication, decides its descriptions and writes them into files. The tools check those files against the whole database, and nothing reaches Drakkar before the curator's go on a report. Every version of every description is kept, so no write is irreversible and a publication can always be curated again.

Three layers make the harness:

| Layer | Where | What it holds |
| -- | -- | -- |
| Instructions | [`AGENTS.md`](AGENTS.md), [`docs/`](docs/) | How the agent works with the user, writes and queries; the curation rules, the database, the tools. |
| Tools | [`src/drakkar/`](src/drakkar/), [`tests/`](tests/) | Python commands that fetch, convert, read, diff, check and write; the only way to write to Drakkar. |
| Processes | [`prompts/`](prompts/) | The `curate` skill, the orchestration of a batch ([`SKILL.md`](prompts/skills/curate/SKILL.md)), the `curator` agent, which curates each publication ([`curator.md`](prompts/agents/curator.md)), and the `upgrade` skill, a UniProt release and its versioning pass ([`SKILL.md`](prompts/skills/upgrade/SKILL.md)). |

The rules are written once, in `docs/`. A skill or an agent holds a whole process, start to end, self-contained: it reads no doc but the biological rules, so its context goes to the publication.

## The tools

All are commands of the project (`uv run <command>`), described in [`docs/tools.md`](docs/tools.md).

| Purpose | Commands | What they do |
| -- | -- | -- |
| Full texts | `drakkar-fetch`, `drakkar-parse` | Download a full text with its supplementary files and a manifest; convert XML, HTML, PDF, Word, spreadsheets. |
| Reading | `drakkar-read`, `drakkar-genbank` | A publication, a UniProt entry, the generic names in use, live descriptions as revision rows; lookups of methods, entries, taxa, sequences and mappings; free read-only SQL; NCBI protein sequences. |
| Re-curation | `drakkar-diff` | A re-curated publication's descriptions against its live ones, as files to add, revise and remove. |
| Writing | `drakkar-add`, `drakkar-revise`, `drakkar-publications`, `drakkar-move`, `drakkar-batch` | Descriptions, revisions and removals, publication states and notes, moves to the special run; a whole batch in one transaction. |
| Checking | `drakkar-check` | Every invariant on the whole database, read-only. |
| Releases | `drakkar-taxonomy`, `drakkar-uniprot` | Load the NCBI taxonomy and a UniProt release (the [`upgrade`](prompts/skills/upgrade/SKILL.md) skill). |

Every write follows the same path ([`docs/database.md` §2](docs/database.md#2-descriptions-and-versioning)). Each row is checked on what it builds on (the publication, the snapshots, the method, the coordinates, the mappings, the note), then every invariant is checked on the whole database inside the same transaction. Without `--commit` the transaction is rolled back: a dry run is the same code as a commit, writes nothing and needs no go. With `--commit`, it commits only when no row is refused and no error is found. What is derived (human names, full-length coordinates, mapping occurrences) is computed by the tools, never given by the agent.

## A batch

A batch is the curation of at most 20 publications, orchestrated by the [`curate`](prompts/skills/curate/SKILL.md) skill. Its work directory, by default `data/sessions/run<run>/batch<n>/`, holds one directory per publication, then the merged files.

```
orchestrator (curate skill)
  1. publications   from the prompt, or the next ones of the oldest vh run
  2. full texts     drakkar-fetch, drakkar-parse     ── no subagent yet; the orchestrator never reads them
  3. curate         one curator agent per publication (curator.md)
                      reads the converted full text and the UniProt entries
                      writes its descriptions and curation notes
  4. merge          batch files: descriptions to add, revise and delete, publications.tsv
  5. dry run        drakkar-batch: the whole batch checked in one transaction, rolled back
  6. report         to the curator, with the errors of the dry run    ── nothing written yet
     ── go ──
  7. commit         drakkar-batch --commit: descriptions, publications, then the move
                      of the publications left selected to the special run
```

- **Full texts first.** The orchestrator fetches every full text and its supplementary files before any subagent starts, from PMC (its open access files, Europe PMC, NCBI, the PMC article page), the publisher's page, then the free copies' PDFs (OpenAlex, Unpaywall), and converts them to text. A publication without the article is fetched once more, and still without it gets no subagent. A subagent downloads a missing supplementary file it needs with `drakkar-fetch --supplement`, and any file it needs to identify an interactor, its coordinates or a mapping (a sequence, an entry, a taxon) from a public database, never the article. When no route works, the curator can provide a PDF.
- **One subagent per publication**, the `curator` agent, with its own context and only the shell and the file tools: it reads the publication, decides each description by the rules and writes files. It never writes to the database.
- **Every description is written.** Each value comes from the first tier that gives it, from the most direct to the most inferred, and the description note names the tier (by its label) and the evidence of each value that is not obvious ([`docs/curation-rules.md` §4](docs/curation-rules.md#4-how-each-value-is-identified)); a publication stays `selected` only for a relevant file the subagent could not get.
- **A dry run before the report.** `drakkar-batch` applies the merged files in one transaction, checks every invariant on the result and rolls back. Its refused rows and errors, inconsistencies between publications among them, go to the report as they are, not fixed.
- **The report leaves no open question**: what each file holds, the publications without a full text or not curated, with why.
- **The go.** After it, the orchestrator commits the batch files, the last write moving the publications the agent could not curate fully (a relevant file missing: the full text or a supplementary file) to the open special run, so the run they came from can be complete. Their manual pass happens there.

**Re-curation.** A publication already curated goes through the same batch. The subagent curates it again from its full text, without looking at its current curation, then `drakkar-diff` compares the result with its live descriptions: the descriptions to add, to revise and to remove. They are committed as a new publication's are, by the agent after the curator's go.

Batches are independent: each takes its own publications, works in its own directory and writes only them. Many could run in parallel, given distinct publications; the default pick, the next publications of the oldest run, serves one batch at a time.

## What is tracked

A publication in a run carries its state, its note and the date of the agent's last pass ([`docs/database.md`](docs/database.md#states) and [`docs/notes.md`](docs/notes.md)): `selected` without a date waits for the agent, `curated` is done, `selected` with a date waits for a manual pass in a special run. The note, rewritten at each pass, says what was decided and keeps the history of passes and moves; each description version has its own note. Together they make every decision traceable without the conversation that took it.

## Running it

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), PostgreSQL with Drakkar, and Claude Code (or another agent that reads [`.agents/skills/`](.agents/skills/)).

```sh
uv sync
cp .env.example .env    # database connection, the address Unpaywall asks for, the NCBI API key
```

In Claude Code, from the repository, `/curate` starts a batch: alone, it takes the next publications; or with a prompt naming publications and a work directory. The agent ends with its report and waits for the go.

The skills are linked from [`.claude/skills/`](.claude/skills/) and [`.agents/skills/`](.agents/skills/), the agent from [`.claude/agents/`](.claude/agents/) and [`.agents/agents/`](.agents/agents/); [`AGENTS.md`](AGENTS.md) is read by the agent at the start of every conversation.

## Development

```sh
uv run pytest                    # on a test database built from sql/schema.sql and tests/fixture.sql, never Drakkar
uv run ruff check && uv run ruff format
uv run pyright
uv run mdformat --wrap no --number --compact-tables docs/ prompts/ AGENTS.md README.md
```

## Layout

```
AGENTS.md            instructions for the agent
docs/                rules, notes, database, tools, derived datasets
  history/           the move from manual curation to the agent's curation (closed)
prompts/skills/      curate (a batch), upgrade (a UniProt release)
prompts/agents/      curator.md (one publication)
src/drakkar/         the tools
sql/schema.sql       the database structure (written by tests/build_fixture.py)
tests/               tests and their fixture
data/                releases, reports, batch directories (not versioned)
```
