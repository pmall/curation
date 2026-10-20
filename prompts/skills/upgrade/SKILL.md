---
name: upgrade
disable-model-invocation: true
description: "UniProt upgrade: load a new NCBI taxonomy and UniProt release, then the versioning pass that moves the obsolete interactors of live descriptions to current snapshots. Use when the user asks to load a release or run the versioning pass."
---

# UniProt upgrade

You load a UniProt release into Drakkar, then move every obsolete interactor of a live description (vh and hh) to the latest snapshot it can be on. Every write is shown in a dry run and committed only after the user's go on its report.

1. **Load**, on `data/<release>/` (the directory is named after the release, e.g. `data/2026_04/`, with `taxonomy/` holding the NCBI taxdump, `uniprot/` the UniProt FTP files `uniprot_sprot_human.xml.gz`, `uniprot_sprot_viruses.xml.gz`, `uniprot_trembl_viruses.xml.gz` and `uniprot_sprot_varsplic.fasta.gz`):

   1. `uv run drakkar-taxonomy data/<release>`: the NCBI taxonomy first, a dry run.
   2. `uv run drakkar-uniprot parse data/<release>`: the XML to TSV, cached.
   3. `uv run drakkar-uniprot upgrade data/<release>`: the import, a dry run; it writes `reports/uniprot_upgrade.md` and `reports/obsolete_vh_descriptions.tsv`.

   Report what each would write (the entries whose taxon is missing from the taxonomy among them); after the go, the same commands with `--commit`, the taxonomy first. A snapshot is unchanged when its accession, taxon, isoform sequences and, for a human entry, primary gene name are the same; anything else makes a new snapshot, and the old one obsolete.

2. **The obsolete interactors**: `uv run drakkar-check data/<release>/reports` lists them (D2), with the descriptions that use them. The unit is the protein, not the description: for each accession on an obsolete snapshot, decide what it becomes in the new release; each description then gets one revision, once the decisions for all its proteins are made. The past curation is taken as valid.

3. **Decide each protein**:

   - **Obvious**, the only one: the same sequences (canonical and isoforms), the same taxon, and a human gene name unchanged or whose old name is now a synonym of the same entry. Everything else is a decision.
   - **Changed sequences** (canonical or isoforms, one added or removed): every mapping sequence is mapped again on every isoform (`uv run drakkar-align mapping`). The viral coordinates stay when the residues between `start2` and `stop2` are unchanged; otherwise a whole protein becomes the whole new protein, and a part of a larger protein is found again in the new sequence (one best match).
   - **A viral taxon change** makes sense for an NCBI merge, a move to a parent or a child, or within one species.
   - **A human gene rename must make sense**: the new name is the gene name of the new snapshot, and the change is checked, e.g. the old name is a synonym of the same entry, and the old name designated this entry when the publication came out (curators chose the protein from the name they read).
   - **A human protein deleted by UniProt** moves only when nothing changes but the accession (same sequences, same gene name). An identical sequence in another gene's entry is no reason to move.
   - **A viral protein deleted by UniProt** moves to an entry with the exact canonical sequence and a sensible taxon (same taxon, NCBI merge, parent, child or same species); otherwise to a near match (MMseqs2, ≥ 70 % identity, ≥ 80 % coverage of both) in which the region is found again (whole protein → whole new protein, a part → its best match) and the mappings are found within the region at 90 % or more. Between equally good candidates: the strain of the publications; otherwise the highest identity, then a Swiss-Prot entry, then the reference strain or the most generic taxon (a name designating no strain or isolate, then the shallowest in the taxonomy), then the smallest accession. Patient isolates with no strain in the publications, matches below 90 % and matches only in another species are put aside.
   - **Human interactors are always updated when they can be**: a description is revised whenever one of its human interactors can be moved. When its other interactor cannot, the revision updates the human side only, and the description stays live with an obsolete interactor.
   - **An interactor that cannot be moved is put aside**, on its old snapshot, with its reason: it waits for the re-curation of its publication.
   - **One name per viral protein**: a viral interactor carries one generic name and a generic name one region of a snapshot. A conflict revealed by a move is settled from the publications. Two descriptions that become identical are duplicates: one is removed into the other (`into`).

4. **Write the files**: the live descriptions to revise, read with `uv run drakkar-read sql` (mappings written as sequences, their extra end residues in lowercase), with their new accessions, coordinates and mappings, into `<dir>/upgrade.revise.tsv` (`drakkar-revise --header` gives the header line). Each new version's note is its `UPDATED` line, `UPDATED: UniProt <release>, <what moved>` (e.g. `UniProt 2026_03, Q77YF9 → P12520 (deleted; NL4-3 Vpr), 1–78 → 1–96`, or `UniProt 2026_03, human side only`). An interactor put aside gets, in place on its live version, the line `ASIDE: side <n> <accession> <why>` (e.g. `side 2 B0FAN5 deleted, HIV-1 patient isolate, no strain in the publication`): plain SQL, with the user's permission. A move to the current snapshot of the same accession is not a revision: the revision tools keep the snapshot of a side whose accession does not change, so tell the user.

5. **Dry run and report**: `uv run drakkar-revise <dir>/upgrade.revise.tsv`. Report, in counts of proteins and of descriptions: the obvious moves, each kind of decision, the interactors put aside with why, the refused rows and errors of the dry run.

6. **Commit**, after the go: `uv run drakkar-revise <dir>/upgrade.revise.tsv --commit`, then the `ASIDE` lines. Last, the obsolete snapshots that no description row references (live or deleted) are deleted, with the user's permission; a snapshot used by a deleted version is kept, and a current snapshot never is.
