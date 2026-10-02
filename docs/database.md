# Drakkar database: structure, versioning and invariants

Last updated: 2026-10-02. Sources: user answers, database inspection, legacy [enyopharma/drakkar-uniprot](https://github.com/enyopharma/drakkar-uniprot) (commit `a4dc16f`). The biological rules are in `curation-rules.md`.

Database: PostgreSQL 18, schema `public`. Drakkar is the curation database. Vinland, the published database, is rebuilt from it at each release. This copy is dedicated to Claude.

## 1. Tables

| Table                  | Role                                                                                          | Notes                                                     |
| ---------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| `runs`                 | A list of PMIDs for a slice of time (`type` `vh` or `hh`, `name` = sequence number).          | Future runs are `vh` only.                                |
| `publications`         | One row per PMID, with PubMed XML converted to JSON in `metadata` (`populated` once fetched). |                                                           |
| `associations`         | (run, pmid): curation state + free-text note (`annotation`).                                  | A paper can be in a `vh` and an `hh` run.                 |
| `descriptions`         | One interaction, versioned (see §2).                                                          | **No foreign keys** to associations, methods or proteins. |
| `methods`              | Whole PSI-MI ontology (1,328 terms), no hierarchy.                                            |                                                           |
| `proteins`             | One row per UniProt entry snapshot (see §3).                                                  |                                                           |
| `proteins_versions`    | The set of **current** snapshots, with gene names and features.                               |                                                           |
| `taxon`, `taxon_name`  | NCBI taxonomy (nested sets).                                                                  | Can lag behind UniProt.                                   |
| `dataset`              | Materialized view joining everything, for consultation only.                                  | Hides descriptions whose viral taxon is missing.          |
| `keywords`, `peptides` | UI highlighting / legacy artefact.                                                            | Ignored.                                                  |

`hh` data is frozen history and is out of scope for curation and invariants.

## 2. Descriptions and versioning

- A description: `association_id` (paper), `method_id`, human interactor (`protein1_id`, `start1`, `stop1`, `name1`), viral interactor (`protein2_id`, `start2`, `stop2`, `name2` = generic name), `mapping1/2` (JSON arrays of mapped sequences with their alignment on each isoform).
- An interactor is (accession, start, stop). In the database, the accession is reached through `proteins.id`, which points to one snapshot of the entry.
- **Nothing is ever deleted.** A revision sets `deleted_at` on the current row and inserts a row with the same `stable_id` and `version + 1`. Removing a description = setting `deleted_at` without a successor.
- **Stable ID rule \[confirmed\]:** a description gets its stable ID when it enters the database, and the ID never changes afterwards. Every revision keeps it, whatever is corrected (method, interactors, mappings; 186 vh stable IDs changed method over their history). Its life ends only by deletion (`deleted_at` without successor). The paper never changes (V6). Uniqueness (D5) applies to **live** rows only.
- Stable IDs: `EY` + 8 hex characters (existing). Claude will use a new prefix, `CW` proposed.
- Allowed write operations: add descriptions, revise descriptions, upgrade UniProt, update association state and note.

## 3. UniProt versioning

### Model

- `proteins`: one row per **entry snapshot** (accession, release, name, description, taxon, canonical and isoform sequences in `sequences`). Descriptions reference `proteins.id`.
- `proteins_versions`: one row per snapshot still valid in the latest imported release (`current_version`). Unique on (accession, current_version): at most one current snapshot per accession.
- A snapshot **absent** from `proteins_versions` is **obsolete**.

### Upgrade process (legacy Perl)

1. Stage the new release: FASTA (canonical + isoforms) and XML (gene names, features) into `uniprot_entries` / `uniprot_metadata`. These staging tables no longer exist.
1. For each root taxon (human 9606, then viruses), take the staged entries whose taxon is under it.
1. For each entry, look for an existing snapshot that is **unchanged**: same accession, same taxon, exactly the same isoform sequences, and (**human only**) the same primary gene name. Viral name changes and description changes are ignored.
1. Unchanged → the snapshot keeps its `proteins.id`. Descriptions using it stay valid with no change.
1. Changed or new → a new `proteins` row. The old snapshot becomes obsolete, and the descriptions using it **need revision**.
1. `proteins_versions` is fully rebuilt for the root taxon, so no garbage collection is needed.

### Consequences

- The import inner-joins `taxon`: an entry whose taxon is missing from `taxon` is **silently skipped**. The taxonomy must be refreshed before or with UniProt.
- The 2021_02 upgrade was followed by bulk revisions (most version ≥ 2 rows were created between 2021-05-11 and 2021-06-02).
- Current state: latest release 2021_02. Releases present: 2019_01, 2020_03 (human only), 2020_05, 2021_02. One live vh description references an obsolete snapshot (EY05645BC3 → G8EFI1, taxon 1559366 missing from `taxon`).
- Future upgrade: rewrite in Python, reading the UniProt FTP files (the unfinished `proteins_v2_xml` script started this).

## 4. Invariants (draft, to agree on)

Scope: `vh` runs only. "Live" = `deleted_at IS NULL`. Severity: **error** = must never happen; **warning** = needs a look.

Current counts were measured on 2026-10-02.

### Referential integrity (no foreign keys, so the script must check)

| ID  | Invariant                                                                  | Severity | Current       |
| --- | -------------------------------------------------------------------------- | -------- | ------------- |
| R1  | Every description references an existing association, method and proteins. | error    | 0             |
| R2  | Every association references an existing run and publication.              | error    | 0 (FKs exist) |
| R3  | Every protein used by a description has a row in `taxon`.                  | error    | 1 (G8EFI1)    |

### Versioning

| ID  | Invariant                                                                              | Severity | Current               |
| --- | -------------------------------------------------------------------------------------- | -------- | --------------------- |
| V1  | (stable_id, version) is unique.                                                        | error    | 0 (unique constraint) |
| V2  | Versions of a stable ID are contiguous from 1.                                         | error    | 0                     |
| V3  | At most one live row per stable ID, and it is the highest version.                     | error    | 0                     |
| V4  | Each non-last version is deleted, with `deleted_at` ≤ the next version's `created_at`. | error    | 0                     |
| V5  | `deleted_at` ≥ `created_at`.                                                           | error    | 0                     |
| V6  | All versions of a stable ID belong to the same association (paper).                    | error    | 0                     |
| V7  | Stable ID format: `^(EY\|CW)[0-9A-F]{8}$`.                                             | error    | 0                     |

### Description content (live rows)

| ID  | Invariant                                                                                                               | Severity                | Current                                               |
| --- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------------------------------------- |
| D1  | Protein 1 is human (`type = 'h'`), protein 2 is viral (`type = 'v'`).                                                   | error                   | 0                                                     |
| D2  | Both proteins are current snapshots (present in `proteins_versions`).                                                   | error                   | 1 (G8EFI1)                                            |
| D3  | 1 ≤ start ≤ stop ≤ canonical length, for both interactors.                                                              | error                   | 0 for vh                                              |
| D4  | Human interactor is full length (start = 1, stop = canonical length).                                                   | error                   | 264                                                   |
| D5  | No two live descriptions share (paper, method, interactor 1, interactor 2), with interactor = (accession, start, stop). | error                   | 70 groups / 216 rows                                  |
| D6  | One generic name (`name2`) per viral interactor, non-empty.                                                             | error                   | 0                                                     |
| D7  | `name1` equals the human protein's current gene name.                                                                   | warning                 | to measure on vh                                      |
| D8  | The method belongs to the PSI-MI interaction detection branch (MI:0001).                                                | error                   | needs the PSI-MI ontology (no hierarchy in `methods`) |
| D9  | Each mapping has at least one 100 % occurrence and lies within [start, stop] of its interactor.                         | error for new data only | 2,496 old mappings below 100 % (not flagged)          |

### Curation state

| ID  | Invariant                                                                        | Severity                | Current                                    |
| --- | -------------------------------------------------------------------------------- | ----------------------- | ------------------------------------------ |
| S1  | A paper with ≥ 1 live description is `curated`.                                  | error                   | 25 rows on `selected` / `discarded` papers |
| S2  | A `curated` paper has ≥ 1 live description.                                      | error                   | 1 (pmid 37097169)                          |
| S3  | A paper Claude decides on (`curated` or `discarded`) has a note.                 | error for new data only | legacy: most notes are empty               |
| S4  | Associations of `vh` runs only contain `vh` descriptions (protein types per D1). | error                   | 0                                          |

### Data scope for "new data only"

Rules marked "new data only" apply to descriptions with the Claude prefix (`CW`) and to associations Claude changed. How to recognise the latter is open: a dated tag in the note, or a list kept by the script.

## 5. Verification script (plan)

- Python project managed with uv, checked with ruff and pyright, run as `uv run drakkar-check`.
- One invariant = one SQL query returning the violating rows (with stable ID, PMID and the values involved), declared with its ID, severity and scope.
- Runs in a **read-only** transaction.
- Output: a Markdown report (counts per invariant + sample rows), formatted with mdformat; non-zero exit code if any error.
- Known legacy violations can be accepted in a baseline file, so the check stays green while still reporting them.
- Run it before and after every write session.

## 6. Open technical questions

1. The PubMed query used to fill runs.
1. The `stable_id` generation code (randomness, collision check).
1. Taxonomy: how was `taxon` / `taxon_name` loaded, and can it be refreshed along with UniProt?
1. Should legacy violations (D4, D5, S1, S2, R3/D2) be fixed by Claude through revisions, with a note, or baselined?
1. Where can the PSI-MI ontology be taken from (OBO file) to check D8?
