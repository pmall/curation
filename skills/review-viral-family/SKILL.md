---
name: review-viral-family
description: "Consistency review of the viral interactors of one or more virus families: find descriptions whose generic names or coordinates disagree, report the revisions, write them once validated. Use when the user names virus families to review. The prompt gives the families and where to write the report."
---

# Consistency review of virus families

## Inputs

- **Families**: one or more virus families.
- **Report location**: a file, or a directory (then name the file `<date>-<families>.md`). If missing, ask.

## Goal

The descriptions are valid; look only for viral interactors that disagree with each other:

- the same protein under two generic names;
- two different proteins under one generic name;
- a wrongly identified protein (sequence or length unlike the others of its generic name);
- coordinates unlike those of the same protein elsewhere.

Ignore everything consistent.

## Step 1: List the viral interactors

Read-only. One row per viral interactor (accession, start, stop) of the live vh descriptions of the families, on current snapshots (skip obsolete descriptions):

- strain group (NCBI taxon of rank species above the species), species
- UniProt description, region sequence and length
- generic name, UniProt chain at these coordinates
- number of descriptions and of publications

Collect the distinct taxa first, then walk their lineage once by `parent_taxon_id`. This listing is working material; it does not go in the report.

## Step 2: Find the inconsistencies

- Read every row, strain group by strain group, comparing strains (group otherwise when the family calls for it).
- Use knowledge of the viruses and their classical protein names to spot oddities, never as evidence.
- Use the sequence as a key: to find outliers across strains, the same protein among curated interactors, and the UniProt entry or chain a region belongs to.

## Step 3: Settle each case

Every case ends **kept**, **revised** or **unsettled**. Decide; never ask the user to choose between names or coordinates. Unsettled = evidence does not decide; write nothing for it.

**Evidence, cheapest first:** UniProt entry (chains, names) → publication title and abstract → full text.

**Name vs coordinates disagree:**

- The publications say which protein the curator meant: the named one → change the coordinates; the one of the region → change the generic name.
- The publications say nothing → the region wins: change the generic name.

**Scope:** only generic names and coordinates. If the fix needs anything else (another accession, another strain), settle what is in scope and note the rest.

**Generic names:**

- Change a name only when it is inconsistent, never for its form (case, spelling).
- The new name is the one already used in Drakkar for that protein across the strains of the virus, never one from the publication.
- No Drakkar name for that protein: follow the convention the strain group uses for its neighbours (UniProt product name form, ORF-number form). Never invent one when an existing name fits.

**Leave alone:** differences of form, real biology (a protein that truly differs in one virus), fragments whose region matches their generic name.

**Borderline cases:** decide them; note the ones worth it in the report.

**Coordinate changes: recheck the mappings before proposing.**

1. Count the mappings of the descriptions concerned.
1. Check that `map_sequence` (`descriptions.py`) reproduces them on the current coordinates (positions on the canonical isoform are relative to the region). Any discrepancy: stop and show it.
1. Recompute them on the proposed coordinates.
   - All found again at the expected place → the proposal holds.
   - Any lost, moved or below threshold → drop the proposal. Investigate that description (publication, entry, strain, other descriptions of the same interactor and publication), then keep it, propose something else, or keep it and note it if the answer is out of scope.

Never write coordinates that break a mapping; never discard a mapping to fit a proposal.

## Step 4: Write the report

Every number and claim comes from a query run for it:

- "identical" = compared residue by residue; otherwise give length, number of differences, identity, and whether the chain boundaries are the same residues;
- mapping claims = a count of the mappings concerned, plus the recheck result;
- lengths, identities, counts of descriptions, entries or mature proteins = query results;
- a name used elsewhere in Drakkar = read from the database, with its interactor and number of descriptions.

Content, nothing else:

1. **Generic name revisions** (table): viral interactor, current name, new name, descriptions, why (one sentence: the inconsistency and what settles it).
1. **Coordinate revisions** (table): viral interactor, current coordinates, new coordinates, descriptions, mappings concerned and recheck result, why.
1. **Left alone**: one line per kind (form only, real biology, fragments, polyproteins, …) with one example each.
1. **Unsettled**: one line each, with why.
1. **Noted**: one line each, when something beyond this review may be wrong.
1. **Totals**: viral interactors and descriptions revised.

One sentence per case, two at most. No inventory of the family, no method, no virology, no questions.

Before delivering, re-read each sentence and name the query behind each claim; query or remove any that has none.

Give the report path and the same lists in chat. **Stop: write nothing to the database before the user validates.**

## Step 5: Write the validated revisions

Plain SQL, one transaction (no new function, not the guard functions of `descriptions.py`):

- Select `FOR UPDATE` the live descriptions of each revised viral interactor only: viral side with that accession, generic name and coordinates.
- Use one `now()::timestamp(0)` for the whole transaction.
- Insert a copy of each live row with `version + 1`, the new generic name or coordinates, the recomputed mappings, and the description note `[<date> Claude] REVISED: <what changes and why> (consistency review of <family>)`.
- Set `deleted_at` of the old row to the same instant.
- Assert rows inserted = rows deleted = rows expected, per revision.

Dry run first (no commit) and show: counts per revision, invariants V3, D3, D5, and each revised interactor read back (mature proteins of a polyprotein tile without hole or overlap). Commit only after the user validates, then run `uv run drakkar-check <report dir>` and report its result.

No git commit unless asked.

## Output

End with:

- date, families, viral interactors and descriptions reviewed, revisions written, report path;
- cases noted;
- generic names new to Drakkar: name, interactor, convention followed;
- what went wrong in the pass (unchecked claim, slow query, unforeseen case), one or two lines.
