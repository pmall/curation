# Notes

The notes only serve Claude to explain and justify its choices later, to an external reviewer or in a report on a curation run or batch: free text.

## Publication note

`associations.annotation`: the notes of the publication, the newest first, each followed by a line `---` and the previous ones. A curation pass writes its note, its first word the state, which the write puts after the date (`[2026-10-06] CURATED …`); a move to a special run writes the note `Moved from run <name>`, dated the same way.

## Description note

`descriptions.annotation`, one note per version. A version made by a curation holds the curation's note. A version made otherwise, and what was decided on a version later without a new version (an interactor not moved, an in-place correction, a removal), are each a line `ACTION: summary` followed by `- ` detail lines. The history of a description is its notes read version by version.

| Action | Why | Example summary |
| -- | -- | -- |
| `UPDATED` | A UniProt release: an interactor moved to its new snapshot (a new version), or kept on its old one, or an isoform renamed (in place) | `UniProt 2026_03, Q77YF9 → P12520 (deleted; NL4-3 Vpr), 1–78 → 1–96`, `UniProt 2026_03, side 2 B0FAN5 not moved: deleted, patient isolate, no strain in the publication` |
| `FIXED` | An error found in Drakkar | `name1 AES → TLE5, gene name of the snapshot` |
| `REMOVED` | The end of a description, in place on its last version, with its reason | `HLA protein`, `not found by the curation` |

## Example

```
[2026-10-21] Moved from run 88
---
[2026-10-20] SELECTED
- Table S2, the screen's hits (Results, "Screen"), could not be had: no URL given
---
Y2H, see table S2
```
