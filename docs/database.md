# Drakkar database: structure, versioning and invariants

Drakkar is the curation database (PostgreSQL, schema `public`); Vinland, the published database, is rebuilt from it at each release.

Its whole structure (tables, constraints, indexes, rules, the `dataset` view) is `sql/schema.sql`, written from the database by `tests/build_fixture.py`, never by hand: run it again after every change of structure. The tests build their database from it.

## 1. Tables

| Table | Role |
| -- | -- |
| `runs` | The PMIDs of one PubMed query (`type` `vh` or `hh`, `name` = sequence number), or a special run (vh, `special-<n>`). New runs are `vh`. |
| `publications` | One row per PMID, with the PubMed record as JSON in `metadata`. |
| `associations` | A publication in a run: its `state`, its publication note (`annotation`) and the date of Claude's last curation pass (`ai_pass_at`): the states below. |
| `descriptions` | Descriptions, versioned (§2), each version with its description note (`annotation`, `notes.md`). |
| `methods` | The PSI-MI ontology, never modified: a missing term is reported to the user. Each term has its `synonyms` and `is_detection`, true for the interaction detection methods (under MI:0001), both from the PSI-MI file. |
| `proteins` | One row per snapshot of a UniProt entry (§3). |
| `proteins_versions` | The current snapshots, with their gene names, synonyms, features (chains, peptides), whether the entry is in Swiss-Prot (`reviewed`) and its secondary accessions (old accessions UniProt merged into it), from the UniProt release; `search`, its accession, names, taxon and protein name in one text, trigram-indexed. |
| `taxon`, `taxon_name` | The NCBI taxonomy. It can lag behind UniProt: a snapshot's taxon can be missing from it (R3). `taxon.search`: all the names of a taxon in one text, trigram-indexed. |
| `dataset` | A materialized view joining everything, one row per description version, for consultation and exports only. Its readers expect its columns, their order and types. A snapshot whose taxon is missing from `taxon` keeps its rows, with taxon name `Obsolete`. Its unique index on `description_id` allows `REFRESH MATERIALIZED VIEW CONCURRENTLY`. |

### States

A publication of a vh run moves through these states, its association's `state` and `ai_pass_at`:

| State + `ai_pass_at` | Meaning |
| -- | -- |
| `pending` | Not pre-curated yet: every publication of a new run starts there. |
| `selected`, null | Kept at pre-curation, from its title and abstract: waiting for Claude's curation pass. |
| `selected`, date | Claude could not curate it fully, a relevant file missing: waiting for a manual pass, in a special run. |
| `curated` | All its relevant files explored and all its descriptions extracted, with or without descriptions (by Claude if dated). |
| `discarded` | Rejected at pre-curation. |

A run is **complete** when every publication is `discarded` or `curated`. Claude is **done with a run** when no publication is `pending` and every `selected` publication has a date. The publications left `selected` with a date are moved, when the user asks, to the open special run, the highest `special-<n>`, so the run they leave can be complete: the association changes run, its descriptions with it, and a `Moved` note goes first in its note (`notes.md`); a new special run is opened when the user says so. A `discarded` publication without a Claude note may have been decided on the abstract or on the full text: the two cannot be told apart, and such states are left as they are.

## 2. Descriptions and versioning

- A description: `association_id` (publication), `method_id`, human interactor (`protein1_id`, `start1`, `stop1`, `name1`), viral interactor (`protein2_id`, `start2`, `stop2`, `name2` = generic name), `mapping1/2` (mapped sequences with their occurrences on each isoform, JSON).
- An interactor is (accession, start, stop); the accession is reached through `proteins.id`, which points to one snapshot of the entry.
- **Nothing is ever deleted.** A revision deletes the live version (`deleted_at`) and inserts the next version under the same stable ID at the same instant; a removal deletes the live version with no successor. A stable ID never changes and keeps its publication (V6); uniqueness (D5) applies to live versions only.
- **Errors in the data** (invariant violations) should not happen: every write is checked (below). An error found anyway is fixed outside the regular process, decided with the user: a fix corrects a description against its own snapshots, never moves it to another snapshot (that is the versioning pass), and goes through `drakkar-revise` with a `FIXED` note. A malformed mapping (D11) is corrected in place, without a revision, on every version that has it: its values stay the same and nothing else in the row changes.
- **Writes** (`src/drakkar/write.py`, `tools.md`): descriptions and publication states are written only by `add_descriptions`, `revise_descriptions` and `update_publications`, or by their commands `drakkar-add`, `drakkar-revise` and `drakkar-publications`; `write_batch` (`drakkar-batch`) runs them on a curation batch. Each writes its rows in one transaction. Each row is checked on what it builds on (a `selected` or `curated` publication, the snapshots, the method, the coordinates, the mappings), never on its note and refused with every problem found. Then every invariant (§4) is checked on the whole database as the transaction sees it, and the transaction commits only on demand (`--commit`), with no row refused and no error; otherwise it rolls back, which makes the dry run. Rules across descriptions (D5, D6, D10) are left to that check, so a change that passes through inconsistent states (a rename carried by several descriptions, a fix with a merge) is judged on its result.
  - A new description gets a new `CW` stable ID, version 1, on a publication of a vh run, on the current snapshots.
  - A revision is version + 1 of the live version it was decided on (refused if the live version changed since), same publication, the old row deleted at the same instant. It keeps the snapshots of the description, even obsolete ones, except on a side whose accession changes. A revision that changes nothing is refused, unless it changes only skipped mappings (below): it is then skipped.
  - A removal deletes the live version without successor and adds its `REMOVED` line to its note. A merged duplicate names its survivor, which has the same publication, method and interactors (those the removed description was decided to have, when given) and holds all its mapping sequences.
  - Derived, never given: human names and full-length coordinates, and mapping occurrences (identity as defined in `glossary.md`; a mapping whose best identity is below 90 % is skipped, the rest of its description written). The occurrences follow fixed rules: exact matches first, on every isoform that has one; otherwise a BLOSUM62 alignment with gaps −10/−2 (an arbitrary choice: only the rules of `curation-rules.md` §3 matter), and the isoforms with the best score keep every placement of their optimal alignments, each with the highest identity among its alignments; on each isoform, overlapping placements form one cluster, chains included, which keeps its first placement (smallest start, then smallest stop). U, O and J, not in BLOSUM62, are aligned as X.
  - A publication update sets the state (`selected` or `curated`) and `ai_pass_at`, and puts the note of the pass first in the publication's note, after its date (`notes.md`).
  - Moving an interactor to the current snapshot of the same accession is the versioning pass, not a revision.

## 3. UniProt versioning

### Model

- `proteins` holds one row per **snapshot** (accession, `version`, name, description, taxon, canonical and isoform sequences in `sequences`). `version` is the release in which the snapshot **first appeared**. Descriptions point to `proteins.id`.
- `proteins_versions` lists the current snapshots: one per accession of the latest release (`current_version`), keyed by (accession, version). A snapshot absent from it is **obsolete**.
- `proteins` only grows: each release adds a snapshot per new or changed entry, and an unchanged entry keeps its snapshot.

### Releases

A release is loaded by the upgrade job (`tools.md`), the NCBI taxonomy first, then UniProt. UniProt keeps only Swiss-Prot and the TrEMBL entries of reference proteomes: human Swiss-Prot entries are mostly updated in place, viral entries used by descriptions are often deleted. An entry whose taxon is missing from the taxonomy is imported, and the taxon is not added (R3).

1. Each entry of the release is matched with an existing snapshot that is **unchanged**: same accession, same taxon, exactly the same isoform sequences, and (**human only**) the same primary gene name. Viral names are not compared, as the curator sets the generic name independently of UniProt; the human gene name is, as a curation relies on it. Description changes are ignored.
2. Unchanged: the snapshot keeps its `proteins.id`, and the descriptions using it stay valid. Changed or new: a new `proteins` row; the old snapshot becomes obsolete, and the descriptions using it need revision (the versioning pass).
3. `proteins_versions` is fully rebuilt: every accession of the release gets one row pointing to its snapshot, new or kept. Accessions removed from UniProt (deleted, merged, demerged) get no row: their snapshots become obsolete too.

**An accession can have several snapshots, and several obsolete ones**: one per release where its entry changed. Different descriptions, or different versions of one description, can use different snapshots of the same accession. So any comparison about a description (sequence, length, gene name, taxon) uses the snapshot the description points to (`protein1_id`, `protein2_id`), never "the latest old snapshot" of the accession. Example: a protein with an older, longer snapshot used by a live description and a later, shorter one: comparing the later one with another entry can wrongly say "same sequence".

After a versioning pass, the obsolete snapshots that no description row references (live or deleted) are deleted. A snapshot used by a deleted version is kept, so that the history of a description can be read; current snapshots are never deleted.

## 4. Invariants

Checked by `uv run drakkar-check <report dir>` (`check.md` and one TSV per violated invariant), and inside every write (§2). Scope: vh and hh. "Live" = `deleted_at IS NULL`. Severity: **error** = must never happen; **warning** = needs a look; **upgrade** = an obsolete interactor, left to the versioning pass; **info** = good to know. Invariants judge a description against the snapshots it points to, current or obsolete. The method chosen is not checked.

| ID | Invariant | Severity |
| -- | -- | -- |
| R3 | Proteins of live descriptions whose taxon is not in `taxon`: a mismatch between UniProt and the NCBI taxonomy, not an error on our side; the `dataset` view lists such descriptions anyway, a question of reading the dataset, not of curation. | info |
| V2 | Versions of a stable ID are contiguous from 1. | error |
| V3 | At most one live row per stable ID, and it is the highest version. | error |
| V4 | Each non-last version is deleted, no later than the next version's creation. | error |
| V5 | `deleted_at` is not before `created_at`. | error |
| V6 | All versions of a stable ID belong to the same publication. | error |
| V7 | Stable ID format: `EY` or `CW` + 8 uppercase hexadecimal characters; `EYUW` + 6 for a bulk import of hh descriptions. | error |
| D1 | Protein 1 is human; protein 2 is viral in vh, human in hh. | error |
| D2 | Both proteins are current snapshots (latest UniProt release). | upgrade |
| D3 | Viral interactors: 1 ≤ start ≤ stop ≤ canonical length (the coordinates of the mature protein). | error |
| D4 | Human interactors are the full protein: start = 1 and stop = canonical length, the only rule for their coordinates. | error |
| D5 | One live description per (publication, method, interactor 1, interactor 2). | error |
| D6 | One non-empty generic name per viral interactor. | error |
| D7 | Human names (`name1`, and `name2` in hh) are the gene name of their snapshot. | warning |
| D9 | Mapping content: an uppercase amino acid sequence, once per side, its `nter` and `cter` (when present, not empty) at its ends, with at least one occurrence. Each stored occurrence is judged on its own, against the protein segment at its coordinates, on the mapping without its `nter` and `cter`: an occurrence recorded at 100 % is exactly the mapping; otherwise the mapping aligned end to end on the segment is no more than 1 point below the recorded identity (gap placement can differ). No identity threshold: low identities are D12 warnings. Whether the mapping could also be found elsewhere or on other isoforms is not checked. Text numbers are read as numbers. | error |
| D10 | One viral interactor (start, stop) per generic name of a viral snapshot (`protein2_id`, generic name): the converse of D6. Grouped by snapshot, not accession: coordinates on different snapshots are not comparable (Vpu P05919: 1–81 is the whole old protein, 1–82 the whole new one). | error |
| D11 | Mapping structure, not content, on every version (live or deleted): a list of objects `{sequence: string, nter: string, cter: string, isoforms: [{accession: string, occurrences: [{start, stop, identity: numbers}]}]}`, `nter` and `cter` optional. Bad structure or bad types, e.g. numbers stored as text, fixed in place without a revision (§2). | error |
| D12 | Mapping identity: the best occurrence of a mapping is below 96 % (`EY` descriptions) or 90 % (`CW`). | warning |
| S1 | A publication with a live description is `selected` (curation in progress) or `curated` (done, with or without descriptions). | error |
| S5 | Run names are unique. | error |
