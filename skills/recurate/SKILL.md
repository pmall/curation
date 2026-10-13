---
name: recurate
description: "Re-curation pass: take publications already curated, check their curation against the publications themselves, list one decision per description in a changes file, test the whole file against the database without writing, correct what the test exposes, then write the validated decisions. Use when the user asks to re-curate, re-check or validate curated publications. The prompt gives the publications and where to write the files."
---

# Re-curation of already curated publications

The descriptions exist and were curated. The pass asks of each one: does it still say what its publication shows? It never adds descriptions and never re-reads a publication for new interactions.

## Inputs

- **Publications**: a list of PMIDs, or how to produce one (a signal, a query, a report). If the list has to be produced, the prompt says how; never invent a selection.
- **Output location**: a directory. It holds `publications.tsv` (the list and why each publication is in it) and `changes.tsv` (one row per description decided). If missing, ask.

## Goal

One decision per live vh description of those publications, each settled on its own evidence, written to a file and tested before anything reaches the database.

The decisions are `keep`, `fix` and `merge`. Unsettled is a valid decision: nothing is written for it and it is reported with why.

## Step 1: Build the dossier

Read-only, one query per table, aggregate then join. Per publication:

- title and abstract from `publications.metadata`;
- every live vh description: human interactor, viral interactor, generic name, region, method, mappings, note — all of them, not only the suspect ones, because a decision on one is often settled by its neighbours;
- per viral accession: UniProt description, taxon, length, gene names, and the chains, peptides and propeptides of `proteins_versions.features`;
- whether each accession is on the current snapshot.

This dossier is working material. It does not go in the files.

## Step 2: Decide each publication

Read the publications one by one, in the dossier, and decide every description of each.

**Evidence, cheapest first** (`curation-rules.md` §1): the UniProt entry of the interactor (its name, its chains) and the title and abstract, which settle most cases; the full text only for what they leave open. A curation mistake is never assumed from the database alone.

**What the description must say:** the interactor is the protein the publication tested, on the closest UniProt entry, with that protein's coordinates and the generic name Drakkar already uses for it (`uv run drakkar-names <accession>`, read-only).

The errors this separates out:

- the entry holds one mature protein and carries the name of the polyprotein — the entry is right, the name is not;
- the entry holds only a part of the protein the publication tested — the entry is wrong;
- the name designates a protein the entry does not hold;
- the coordinates record the truncated construct the experiment used — a construct is a mapping, the interactor is the protein;
- the human interactor is another protein.

**A truncated copy of the protein it is named after is the curator's choice and is kept**: a 70-residue HBx entry named `HBx`, a 16-residue Tax entry named `Tax1`. The name still designates that protein.

**Decide only what the evidence of that publication settles.** A description is fixed when its own publication and its own entry show the record is wrong, never because a comparable description elsewhere was decided one way. Where they leave the case open, the curated value stands and the decision is `unsettled`, with why. Borderline is not a reason to pick a side; it is the definition of unsettled.

## Step 3: Write the changes file

`changes.tsv`, one row per description, tab separated:

| Column           | Content                                                                                                                                                                                    |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `stable_id`      | the description decided                                                                                                                                                                    |
| `run_id`, `pmid` | where it belongs                                                                                                                                                                           |
| `decision`       | `keep`, `fix`, `merge` or `unsettled`                                                                                                                                                      |
| `changes`        | the fields to write and their new values (`name2 Gag -> CA`; `accession Q71B32 -> P04591; region -> 1-500`), or the delete or merge to perform. Empty on a keep                            |
| `evidence`       | why: what the publication tested (title, abstract), then what the entry holds. One self-contained sentence per row — never "same as EY…", never a clause that contradicts its own decision |
| `note`           | the description note to write. Empty on a keep                                                                                                                                             |

`publications.tsv` holds one row per publication with why it is in the pass.

## Step 4: Test the file, write nothing

The transaction asserts the invariants on its result (step 5), so the file does not have to test them beforehand. Test what it cannot: that each row says something true about its own description.

1. **Each row still applies**: the stable ID is a live vh description of that publication, and every "from" value matches the database now.
1. **Each target is writable**: the accession exists and is on the current snapshot, the new region is inside its length, the new generic name is one `drakkar-names` already uses for that protein.
1. **Re-read each evidence line against its own decision.** Evidence that says the record is right under a `fix`, or a cross-reference instead of a reason, is a decision to re-examine, not a wording to patch.

Correct the file, then run the test again until it comes back clean.

## Step 5: Report, then write

Report in chat, once, with final counts (`counts-final-once`): the kinds of error with their counts of descriptions and publications, one example each; what the test exposed and how it was settled; the unsettled cases with why. The totals add up to the descriptions decided. **Stop: write nothing to the database before the user validates.**

Then write the validated decisions, plain SQL, one transaction, one `now()::timestamp(0)`:

- select `FOR UPDATE` the live descriptions named in the file;
- insert a copy with `version + 1`, the new values and the note `[<date> Claude] REVISED: <what changes and why>`, and set `deleted_at` of the old row to the same instant;
- assert rows inserted and deleted against the file, per decision, and assert the invariants on the result: V3, D3, D5, D6, D10.

Dry run first and show the counts per kind. A fix that lands on values another live description already carries breaks D5 here: that description is a duplicate, not an update. Before deleting it, compare it with the survivor field by field — mappings on both sides, note. A plain delete is right only when it holds nothing the survivor lacks; when it holds a mapping the survivor has not got, carry that mapping over first. Then run the dry run again.

Commit once the user has said go, then `uv run drakkar-check <report dir>` and report its result. No git commit unless asked.

## Output

End with: publications and descriptions decided, decisions by kind, what the test exposed, unsettled cases, the file paths, and in one or two lines what went wrong in the pass.
