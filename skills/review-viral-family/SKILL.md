---
name: review-viral-family
description: "Consistency review of the viral interactors of one or more virus families named in the prompt: produce a report to inspect and validate with the user, then write the validated revisions. Use when the user names virus families to review."
---

# Consistency review of virus families

The prompt names one or more virus families. Claude, as the curator, reviews their viral interactors, writes a report for the user to inspect and validate, and writes the revisions once they are validated.

The descriptions are valid: they follow every rule of the database. The review does not look for errors; it looks for descriptions that are valid but do not agree with each other. The viral interactors were curated over years by different curators, and the derived datasets group strains as (a common taxon, generic name): the same protein under two generic names becomes two proteins, two proteins under one generic name become one, and a wrongly identified protein carries interactions that are not its own. Once a family is reviewed, its naming in Drakkar is consistent, and live curation takes the generic names of new interactors from it.

## 1. List the viral interactors

One row per viral interactor (accession, start, stop) of the live vh descriptions of the families, on current snapshots (the obsolete descriptions are put aside, waiting for re-curation): strain group (the NCBI taxon of rank species above its species), species, UniProt description, region sequence and length, generic name, the UniProt chain at these coordinates, number of descriptions and publications. Read-only queries, fast: collect the distinct taxa first, then walk their lineage once by `parent_taxon_id`.

## 2. Find the inconsistencies

Read every row as the curator, strain group by strain group, comparing the strains (group them otherwise when the family calls for it). Use what you know of these viruses and their classical protein names to spot what is strange, never as evidence. Look for the same protein under two generic names, two different proteins under one generic name, a wrongly identified protein (a sequence or a length unlike the others of its generic name), coordinates unlike those of the same protein elsewhere.

The sequence is a key, not evidence: it finds the outliers across strains, finds the same protein among the curated interactors so their generic names and coordinates can be compared, and leads to the UniProt entry or chain a region belongs to.

## 3. Settle each one

The evidence, cheapest first: the UniProt entry (chains, names), then the title and abstract of the publications, the full text as a last resort. When the generic name and the coordinates disagree, UniProt shows the mismatch, not which one is wrong: the publications decide whether the curator meant the named protein (the coordinates change) or the protein of the region (the generic name changes). In doubt, the curated value stands, and the case is an open question.

The fewest revisions: a generic name changes only when it is inconsistent, never for its form (case, spelling), and the new one is the generic name already used in Drakkar for that protein across the strains of the virus, never taken from the publication. Leave alone what only differs in form, real biology (a protein that truly differs in one virus), and a fragment whose region matches its generic name.

## 4. Report

Write the report in `data/<current release>/reports/consistency-review/`, named after the date and the families: the naming of each family in Drakkar, each proposed revision with its evidence and the number of descriptions it changes, the open questions, what is left as it is and why. Give the path in chat and stop: nothing is written to the database before the user validates.

## 5. Revisions, once validated

Each description concerned by a validated revision gets a new version, in plain SQL, in one transaction: a copy of the live row with the new generic name or coordinates and its description note, the old version deleted at the same instant. New coordinates: the viral mappings are searched again on them. Run the transaction without committing, check that the data stays valid, and show the result; commit only when the user validates it, then run `uv run drakkar-check <report dir>`.

## 6. Record

Add the families to `docs/history/04-consistency-review.md`: date, viral interactors and descriptions reviewed, revisions written, and the open questions, which are settled together once every family is reviewed. No git commit unless the user asks.
