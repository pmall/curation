# Fixing the invalid data of the current database

This is the list of invalid data in Drakkar as it stands today, on UniProt 2021_02, before any upgrade. It covers invariant violations only: each description is judged against the protein snapshots it points to, whether they are obsolete or not, and a fix never moves it to another snapshot. Moving descriptions off obsolete snapshots is the UniProt upgrade job, done later (`database.md` §2). Terms are defined in `glossary.md`.

Rules: each problem is fixed one at a time, only when the user says so. Each fix is first explained in plain words, with examples and a count, and nothing is written until the user approves that specific fix. No description is physically deleted, and no throwaway version is created.

Workflow \[confirmed 2026-10-06\]:

- A problem is defined by its fix (what we change), not by how it is detected.
- Problems are fixed in the order of this list, because some fixes depend on others. Viral names and coordinates concern a viral protein as a whole, across all its descriptions: they are decisions (which name, which coordinates are right; UniProt chains are the source of truth for a mature protein). They come before duplicates, because putting a viral interactor on its right coordinates can turn two descriptions into one. Mappings come last, because their occurrences are computed on the interactor's snapshot and coordinates.
- Points 1 to 9 fix only the descriptions that need that single fix. A description that needs several fixes is set aside in point 10, fixed last, in a single revision that merges all its corrections.
- The description list, with its point, is `data/2021_02/reports/fix-list-2026-10-06.tsv`, built by `uv run drakkar-fix-list <check report dir> <output TSV>` (`src/drakkar/fix_list.py`). Rebuild it after each fix, from a new check report.

Source: `uv run drakkar-check` on 2026-10-06, read-only. The full rows are in `data/2021_02/reports/check-2026-10-06/` (`check.md`, plus one TSV per invariant, named after the invariant ID in brackets below).

Scope measured: 117,457 live vh descriptions in 6,048 publications, and 299,446 live hh descriptions in 9,363 publications. Versioning, stable IDs and protein types have no violations.

## Problems

Counts are descriptions (stable IDs), each in a single point.

| #   | Problem                                                                                         | Invariants | vh descriptions | hh descriptions | Status         |
| --- | ----------------------------------------------------------------------------------------------- | ---------- | --------------: | --------------: | -------------- |
| 1   | Descriptions on a publication not selected or curated                                           | S1         |               7 |               0 | to do          |
| 2   | Viral protein whose species is missing from the taxonomy                                        | R3         |               1 |               0 | to do          |
| 3   | Human gene name out of date (warning)                                                           | D7         |           1,120 |               0 | to do          |
| 4   | Human coordinates not 1 to the length                                                           | D4         |             264 |             346 | to do          |
| 5   | Viral name: the same (accession, name) has inconsistent coordinates across descriptions         | D10        |               0 |               — | nothing to fix |
| 6   | Viral coordinates: the same (accession, start, stop) has inconsistent names across descriptions | D6         |               0 |               — | nothing to fix |
| 7   | Same description recorded several times                                                         | D5         |             216 |               0 | to do          |
| 8   | Human mappings not fitting the sequences (content)                                              | D9         |               0 |               0 | nothing to fix |
| 9   | Viral mappings not fitting the sequences (content)                                              | D9         |              36 |               — | to do          |
| 10  | Descriptions that need several fixes, fixed last                                                | several    |               0 |               3 | to do          |

### 1. Descriptions on a publication not selected or curated [S1]

Three vh publications have live descriptions but are marked `discarded`: PMID 10603321 (run 1-16, 3 descriptions), PMIDs 41586518 and 41902231 (run 85, 2 descriptions each). Either the state is wrong or the descriptions are.

### 2. Viral protein whose species is missing from the taxonomy [R3]

The vh description EY05645BC3 (PMID 29290611) uses G8EFI1, whose taxon 1559366 is not in the `taxon` table. The fix is a taxonomy one: add the missing taxon, without revising the description. The description is also on an obsolete snapshot of G8EFI1, which is left to the upgrade job; G8EFI1 is already deleted from UniProt in 2021_02, so choosing another entry will be a curation decision.

### 3. Human gene name out of date [D7, warning]

1,120 vh descriptions, covering about 150 distinct (accession, recorded name, gene name) combinations, have a human name that is not the gene name of their snapshot. Most are renamings, for example CYR61 → CCN1 and TMEM189 → PEDS1. One has "N/A" as the name (A6NNZ2, gene TUBB8B). The 3 hh descriptions with this problem also have wrong coordinates (point 10).

### 4. Human coordinates not 1 to the length [D4]

610 descriptions (264 vh, 346 hh) have a human interactor whose coordinates are not 1 to the length of its sequence. The fix is the only rule for a human interactor: 1 to the length. Counting all 620 violations: in vh, 123 go past the end and 141 stop short; in hh, 294 go past the end and 62 stop short. For example, O60645 is recorded as 1–756 but has 745 residues, and E9PRG8 is recorded as 1–122 but has 123 residues. None of these descriptions is on an obsolete snapshot: most likely the coordinates were not updated when the description was moved to a new snapshot.

### 5. Viral name: the same (accession, name) has inconsistent coordinates across descriptions [D10]

No (accession, name) has inconsistent coordinates today: nothing to fix. The fix would be a decision for the virus as a whole: which coordinates are right.

### 6. Viral coordinates: the same (accession, start, stop) has inconsistent names across descriptions [D6]

No (accession, start, stop) has inconsistent names today: nothing to fix. The fix would be a decision for the virus as a whole: which name is right.

### 7. Same description recorded several times [D5]

A description, (PMID, PSI-MI ID, interactor 1, interactor 2), is recorded once. There are 70 groups of live descriptions with the same combination: 216 descriptions, 146 of them extra, in 6 vh publications. By publication: PMID 31873071 (25 groups), 31710650 (22), 30209081 (12), 21454588 (7), 27775586 (3), 25782006 (1). For example, PMID 21454588 has HLA-A (P04439) with B2VQG4 by MI:0070 recorded 5 times. That publication is about HLA, which may not be a PPI under the curation rules.

### 8. Human mappings not fitting the sequences [D9]

No human mapping has a content problem: nothing to fix. Structure problems are fixed in place (see below).

### 9. Viral mappings not fitting the sequences [D9]

36 vh descriptions (53 mappings) in 6 publications:

- 16 mappings have no occurrence. All are in PMID 34799561: 16-residue peptides on the polyproteins P0C6T5, P0C6U2 and P0C6U8.
- 36 mappings claim a 100 % occurrence that does not match the sequence, and 1 has an occurrence outside the sequence: on Q99IB8, P03377 and P06935, mostly in PMIDs 25485706 and 27375898.

### 10. Descriptions that need several fixes

Three hh descriptions, each fixed in a single revision:

- EY88BB570E (PMID 25416956): name AES → TLE5 (Q08117), and Q9BSW2 recorded as 1–395 out of 731 residues.
- EYC706A74A (PMID 25416956): name CCDC155 → KASH5 (Q8N6L0), and P17544 recorded as 1–494 out of 483 residues.
- EYUW004803 (PMID 32296183): name FAM86C1 → FAM86C1P (Q9NVL1), and Q9BSW2 recorded as 1–395 out of 731 residues.

## In-place structure fix: malformed mappings [D11]

A malformed mapping has a bad structure or bad types, while its content is right. Fixing it is not a change in the data, so not a revision: the rows are corrected in place \[confirmed 2026-10-06, `database.md` §2\]. The only structure problem today: 5,100 live hh descriptions (7,830 mappings, 159 publications, created between 2019-11-27 and 2021-05-25) store the numbers of their occurrences as text, e.g. `"start":"204","identity":"98.64865"`, instead of numbers. Read as numbers, their positions fit the sequences. The fix turns each text number into the same number and changes nothing else. It is independent of the points above: 3 of these descriptions are also in point 4. 54 deleted hh versions have the same format. **Open:** fix them in place too (proposed: yes, same format-only change), or live descriptions only?

## Not in this list: obsolete descriptions

14,485 live descriptions are on an obsolete snapshot: 14,484 hh descriptions (440 proteins, 866 publications), left over from past upgrades never applied to hh, and the vh description of problem 2. Besides problem 2, 141 of them also have occurrence numbers as text, fixed in place without touching their snapshot. They are moved to current snapshots by the UniProt upgrade job, later.
