# Fixing the invalid data of the current database

This is the list of invalid data in Drakkar as it stands today, on UniProt 2021_02, before any upgrade. It covers invariant violations only: each description is judged against the protein snapshots it points to, whether they are obsolete or not, and a fix never moves it to another snapshot. Moving descriptions off obsolete snapshots is the UniProt upgrade job, done later (`database.md` §2). Terms are defined in `glossary.md`.

Rules: each problem is fixed one at a time, only when the user says so. Each fix is first explained in plain words, with examples and a count, and nothing is written until the user approves that specific fix. No description is physically deleted, and no throwaway version is created.

Workflow \[confirmed 2026-10-06\]:

- A problem is defined by its fix (what we change), not by how it is detected.
- Problems are fixed in the order of this list, because some fixes depend on others. Viral names and coordinates concern a viral protein as a whole, across all its descriptions: they are decisions (which name, which coordinates are right; UniProt chains are the source of truth for a mature protein). They come before duplicates, because putting a viral interactor on its right coordinates can turn two descriptions into one. Mappings come last, because their occurrences are computed on the interactor's snapshot and coordinates.
- Points 1 to 9 fix only the descriptions that need that single fix. A description that needs several fixes is set aside in point 10, fixed last, in a single revision that merges all its corrections.
- The description list, with its point, is `data/2021_02/reports/fix-list-2026-10-06.tsv` (rebuilt after point 1), built by `uv run drakkar-fix-list <check report dir> <output TSV>` (`src/drakkar/fix_list.py`). Rebuild it after each fix, from a new check report.

Source: `uv run drakkar-check` on 2026-10-06, read-only. The full rows are in `data/2021_02/reports/check-2026-10-06/` (`check.md`, plus one TSV per invariant, named after the invariant ID in brackets below).

Scope measured: 117,457 live vh descriptions in 6,048 publications, and 299,446 live hh descriptions in 9,363 publications. Versioning, stable IDs and protein types have no violations.

## Problems

Counts are descriptions (stable IDs), each in a single point.

| #   | Problem                                                                                         | Invariants | vh descriptions | hh descriptions | Status         |
| --- | ----------------------------------------------------------------------------------------------- | ---------- | --------------: | --------------: | -------------- |
| 1   | Descriptions on a publication not selected or curated                                           | S1         |               7 |               0 | done           |
| 2   | Viral protein whose species is missing from the taxonomy                                        | R3         |               1 |               0 | upgrade        |
| 3   | Human gene name out of date (warning)                                                           | D7         |           1,120 |               0 | done           |
| 4   | Human coordinates not 1 to the length                                                           | D4         |             264 |             346 | done           |
| 5   | Viral name: the same (accession, name) has inconsistent coordinates across descriptions         | D10        |               0 |               — | nothing to fix |
| 6   | Viral coordinates: the same (accession, start, stop) has inconsistent names across descriptions | D6         |               0 |               — | nothing to fix |
| 7   | Same description recorded several times                                                         | D5         |             216 |               0 | done           |
| 8   | Human mappings not fitting the sequences (content)                                              | D9         |       see below |       see below | open           |
| 9   | Viral mappings not fitting the sequences (content)                                              | D9         |       see below |               — | open           |
| 10  | Descriptions that need several fixes, fixed last                                                | several    |               0 |               3 | to do          |

### 1. Descriptions on a publication not selected or curated [S1]

**Done on 2026-10-06** (approved by the user), in two writes:

- The 7 descriptions are removed (their live version deleted, no successor): `UPDATE descriptions SET deleted_at = now()` on their live rows. Report: `data/2021_02/reports/remove-descriptions-of-discarded/applied.tsv`.
- The 3 publications are set `curated`, with no description: `UPDATE associations SET state = 'curated', updated_at = now()`. Their curator's note is kept, and `ai_pass_at` stays empty (not a Claude pass). Report: `data/2021_02/reports/curate-discarded-after-selection/applied.tsv`.

Check after: `data/2021_02/reports/check-2026-10-06-after-point-1/` (S1 = 0, versioning unchanged).

Three vh publications had live descriptions but were marked `discarded`: PMID 10603321 (run 1-16, 3 descriptions), PMIDs 41586518 and 41902231 (run 85, 2 descriptions each). They had been selected and read: the descriptions were added, then the full text showed the host protein is not human (mouse hnRNP-A1 with MHV, porcine DDX5 with PEDV, tree shrew RNF6 with Zika). Both the state and the descriptions were wrong. `discarded` is a pre-curation decision only: a selected publication found without a virus–human PPI on the full text is `curated` with no description [confirmed 2026-10-06].

### 2. Viral protein whose species is missing from the taxonomy [R3]

**Left to the UniProt upgrade** \[confirmed 2026-10-06\]: taxonomy problems go with the UniProt upgrade, which loads the NCBI taxonomy first.

The vh description EY05645BC3 (PMID 29290611) uses G8EFI1 (Lloviu virus nucleoprotein), whose taxon 1559366 is not in the `taxon` table. NCBI deleted that taxon when the species was renamed *Cuevavirus lloviuense* (taxon 3052148), so it cannot be loaded. G8EFI1 is not deleted from UniProt: it is in 2026_03 with taxon 3052148 and the same sequence (749 residues). It is missing from our 2021_02 release, most likely because the legacy Perl import skipped entries whose taxon was missing. The upgrade gives G8EFI1 a new snapshot on taxon 3052148, and `update_snapshots` moves the description to it: same accession, same sequence, no curation decision.

### 3. Human gene name out of date [D7, warning]

**Done on 2026-10-06** (approved by the user): each of the 1,120 descriptions is revised to the gene name of the snapshot it is on, nothing else. A revision copies the live row, changes only what is fixed, and saves it as the next version; the old version is deleted at the same instant [confirmed 2026-10-06]. Plain SQL: `INSERT INTO descriptions (stable_id, version, name1, <other columns copied>, created_at) SELECT stable_id, version + 1, <gene name of protein1_id>, <other columns>, now()` from the live rows, then `UPDATE descriptions SET deleted_at = now()` on them. Checked before committing: 1,120 new versions, every other column (mappings included) byte-identical. Report: `data/2021_02/reports/point-3-gene-names/applied.tsv`; check after: `data/2021_02/reports/check-2026-10-06-after-point-3/` (D7 = 0 in vh, versioning unchanged).

Reviewed against HGNC before the fix (`data/2021_02/reports/point-3-gene-names-review.tsv`): all 149 proteins make sense, the recorded name and the gene name are the same gene. 140 are HGNC previous symbols of the gene; the others are protein names in use (MIC13, RYDEN), an old symbol shared with EPRS1 but on the right accession (QARS), a missing name ("N/A"), or genes renamed again since 2021_02 (UQCC6, H2BC12L, H2AC25, H2BC26, and METTL13, whose 2021_02 name is EEF1AKNMT): those follow the snapshot now and the upgrade later.

1,120 vh descriptions, covering about 150 distinct (accession, recorded name, gene name) combinations, have a human name that is not the gene name of their snapshot. Most are renamings, for example CYR61 → CCN1 and TMEM189 → PEDS1. One has "N/A" as the name (A6NNZ2, gene TUBB8B). The 3 hh descriptions with this problem also have wrong coordinates (point 10).

### 4. Human coordinates not 1 to the length [D4]

**Done on 2026-10-06** (approved by the user): each of the 610 descriptions is revised, the wrong human side set to 1 to the length of the snapshot it is on, nothing else (463 on interactor 1, 154 on interactor 2: 7 hh descriptions had both). Plain SQL, as in point 3: copy of the live row with only `start`/`stop` of that side changed, as version + 1, the old version deleted at the same instant. Checked before committing: every other column byte-identical. Report: `data/2021_02/reports/point-4-human-coordinates/applied.tsv`; check after: `data/2021_02/reports/check-2026-10-06-after-point-4/` (D4 = 0 except the 3 descriptions of point 10, versioning unchanged).

Reviewed before the fix (`data/2021_02/reports/point-4-human-coordinates-review.tsv`): every case has the same story. An earlier version of the description had the same coordinates, and they were 1 to the length of its snapshot; the description was then moved to a newer snapshot of a different length without updating them. In one case the protein itself changed: EY488D795C was on Q31612 (an HLA-B allele, 363 residues), then moved to P01889 (HLA-B, 362 residues) in May 2021, still 1–363. None of these descriptions had a wrong name.

610 descriptions (264 vh, 346 hh) have a human interactor whose coordinates are not 1 to the length of its sequence. The fix is the only rule for a human interactor: 1 to the length. Counting all 620 violations: in vh, 123 go past the end and 141 stop short; in hh, 294 go past the end and 62 stop short. For example, O60645 is recorded as 1–756 but has 745 residues, and E9PRG8 is recorded as 1–122 but has 123 residues. None of these descriptions is on an obsolete snapshot: most likely the coordinates were not updated when the description was moved to a new snapshot.

### 5. Viral name: the same (accession, name) has inconsistent coordinates across descriptions [D10]

No (accession, name) has inconsistent coordinates today: nothing to fix. The fix would be a decision for the virus as a whole: which coordinates are right.

### 6. Viral coordinates: the same (accession, start, stop) has inconsistent names across descriptions [D6]

No (accession, start, stop) has inconsistent names today: nothing to fix. The fix would be a decision for the virus as a whole: which name is right.

### 7. Same description recorded several times [D5]

**Done on 2026-10-06** (approved by the user). The 70 groups had two causes, and in every group the copies were identical in every column and created by a bulk import in the same second:

- **The same row imported several times** (58 groups, 125 descriptions, PMIDs 30209081, 31710650, 31873071, imported in January 2021): identical from their first version. One copy is kept per group (the first stable ID in alphabetical order), the 67 others are removed (their live version deleted, no successor). Report: `data/2021_02/reports/point-7-duplicates/applied.tsv`.
- **HLA alleles merged** (12 groups, 91 descriptions, PMIDs 21454588, 25782006, 27775586, 30209081): each copy was first on a different HLA allele entry; on 2021-05-26 they were all moved to the reference entries (HLA-A P04439, HLA-B P01889, HLA-C P10321), which made them identical. The biologists decided to remove every description involving an HLA protein \[confirmed 2026-10-06\]: 1,076 live descriptions (241 vh in 77 publications, 835 hh in 73 publications, any `HLA-` gene), removed the same way. This settles these groups. List reviewed before: `data/2021_02/reports/hla-descriptions.tsv`; report: `data/2021_02/reports/hla-removal/applied.tsv`. Rule: `curation-rules.md` §4.

Check after: `data/2021_02/reports/check-2026-10-06-after-point-7/` (D5 = 0, no live HLA description, versioning unchanged).

A description, (PMID, PSI-MI ID, interactor 1, interactor 2), is recorded once. There are 70 groups of live descriptions with the same combination: 216 descriptions, 146 of them extra, in 6 vh publications. By publication: PMID 31873071 (25 groups), 31710650 (22), 30209081 (12), 21454588 (7), 27775586 (3), 25782006 (1). For example, PMID 21454588 has HLA-A (P04439) with B2VQG4 by MI:0070 recorded 5 times. That publication is about HLA, which may not be a PPI under the curation rules.

### 8. Human mappings not fitting the sequences [D9]

### 9. Viral mappings not fitting the sequences [D9]

**Open** (2026-10-06). Points 8 and 9 are handled together: a wrong mapping, human or viral, is fixed by realigning its sequence (taken from the publication, never changed) on the snapshot, and a mapping that cannot be realigned is a problem for the curator [confirmed 2026-10-06]. Alignments on isoforms count like those on the canonical sequence.

D9 is incomplete: it verifies only occurrences stored at 100 % (53 viral mappings in 36 descriptions). A full audit (`data/2021_02/reports/mapping-audit.tsv`, read-only) realigned every live mapping with `map_sequence` and compared with what is stored: 643 human mappings (495 descriptions) and 417 viral mappings (364 descriptions) differ, mostly isoforms where the sequence aligns but is not stored; 19 mappings do not realign at all (16 coronavirus peptides of PMID 34799561 crossing the boundary of their mature protein or on the wrong one, 2 HCV Core peptides of PMID 25485706 starting with the initiator methionine outside Core 2–191, and WNK1 in EY8EDA52AB).

**These counts are not reliable**: `map_sequence` does not compute identity as the old curation app did, and the old app is right [confirmed 2026-10-06]. Example: EY8EDA52AB, WNK1 on isoform Q9H4A3-5, stored at 96.31 % (418 identities / 434), 95.87 % with `map_sequence`, so wrongly below 96 %. A realignment of 842 descriptions applied on 2026-10-06 dropped 75 such isoform occurrences: it was undone the same day (the 842 new versions physically deleted, the previous versions live again, every mapping checked identical to before, `descriptions_id_seq` set back to the highest id). Before any realignment: get the old app's identity formula, and check that our alignment reproduces the stored values.

### 10. Descriptions that need several fixes

Three hh descriptions, each fixed in a single revision:

- EY88BB570E (PMID 25416956): name AES → TLE5 (Q08117), and Q9BSW2 recorded as 1–395 out of 731 residues.
- EYC706A74A (PMID 25416956): name CCDC155 → KASH5 (Q8N6L0), and P17544 recorded as 1–494 out of 483 residues.
- EYUW004803 (PMID 32296183): name FAM86C1 → FAM86C1P (Q9NVL1), and Q9BSW2 recorded as 1–395 out of 731 residues.

## In-place structure fix: malformed mappings [D11]

**Done on 2026-10-06** (approved by the user): 5,154 rows (5,100 live, 54 deleted versions, 5,129 stable IDs), 51,015 values. Only the quotes were removed: each number keeps its digits (`"100"` → `100`, `"99.72973"` → `99.72973`), as the rest of the database writes them. Checked before committing: no malformed mapping left (D11 = 0), mapping content unchanged (same D9 rows), all other columns and the row count unchanged, and every rewritten column equal to the old text with only those quotes removed. Function: `fix_mapping_numbers` (`src/drakkar/fixes.py`); report of every rewritten column: `data/2021_02/reports/fix-mapping-numbers/applied.tsv`; check after: `data/2021_02/reports/check-2026-10-06-after-numbers/`.

A malformed mapping has a bad structure or bad types, while its content is right. Fixing it is not a change in the data, so not a revision: the rows are corrected in place \[confirmed 2026-10-06, `database.md` §2\]. The only structure problem today: 5,100 live hh descriptions (7,830 mappings, 159 publications, created between 2019-11-27 and 2021-05-25) store the numbers of their occurrences as text, e.g. `"start":"204","identity":"98.64865"`, instead of numbers. Read as numbers, their positions fit the sequences. The fix turns each text number into the same number and changes nothing else. It is independent of the points above: 3 of these descriptions are also in point 4. 54 deleted hh versions (102 sides) have the same format, 29 of them in descriptions whose live version is fine. **All are fixed, live and deleted versions** \[confirmed 2026-10-06\]: numbers as text should never have been there. The fix list marks 5,129 descriptions (`malformed_mapping`): 5,100 with a live version to fix, 29 with only a deleted one.

## Not in this list: obsolete descriptions

14,485 live descriptions are on an obsolete snapshot: 14,484 hh descriptions (440 proteins, 866 publications), left over from past upgrades never applied to hh, and the vh description of problem 2. Besides problem 2, 141 of them also have occurrence numbers as text, fixed in place without touching their snapshot. They are moved to current snapshots by the UniProt upgrade job, later.
