# Drakkar curation

Drakkar is the curation database of virus–human protein–protein interactions. This repository is the harness in which an AI agent curates it: the instructions it follows, the tools it works through, and the orchestration that turns a list of publications into checked writes, under the supervision of a curator.

What a right description is, what the database holds and how it is versioned are not explained here:

- [`docs/glossary.md`](docs/glossary.md): the terms, one meaning each, used everywhere;
- [`docs/curation-rules.md`](docs/curation-rules.md): the acceptance criteria, the conventions, the mappings, the notes, the states of a publication;
- [`docs/database.md`](docs/database.md): the tables, versioning, UniProt releases, invariants;
- [`docs/derived-datasets.md`](docs/derived-datasets.md): what is exported from Drakkar;
- [`docs/tools.md`](docs/tools.md): the file formats and every tool.

## The idea

The agent curates; the curator supervises. The agent reads each publication, decides its descriptions and writes them into files. The tools check those files against the whole database, and nothing reaches Drakkar before the curator's go on a report. Every version of every description is kept, so no write is irreversible and a publication can always be curated again.

Three layers make the harness:

| Layer        | Where                                              | What it holds                                                                                                                                                 |
| ------------ | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Instructions | [`AGENTS.md`](AGENTS.md), [`docs/`](docs/)         | How the agent works with the user, writes and queries; the curation rules, the database, the tools.                                                           |
| Tools        | [`src/drakkar/`](src/drakkar/), [`tests/`](tests/) | Python commands that fetch, convert, read, diff, check and write; the only way to write to Drakkar.                                                           |
| Processes    | [`skills/`](skills/)                               | The `curate` skill: the orchestration of a batch ([`SKILL.md`](skills/curate/SKILL.md)) and the prompt of each subagent ([`item.md`](skills/curate/item.md)). |

The rules are written once, in `docs/`, and the skills point to them. A skill holds a whole process, start to end. What the tools meet on real publications (failed fetches, bad conversions, mappings the rules cannot record) goes into [`docs/logs/`](docs/logs/), to improve the tools.

## The tools

All are commands of the project (`uv run <command>`), described in [`docs/tools.md`](docs/tools.md).

| Purpose     | Commands                                                                                 | What they do                                                                                                                    |
| ----------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Full texts  | `drakkar-fetch`, `drakkar-parse`                                                         | Download a full text with its supplementary files and a manifest; convert XML, HTML, PDF, Word, spreadsheets.                   |
| Reading     | `drakkar-read`                                                                           | A publication, a UniProt entry, the generic names in use, live descriptions as revision rows.                                   |
| Re-curation | `drakkar-diff`                                                                           | A re-curated publication's descriptions against its live ones, as files to add, revise and remove.                              |
| Writing     | `drakkar-add`, `drakkar-revise`, `drakkar-publications`, `drakkar-move`, `drakkar-batch` | Descriptions, revisions and removals, publication states and notes, moves to the special run; a whole batch in one transaction. |
| Checking    | `drakkar-check`                                                                          | Every invariant on the whole database, read-only.                                                                               |
| Releases    | `drakkar-taxonomy`, `drakkar-uniprot`                                                    | Load the NCBI taxonomy and a UniProt release ([`docs/database.md` §3](docs/database.md#3-uniprot-versioning)).                  |

Every write follows the same path ([`docs/database.md` §2](docs/database.md#2-descriptions-and-versioning)). Each row is checked on what it builds on (the publication, the snapshots, the method, the coordinates, the mappings, the note), then every invariant is checked on the whole database inside the same transaction. Without `--commit` the transaction is rolled back: a dry run is the same code as a commit, writes nothing and needs no go. With `--commit`, it commits only when no row is refused and no error is found. What is derived (human names, full-length coordinates, mapping occurrences) is computed by the tools, never given by the agent.

## A batch

A batch is the curation of at most 20 publications, orchestrated by the [`curate`](skills/curate/SKILL.md) skill. Its work directory, by default `data/sessions/run<run>/batch<n>/`, holds one directory per publication, then the merged files.

```
orchestrator (curate skill)
  1. publications   from the prompt, or the next ones of the oldest vh run
  2. full texts     drakkar-fetch, drakkar-parse     ── no subagent yet; the orchestrator never reads them
  3. curate         one subagent per publication (item.md)
                      reads the converted full text and the UniProt entries
                      writes its descriptions, curation notes, unsettled descriptions
  4. merge          batch files: descriptions to add, revise and delete, publications.tsv
  5. dry run        drakkar-batch: the whole batch checked in one transaction, rolled back
  6. report         to the curator, with the errors of the dry run    ── nothing written yet
     ── go ──
  7. commit         drakkar-batch --commit: descriptions, publications, then the move
                      of the publications left selected to the special run
```

- **Full texts first.** The orchestrator fetches every full text and its supplementary files before any subagent starts, from PMC (its open access files, Europe PMC, NCBI, the PMC article page), the publisher's page, then the free copies' PDFs (OpenAlex, Unpaywall), and converts them to text. A closed article gets no subagent; a free one no route gave is fetched once more. A subagent downloads only a missing supplementary file it needs, with `drakkar-fetch --supplement`, never the article. When no route works, the curator can provide a PDF.
- **One subagent per publication**, with its own context: it reads the publication, decides each description by the rules and writes files. It never writes to the database.
- **Unsettled is said, not guessed.** A description the subagent cannot settle goes to `descriptions.unsettled.tsv` with why ([`item.md`](skills/curate/item.md)); the publication stays `selected`.
- **A dry run before the report.** `drakkar-batch` applies the merged files in one transaction, checks every invariant on the result and rolls back. Its refused rows and errors, inconsistencies between publications among them, go to the report as they are, not fixed.
- **The report leaves no open question**: what each file holds, the publications without a full text or not curated, with why.
- **The go.** After it, the orchestrator commits the batch files, the last write moving the publications the agent could not curate fully (no full text, a file it could not read, an unsettled description) to the open special run, so the run they came from can be complete. Their manual pass happens there.

**Re-curation.** A publication already curated goes through the same batch. The subagent curates it again from its full text, without looking at its current curation, then `drakkar-diff` compares the result with its live descriptions: the descriptions to add, to revise and to remove. They are committed as a new publication's are, by the agent after the curator's go.

Batches are independent: each takes its own publications, works in its own directory and writes only them. Many could run in parallel, given distinct publications; the default pick, the next publications of the oldest run, serves one batch at a time.

## What is tracked

A publication in a run carries its state, its note and the date of the agent's last pass ([`docs/curation-rules.md` §2](docs/curation-rules.md#2-process) and [§5](docs/curation-rules.md#5-notes)): `selected` without a date waits for the agent, `curated` is done, `selected` with a date waits for a manual pass in a special run. The note, rewritten at each pass, says what was decided and keeps the history of passes and moves; each description version has its own note. Together they make every decision traceable without the conversation that took it.

## Running it

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), PostgreSQL with Drakkar, and Claude Code (or another agent that reads [`.agents/skills/`](.agents/skills/)).

```sh
uv sync
cp .env.example .env    # database connection, and the address Unpaywall asks for
```

In Claude Code, from the repository, `/curate` starts a batch: alone, it takes the next publications; or with a prompt naming publications and a work directory. The agent ends with its report and waits for the go.

The skill is linked from [`.claude/skills/`](.claude/skills/) and [`.agents/skills/`](.agents/skills/); [`AGENTS.md`](AGENTS.md) is read by the agent at the start of every conversation.

## Development

```sh
uv run pytest                    # on a test database built from sql/schema.sql and tests/fixture.sql, never Drakkar
uv run ruff check && uv run ruff format
uv run pyright
uv run mdformat --wrap no --number docs/ skills/ AGENTS.md README.md
```

## Layout

```
AGENTS.md            instructions for the agent
docs/                rules, database, tools, derived datasets, next steps (todo.md)
  logs/              cases met by the tools on real publications
  history/           the move from manual curation to the agent's curation (closed)
skills/curate/       SKILL.md (the batch), item.md (one publication)
src/drakkar/         the tools
sql/schema.sql       the database structure (written by tests/build_fixture.py)
tests/               tests and their fixture
data/                releases, reports, batch directories (not versioned)
```
