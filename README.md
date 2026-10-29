# Drakkar

Drakkar is the curation database of virus–human protein–protein interactions. This repository is the harness in which an AI agent curates Drakkar under the user's supervision: the Drakkar database and everything around it, the curation that uses it, and the instructions the agent follows.

## The idea

The agent curates; the user supervises. The agent reads each publication, decides its descriptions and writes them into files. Drakkar's writes check those files against the whole database, and nothing reaches Drakkar before the user's go on a report. Every version of every description is kept, so no write is irreversible and a publication can always be curated again.

## Instructions

[`AGENTS.md`](AGENTS.md) is read by the agent at the start of every conversation: how it works with the user, writes to and queries the database. Each package explains its own rules in its `docs/`:

- Database: [`glossary.md`](database/docs/glossary.md), the terms, one meaning each, used everywhere; [`database.md`](database/docs/database.md), the tables, the states of a publication, the publication and description notes, versioning, UniProt releases, invariants; [`datasets.md`](database/docs/datasets.md), what is exported from Drakkar; [`tools.md`](database/docs/tools.md), the file formats and the `database-*` commands.
- Curation: [`curation-rules.md`](curation/docs/curation-rules.md), the biological rules explained in full (the principles, what is curated, how each value of a description is identified), which the curator agent's prompt holds in condensed form; [`tools.md`](curation/docs/tools.md), the `curation-*` commands; [`glossary.md`](curation/docs/glossary.md), the curation's own terms.

The Drakkar database is made for many clients and is unaware of the curation; the curation is made for the Drakkar database and uses its terms, so a curation doc may point to a database doc, never the reverse.

Each rule is written once, in its package's docs, except the curation rules: the curator agent's prompt holds them, and `curation-rules.md` explains them. Each skill and the agent are self-contained: each holds its whole process, start to end, and reads no doc, so its context goes to its job.

## Two packages

The repository is a uv workspace of two packages, each standing alone:

- [`database/`](database/), **the Drakkar database** and everything around it: its structure, the commands that read, check and write it, `database-*`, the only way to write to it; the UniProt releases it loads; the datasets it exports, with the generic viral proteins they show.
- [`curation/`](curation/), **the curation**, a client of the Drakkar database: the commands that set up and assemble a curation, `curation-*`, which never touch the database; the agent and the skills that curate.

The curation never imports the Drakkar database's code: it reaches it only through the `database-*` commands its agent and skills run. Both are run from the repository root with `uv run <command>` and described in each package's `tools.md`.

## Database

| Purpose | Commands | What they do |
| -- | -- | -- |
| Reading | `database-read` | Look up methods, taxa, entries (by accession, name or sequence), sequences and the generic names in use; run any read-only SQL query. |
| Mapping | `database-mapping` | Compute the occurrences of mapping sequences on an identified entry exactly as the write does, to check them. |
| Diffing | `database-diff` | Compare a publication's curated descriptions with its live ones, and write the differences as files to add, revise and remove. |
| Writing | `database-add`, `database-revise`, `database-publications`, `database-batch` | Write descriptions, revisions and removals, publication states and notes; write a whole batch in one transaction. |
| Checking | `database-check` | Check every invariant on the whole database, read-only. |
| Releases | `database-taxonomy`, `database-uniprot` | Load the NCBI taxonomy and a UniProt release. |
| Generic viral proteins | `database-generic` | Keep the species and the generic viral proteins of the vh descriptions dataset (`database/generic/`) in step with Drakkar. |
| Derived datasets | `database-export` | Export the vh and hh descriptions, the sequences of the viral interactors and the mappings, as files for other applications. |

Every write follows the same path ([`database.md` §2](database/docs/database.md#2-descriptions-and-versioning)). Each row is checked against what it builds on (the publication, the snapshots, the method, the coordinates, the mappings), never against its note; then every invariant is checked on the whole database, inside the same transaction. Without `--commit`, the transaction is rolled back: a dry run runs the same code as a commit, writes nothing and needs no go. With `--commit`, it commits only when no row is refused and no error is found. What is derived (human names, full-length coordinates, mapping occurrences) is computed by the tools, never given by the agent.

A publication in a run carries its state, its note and the date of the agent's last pass (`database.md`, [states](database/docs/database.md#states) and [notes](database/docs/database.md#notes)): `selected` without a date waits for the agent, `curated` is done, `selected` with a date waits for a manual pass in a special run. Each pass and each move puts its note at the top of the publication's note, so that note keeps their whole history; each description version has its own note. Together, they make every decision traceable without the conversation that made it.

The [`export`](database/skills/export/SKILL.md) skill brings the generic viral proteins in step, then exports the derived datasets ([`datasets.md`](database/docs/datasets.md)).

## Curation

| Purpose | Commands | What they do |
| -- | -- | -- |
| Full texts | `curation-fetch`, `curation-download`, `curation-parse` | Download a full text with its supplementary files, convert them and list them in a manifest; download and convert one file from a URL; convert files (XML, HTML, PDF, Word, spreadsheets) to texts named by their format. |
| NCBI sequences | `curation-genbank` | Search NCBI protein records and read their sequences, for a strain UniProt lacks. |
| Notes | `curation-notes` | Build a batch's publications file from its publication notes. |

An agent curates, a skill runs it:

- The [`curator`](curation/agents/curator.md) agent curates one publication from its full text, in its publication directory, into its descriptions and its publication note. Its prompt is the whole curation: it holds the curation rules in condensed form; [`curation-rules.md`](curation/docs/curation-rules.md) explains them.
- The [`curate`](curation/skills/curate/SKILL.md) skill curates a batch of publications, one or many, each by a curator agent, then merges the results, dry-runs them and writes them after the user's go. A single publication is a batch of one.

A batch's work directory, by default `_data/sessions/run<run>/batch<n>/` (`_data/sessions/batch<n>/` when its publications come from several runs), holds one directory per publication and the merged files.

```
orchestrator (curate skill)
  1. publications   from the prompt
  2. full texts     curation-fetch, unless done        ── no subagent yet; the orchestrator never reads them
  3. curate         one curator agent per publication (curator.md)
                      reads the converted full text and the UniProt entries
                      writes its descriptions and its publication note
  4. merge          batch files: descriptions.jsonl (cat), publications.jsonl (curation-notes)
  5. dry run        database-batch: the whole batch checked in one transaction, rolled back
  6. report         to the user, with the errors of the dry run       ── nothing written yet
     ── go ──
  7. commit         database-batch --commit: descriptions, publications
```

- **Full texts first.** Before any subagent starts, the orchestrator fetches every full text with its supplementary files and converts them to text. It tries PMC (its open access files, Europe PMC, NCBI, the PMC article page), then the publisher's page, then the PDFs of free copies (OpenAlex, Unpaywall). A free article that could not be downloaded is fetched once more; a publication still without its article gets no subagent. A subagent never downloads the article: it downloads a missing supplementary file it needs from the URL the text gives (`curation-download`), and any file it needs to identify an interactor, its coordinates or a mapping (a sequence, an entry, a taxon) from a public database. When no route works, the user can provide the files: they are set up as the fetch would set them up, with their manifest.
- **One subagent per publication**: the `curator` agent, with its own context, the shell, a tool to read files and web search. It reads the publication, decides each description by the rules and writes files; it never writes to the database.
- **Every description is written.** Each value comes from the first tier that gives it, from the most direct to the most inferred ([`curation-rules.md`](curation/docs/curation-rules.md)); a publication stays `selected` only when the subagent could not get a relevant file.
- **A dry run before the report.** `database-batch` applies the merged files in one transaction, checks every invariant on the result and rolls back. Its refused rows and errors, including inconsistencies between publications, go into the report as they are, unfixed.
- **The report leaves no open question**: it says what each file holds, which publications have no full text or were not curated, and why.
- **The go.** The orchestrator then commits the batch files. The publications the agent could not curate fully (a relevant file missing: the full text or a supplementary file) stay `selected` with a date. When the user asks, they are moved to the open special run, where their manual pass happens, so that the run they came from can be complete.

Batches are independent: each takes its own publications, works in its own directory and writes only those. Several batches can run in parallel on distinct publications.

## Running it

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), PostgreSQL with Drakkar, and Claude Code.

```sh
uv sync                 # both packages
cp .env.example .env    # database connection, the address Unpaywall asks for, the NCBI API key
```

In Claude Code, run from the repository, `/curate` starts a batch on the publications its prompt asks for, one PMID or several, in the work directory the prompt names or the default one. The agent ends with its report and waits for the go. `/export` exports the derived datasets.

[`.claude/skills/`](.claude/skills/) and [`.claude/agents/`](.claude/agents/) link the skills and the agent of both packages. Every skill is started by the user only: Claude never starts one on its own.

## Development

```sh
uv run pytest                    # database/tests/ on a test database built from its sql/schema.sql and tests/fixture.sql, never Drakkar; curation/tests/ with no database
uv run ruff check && uv run ruff format
uv run pyright
uv run mdformat --wrap no --number --compact-tables database/docs/ database/skills/ database/generic/ curation/docs/ curation/agents/ curation/skills/ AGENTS.md README.md
```

Each package also runs its own tests and checks from its folder.

## Layout

```
AGENTS.md            instructions for the agent
.claude/             links to the agent and the skills of both packages
pyproject.toml       the workspace of the two packages
database/            the Drakkar database
  docs/              glossary, database, tools, derived datasets; history/ (closed)
  src/database/      reads, checked writes, invariants, releases, exports
  tests/             their tests and fixture
  sql/schema.sql     the database structure (written by tests/build_fixture.py)
  skills/            export (the derived datasets, the generic viral proteins first)
  generic/           the species and generic viral proteins of the vh descriptions dataset
curation/            the curation, a client of the Drakkar database
  docs/              curation rules, tools, glossary; history/ (closed)
  src/curation/      full texts, NCBI sequences, a batch's notes
  tests/             their tests and samples
  agents/            curator.md (one publication curated)
  skills/            curate (a batch of publications, one or many)
_data/               releases, reports, batch directories (not versioned)
```
