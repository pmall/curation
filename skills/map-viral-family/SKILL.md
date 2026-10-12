---
name: map-viral-family
description: Map the Drakkar viral interactors of one or more virus families to the viral proteins reference (docs/viruses/<family>.md) on the current UniProt release, catch the misnamed interactors and wrong regions, and revise the descriptions once the user approves. Use when the user names one or more virus families to map, normalize or check against the reference.
---
# Map a virus family to the viral proteins reference

The families are given in the prompt, as family file names of `docs/viruses/` (e.g. `retroviridae`). One family is one complete pass: review, approval, writes. Several families are done one after the other, the biggest first, each with its own approval; never all at once.

**Goal:** every live vh viral interactor of the family carries the generic name of its protein in the reference, on the region of that protein, and interactors with the same name within a species are the same protein. The reference is right (Claude made it): a problem in the reference itself (a wrong name, a missing target, a wrong region) is reported to the user, and nothing is done for that target before the user decides.

## Rules

- **No write before approval.** Nothing is written to the database until the user approves that family. The only write is `drakkar-viruses apply --commit`; never SQL or any other route.
- **Read-only on the project.** No edits to `docs/`, to the family file or to this skill. A target that looks wrong in the reference is recorded at the top of `review.md` as a reference problem, and nothing is done for it.
- **No git commit**, and no `docs/history/` file, unless the user asks.
- **No sub-agents** inside the pass: the interactors are checked by the one running the skill.
- **Cheapest evidence first**: the UniProt entry of the interactor and the title and abstract of its publications settle most mismatches; the full text is the last resort, read only for what they leave open (PubMed tools, e.g. `get_article_metadata` and `get_full_text_article`, loaded with ToolSearch).
- **Counts** come from the files or a fresh query, never from memory; tables add up to their totals.

## Running in a sub-agent

The usual way: the main session starts one background agent per family, with only the family name and this skill. The agent runs §1 to §3 and the dry run of §4. It then **stops** and replies with a short report:

- counts per decision (interactors and descriptions);
- the dry-run result (descriptions, viral mappings recomputed per region change, or the problems);
- the reference problems;
- the special cases (publication-based decisions with what the publication says, per-publication splits, regions kept, unresolved);
- anything in the tool that did not work.

The main session takes the report to the user, and passes the approval, or the corrections, back to the same agent. Only then does the agent run `--commit` and the checks after the writes. An agent never asks the user anything, and never commits without that message.

Read first: `docs/viruses.md` (identifying and naming a protein, regions §3), the family file, `docs/glossary.md`, `docs/curation-rules.md` §6 (description notes) and `docs/database.md` §2 (revisions). They are the rules; this skill is the process.

## 1. The worksheet

```
uv run drakkar-viruses review <family> [<family>...]
```

For each family, in `data/viruses/<family>/` (disposable):

- `summary.md`: interactors and descriptions per verdict.
- `interactors.tsv`: one line per live vh viral interactor (snapshot, start, stop, Drakkar name) of the family's species. It lists the UniProt name of the entry, the entry length, the UniProt chains at the region (`chains`, current snapshots only), whether the region is the whole entry, a chain or neither (`region`), the best target of its species with identity and both coverages, the verdict (`same`, `rename`, `partial`, `no target`), `quick`, and the PMIDs and stable IDs of its descriptions.
- `names.tsv`: one line per (species, Drakkar name), with the targets its interactors hit and `consistent`.
- `targets.tsv`: the targets, how many interactors each one gets, and the problems reading their reference.

The alignment only searches the family's own targets, within the interactor's species. A `quick` match (identity ≥ 95 %, interactor and target each ≥ 95 % covered) means the sequence is the target's protein beyond doubt. It is never a decision: **every line is checked by hand**, quick or not. The worksheet is the list to go through, not the answer. A target problem in `targets.tsv` is a reference problem: report it.

## 2. Check every interactor

Take the interactors one by one, species by species, three checks each: **sequence, name, region**. When all three match the reference, the interactor is `ok`. **Anything that is a real mismatch goes back to the curation** (spelling is not: see Name below) (the general rule, `docs/curation-rules.md` §1: the publications are the truth): the evidence is taken in this order, and stops as soon as it settles the case: the **UniProt entry** of the interactor (its name, its chains), then the **title and abstract** of its publications (PMIDs in the worksheet), then, only for what is still open, the **full text** (it is expensive: read it for one case at a time, never as a routine). When a publication has no full text available, the title and abstract and the UniProt entry of the interactor decide, and the reason says so. A publication that identifies its proteins by UniProt entry (e.g. peptide libraries tiled on UniProt proteomes) confirms the entry and its UniProt name, not the name Drakkar gave it. A Drakkar mistake is never assumed from the sequence alone: even when the sequence is clear (e.g. a protein named `N` whose sequence is ORF6), the publication confirms what was studied before the change.

**Sequence.** A `quick` match is the target's protein. Otherwise compare the UniProt name, chains and length of the entry with the target row (reference, length, *Also called*, the `Names:` line), and the sequence of the region with the target's region. A low identity is expected between distant strains (HIV-1 subtypes, SIV lineages); a different protein is not. `no target`, or a hit that doesn't fit: the protein may be absent from the reference, which is a reference problem.

**Name.** The Drakkar name must be the target's generic name. On a matching sequence, **the same name written differently is a direct update**, with no check of any kind: case (`orf3` → `ORF3`), hyphen or separator (`LHDAg` → `L-HDAg`, `papain-like_protease` → `papain-like protease`), spacing, or a name the target lists under *Also called*. It is the same protein under the same name; the reason is just the reference. Only a **different name** (another protein's, or one nothing connects to the target) is a mismatch: the UniProt entry (its name, or its chain at the region) and the publications decide. When the publications disagree, decide per publication: list only the right stable IDs in the change.

**Region.** The region must be the target's protein: a UniProt chain of the interactor's own entry (`chains`), or the whole entry when the target is the whole protein. If it differs, the publication decides:

- the construct is the whole protein, or nothing says otherwise: the new coordinates are the chain of the target's protein in the interactor's entry. When the entry has no chain features (TrEMBL, obsolete snapshot), take them from the alignment on the target's region, and say so in the reason;
- the publication used that region (a domain, a fragment, a truncated construct), or the entry is a fragment: the region is kept;
- a short region (≤ 20 residues) is a mapping question: kept;
- the family file marks `joined chains` or `whole polyprotein`: kept, as the reference says.

A region change moves the viral mappings with it: their occurrences are positions relative to the region. `apply` recomputes them, but only after it reproduces the stored ones on the old region (when the region keeps its start, the recomputed occurrences are identical: `recomputed, same`), and it refuses a mapping that no longer fits the new region (no occurrence at 90 % or more). In `review.md`, every region change lists its descriptions with a viral mapping and what happens to it. A mapping that is not reproduced, or no longer fits, is a curation question: the publication decides (the region or the mapping is wrong), never forced.

**Strains.** In `names.tsv`, every (species, name) must have all its interactors on one target. A name on several targets means some interactors are misnamed: go back to them until each species' names are consistent.

**Decisions**, one per interactor (or per group of stable IDs when publications disagree): `ok`; `rename`; `region`; `rename + region`; `kept` (a region not the whole target, justified by the publication or the entry); `unresolved` (only when the publications have been read and still do not settle it, or when the fix is outside this pass: the interactor is on the wrong UniProt entry, or on an obsolete snapshot that should move; never move a description to another snapshot). Every non-`ok` decision has its evidence, citing the publication when one was read.

The skill changes `name2`, `start2` and `stop2`, and nothing else. The family file's *To check* notes are checked like any interactor; the result goes in `review.md`, and the family file is not edited.

Big families: go species by species, and save the decisions to the files of §3 as they are made, so the work survives a context reset. Small families: the same steps, at once.

## 3. The review files

In `data/viruses/<family>/`, the temporary record that the user validates:

**`review.md`**: what the user reads to approve.

- Counts: interactors and descriptions per decision (`ok`, `rename`, `region`, `rename + region`, `kept`, `unresolved`), adding up to the totals of `summary.md`.
- Every change, grouped by species and Drakkar name: what it is, the evidence (target and identity, UniProt name or chain, PMID and what the publication says), and how many descriptions it touches. The obvious renames of a whole name (e.g. `LHDAg` → `L-HDAg` everywhere) take one line each.
- The special cases: publication-based decisions, per-publication splits, regions kept, unresolved interactors, anything arbitrary.
- Reference problems, if any, at the top: they block their targets.

Run `uv run mdformat --wrap no` on it.

**`changes.tsv`**: what `apply` writes. A TSV with a header, one line per interactor change, written as plain tab-separated text (no CSV quoting: reasons contain double quotes):

| Column                                 | Content                                                                                                   |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `protein2_id`                          | The snapshot of the interactor (from `interactors.tsv`).                                                  |
| `start2`, `stop2`, `name2`             | The interactor as it is now (`start`, `stop`, `drakkar_name` of `interactors.tsv`).                       |
| `new_start2`, `new_stop2`, `new_name2` | What it becomes (unchanged values repeated).                                                              |
| `stable_ids`                           | The descriptions revised, space-separated: all of the interactor's, or the ones the publications decided. |
| `reason`                               | The evidence, written into the note (below).                                                              |

**The note** of each new version is `[<date> Claude] FIXED: <what changed>, <reason>`. `apply` writes the date and what changed (`name2 X → Y`, `region a–b → c–d`); the reason is yours. It is read by the next pass and summed up into a document later, so it must stand alone, short, with the evidence and the reference file:

- `viral proteins reference (retroviridae.md): UniProt "Protein Nef"`
- `viral proteins reference (coronaviridae.md): chain 1–180 "Host translation inhibitor nsp1" of P0DTC1`
- `viral proteins reference (flaviviridae.md): PMID 12345678 abstract studies NS1, not E`
- `viral proteins reference (coronaviridae.md): PMID 12345678 full text, full-length nsp3 (Table S1)`
- `viral proteins reference (papillomaviridae.md): aligned on target E6 P03126 1–158 (97 %), entry without chains`

## 4. Approval, then writes

1. Dry run: `uv run drakkar-viruses apply data/viruses/<family>/changes.tsv`. Nothing is written or kept. It checks every line against the live rows, and refuses a stable ID that is not live, not on that interactor, or listed twice. When the region changes, it recomputes the `mapping2` occurrences (they are relative to the coordinates), but only if it first reproduces the stored ones. It also checks D5, D6 and D10 on the family's accessions. Any problem means it writes nothing: fix the changes file, or show the problem to the user. A mapping that is not reproduced or falls outside the new region is shown to the user, never forced.
1. Show the user `review.md` in a few lines (counts, special cases, problems), plus the dry-run result and its descriptions count. Wait for approval of that family.
1. After approval: `uv run drakkar-viruses apply data/viruses/<family>/changes.tsv --commit`. Each description gets version + 1 with only the viral side changed, and the old version is deleted at the same instant (`timestamp(0)`). The list is in `applied.tsv`.
1. Check: `uv run drakkar-viruses review <family>` again. Every interactor left is `same` or a case decided as `kept` or `unresolved`, and every name in `names.tsv` is on one target. Then `uv run drakkar-check data/<release>/reports/check-<date>-<family>/`, which must show no new error.
1. Report the counts to the user, and give the lines to add to `docs/open.md` (one section per family: every `unresolved` interactor, and every `kept` one whose entry or region stays wrong), with its descriptions and the open question. The file is the only record of these cases: the review files are disposable, and an interactor left unchanged has no description note. The user adds them: no git commit and no `docs/history/` file unless the user asks.
