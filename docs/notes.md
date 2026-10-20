# Notes

The notes are Claude's memory of its curation: from them alone, Claude can tell what it read on a publication, what it kept and left out and why, and how each description was decided, to curate it again, update it and report on it. A description note carries no date: a version is dated by its `created_at`. A publication note keeps the dated history of its passes and moves. Notes are short, a few words per line, with fixed labels so they can be searched: a report reads the headers for the states, the `Not read` lines for the relevant files missing, the `Not kept` lines for what was left out, and the `best-effort` description lines for the values a reviewer should see. A note never holds a number the database already gives, such as the count of descriptions.

## Publication note

`associations.annotation`: the notes of the publication, the newest first, each followed by a line `---` and the previous ones. A curation pass writes its note, a header line `STATE: summary` and its detail lines; a move to a special run writes the note `Moved YYYY-MM-DD: from run <name>`.

| State | Summary |
| -- | -- |
| `SELECTED` | Before a pass, what the abstract suggests; after one, as `CURATED`, then the relevant files missing. |
| `DISCARDED` | `<reason code>`, then a short why: `no-viral-protein`, `no-human-protein`, `no-ppi` (no physical interaction suggested), `non-human-host`, `review`, `preprint`, `not-research` (editorial, erratum, protocol…), `other`. |
| `CURATED` | The source (`from PMC1234567`, `from <URL>`, `from a PDF provided by the user`, `from curator file <name>`), then what the publication shows in a few words; with no description, why. |

Detail lines, in this order:

- `Full text:` the line written by the fetch (`tools.md`), or `Full text: PDF provided by the user`.
- `Strain: <strain> (<where in the publication>)`, when one strain holds for all the viral interactors; otherwise each description's `Entry` line gives it.
- `Not read: <file> (<where cited>) — <why>`, one per supplementary file listed or cited and not read: `not relevant, <what it holds>`, or `relevant, <why it could not be read>`, which keeps the publication `selected`.
- `Not kept: <pair or claim> (<where>) — <reason>`, one per pair the publication shows that is not a description, the reason in words.
- `Remark: <anything a next pass needs that no other line holds>` (for a curator file, how ambiguous rows were interpreted).
- `Pass YYYY-MM-DD: <outcome>`, dated by the curation: `curated from <source>`, `re-curated from <source>`, `partial from <source>, <files> missing`, `not accessible (<why>)`.

## Description note

`descriptions.annotation`, one note per version: the decision that made the version, then the decisions taken on it later without a new version (an interactor put aside, an in-place correction, a removal), each a line `ACTION: summary` followed by `- ` detail lines. The history of a description is its notes read version by version.

| Action | When | Example summary |
| -- | -- | -- |
| `CREATED` | A new description: its method and where the publication shows it | `anti-tag co-IP (MI:0007), Fig. 2B and 5C` |
| `REVISED` | A revision in a re-curation, written by `drakkar-diff`: what changed, then the new evidence | `re-curation, mappings2 1 added, 0 removed; anti-tag co-IP (MI:0007), Fig. 2B` |
| `FIXED` | A fix of an error in the data | `name1 AES → TLE5, gene name of the snapshot` |
| `UPDATED` | A revision of the versioning pass | `UniProt 2026_03, Q77YF9 → P12520 (deleted; NL4-3 Vpr), 1–78 → 1–96` |
| `ASIDE` | An interactor put aside, in place on the live version | `side 2 B0FAN5 deleted, HIV-1 patient isolate, no strain in the publication` |
| `CORRECTED` | An in-place correction, no new version | `isoform renamed by UniProt, P01106-1 → P01106` |
| `REMOVED` | A removal, in place on the last version; by a re-curation, its reason is in the publication note's `Not kept` line | `HLA protein`, `not found by the re-curation` |

The detail lines of a `CREATED` note are written for each value that is not obvious, and only for those. Obvious are an accession the publication gives, a human protein by its gene name, a viral protein of the publication's strain by its name, a chain of the entry, and a mapping the publication writes or the subsequence of the interactor at coordinates the publication gives. Each line names the tier of the value by its label (`curation-rules.md` §4), its evidence, and every source outside Drakkar by its identifier (`GenBank BAB32872.1`, `UniSave P26662 v45`, `Addgene 12345`):

- `Entry: <as published> (<where>) → <accession> (<strain of the entry>), <label>: <evidence>`; for a family or a complex, the member chosen and why.
- `Coordinates: <start>–<stop>, <label>: <evidence>`, for a mature protein.
- `Mapping: <as published> (<where>), <label>: <evidence>`, with the sequence it was taken from; below 90 % identity, why it is kept.
- `Remark: <what was arbitrary, what stays uncertain, what would change the decision>`.

## Examples

```
CURATED: from PMC1234567, co-IP and pull-down of HCV NS5A with human kinases.
- Full text: PMC1234567 (cc by)
- Strain: genotype 1b, Con1 (Methods, "Plasmids")
- Not read: Video S1 (Fig. 5) — not relevant, live imaging
- Not kept: NS5A × TRIM25 (Discussion) — only cited from ref. 12
- Pass 2026-10-06: curated from PMC1234567
```

```
Moved 2026-10-21: from run 88
---
SELECTED: from PMC2345678, Y2H screen of ZIKV proteins against a human library; Table S2 missing.
- Full text: PMC2345678 (cc by), supplementary files missing: Table S2
- Not read: Table S2 (Results, "Screen") — relevant, missing: tried PMC open access files, the publisher's page, Europe PMC
- Pass 2026-10-20: partial from PMC2345678, Table S2 missing
---
Y2H, see table S2
```

```
CREATED: anti-tag co-IP (MI:0007), Fig. 2B and 3A.
- Entry: NS3, isolate HCV-N (Methods) → P26662 (H77), sequence: closest to GenBank AF139594 (HCV-N)
- Mapping: NS3 1–180 (Fig. 4, deletion mutant), coordinates: residues 1–180 of GenBank AF139594 (HCV-N)
```
