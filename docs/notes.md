# Notes

The notes only serve Claude to explain its choices later, to an external reviewer or in a report on a curation run or batch. Free text, in short lines, under the labels below, which make them easy to read and search.

## Publication note

`associations.annotation`: the notes of the publication, the newest first, each followed by a line `---` and the previous ones. A curation pass writes its note, a header line `STATE: summary` and its detail lines, which the write puts after the date (`[2026-10-06] CURATED: …`); a move to a special run writes the note `Moved from run <name>`, dated the same way.

| State | Summary |
| -- | -- |
| `SELECTED` | Before a pass, what the abstract suggests; after one, as `CURATED`, or `no full text, <why>`. |
| `DISCARDED` | `<reason code>`, then a short why: `no-viral-protein`, `no-human-protein`, `no-ppi` (no physical interaction suggested), `non-human-host`, `review`, `preprint`, `not-research` (editorial, erratum, protocol…), `other`. |
| `CURATED` | What the publication shows, in a few words; with no description, why. |

Detail lines:

- `Strain:` the strain and where the publication gives it, when one strain holds for all the viral interactors; otherwise each description's `Entry` line gives it.
- `Not read:` each supplementary file listed or cited and not read, where it is cited and why: not relevant (what it holds), or relevant and why it could not be read, which keeps the publication `selected`.
- `Not kept:` each pair the publication shows that is not a description, where and why.
- `Remark:` anything else a reviewer or a report needs (for a curator file, how ambiguous rows were interpreted).

## Description note

`descriptions.annotation`, one note per version. A version made by a curation holds the curation's note: the method and where the publication shows it (`anti-tag co-IP (MI:0007), Fig. 2B and 5C`), with the assay as published when the term is only the closest one, then `- ` detail lines. A version made otherwise, and what was decided on a version later without a new version (an interactor not moved, an in-place correction, a removal), are each a line `ACTION: summary` followed by `- ` detail lines. The history of a description is its notes read version by version.

| Action | Why | Example summary |
| -- | -- | -- |
| `UPDATED` | A UniProt release: an interactor moved to its new snapshot (a new version), or kept on its old one, or an isoform renamed (in place) | `UniProt 2026_03, Q77YF9 → P12520 (deleted; NL4-3 Vpr), 1–78 → 1–96`, `UniProt 2026_03, side 2 B0FAN5 not moved: deleted, patient isolate, no strain in the publication` |
| `FIXED` | An error found in Drakkar | `name1 AES → TLE5, gene name of the snapshot` |
| `REMOVED` | The end of a description, in place on its last version, with its reason | `HLA protein`, `not found by the curation` |

A curation's detail lines explain each value that was a choice: a line naming the value (`Entry`, `Coordinates`, `Mapping`), its tier by its label (`curation-rules.md` §4), its evidence and any source outside Drakkar by its identifier (`GenBank BAB32872.1`, `UniSave P26662 v45`, `Addgene 12345`). An `Entry` line says whether the entry has the sequence the publication used (a viral entry without one has it), and for a family or a complex, the member chosen and why; a `Remark` line, anything else the decision needs (a tie broken by judgement, a disagreement between the publication's sources, a natural post-translational modification). No line for an accession the publication gives, a human protein by its gene name, a viral protein of the publication's strain by its name, a mature protein the entry annotates, a mapping the publication writes or the subsequence of the interactor at coordinates the publication gives.

## Examples

```
[2026-10-06] CURATED: co-IP and pull-down of HCV NS5A with human kinases
- Strain: genotype 1b, Con1 (Methods, "Plasmids")
- Not read: Video S1 (Fig. 5) — not relevant, live imaging
- Not kept: NS5A × TRIM25 (Discussion) — only cited from ref. 12
```

```
[2026-10-21] Moved from run 88
---
[2026-10-20] SELECTED: Y2H screen of ZIKV proteins against a human library
- Not read: Table S2 (Results, "Screen") — relevant, no URL given
---
Y2H, see table S2
```

```
anti-tag co-IP (MI:0007), Fig. 2B and 3A
- Entry: NS3, isolate HCV-N (Methods) → P26662 (H77, not own sequence), sequence: closest to GenBank AF139594 (HCV-N)
- Mapping: NS3 1–180 (Fig. 4, deletion mutant), coordinates: residues 1–180 of GenBank AF139594 (HCV-N)
```
