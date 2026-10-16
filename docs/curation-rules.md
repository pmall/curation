# Curation rules (biological)

The curation method is the one published in the PNAS 2024 SI appendix (doi:10.1073/pnas.2308776121, supporting text pp. 3–10). Terms are defined in `glossary.md`; the database side (tables, versioning, invariants) is in `database.md`.

## 1. Context

- Scope: **virus–human (vh) protein–protein interactions**. Human–human (hh) descriptions get no new curation.
- **Full texts**: a publication is read in its full text, with its supplementary files, from any copy at hand: PMC, the publisher, a repository, or a PDF the user provides; never a preprint, which is not peer-reviewed (§3). Images are never read. The license of a copy does not restrict curation: it is a question for the derived datasets (`derived-datasets.md`). How full texts are fetched and converted: `tools.md`. Without a full text, a publication needs a manual pass (§2), or a curator file: an Excel file describing its interactions, which Claude interprets.
- **Curation is valid at its time**: a description was right on the UniProt snapshots it was curated on. Updating it to a new release is best effort; when a viral protein is gone from UniProt (e.g. a patient isolate), the description stays live on its old snapshot, and its mappings stay good data.
- **Exact curation, not grouping**: the job is that each description is exactly right (accessions, coordinates, generic names, mappings). How the data is grouped (species, taxonomy levels, strains abstracted into one interactor) is the concern of the applications that consume it (`derived-datasets.md`). Grouping is only a tool to spot curation errors, never a problem to report.
- **The publications are the truth**: a description says what its publication shows, read in its full text, on its interactors' own UniProt entries (their names, chains and sequences). A description already in the database is held to the same: anything that does not match its publication (a name, a region, a strain, an entry, a sequence) goes back to the curation. A curation mistake is never assumed from the database alone. What nothing settles is put aside, with the reason.
- **Claude is the curator**: Claude takes the decisions itself and reports them. Leaving a case unsettled is a valid decision: nothing is written for it, and it is reported as unsettled, with why.
- **Unsettled is better than wrong**: a value is written only when the publication or the interactor's own UniProt entry (its sequence, its chain features) gives it. Never derived from another entry, from other Drakkar descriptions, from a document Claude wrote, or by computation (e.g. a mature protein's coordinates borrowed from another strain's chains and shifted): when the entry has no chain for a mature protein, its coordinates are not settled. A value Claude reads from free text (e.g. a name in an entry's description) is stated as Claude's reading, never as the source's. Borderline is unsettled, and a borderline case settled once never becomes a rule.
- **Each description is judged on its own**: against its own publication, its own UniProt entries and the invariants, never by comparison with how another description was decided. A difference between two comparable descriptions only points at rows to look at again.
- **Ambiguous cases: the original curator's choice stands**: when the rules leave a case open (an open convention, or evidence that does not settle it), the curated value is kept and the case is reported as unsettled.
- **An interactor is one protein everywhere**: renaming an interactor that other publications also carry is unsettled, since one interactor cannot be one protein in one publication and another protein in the next.
- **Generic names follow the Drakkar naming**: the generic name names the protein the publication tested, written as Drakkar already names it. Before naming a viral interactor, look at the names already used for the strain, then the virus, then the family (`uv run drakkar-read curation-names <pmid> <accession>`, which leaves out the publication curated), and follow them: reuse the existing name of that protein rather than the publication's spelling (`orf6`, not `orf-6`), and for a new protein follow the form its neighbours use. Consistency is hard at the accession level (one generic name per region of an entry, one region per generic name: D6, D10) and soft at the strain level (within one strain, the same protein keeps one generic name when curating; not checked). Consistency at the generic protein level (the same protein under one name across the strains of a virus) is a concern of the derived datasets (`derived-datasets.md`): curated descriptions are not revised for it.

## 2. Process

1. A PubMed query collects new PMIDs since the last run. One run per batch. Every publication starts `pending` (not pre-curated).

2. **Pre-curation** on title and abstract, by Claude, for every publication: `selected` or `discarded`. The goal is to remove the query's false positives. A publication is `selected` as soon as the abstract suggests it may contain a virus–human PPI: **the goal is exhaustiveness**, so in doubt, select. `discarded` is a pre-curation decision only.

3. **Curation pass** by Claude on each selected publication, from its full text (§1). Once the full text has been read, the publication is `curated`, **whether descriptions were found or not**. A curated publication with zero descriptions is a valid outcome: the publication was reviewed and reports no interaction that meets the criteria. The note says why. A publication is `curated` only when **everything that can carry an interaction has been read**: its full text and every supplementary file that may hold one. A file whose content bears on no interaction is not one of them: an image, a video, a file of raw source data whose values are already in a table that was read. A file that may hold an interaction and could not be read — not fetched, held by no copy, failed to convert, or its content left uncertain — leaves the publication `selected` with its pass date, whatever the read part showed; the descriptions found are recorded all the same, and the note says which file and why. **An unsettled description leaves it `selected` too**: the publication is `curated` only when every description it holds is settled and recorded.

4. Every selected publication Claude went through gets the date of the pass in `associations.ai_pass_at` (`database.md` §1), curated or not. A publication still `selected` with a date needs a **manual pass**: curated by hand, or handed to Claude as a curator file. Its note says why Claude could not curate it fully (e.g. no accessible full text, or supplementary files it needs that no accessible copy holds, with the URL when there is one).

5. **Re-curation** of a curated publication: curated again from its full text, without looking at its current curation, and diffed against its live descriptions (`tools.md`).

**Tracking:**

| State + `ai_pass_at` | Meaning                                        |
| -------------------- | ---------------------------------------------- |
| `pending`            | Not pre-curated yet.                           |
| `selected`, null     | Waiting for Claude's curation pass.            |
| `selected`, date     | Claude could not curate it fully: manual pass. |
| `curated`            | Done (by Claude if dated).                     |
| `discarded`          | Rejected at pre-curation.                      |

A run is **complete** when every publication is `discarded` or `curated`. Claude is **done with a run** when no publication is `pending` and every `selected` publication has a date.

A `discarded` publication without a Claude note may have been decided on the abstract or on the full text: the two cannot be told apart, and such states are left as they are.

## 3. Acceptance criteria

01. Peer-reviewed article with a PMID. Reviews without experimental evidence are discarded.
02. Host protein is **human and wild type** (check cell lines, plasmids, cDNA library origin, primers). No evidence → discard.
03. Human identifier from the **Swiss-Prot human reference proteome**.
04. Viral taxon clearly identified, viral protein **wild type**. Strain recorded when clearly described.
05. Viral protein identified in UniProt, with a **standard generic name** (all "non-structural protein 1" variants → `NS1`).
06. Mature proteins from polyproteins are interactors with coordinates (e.g. DENV1 NS5 = `B5AGU1[2494-3392]`).
07. The method detects a **physical** interaction. Excluded: colocalization, functional interaction, citing an interaction shown elsewhere. Included: binary methods (co-crystal, Y2H) and complex-detection methods (co-IP…).
08. Method from the PSI-MI **interaction detection method** branch (MI:0001).
09. Interaction domains (mappings) are collected when clearly identified in the article. See *Mappings* below for how to get their exact sequence.
10. **Tagged proteins** (GFP, FLAG, HA, GST fusions…) are curated as the wild-type protein: the interactor never carries the tag, while a mapping keeps it as extra end residues (*Mappings* below).
11. **Fragments** (truncated constructs used to locate the binding region) are accepted: the interactor is the protein, the fragment is recorded as a mapping.
12. High-throughput publications: assess the rawest data available (e.g. ORF sequences) by alignment to assign the right accession. **Scoring thresholds are the authors' own** (their high-confidence list or cut-off).
13. **No HLA proteins**: a description involving an HLA protein (any `HLA-` gene, vh or hh) is not curated.
14. Viral strain: when the publication gives none, the choice is arbitrary: prefer a **Swiss-Prot** entry; if still undecided, the entry most used in Drakkar for the same virus and generic name.
15. **Swiss-Prot over TrEMBL** whenever both fit.
16. **A name change of a human interactor must make sense**: the new name is the gene name of the snapshot in the database, and the change is checked, e.g. the old name is a synonym of the same UniProt entry, and the old name designated this entry when the publication came out (curators chose the protein from the name they read; `database.md` §3, versioning pass). When it does not make sense, it is not renamed: the case is reported as unsettled.
17. Existing notes are not a source of rules: they can be outdated or wrong. Only the criteria written here apply.

### Mappings: the exact sequence on the closest UniProt entry

The underlying philosophy of the curation, and the reason mismatches are allowed.

> **Fundamental rule.** A mapping, its extra end residues aside (below), may differ from its interactor (mismatches, gaps) for one reason only: the UniProt sequence is not exactly the one used in the experiment of the publication.
>
> - **Viral:** the UniProt entry is not the publication's strain, but the closest one.
> - **Human:** the Swiss-Prot sequence changed between versions.
>
> Any other difference is an error: in the mapping, in the interactor, or in the alignment.

1. **The mapping comes first, especially a short one**: mappings of 20 residues or less get special attention, and a mapping is at least 4 residues (a small motif). Drakkar stores the exact sequence used in the experiment of the publication, and the downstream work uses these sequences. The mapping is taken from the publication's own strain, never from the UniProt entry:
   - the publication gives the sequence: it is taken as written;
   - the publication gives a strain and coordinates on that strain: the subsequence is extracted exactly from that strain's sequence. When UniProt has no entry for the strain, the strain's sequence is taken from GenBank, and the GenBank entry used is recorded in the description note (`Mapping` line, §5).
2. **The interaction is anchored on UniProt.** The interactor is the UniProt entry of the publication's strain, or the closest entry when UniProt does not have that strain (C3).
3. **The alignment links the two.** The mapping, which may come from another strain than the interactor, is aligned on the interactor and its isoforms with a **90 % identity** threshold (C4, a warning, not a hard limit), to tolerate the differences between strains. A single description then keeps both the UniProt reference and the exact mapping. The alignment only locates the mapping: it never changes it.
4. **Extra end residues are named, not aligned.** The sequence used in the experiment can carry, at its N- or C-terminal end, residues that are not on its interactor: the protein's own residues just outside it (the initiator methionine before a mature protein, residues of the polyprotein past its end) or residues of the construct (a tag, a linker). The mapping keeps the whole sequence and names these residues in `nter` (at its start) and `cter` (at its end); its occurrences locate the rest. E.g. HCV Core is 2–191 of the polyprotein, so `MSTNPKPQRKTKRNT` gets `nter` M and is exact on Core. In the files they are written in lowercase (`mSTNPKPQRKTKRNT`, `tools.md`). A peptide across the cleavage site between two mature proteins cannot be recorded: it is skipped and listed in the publication note.

At 90 %, a mapping of 10 residues or more can have one mismatch or gap; a shorter one must match exactly. Why 90 %: small mappings matter most, and UniProt keeps few strains (viral TrEMBL entries outside reference proteomes are deleted, `database.md` §3), so a publication whose exact strain was in an earlier release may now have to be mapped on the closest one.

## 4. Conventions

| ID  | Convention                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C1  | A publication × method × human interactor × viral interactor is recorded **once**; several regions found for it are several mappings of that description. Several live descriptions for the same publication, method, human interactor and viral interactor are an error, fixed by merging them into one (D5).                                                                                                                                                              |
| C2  | A viral interactor always has the same generic name. Reuse the existing name when the interactor is already known.                                                                                                                                                                                                                                                                                                                                                          |
| C3  | The interactor is the UniProt entry **closest** to the publication's protein: the exact strain when it exists, otherwise the closest entry of the same virus, documented and justified in the description note (`Strain` line, §5). The mappings still come from the publication's strain (§3, mappings).                                                                                                                                                                   |
| C4  | The mapping is aligned on the interactor and its isoforms, to verify it belongs to the protein, find all occurrences and get positions. Its identity should reach **90 %** on at least one isoform, to tolerate strain differences (§3, mappings). It is a warning, not a hard limit: below 90 %, the mapping is kept with its best alignment only if the `Mapping` line of the description note explains why. `EY` descriptions were curated at 96 %: below it, D12 warns. |
| C5  | Only proteins from the latest UniProt release in Drakkar are used.                                                                                                                                                                                                                                                                                                                                                                                                          |

## 5. Notes

Two notes, each fact in one place:

| Note                                         | Explains                                                                                                   | Written                                                       |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Publication note (`associations.annotation`) | Decisions about the publication: full-text source, its strain, what was not kept and why, remarks, passes. | At each curation pass, rewritten whole.                       |
| Description note (`descriptions.annotation`) | Claude's decisions about one description: its evidence, a closest entry, its mappings, fixes and updates.  | With each decision, one note per version, empty when obvious. |

Both are for a future human reviewer, and both stay **short**: a few words per decision, never an essay. A versioning pass or a fix writes only description notes, never the publication note.

### Publication note

**The note holds the latest state**: each time Claude acts on a publication, it rewrites the whole note, so it always describes the current state. The only exception is the **pass history** at the end: one short `Pass` line per curation pass, kept across rewrites. **Curator note:** on Claude's first pass (`ai_pass_at` null), a non-empty existing note was written by a curator (e.g. a past curation Claude now reviews). Claude keeps it **verbatim** in a final block, never edited, and kept across every rewrite.

A header line, optional `- ` detail lines, the pass history (oldest first), then the curator note if there was one:

```
[YYYY-MM-DD Claude] STATE: summary
- Label: detail
- Pass YYYY-MM-DD: outcome
--- Curator note (before Claude) ---
<previous note, verbatim>
```

The header is fixed so the write tools can check it: the date of the last rewrite, `Claude`, the association state in capitals, then a one-line summary. The state in the header must match `associations.state`. A note never holds a number the database already gives, such as the count of descriptions: it would go stale with the next revision.

| State       | Summary                                                                                                                             | Detail lines                                                                           |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `SELECTED`  | What the abstract suggests; after a partial curation pass, what was curated and which files are missing.                            | `Full text` once checked; `Strain`, `Not kept`, `Remark` after a partial pass; `Pass`. |
| `DISCARDED` | `<reason code>`, then a short why.                                                                                                  | —                                                                                      |
| `CURATED`   | Source: `from PMC1234567`, `from <URL>`, `from a PDF provided by the user` or `from curator file <name>`; with no description, why. | `Strain`, `Not kept`, `Remark`; `Pass`.                                                |

Pre-curation discard reason codes: `no-viral-protein`, `no-human-protein`, `no-ppi` (no physical interaction suggested), `non-human-host`, `review`, `preprint`, `not-research` (editorial, erratum, protocol…), `other`.

Detail line formats:

- `Full text:` the line written by the fetch (`tools.md`): `Full text: <PMCID> (<license>)`, followed by `, supplementary files not offered by this source` when the PMC copy came without them, `Full text: <source> (<license>, <URL>)` for another copy, or `Full text: closed — <why>` (e.g. not open access anywhere, or open access at <URL> but download blocked); `Full text: PDF provided by the user` for a PDF the user provides
- `Strain: <strain> (<where in the publication>)`: the strain of the publication, when it holds for all its descriptions.
- `Not kept: <pair or claim> — <reason>`
- `Remark: <anything a reviewer should know>` (for a curator file: how ambiguous rows were interpreted)
- `Pass YYYY-MM-DD: <outcome>`, one per curation pass, e.g. `not accessible (not open access)`, `curated from PMC1234567`, `curated from <URL>`, `curated from a PDF provided by the user`, `curated from curator file <name>`, `re-curated from PMC1234567`. The date of the last `Pass` line equals `associations.ai_pass_at`.

### Description note

**One note per version**, holding the decisions taken on that version: first the decision that created it, then the decisions taken on it later without a new version (an interactor put aside, an in-place correction, a removal). The history of a description is its notes read version by version: nothing is repeated from one version to the next. **The note is written for the next pass**, Claude's own memory for future curation and revisions: what was decided and why, what was arbitrary, what stays uncertain, and what would change the decision (e.g. `arbitrary tie: move if its strain gets an entry`). **It is empty when the curation is obvious**: no line is forced. Versions written before Claude have an empty note. In-place structure fixes (e.g. numbers stored as text, D11) get no note.

Each decision is a header line, optionally followed by `- ` detail lines:

```
[YYYY-MM-DD Claude] ACTION: summary
- Label: detail
```

| Action      | When                                                  | Example summary                                                              |
| ----------- | ----------------------------------------------------- | ---------------------------------------------------------------------------- |
| `CREATED`   | New description (curation pass)                       | `anti-tag co-IP (MI:0007), Fig. 2B`                                          |
| `REVISED`   | Revision during curation                              | `method MI:0007 → MI:0096, Fig. 3A is a pull-down`                           |
| `FIXED`     | A fix of an error in the data                         | `name1 AES → TLE5, gene name of the snapshot`                                |
| `UPDATED`   | Revision of the versioning pass                       | `UniProt 2026_03, Q77YF9 → P12520 (deleted; NL4-3 Vpr), 1–78 → 1–96`         |
| `ASIDE`     | An interactor put aside, in place on the live version | `side 2 B0FAN5 deleted, HIV-1 patient isolate, no strain in the publication` |
| `CORRECTED` | In-place correction, no new version (not D11)         | `isoform renamed by UniProt, P01106-1 → P01106`                              |
| `REMOVED`   | Description removed, in place on its last version     | `HLA protein (§3)`                                                           |

`ASIDE` and `CORRECTED` are written in place, outside the write tools, with the user's permission.

Detail line formats:

- `Strain: <strain> (<where>) → <accession> (<strain of the entry>), closest entry: <justification>` (e.g. identity of the protein or of the mappings, same genotype). Required for every interactor that is not the publication's exact strain.
- `Mapping: <start>–<stop> (<evidence>)`; for a mapping below 90 % identity, why it is kept (e.g. `92 % on P0C6U8: closest strain`); followed by `, sequence from GenBank <accession> (<strain>)` when the mapping was extracted from a GenBank entry because UniProt has no entry for the publication's strain.

### Examples

Publication notes:

```
[2026-10-06 Claude] CURATED: from PMC1234567.
- Strain: genotype 1b, Con1 (Methods, "Plasmids").
- Not kept: NS5A × TRIM25 — only cited from ref. 12.
- Pass 2026-10-06: curated from PMC1234567.
```

```
[2026-10-20 Claude] CURATED: from PMC2345678.
- Pass 2026-10-20: reviewed, curated from PMC2345678.
--- Curator note (before Claude) ---
Co-IP fig 2, NS1 only
```

```
[2026-10-05 Claude] DISCARDED: no-ppi — viral protein–RNA interaction, no host protein.
```

```
[2026-10-05 Claude] SELECTED: Y2H screen of ZIKV proteins against a human library.
- Full text: closed — not open access anywhere.
- Pass 2026-10-05: not accessible (not open access).
```

The same publication after a curator file:

```
[2026-10-15 Claude] CURATED: from curator file run88_manual.xlsx.
- Remark: row 7 gives "ZIKV E"; the publication's strain (PRVABC59) was used for the accession.
- Pass 2026-10-05: not accessible (not open access).
- Pass 2026-10-15: curated from curator file run88_manual.xlsx.
```

```
[2026-10-06 Claude] CURATED: from PMC7654321, no description.
- Remark: no physical interaction. Only a luciferase reporter assay (Fig. 3) and colocalization (Fig. 5).
- Pass 2026-10-06: curated from PMC7654321.
```

Description notes, one per version:

```
version 1: [2026-10-06 Claude] CREATED: anti-tag co-IP (MI:0007), Fig. 2B; pull-down (MI:0096), Fig. 3A.
           - Mapping: 2209–2274 (Fig. 4, deletion mutants).
version 2: [2026-11-02 Claude] UPDATED: UniProt 2026_04, new snapshot of P26662, mapping identity 100 → 98.5 %.
```

```
version 3: [2026-10-08 Claude] UPDATED: UniProt 2026_03, human side only.
           [2026-10-08 Claude] ASIDE: side 2 B0FAN5 deleted, HIV-1 patient isolate, no strain in the publication.
```
