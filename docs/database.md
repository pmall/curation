# Drakkar database: structure, versioning and invariants

Last updated: 2026-10-05. Sources: user answers, database inspection, legacy [enyopharma/drakkar-uniprot](https://github.com/enyopharma/drakkar-uniprot) (commit `a4dc16f`). The biological rules are in `curation-rules.md`.

Database: PostgreSQL 18, schema `public`. Drakkar is the curation database. Vinland, the published database, is rebuilt from it at each release. This copy is dedicated to Claude.

## 1. Tables

| Table                  | Role                                                                                          | Notes                                                |
| ---------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `runs`                 | A list of PMIDs for a slice of time (`type` `vh` or `hh`, `name` = sequence number).          | Future runs are `vh` only, split in two (see below). |
| `publications`         | One row per PMID, with PubMed XML converted to JSON in `metadata` (`populated` once fetched). |                                                      |
| `associations`         | (run, pmid): curation state + free-text note (`annotation`).                                  | A paper can be in a `vh` and an `hh` run.            |
| `descriptions`         | One interaction, versioned (see §2).                                                          | No foreign keys yet (to be added, see §5).           |
| `methods`              | Whole PSI-MI ontology (1,328 terms), no hierarchy.                                            | Never modified.                                      |
| `proteins`             | One row per UniProt entry snapshot (see §3).                                                  |                                                      |
| `proteins_versions`    | The set of **current** snapshots, with gene names and features.                               |                                                      |
| `taxon`, `taxon_name`  | NCBI taxonomy (nested sets).                                                                  | Can lag behind UniProt.                              |
| `dataset`              | Materialized view joining everything, for consultation only.                                  | Definition in `sql/dataset.sql`.                     |
| `keywords`, `peptides` | UI highlighting / legacy artefact.                                                            | Ignored.                                             |

`hh` data is frozen history and is out of scope for curation and invariants.

### Runs and full-text access [confirmed]

One run per PubMed batch, with plain numeric names. Association states: `pending` (default, not pre-curated), `selected`, `discarded`, `curated`; no new state for now. Claude's work is tracked on the association: `ai_pass_at` (§5) is the date of Claude's curation pass. Per-run status (complete, done by Claude) is defined in `curation-rules.md` §3 and reported by the check script.

Full-text availability, measured on run 87 (2,328 PMIDs, 2026-10-05):

| Category                                 | PMIDs | `selected` | What Claude can download                                                       |
| ---------------------------------------- | ----: | ---------: | ------------------------------------------------------------------------------ |
| PMC, open access subset                  | 1,289 |        114 | Structured XML through the APIs (Europe PMC `fullTextXML`, NCBI BioC, PMC OA). |
| PMC, not open access (incl. manuscripts) |    58 |          2 | Readable on the web only; text mining not allowed, so not accessible.          |
| PMC, bioRxiv preprint                    |   134 |          1 | Not peer-reviewed: discarded at pre-curation anyway.                           |
| Not in PMC, open access elsewhere        |   322 |         25 | Publisher, repository or preprint copy; plain download worked for 6 of the 25. |
| Not in PMC, not open access              |   525 |         27 | Abstract only.                                                                 |

Open access status outside PMC comes from OpenAlex. Most failed downloads were Elsevier (redirect pages; Elsevier has a text-mining API with a free key), PNAS and Taylor & Francis (HTTP 403).

Papers reach PMC with a lag: 75–84 % of the papers of runs 70–79 (2022–2023) are in PMC today, against 60–67 % for runs 80–87.

`runs.name` has no unique constraint; the check script verifies it (S5).

## 2. Descriptions and versioning

- A description: `association_id` (paper), `method_id`, human interactor (`protein1_id`, `start1`, `stop1`, `name1`), viral interactor (`protein2_id`, `start2`, `stop2`, `name2` = generic name), `mapping1/2` (JSON arrays of mapped sequences with their alignment on each isoform).
- An interactor is (accession, start, stop). In the database, the accession is reached through `proteins.id`, which points to one snapshot of the entry.
- **Nothing is ever deleted.** A revision sets `deleted_at` on the current row and inserts a row with the same `stable_id` and `version + 1`. Removing a description = setting `deleted_at` without a successor.
- **Stable ID rule \[confirmed\]:** a description gets its stable ID when it enters the database, and the ID never changes afterwards. Every revision keeps it, whatever is corrected (method, interactors, mappings; 186 vh stable IDs changed method over their history). Its life ends only by deletion (`deleted_at` without successor). The paper never changes (V6). Uniqueness (D5) applies to **live** rows only.
- **Stable ID prefix = origin \[confirmed\]:** `EY` = created through the web interface (retired as the main path, but it may still be used occasionally, so new `EY` rows can appear); `CW` = created by Claude, whatever the source (full text, curator Excel file). Both are followed by 8 uppercase hex characters. Claude draws them from a random source (Python `secrets.token_hex(4)`). **Collision check \[confirmed\]:** before inserting, look the candidate up among **all** rows of `descriptions` (live and deleted, any prefix) and draw again if it exists. With 4.3 billion values and one writer, a retry is very unlikely, but the check is mandatory.
- Allowed write operations: add descriptions, revise descriptions, upgrade UniProt (and taxonomy), update association state and note, create runs and associations, apply the schema changes of §5 (foreign keys, `associations.ai_pass_at`).

## 3. UniProt versioning

### Model

- `proteins`: one row per **entry snapshot** (accession, `version`, name, description, taxon, canonical and isoform sequences in `sequences`). `version` is the release in which this snapshot **first appeared**, not the latest release. Unique on (accession, version). Descriptions reference `proteins.id`.
- `proteins_versions`: one row per snapshot still valid in the latest imported release (`current_version`), keyed by (accession, version) → `proteins`. Unique on (accession, current_version): at most one current snapshot per accession.
- A snapshot **absent** from `proteins_versions` is **obsolete**.
- `proteins` is **append-only**: it accumulates snapshots over the upgrades. `proteins_versions` is the pointer to "what is current".

### Upgrade process

Python port of the legacy Perl tools (`drakkar-taxonomy`, `drakkar-uniprot`), in `src/drakkar/`:

```
uv run drakkar-taxonomy <taxdump dir> [--dry-run]           # 1. NCBI taxonomy first
uv run drakkar-uniprot parse <release dir>                   # 2. UniProt XML → TSV (cached)
uv run drakkar-uniprot upgrade <release> <release dir> [--dry-run]
```

Sources: NCBI `taxdump.tar.gz`; UniProt FTP `uniprot_sprot_human.xml.gz`, `uniprot_sprot_viruses.xml.gz`, `uniprot_trembl_viruses.xml.gz` (all viral TrEMBL) and `uniprot_sprot_varsplic.fasta.gz` (isoforms). Each tool runs in one transaction; `--dry-run` rolls back. The upgrade writes `report.md` and `obsolete_vh_descriptions.tsv` (the descriptions to revise) in the release directory.

Differences with the Perl tools: entries whose taxon is missing from `taxon` are imported and reported instead of skipped (the type comes from the file); retired taxa keep their names; taxon names are written as a diff.

The matching logic (same as the Perl import):

1. Stage the new release: FASTA (canonical + isoforms) and XML (gene names, features) into `uniprot_entries` / `uniprot_metadata`. These staging tables no longer exist.
1. For each root taxon (human 9606, then viruses), take the staged entries whose taxon is under it.
1. For each entry, look for an existing snapshot that is **unchanged**: same accession, same taxon, exactly the same isoform sequences, and (**human only**) the same primary gene name. Viral names are not compared because the curator sets the viral name (`name2`, generic name) independently of UniProt. The human gene name is compared because a curation can rely on it (`name1`, and the paper names the human protein by its gene). Description changes are ignored. [confirmed]
1. Unchanged → the snapshot keeps its `proteins.id`. Descriptions using it stay valid with no change.
1. Changed or new → a new `proteins` row. The old snapshot becomes obsolete, and the descriptions using it **need revision**.
1. `proteins_versions` is fully rebuilt for the root taxon: every accession of the new release gets one row pointing to its snapshot (new or kept), with `current_version` set to the new release. Accessions removed from UniProt (deleted, merged, demerged) get no row: their snapshots become obsolete too.

So `proteins` holds every snapshot of every accession that ever entered the database.

### What accumulates, and garbage collection

Example: release R2 changes the sequence of P12345, whose snapshot (id 10, `version` R1) was current.

| Step          | `proteins`                                       | `proteins_versions`                            |
| ------------- | ------------------------------------------------ | ---------------------------------------------- |
| Before        | id 10 (P12345, R1)                               | (P12345, R1) → current R1                      |
| Upgrade to R2 | id 10 kept; **id 99 (P12345, R2) inserted**      | rebuilt: (P12345, R2) → current R2             |
| After         | id 10 is obsolete, still referenced by its users | descriptions on id 10 must be revised to id 99 |

An unchanged entry inserts nothing: its snapshot stays, and only `current_version` moves to R2. So each upgrade adds one row per **new or changed** entry, and nothing is removed. Serial ids are never reused, so deleting would not cause collisions either: keeping everything is a choice for history, not a technical constraint.

"Garbage collection" would mean deleting obsolete snapshots that **no description row** (live or deleted) references. Snapshots referenced only by deleted versions must be kept, otherwise the history of a description can no longer be read. Measured on 2026-10-05:

| Snapshots                                       |  Human |     Viral |
| ----------------------------------------------- | -----: | --------: |
| Current, used by a description                  | 17,281 |     3,136 |
| Current, unused                                 |  3,114 | 4,903,966 |
| Obsolete, used (by deleted rows, except G8EFI1) |    512 |        55 |
| Obsolete, unused (GC candidates)                |    143 |    36,764 |

The GC candidates are 0.7 % of the table (2.6 GB). The bulk is the current but unused viral entries (all viral UniProt, TrEMBL included), which GC would not touch. Some snapshots end up useless (never used, no longer in UniProt), but they stay few over time. **Decision: no garbage collection** [confirmed].

**Revised on 2026-10-05 \[confirmed\]:** UniProt 2026_03 deleted most viral TrEMBL entries, which left 4,062,406 viral snapshots obsolete and used by no description (live or deleted). Plan: first revise all obsolete and invalid descriptions, then delete the obsolete snapshots that no description row references, for a slim database. The foreign keys prevent deleting any snapshot still referenced.

### Consequences

- **A UniProt upgrade includes the taxonomy** \[confirmed\]: load the latest NCBI `taxdump` first, then UniProt. Some inconsistencies remain, usually for obscure taxa: resolve merged taxa with `merged.dmp`, and report (do not skip) the remaining ones.
- The 2021_02 upgrade was followed by bulk revisions (most version ≥ 2 rows were created between 2021-05-11 and 2021-06-02).
- **2026-10-05 upgrade:** NCBI taxonomy of 2026-10-05, then UniProt 2026_03 (releases present: 2019_01, 2020_03, 2020_05, 2021_02, 2026_03). 230,069 new snapshots, 1,130,162 current entries. 14,607 live vh descriptions (1,580 papers) now reference obsolete snapshots and must be revised [confirmed: next step, before curation resumes].
- **UniProt now keeps only Swiss-Prot and the TrEMBL entries of reference proteomes**: other TrEMBL entries are deleted ("not part of a reference proteome"; viral TrEMBL went from 4.9 M to 1.1 M entries). 507 viral accessions used by live vh descriptions were deleted. About half have an identical sequence in a current entry of the same virus; the others need a check against the paper. Rules C3 and C4 (`curation-rules.md`) cover the choice of the closest entry and the mapping identity (≥ 96 %).
- The `dataset` view was redefined on 2026-10-05 (`sql/dataset.sql`): same columns, taxa read from the taxonomy for both proteins (it hard-coded the *Homo sapiens* nested-set values), no description hidden by a missing taxon, and indexes (unique on `description_id`, so `REFRESH MATERIALIZED VIEW CONCURRENTLY dataset` works).

## 4. Invariants (draft, to agree on)

Scope: `vh` runs only. "Live" = `deleted_at IS NULL`. Severity: **error** = must never happen; **warning** = needs a look.

Current counts were measured on 2026-10-02.

### Referential integrity

| ID  | Invariant                                                                  | Severity | Current             |
| --- | -------------------------------------------------------------------------- | -------- | ------------------- |
| R1  | Every description references an existing association, method and proteins. | error    | 0 (FKs planned, §5) |
| R2  | Every association references an existing run and publication.              | error    | 0 (FKs exist)       |
| R3  | Every protein used by a description has a row in `taxon`.                  | error    | 1 (G8EFI1)          |
| R4  | Every `proteins_versions` row references an existing `proteins` snapshot.  | error    | 0 (FK planned, §5)  |

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

| ID  | Invariant                                                                                                                     | Severity | Current                                                                   |
| --- | ----------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------- |
| D1  | Protein 1 is human (`type = 'h'`), protein 2 is viral (`type = 'v'`).                                                         | error    | 0                                                                         |
| D2  | Both proteins are current snapshots (present in `proteins_versions`).                                                         | error    | 1 (G8EFI1)                                                                |
| D3  | 1 ≤ start ≤ stop ≤ canonical length, for both interactors.                                                                    | error    | 0 for vh                                                                  |
| D4  | Human interactor is full length (start = 1, stop = canonical length).                                                         | error    | 264                                                                       |
| D5  | No two live descriptions share (paper, method, interactor 1, interactor 2), with interactor = (accession, start, stop).       | error    | 70 groups / 216 rows                                                      |
| D6  | One generic name (`name2`) per viral interactor, non-empty.                                                                   | error    | 0                                                                         |
| D7  | `name1` equals the human protein's current gene name.                                                                         | warning  | to measure on vh                                                          |
| D8  | The method belongs to the PSI-MI interaction detection branch (MI:0001).                                                      | error    | needs the PSI-MI ontology (no hierarchy in `methods`)                     |
| D9  | Each mapping has at least one occurrence at ≥ 96 % identity, within [start, stop] of its interactor (`curation-rules.md` C4). | error    | 16 vh mappings with no occurrence (on 2026-10-05, before the UniProt fix) |

### Curation state

| ID  | Invariant                                                                                  | Severity                | Current                                    |
| --- | ------------------------------------------------------------------------------------------ | ----------------------- | ------------------------------------------ |
| S1  | A paper with ≥ 1 live description is `curated`.                                            | error                   | 25 rows on `selected` / `discarded` papers |
| S2  | *Dropped*: a `curated` paper may have zero descriptions (full text read, nothing found).   | —                       | pmid 37097169 is valid                     |
| S3  | A paper Claude decides on (`curated` or `discarded`) has a note.                           | error for new data only | legacy: most notes are empty               |
| S4  | Associations of `vh` runs only contain `vh` descriptions (protein types per D1).           | error                   | 0                                          |
| S5  | Run names are unique.                                                                      | error                   | 0                                          |
| S6  | A Claude note starts with the template header, and its state matches `associations.state`. | error for new data only | 0                                          |
| S7  | A paper with a non-null `ai_pass_at` is `selected` or `curated`, and has a Claude note.    | error for new data only | 0                                          |
| S8  | The date of the last `Pass` line of a Claude note equals `ai_pass_at`.                     | error for new data only | 0                                          |

### Data scope for "new data only"

Rules marked "new data only" apply to descriptions with the Claude prefix (`CW`) and to associations whose note has a Claude entry (`[YYYY-MM-DD Claude] ACTION:`, template in `curation-rules.md` §6).

## 5. Schema changes [allowed by the user]

Foreign keys. Every one holds today (0 orphans, measured 2026-10-05), and none conflicts with the ingestion order: proteins are inserted before `proteins_versions` is rebuilt, and runs, associations and proteins exist before a description is inserted.

```sql
ALTER TABLE descriptions
  ADD FOREIGN KEY (association_id) REFERENCES associations (id),
  ADD FOREIGN KEY (method_id) REFERENCES methods (id),
  ADD FOREIGN KEY (protein1_id) REFERENCES proteins (id),
  ADD FOREIGN KEY (protein2_id) REFERENCES proteins (id);
ALTER TABLE proteins_versions
  ADD FOREIGN KEY (accession, version) REFERENCES proteins (accession, version);
```

Not added: `proteins.ncbi_taxon_id` → `taxon`, because taxonomy can lag behind UniProt and the FK would block the import. R3 stays a script check.

Date of Claude's curation pass on associations:

```sql
ALTER TABLE associations ADD COLUMN ai_pass_at timestamp;
```

Null = Claude has not made its curation pass on this paper. A date = the last pass, whatever its outcome. The history of passes is kept in the note (`Pass` lines, `curation-rules.md` §6). `selected` with a date = needs a manual pass. A new association state may come later, not now.

## 6. Verification script (plan)

- Python project managed with uv, checked with ruff and pyright, run as `uv run drakkar-check`.
- One invariant = one SQL query returning the violating rows (with stable ID, PMID and the values involved), declared with its ID, severity and scope.
- Runs in a **read-only** transaction.
- Output: a Markdown report (counts per invariant + sample rows), formatted with mdformat; non-zero exit code if any error.
- Known legacy violations can be accepted in a baseline file, so the check stays green while still reporting them.
- Run it before and after every write session.

## 7. Open technical questions

1. The PubMed query used to fill runs.
1. Taxonomy: the legacy loading script (source files, nested-set computation), to reuse in the upgrade.
1. Legacy violations (D4, D5, S1, R3/D2) are fixed after the UniProt upgrade [confirmed]. Open: through revisions with a note on the paper, for each of them?
1. Licenses: many open access papers (including part of the PMC open access subset) are under non-commercial licenses (CC BY-NC, BY-NC-ND). Does Drakkar's use allow text-mining them?
1. An Elsevier text-mining API key, to download Elsevier open access papers (most of the failed downloads)?

### Resolved

- `stable_id` generation: any randomness, with a collision check (§2).
- PSI-MI: the `methods` table is never modified. D8 uses the PSI-MI OBO file (HUPO-PSI `psi-mi.obo`), downloaded and pinned in the repository, read-only, only to get the MI:0001 hierarchy. A term needed but missing from `methods` is reported to the user.
- Garbage collection of obsolete proteins: done after the descriptions are revised (§3).
- Runs: no split. One run per batch; full-text access is stored on the publication and checked at curation time (§1).
