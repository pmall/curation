# Drakkar database: structure, versioning and invariants

Last updated: 2026-10-06. Sources: user answers, database inspection, legacy [enyopharma/drakkar-uniprot](https://github.com/enyopharma/drakkar-uniprot) (commit `a4dc16f`). The biological rules are in `curation-rules.md`.

Database: PostgreSQL 18, schema `public`. Drakkar is the curation database. Vinland, the published database, is rebuilt from it at each release. This copy is dedicated to Claude.

## 1. Tables

| Table                  | Role                                                                                          | Notes                                                |
| ---------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `runs`                 | A list of PMIDs for a slice of time (`type` `vh` or `hh`, `name` = sequence number).          | Future runs are `vh` only, split in two (see below). |
| `publications`         | One row per PMID, with PubMed XML converted to JSON in `metadata` (`populated` once fetched). |                                                      |
| `associations`         | (run, pmid): curation state + free-text note (`annotation`).                                  | A paper can be in a `vh` and an `hh` run.            |
| `descriptions`         | One interaction, versioned (see §2).                                                          | Foreign keys since 2026-10-05 (§5).                  |
| `methods`              | Whole PSI-MI ontology (1,328 terms), no hierarchy.                                            | Never modified.                                      |
| `proteins`             | One row per UniProt entry snapshot (see §3).                                                  |                                                      |
| `proteins_versions`    | The set of **current** snapshots, with gene names and features.                               |                                                      |
| `taxon`, `taxon_name`  | NCBI taxonomy (nested sets).                                                                  | Can lag behind UniProt.                              |
| `dataset`              | Materialized view joining everything, for consultation only.                                  | Definition in `sql/dataset.sql`.                     |
| `keywords`, `peptides` | UI highlighting / legacy artefact.                                                            | Ignored.                                             |

`hh`: no new curation, but existing hh descriptions are checked and corrected like vh ones (UniProt upgrades, invariants).

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

- A description: `association_id` (publication), `method_id`, human interactor (`protein1_id`, `start1`, `stop1`, `name1`), viral interactor (`protein2_id`, `start2`, `stop2`, `name2` = generic name), `mapping1/2` (JSON arrays of mapped sequences with their alignment on each isoform).
- An interactor is (accession, start, stop). In the database, the accession is reached through `proteins.id`, which points to one snapshot of the entry.
- **Nothing is ever deleted.** A revision sets `deleted_at` on the current row and inserts a row with the same `stable_id` and `version + 1`. Removing a description = setting `deleted_at` without a successor.
- **Structure fixes are made in place \[confirmed 2026-10-06\]:** a mapping whose JSON structure or types are wrong, while its content is right, is corrected in the row itself, without a revision: it is not a change in the data. Every version that has it is corrected, live or deleted. The only case so far: occurrence numbers stored as text (`"start":"204"` → `"start":204`, D11). The values read as numbers stay the same, and nothing else in the row changes.
- **Stable ID rule \[confirmed\]:** a description gets its stable ID when it enters the database, and the ID never changes afterwards. Every revision keeps it, whatever is corrected (method, interactors, mappings; 186 vh stable IDs changed method over their history). Its life ends only by deletion (`deleted_at` without successor). The paper never changes (V6). Uniqueness (D5) applies to **live** rows only.
- **Stable ID prefix = origin \[confirmed\]:** `EY` = created through the web interface (retired as the main path, but it may still be used occasionally, so new `EY` rows can appear); `CW` = created by Claude, whatever the source (full text, curator Excel file). Both are followed by 8 uppercase hex characters. Claude draws them from a random source (Python `secrets.token_hex(4)`). **Collision check \[confirmed\]:** before inserting, look the candidate up among **all** rows of `descriptions` (live and deleted, any prefix) and draw again if it exists. With 4.3 billion values and one writer, a retry is very unlikely, but the check is mandatory.
- **Fixing descriptions \[confirmed\]:** each kind of fix is reviewed with the user, with examples, before anything is written. No description is ever physically deleted, and no throwaway version is created. Maintenance revisions (UniProt upgrade, integrity fixes) do not touch the paper's note: the note explains curation only. Moving a viral protein to another UniProt entry (especially a mature protein, with its source entry and coordinates) is a curation decision, never a mechanical one.
- **Two separate jobs \[confirmed 2026-10-06\]:** fixing the invalid data of the database (invariant violations, list in `02-data-fixes.md`) and updating the descriptions made obsolete by a UniProt upgrade are different concepts and are never mixed: a fix judges and corrects a description against its own protein snapshots and never moves it to another snapshot; the upgrade moves descriptions from obsolete snapshots to current ones, including the hh descriptions left on snapshots made obsolete by past upgrades. A description with several problems is corrected in a single revision: each kind of problem is decided with the user, the decisions are recorded per stable ID, and the description is revised once all its problems are decided. The fixes come first, on the current release (2021_02); the UniProt upgrade comes after, on a clean database.
- **Guard functions** (`src/drakkar/descriptions.py`): on the regular curation route, Claude writes descriptions only through `add_description` (new `CW` stable ID, version 1, on a publication of a vh run: it can also be in an hh run, which is left untouched), `mark_curated` (end of a curation pass: the publication is set `curated`, its note replaced by one checked against the template of `curation-rules.md` §6 with the count of its live descriptions, pass history and curator note kept, and `ai_pass_at` set; alone, for a pass that adds no description, e.g. a publication already curated), `curate_publication` (a curation pass: all the descriptions found are added at once, then `mark_curated`; all or nothing) `revise_description` (a revision during curation, never a data fix: it recomputes everything derived from the snapshots; version + 1 of a live stable ID, same publication, the old row deleted at the same instant; a revision that changes nothing is refused; it keeps the snapshots of the description, even obsolete ones, and only a side whose accession changes takes the current snapshot of the new accession) and `update_snapshots` (the upgrade job, and only it: version + 1 that moves a description to the current snapshots, with the same method, accessions, viral coordinates, generic name and mapping sequences; only what derives from the snapshots follows: human names and full-length coordinates, mapping occurrences; refused when the description is already current, when an accession was deleted from UniProt or when the sequence of a viral interactor changed between its coordinates, both curation decisions, or when the result breaks an invariant). A publication is named by its run ID and PMID; the association ID stays internal. The caller gives accessions, method, viral coordinates, generic name and mapping sequences; the functions take the snapshots (current ones for a new description), the human gene names and full-length coordinates, compute the mapping occurrences (exact matches, otherwise a BLOSUM62 alignment, identity over the alignment length), check R3, D1–D7 and D9 against the database, and refuse the write with every problem found. Both refuse a `pending` or `discarded` publication (its state must be reconsidered first) and accept a `selected` one (curation in progress) or a `curated` one (curation done, whether descriptions were found or not). They prevent inconsistent writes, and never add to an existing mess, but detecting and fixing problems is not their concern (that is `drakkar-check` and the corrections). So they check only what a write builds on: the versioning (V2–V7) of the stable ID being read or revised (its rows are locked), a single association, method and current snapshot, a canonical sequence (and a gene name for a human protein), and well-formed mapping JSON when reading a description. The description count of a publication is its number of live stable IDs. They never commit: the caller commits, or rolls back for a dry run. Corrections of the database (`02-data-fixes.md`) do not use these functions: a fix is a revision in plain SQL that copies the live row, changes only what is fixed, and deletes the old version at the same instant; removing a description deletes its live version without successor. Renaming concerns only the wrongly named descriptions of an interactor (accession, start, stop), not all of them.
- Allowed write operations: add descriptions, revise descriptions, upgrade UniProt (and taxonomy), update association state and note, create runs and associations, apply the schema changes of §5 (foreign keys, `associations.ai_pass_at`), and fix malformed mappings in place (structure only, never the content).

## 3. UniProt versioning

**Vocabulary \[confirmed 2026-10-06\]:** a *version* is always a version of a description (stable ID, `descriptions.version`: 1, 2, 3…). A protein has *snapshots*, never versions: a snapshot is a UniProt entry as it was in a release, *current* or *obsolete*. The schema names `proteins.version` (the release a snapshot first appeared in) and `proteins_versions` (the current snapshots) are legacy and stay.

### Model

- `proteins`: one row per **entry snapshot** (accession, `version`, name, description, taxon, canonical and isoform sequences in `sequences`). `version` is the release in which this snapshot **first appeared**, not the latest release. Unique on (accession, version). Descriptions reference `proteins.id`.
- `proteins_versions`: one row per snapshot still valid in the latest imported release (`current_version`), keyed by (accession, version) → `proteins`. Unique on (accession, current_version): at most one current snapshot per accession.
- A snapshot **absent** from `proteins_versions` is **obsolete**.
- `proteins` is **append-only**: it accumulates snapshots over the upgrades. `proteins_versions` is the pointer to "what is current".

### Upgrade process

Python port of the legacy Perl tools (`drakkar-taxonomy`, `drakkar-uniprot`), in `src/drakkar/`:

```
uv run drakkar-taxonomy data/2026_03 [--dry-run]          # 1. NCBI taxonomy first
uv run drakkar-uniprot parse data/2026_03                 # 2. UniProt XML → TSV (cached)
uv run drakkar-uniprot upgrade data/2026_03 [--dry-run]   # 3. import; the release is the directory name
```

**Data is scoped by UniProt release** \[confirmed\]: `data/<release>/` holds `taxonomy/` (the NCBI taxdump loaded with this release), `uniprot/` (the FTP files and their parsed TSV), `reports/` (upgrade report, descriptions to revise, and later the revision reports) and a `README.md` (dates and sources). `data/` is not versioned in git.

Sources: NCBI `taxdump.tar.gz`; UniProt FTP `uniprot_sprot_human.xml.gz`, `uniprot_sprot_viruses.xml.gz`, `uniprot_trembl_viruses.xml.gz` (all viral TrEMBL) and `uniprot_sprot_varsplic.fasta.gz` (isoforms). Each tool runs in one transaction; `--dry-run` rolls back. The upgrade writes `reports/uniprot_upgrade.md` and `reports/obsolete_vh_descriptions.tsv` (the descriptions to revise).

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

**Revised on 2026-10-05 \[confirmed\]:** UniProt 2026_03 deletes most viral TrEMBL entries, which leaves 4,062,406 viral snapshots obsolete and used by no description (live or deleted). Plan: first revise all obsolete and invalid descriptions, then delete the obsolete snapshots that no description row references, for a slim database. The foreign keys prevent deleting any snapshot still referenced.

### Consequences

- **A UniProt upgrade includes the taxonomy** \[confirmed\]: load the latest NCBI `taxdump` first, then UniProt. Some inconsistencies remain, usually for obscure taxa: resolve merged taxa with `merged.dmp`, and report (do not skip) the remaining ones.
- The 2021_02 upgrade was followed by bulk revisions (most version ≥ 2 rows were created between 2021-05-11 and 2021-06-02).
- **Current state:** latest release 2021_02. A trial of the taxonomy + UniProt 2026_03 upgrade was run on 2026-10-05, followed by an automatic fix of descriptions that was not acceptable; the database was restored from the dump. The upgrade is to be redone step by step with the user, after the invalid data is fixed (§2). What the trial measured: 230,069 new snapshots, 1,130,162 current entries, 14,607 live vh descriptions (1,580 papers) on obsolete snapshots; the 2026_03 data and the trial reports are in `data/2026_03/`.
- **UniProt now keeps only Swiss-Prot and the TrEMBL entries of reference proteomes**: other TrEMBL entries are deleted ("not part of a reference proteome"; viral TrEMBL went from 4.9 M to 1.1 M entries). 507 viral accessions used by live vh descriptions are deleted in 2026_03. About half have an identical sequence in a current entry of the same virus; the others need a check against the paper. Rules C3 and C4 (`curation-rules.md`) cover the choice of the closest entry and the mapping identity (≥ 96 %).
- The `dataset` view was redefined on 2026-10-05 (`sql/dataset.sql`): same columns, taxa read from the taxonomy for both proteins (it hard-coded *Homo sapiens* nested-set values that were already stale), no description hidden by a missing taxon, and indexes (unique on `description_id`, so `REFRESH MATERIALIZED VIEW CONCURRENTLY dataset` works).

## 4. Invariants

Checked by `uv run drakkar-check <report dir>` (report: `check.md` and one TSV per violated invariant). Scope: **vh and hh** [confirmed: hh descriptions are corrected too]. "Live" = `deleted_at IS NULL`. Severity: **error** = must never happen; **warning** = needs a look; **upgrade** = not an invariant violation: the description is obsolete, left to the upgrade job. Invariants judge a description against the snapshots it points to, whether they are obsolete or not: coordinates within its sequence, mappings found in it, names equal to its gene names. Being on current snapshots (D2) is a separate question, handled by the upgrade job (§2), and is reported, not counted as an error. The method chosen by the curator is not checked (D8 dropped [confirmed]).

Counts measured by `drakkar-check` on 2026-10-06, on UniProt 2021_02, before any fix (rows of the report, vh / hh). The fix list is `02-data-fixes.md`:

| ID  | Invariant                                                                                                                                                                                                                                                                                      | Severity             |             vh |                                                                             hh |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | -------------: | -----------------------------------------------------------------------------: |
| R3  | Every protein of a live description has a row in `taxon`.                                                                                                                                                                                                                                      | error                |              1 |                                                                              0 |
| V2  | Versions of a stable ID are contiguous from 1.                                                                                                                                                                                                                                                 | error                |              0 |                                                                              0 |
| V3  | At most one live row per stable ID, and it is the highest version.                                                                                                                                                                                                                             | error                |              0 |                                                                              0 |
| V4  | Each non-last version is deleted, no later than the next version's creation.                                                                                                                                                                                                                   | error                |              0 |                                                                              0 |
| V5  | `deleted_at` is not before `created_at`.                                                                                                                                                                                                                                                       | error                |              0 |                                                                              0 |
| V6  | All versions of a stable ID belong to the same publication.                                                                                                                                                                                                                                    | error                |              0 |                                                                              0 |
| V7  | Stable ID format: `EY` or `CW` + 8 uppercase hexadecimal characters; legacy hh bulk import: `EYUW` + 6.                                                                                                                                                                                        | error                |              0 |                                                                              0 |
| D1  | Protein 1 is human; protein 2 is viral in vh, human in hh.                                                                                                                                                                                                                                     | error                |              0 |                                                                              0 |
| D2  | Both proteins are current snapshots (latest UniProt release).                                                                                                                                                                                                                                  | upgrade              |              1 |                                                                         14,484 |
| D3  | Viral interactors: 1 ≤ start ≤ stop ≤ canonical length (the coordinates of the mature protein).                                                                                                                                                                                                | error                |              0 |                                                                              0 |
| D4  | Human interactors are the full protein: start = 1 and stop = canonical length, the only rule for their coordinates.                                                                                                                                                                            | error                |            264 |                                                                            356 |
| D5  | One live description per (publication, method, interactor 1, interactor 2).                                                                                                                                                                                                                    | error                |      70 groups |                                                                              0 |
| D6  | One non-empty generic name per viral interactor.                                                                                                                                                                                                                                               | error                |              0 |                                                                              0 |
| D7  | Human names (`name1`, and `name2` in hh) are the gene name of their snapshot.                                                                                                                                                                                                                  | warning              |          1,120 |                                                                              3 |
| D9  | Mapping content: an uppercase amino acid sequence, once per side, with an occurrence at ≥ 96 % identity that fits the sequences of the snapshot (C4). Text numbers are read as numbers. Human and viral mappings are separate fixes.                                                           | error                |             53 |                                                                              0 |
| D10 | One viral interactor (start, stop) per generic name of a viral protein (accession, generic name): the converse of D6.                                                                                                                                                                          | error                |              0 |                                                                              0 |
| D11 | Mapping structure, not content, on every version (live or deleted): a list of objects `{sequence: string, isoforms: [{accession: string, occurrences: [{start, stop, identity: numbers}]}]}`. Bad structure or bad types, e.g. numbers stored as text, fixed in place without a revision (§2). | error                |              0 | 0 (fixed in place on 2026-10-06; before: 7,256 live sides + 102 deleted sides) |
| S1  | A publication with a live description is `selected` (curation in progress) or `curated` (done, with or without descriptions).                                                                                                                                                                  | error                | 3 publications |                                                                              0 |
| S3  | A publication Claude decides on has a note.                                                                                                                                                                                                                                                    | error, new data only |              — |                                                                              — |
| S5  | Run names are unique.                                                                                                                                                                                                                                                                          | error                |              0 |                                                                              0 |
| S6  | A Claude note starts with the template header, and its state matches `associations.state`.                                                                                                                                                                                                     | error, new data only |              — |                                                                              — |
| S7  | A publication with a non-null `ai_pass_at` is `selected` or `curated`, and has a Claude note.                                                                                                                                                                                                  | error, new data only |              — |                                                                              — |
| S8  | The date of the last `Pass` line of a Claude note equals `ai_pass_at`.                                                                                                                                                                                                                         | error, new data only |              — |                                                                              — |

S3, S6–S8 apply to Claude's work and are not implemented yet. One invariant per fix: D3 and D4 are separate fixes (viral: the coordinates of the mature protein; human: 1 to the length), and a description violating both is fixed in a single revision. R1, R2, R4 and V1 are enforced by foreign keys and unique constraints.

### Integration checks (planned)

Not invariants: no rule is broken, but a big disparity is worth a look [confirmed 2026-10-06]. Not implemented yet.

- **I1, mature protein length across accessions:** mature proteins are scoped by accession (D6, D10), but the same mature protein (same virus, same generic name) is supposed to have about the same length on every accession. A big length disparity between accessions is reported for review. To decide when implementing: the virus level used to group accessions (e.g. the species in the taxonomy) and the size of a "big" disparity.

### Data scope for "new data only"

Rules marked "new data only" apply to descriptions with the Claude prefix (`CW`) and to associations whose note has a Claude entry (`[YYYY-MM-DD Claude] ACTION:`, template in `curation-rules.md` §6).

## 5. Schema changes (applied on 2026-10-05)

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

## 6. Verification script

`uv run drakkar-check <report dir>` (`src/drakkar/check.py`): one query per invariant, run in a transaction that only creates temporary tables and is always rolled back; a Markdown summary (`check.md`) and one TSV of violating rows per invariant; exit code 1 if any error. Run it before and after every write session.

## 7. Open technical questions

1. The PubMed query used to fill runs.
1. Taxonomy: the legacy loading script (source files, nested-set computation), to reuse in the upgrade.
1. Licenses: many open access papers (including part of the PMC open access subset) are under non-commercial licenses (CC BY-NC, BY-NC-ND). Does Drakkar's use allow text-mining them?
1. An Elsevier text-mining API key, to download Elsevier open access papers (most of the failed downloads)?

### Resolved

- Order of work (2026-10-06): the invalid data of the current database is fixed first, one kind at a time with the user, then the UniProt upgrade is done as a separate job (§2).
- `stable_id` generation: any randomness, with a collision check (§2).
- PSI-MI: the `methods` table is never modified. D8 uses the PSI-MI OBO file (HUPO-PSI `psi-mi.obo`), downloaded and pinned in the repository, read-only, only to get the MI:0001 hierarchy. A term needed but missing from `methods` is reported to the user.
- Garbage collection of obsolete proteins: done after the descriptions are revised (§3).
- Runs: no split. One run per batch; full-text access is stored on the publication and checked at curation time (§1).
