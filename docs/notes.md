# Notes

The notes are Claude's memory of its curation: from them alone, Claude can tell what it read on a publication, what it kept and left out and why, and how each description was decided, to curate it again, update it and report on it. A description note carries no date: a version is dated by its `created_at`. A publication note keeps the dated history of its passes and moves. Notes are short, a few words per line, with fixed labels so they can be searched: a report reads the headers for the states and the dates of the passes, the `Not read` lines for the relevant files missing, the `Not kept` lines for what was left out, and the `best-effort` description lines for the values a reviewer should see. A note never holds a number the database already gives, such as the count of descriptions.

## Publication note

`associations.annotation`: the notes of the publication, the newest first, each followed by a line `---` and the previous ones. A curation pass writes its note, a header line `STATE: summary`, which the write dates (`CURATED 2026-10-06: …`), and its detail lines; a move to a special run writes the note `Moved YYYY-MM-DD: from run <name>`.

| State | Summary |
| -- | -- |
| `SELECTED` | Before a pass, what the abstract suggests; after one, as `CURATED`, or `no full text, <why>`. |
| `DISCARDED` | `<reason code>`, then a short why: `no-viral-protein`, `no-human-protein`, `no-ppi` (no physical interaction suggested), `non-human-host`, `review`, `preprint`, `not-research` (editorial, erratum, protocol…), `other`. |
| `CURATED` | What the publication shows, in a few words; with no description, why. |

Detail lines, in this order:

- `Strain: <strain> (<where in the publication>)`, when one strain holds for all the viral interactors; otherwise each description's `Entry` line gives it.
- `Not read: <file> (<where cited>) — <why>`, one per supplementary file listed or cited and not read: `not relevant, <what it holds>`, or `relevant, <why it could not be read>`, which keeps the publication `selected`.
- `Not kept: <pair or claim> (<where>) — <reason>`, one per pair the publication shows that is not a description, the reason in words.
- `Remark: <anything a next pass needs that no other line holds>` (for a curator file, how ambiguous rows were interpreted).

## Description note

`descriptions.annotation`, one note per version. A version made by a curation holds the curation's note: the method and where the publication shows it (`anti-tag co-IP (MI:0007), Fig. 2B and 5C`), then `- ` detail lines; whether it is a first curation or a re-curation, its version and `created_at` say. A version made otherwise, and what was decided on a version later without a new version (an interactor not moved, an in-place correction, a removal), are each a line `ACTION: summary` followed by `- ` detail lines. The history of a description is its notes read version by version.

| Action | Why | Example summary |
| -- | -- | -- |
| `UPDATED` | A UniProt release: an interactor moved to its new snapshot (a new version), or kept on its old one, or an isoform renamed (in place) | `UniProt 2026_03, Q77YF9 → P12520 (deleted; NL4-3 Vpr), 1–78 → 1–96`, `UniProt 2026_03, side 2 B0FAN5 not moved: deleted, patient isolate, no strain in the publication` |
| `FIXED` | An error found in Drakkar | `name1 AES → TLE5, gene name of the snapshot` |
| `REMOVED` | The end of a description, in place on its last version, with its reason; by a re-curation, its reason is in the publication note's `Not kept` line | `HLA protein`, `not found by the re-curation` |

The detail lines of a curation's note are written for each value that is not obvious, and only for those. Obvious are an accession the publication gives, a human protein by its gene name, a viral protein of the publication's strain by its name, a chain of the entry, and a mapping the publication writes or the subsequence of the interactor at coordinates the publication gives. Each line names the tier of the value by its label (`curation-rules.md` §4), its evidence, and every source outside Drakkar by its identifier (`GenBank BAB32872.1`, `UniSave P26662 v45`, `Addgene 12345`):

- `Entry: <as published> (<where>) → <accession> (<strain of the entry>), <label>: <evidence>`; for a family or a complex, the member chosen and why.
- `Coordinates: <start>–<stop>, <label>: <evidence>`, for a mature protein.
- `Mapping: <as published> (<where>), <label>: <evidence>`, with the sequence it was taken from; below 90 % identity, why it is kept.
- `Remark: <what was arbitrary, what stays uncertain, what would change the decision>`.

## Examples

```
CURATED 2026-10-06: co-IP and pull-down of HCV NS5A with human kinases
- Strain: genotype 1b, Con1 (Methods, "Plasmids")
- Not read: Video S1 (Fig. 5) — not relevant, live imaging
- Not kept: NS5A × TRIM25 (Discussion) — only cited from ref. 12
```

```
Moved 2026-10-21: from run 88
---
SELECTED 2026-10-20: Y2H screen of ZIKV proteins against a human library
- Not read: Table S2 (Results, "Screen") — relevant, no URL given
---
Y2H, see table S2
```

```
anti-tag co-IP (MI:0007), Fig. 2B and 3A
- Entry: NS3, isolate HCV-N (Methods) → P26662 (H77), sequence: closest to GenBank AF139594 (HCV-N)
- Mapping: NS3 1–180 (Fig. 4, deletion mutant), coordinates: residues 1–180 of GenBank AF139594 (HCV-N)
```
