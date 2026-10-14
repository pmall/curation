# To do

Next steps, in order.

1. **Rerun the recurate test** on its test publications, with the subagents on Sonnet: if their decisions are weaker than the default model's, switch the skill back. Then the rest of the re-curation selection, one session at a time.
1. **Try the curate skill** on a few selected publications.
1. **At the next UniProt release, the versioning tool**: list the obsolete interactors of live descriptions, and the obvious moves; Claude writes the revision file. The revision tools then need a way to move an interactor to the current snapshot of the same accession.
1. **Generic viral proteins**: a viral pass that lists the species in Drakkar and groups the viral interactors of each species under one generic name, for the vh datasets (`derived-datasets.md`).
1. **Pre-curation**, once every publication already in Drakkar is curated: optimize the PubMed query against the selected and discarded publications of Drakkar, then a pre-curation skill (large batches, a small model deciding `selected` or `discarded` from the title and abstract).
1. **Checks of Claude's notes**, on the publications Claude worked on: a publication Claude decides on has a note; a Claude note starts with the template header and its state matches `associations.state`; a publication with a non-null `ai_pass_at` is `selected` or `curated` and has a Claude note; the date of the last `Pass` line of a Claude note equals `ai_pass_at`.
1. **Mature protein length across accessions**, a check for review, not an invariant: the same mature protein (same virus, same generic name) should have about the same length on every accession. To decide: the virus level that groups accessions and the size of a big disparity.
