# Fixing the invalid data of the current database

This is the list of invalid data in Drakkar as it stands today, on UniProt 2021_02, before any upgrade. It covers invariant violations only: each description is judged against the protein snapshots it points to, whether they are obsolete or not, and a fix never moves it to another snapshot. Moving descriptions off obsolete snapshots is the UniProt upgrade job, done later (`database.md` §2).

Rules: each problem is fixed one at a time, only when the user says so. Each fix is first explained in plain words, with examples and a count, and nothing is written until the user approves that specific fix. No description is physically deleted, and no throwaway version is created. A description with several problems is corrected in a single revision: the decisions are recorded per stable ID, and the description is revised once all its problems are decided.

Source: `uv run drakkar-check` on 2026-10-06, read-only. The full rows are in `data/2021_02/reports/check-2026-10-06/` (`check.md`, plus one TSV per invariant, named after the invariant ID in brackets below).

Scope measured: 117,457 live vh descriptions in 6,048 publications, and 299,446 live hh descriptions in 9,363 publications. Versioning, stable IDs, protein types and viral generic names have no violations.

## Problems

| #   | Problem                                               | Invariant | vh rows | hh rows | Status |
| --- | ----------------------------------------------------- | --------- | ------: | ------: | ------ |
| 1   | Descriptions on a publication not selected or curated | S1        |  3 pub. |       0 | to do  |
| 2   | Viral protein with an unknown species (taxonomy fix)  | R3        |       1 |       0 | to do  |
| 3   | Same interaction recorded several times               | D5        |  70 gr. |       0 | to do  |
| 4   | Viral mapping not found in the protein sequence       | D9        |      53 |       0 | to do  |
| 5   | Human coordinates past the end of the sequence        | D3        |     123 |     294 | to do  |
| 6   | Human interactor not the full-length protein          | D4        |     264 |     356 | to do  |
| 7   | Human gene name out of date (warning)                 | D7        |   1,120 |       3 | to do  |

### 1. Descriptions on a publication not selected or curated [S1]

Three vh publications have live descriptions but are marked `discarded`: PMID 10603321 (run 1-16, 3 descriptions), PMIDs 41586518 and 41902231 (run 85, 2 descriptions each). Either the state is wrong or the descriptions are.

### 2. Viral protein with an unknown species [R3]

The vh description EY05645BC3 (PMID 29290611) uses G8EFI1, whose taxon 1559366 is not in the `taxon` table. The fix is a taxonomy one: add the missing taxon, without revising the description. The description is also on an obsolete snapshot of G8EFI1, which is left to the upgrade job; G8EFI1 is already deleted from UniProt in 2021_02, so choosing another entry will be a curation decision.

### 3. Same interaction recorded several times [D5]

There are 70 groups of identical live descriptions (same publication, method, human protein and viral protein), which adds up to 146 extra rows in 6 vh publications. By publication: PMID 31873071 (25 groups), 31710650 (22), 30209081 (12), 21454588 (7), 27775586 (3), 25782006 (1). For example, PMID 21454588 has HLA-A (P04439) with B2VQG4 by MI:0070 recorded 5 times. That publication is about HLA, which may not be a PPI under the curation rules.

### 4. Viral mapping not found in the protein sequence [D9]

53 vh descriptions in 6 publications:

- 16 have no match at all. All are in PMID 34799561: 16-residue peptides on the polyproteins P0C6T5, P0C6U2 and P0C6U8.
- 37 claim a 100 % match that is not found in the sequence: on Q99IB8 (24), P03377 (11) and P06935 (2), mostly in PMIDs 25485706 (23) and 27375898 (11).

### 5. Human coordinates past the end of the sequence [D3]

123 vh rows and 294 hh rows, on 36 human proteins, have a stop greater than the sequence length. For example, O60645 is recorded as 1–756, but its sequence has 745 residues. All of these rows are also in problem 6.

### 6. Human interactor not the full-length protein [D4]

264 vh rows and 356 hh rows, on 57 human proteins, have coordinates other than 1 to the sequence length. In vh, 123 are longer than the sequence and 141 are shorter; in hh, 294 are longer and 62 are shorter. For example, E9PRG8 is recorded as 1–122, but its sequence has 123 residues. None of these rows is on an obsolete snapshot, so the coordinates do not match the snapshot the description points to. Most likely the coordinates were not updated when the description was moved to the new version.

### 7. Human gene name out of date [D7, warning]

1,120 vh rows and 3 hh rows, covering about 150 distinct (accession, recorded name, current gene name) combinations, have a human name that is not the gene name of their snapshot. Most are renamings, for example CYR61 → CCN1 and TMEM189 → PEDS1. One vh row has "N/A" as the name (A6NNZ2, gene TUBB8B). The 3 hh rows: AES → TLE5, CCDC155 → KASH5, FAM86C1 → FAM86C1P.

## Descriptions with several problems

1,986 descriptions have at least one problem. Each is revised once, with all its corrections:

| Problems                                        | Descriptions |
| ----------------------------------------------- | -----------: |
| past the end + not full length (5, 6)           |          411 |
| past the end + not full length + name (5, 6, 7) |            1 |
| not full length + name (6, 7)                   |            2 |
| not full length only (6)                        |          199 |
| name only (7)                                   |        1,120 |
| mapping not found (4)                           |           36 |
| duplicated (3)                                  |          216 |
| missing taxon (2)                               |            1 |

## Not in this list: obsolete descriptions

14,485 live descriptions are on an obsolete snapshot: 14,484 hh rows (440 proteins, 866 publications), left over from past upgrades never applied to hh, and the vh description of problem 2. None of them has another problem from this list. They are moved to current snapshots by the UniProt upgrade job.
