# Curation rules (biological)

Last updated: 2026-10-09. Sources: user answers, PNAS 2024 SI appendix (doi:10.1073/pnas.2308776121, supporting text pp. 3–10). The database side (tables, versioning, invariants) is in `database.md`.

Status tags: **[confirmed]** stated by the user or the SI · **[observed]** seen in past curation, not yet confirmed · **[proposed]** my suggestion, to be validated.

## 1. Context

- Manual curation is stopped. Claude now curates and is the only writer. **[confirmed]**
- Scope: **virus–human (vh) protein–protein interactions** only. Human–human curation is discontinued. **[confirmed]**
- Full texts, in order of priority: **PMC open access** (structured XML, no parsing needed), then **other legal open access copies** (publisher, repository, preprint server; Claude parses HTML or PDF). For other publications, curators may hand over Excel files describing interactions; Claude interprets and inserts them (later). **[confirmed]**
- Claude inserts every new description, whatever its source (full text or curator file), with a `CW` stable ID. `EY` IDs came from the web interface, which is retired. **[confirmed]**
- Publications whose full text Claude cannot access need a human intervention (or a curator file). **[confirmed]**
- **Curation is valid at its time** \[confirmed 2026-10-09\]: a description was right on the UniProt snapshots it was curated on. Updating it to a new release is best effort; when a viral protein is gone from UniProt (e.g. a patient isolate), the description stays live on its old snapshot, and its mappings stay good data.
- **Human interactors are always on the latest Swiss-Prot** \[confirmed 2026-10-09\]: the derived datasets are used on the latest human Swiss-Prot release, so a description is revised whenever one of its human interactors can be updated (`database.md` §3, versioning pass).

## 2. Vocabulary

| Term         | Meaning                                                                                                                                                     |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Interactor   | **(UniProt accession, start, stop)**. Human: always the full protein. Viral: the full protein or a mature protein cleaved from a polyprotein.               |
| Description  | One interaction reported by one publication: human interactor × viral interactor × PSI-MI detection method, with optional mappings.                         |
| Mapping      | The sequence of an interaction domain, exactly as used in the publication's experiment (§4, mappings). It is the reference and is never adapted to UniProt. |
| Generic name | The standard name of a viral interactor (e.g. `NS1`), independent of how UniProt or the publication names it.                                               |
| Note         | Free text justifying the decisions: the publication note, and the description note for one description (§6). **Very important.**                            |

## 3. Process **[confirmed]**

1. A PubMed query collects new PMIDs since the last run. One run per batch. Every publication starts `pending` (not pre-curated).

1. **Pre-curation** on title and abstract, by Claude, for every publication: `selected` or `discarded`. The goal is to remove the query's false positives; about 10 % are selected. A publication is `selected` as soon as the abstract suggests it may contain a virus–human PPI: **the goal is exhaustiveness**, so in doubt, select. **[confirmed]** `discarded` is a pre-curation decision only.

1. **Curation pass** by Claude on each selected publication, from its full text when Claude can get one: first the PMC open access XML (no parsing needed), otherwise another legal open access copy that Claude parses. Once the full text has been read, the publication is `curated`, **whether descriptions were found or not**. A curated publication with zero descriptions is a valid outcome: the publication was reviewed and reports no interaction that meets the criteria. The note says why.

1. Every selected publication Claude went through gets the date of the pass in `associations.ai_pass_at` (`database.md` §5), curated or not. A publication still `selected` with a date needs a **manual pass**: curated by hand, or handed to Claude as a curator file. Its note says why Claude could not curate it (e.g. no accessible full text, with the URL when there is one).

**Tracking \[confirmed\]:**

| State + `ai_pass_at` | Meaning                                  |
| -------------------- | ---------------------------------------- |
| `pending`            | Not pre-curated yet.                     |
| `selected`, null     | Waiting for Claude's curation pass.      |
| `selected`, date     | Claude could not curate it: manual pass. |
| `curated`            | Done (by Claude if dated).               |
| `discarded`          | Rejected at pre-curation.                |

A run is **complete** when every publication is `discarded` or `curated`. Claude is **done with a run** when no publication is `pending` and every `selected` publication has a date. Publications in PMC outside the open access subset cannot be text-mined: Claude uses them only if an open access copy exists elsewhere.

Legacy: in past runs, `discarded` may have been decided on the abstract or on the full text; the two cases cannot be told apart. Legacy states are left as they are.

## 4. Acceptance criteria **[confirmed, SI]**

1. Peer-reviewed article with a PMID. Reviews without experimental evidence are discarded.
1. Host protein is **human and wild type** (check cell lines, plasmids, cDNA library origin, primers). No evidence → discard.
1. Human identifier from the **Swiss-Prot human reference proteome**.
1. Viral taxon clearly identified, viral protein **wild type**. Strain recorded when clearly described.
1. Viral protein identified in UniProt, with a **standard generic name** (all "non-structural protein 1" variants → `NS1`).
1. Mature proteins from polyproteins are interactors with coordinates (e.g. DENV1 NS5 = `B5AGU1[2494-3392]`).
1. The method detects a **physical** interaction. Excluded: colocalization, functional interaction, citing an interaction shown elsewhere. Included: binary methods (co-crystal, Y2H) and complex-detection methods (co-IP…).
1. Method from the PSI-MI **interaction detection method** branch (MI:0001).
1. Interaction domains (mappings) are collected when clearly identified in the article. See *Mappings* below for how to get their exact sequence.
1. **Tagged proteins** (GFP, FLAG, HA, GST fusions…) are curated as the wild-type protein: only the protein sequence is kept, never the tag. **[confirmed]**
1. **Fragments** (truncated constructs used to locate the binding region) are accepted: the interactor is the protein, the fragment is recorded as a mapping. **[confirmed]**
1. High-throughput publications: assess the rawest data available (e.g. ORF sequences) by alignment to assign the right accession. **Scoring thresholds are the authors' own** (their high-confidence list or cut-off). **[confirmed]**
1. **No HLA proteins**: a description involving an HLA protein (any `HLA-` gene, vh or hh) is not curated. The existing ones (241 vh, 835 hh) were removed on 2026-10-06 (`history/02-data-fixes.md` point 7). **[confirmed 2026-10-06, by the biologists]**
1. Viral strain: when the publication gives none, the choice is arbitrary: prefer a **Swiss-Prot** entry; if still undecided, the entry most used in Drakkar for the same virus and generic name. **[confirmed]**
1. **Swiss-Prot over TrEMBL** whenever both fit. **[confirmed]**
1. **A name change of a human interactor must make sense** \[confirmed 2026-10-07\]: the new name is the gene name of the snapshot in the database, and the change is checked, e.g. the old name is a synonym of the same UniProt entry, and the old name designated this entry when the publication came out (curators chose the protein from the name they read; `database.md` §3, versioning pass). When it does not make sense, it is a question for the user, not a renaming.
1. Existing notes are not a source of rules: they can be outdated or wrong. Only the criteria written here apply. **[confirmed]**

### Mappings: the exact sequence on the closest UniProt entry **[confirmed 2026-10-07]**

The underlying philosophy of the curation, and the reason mismatches are allowed.

> **Fundamental rule.** A mapping may differ from its interactor (mismatches, gaps) for one reason only: the UniProt sequence is not exactly the one used in the experiment of the publication.
>
> - **Viral:** the UniProt entry is not the publication's strain, but the closest one.
> - **Human:** the Swiss-Prot sequence changed between versions.
>
> Any other difference is an error: in the mapping, in the interactor, or in the alignment.

1. **The mapping comes first, especially a short one** \[confirmed 2026-10-09\]: mappings of 20 residues or less get special attention, and a mapping is at least 4 residues (a small motif). Drakkar stores the exact sequence used in the experiment of the publication, and the downstream work uses these sequences. The mapping is taken from the publication's own strain, never from the UniProt entry:
   - the publication gives the sequence: it is taken as written;
   - the publication gives a strain and coordinates on that strain: the subsequence is extracted exactly from that strain's sequence. When UniProt has no entry for the strain, the strain's sequence is taken from GenBank, and the GenBank entry used is recorded in the description note (`Mapping` line, §6).
1. **The interaction is anchored on UniProt.** The interactor is the UniProt entry of the publication's strain, or the closest entry when UniProt does not have that strain (C3).
1. **The alignment links the two.** The mapping, which may come from another strain than the interactor, is aligned on the interactor and its isoforms with a **90 % identity** threshold (C4, a warning, not a hard limit), to tolerate the differences between strains. A single description then keeps both the UniProt reference and the exact mapping. The alignment only locates the mapping: it never changes it.

At 90 %, a mapping of 10 residues or more can have one mismatch or gap; a shorter one must match exactly. Why 90 %: small mappings matter most, and new UniProt releases keep fewer strains (most viral TrEMBL entries are deleted, `database.md` §3), so a publication whose exact strain was in an earlier release may now have to be mapped on the closest one.

**Thresholds are warnings** \[confirmed 2026-10-07\]: 90 % for future curation, 96 % for the legacy data, which was curated at 96 %. A mapping below the threshold is not an error: below 90 %, it is accepted only with an explanation in the `Mapping` line of the description note (§6). The legacy edge cases decided one by one (below 96 %) are in `history/02-data-fixes.md`, point 9.

## 5. Conventions

| ID  | Convention                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Status    |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------- |
| C1  | A publication × method × human interactor × viral interactor is recorded **once**; several regions found for it are several mappings of that description. Several live descriptions for the same publication, method, human interactor and viral interactor are an error, fixed by merging them into one (D5).                                                                                                                                                                 | confirmed |
| C2  | A viral interactor always has the same generic name. Reuse the existing name when the interactor is already known. The same protein has the same generic name across the strains of a virus: other applications abstract the strains into one generic interactor [confirmed 2026-10-09].                                                                                                                                                                                       | confirmed |
| C3  | The interactor is the UniProt entry **closest** to the publication's protein: the exact strain when it exists (about 96 % of cases), otherwise the closest entry of the same virus, documented and justified in the description note (`Strain` line, §6). The mappings still come from the publication's strain (§4, mappings).                                                                                                                                                | confirmed |
| C4  | The mapping is aligned on the interactor and its isoforms, to verify it belongs to the protein, find all occurrences and get positions. Its identity should reach **90 %** on at least one isoform, to tolerate strain differences (§4, mappings). It is a warning, not a hard limit: below 90 %, the mapping is kept with its best alignment only if the `Mapping` line of the description note explains why. Legacy descriptions were curated at 96 %, also a warning (D12). | confirmed |
| C5  | Only proteins from the latest UniProt release in Drakkar are used.                                                                                                                                                                                                                                                                                                                                                                                                             | confirmed |

## 6. Notes **[confirmed: free text, format chosen by Claude]**

Two notes, each fact in one place \[confirmed 2026-10-09\]:

| Note                                         | Explains                                                                                                   | Written                                                       |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Publication note (`associations.annotation`) | Decisions about the publication: full-text source, its strain, what was not kept and why, remarks, passes. | At each curation pass, rewritten whole.                       |
| Description note (`descriptions.annotation`) | Claude's decisions about one description: its evidence, a closest entry, its mappings, fixes and updates.  | With each decision, one note per version, empty when obvious. |

Both are for a future human reviewer, and both stay **short**: a few words per decision, never an essay. Maintenance (fixing pass, versioning pass) writes only description notes, never the publication note.

### Publication note

**The note holds the latest state** **[confirmed]**: each time Claude acts on a publication, it rewrites the whole note, so it always describes the current state. The only exception is the **pass history** at the end: one short `Pass` line per curation pass, kept across rewrites. **Curator note \[confirmed\]:** on Claude's first pass (`ai_pass_at` null), a non-empty existing note was written by a curator (e.g. a past curation Claude now reviews). Claude keeps it **verbatim** in a final block, never edited, and kept across every rewrite.

A header line, optional `- ` detail lines, the pass history (oldest first), then the curator note if there was one:

```
[YYYY-MM-DD Claude] STATE: summary
- Label: detail
- Pass YYYY-MM-DD: outcome
--- Curator note (before Claude) ---
<previous note, verbatim>
```

The header is fixed so the check script can parse it: the date of the last rewrite, `Claude`, the association state in capitals, then a one-line summary. The state in the header must match `associations.state`.

| State       | Summary                                                                                            | Detail lines                            |
| ----------- | -------------------------------------------------------------------------------------------------- | --------------------------------------- |
| `SELECTED`  | What the abstract suggests.                                                                        | `Full text` once checked; `Pass`.       |
| `DISCARDED` | `<reason code>`, then a short why.                                                                 | —                                       |
| `CURATED`   | Source and count: `from PMC1234567, 3 descriptions` or `from curator file <name>, N descriptions`. | `Strain`, `Not kept`, `Remark`; `Pass`. |

Pre-curation discard reason codes \[confirmed\]: `no-viral-protein`, `no-human-protein`, `no-ppi` (no physical interaction suggested), `non-human-host`, `review`, `preprint`, `not-research` (editorial, erratum, protocol…), `other`.

Detail line formats:

- `Full text: PMC open access (PMCID)`, `Full text: <source> (<license>, <URL>)` for another open access copy, or `Full text: closed — <why>` (not open access anywhere, or open access at <URL> but download blocked)
- `Strain: <strain> (<where in the publication>)`: the strain of the publication, when it holds for all its descriptions.
- `Not kept: <pair or claim> — <reason>`
- `Remark: <anything a reviewer should know>` (for a curator file: how ambiguous rows were interpreted)
- `Pass YYYY-MM-DD: <outcome>`, one per curation pass, e.g. `not accessible (not open access)`, `curated from PMC1234567`, `curated from curator file <name>`. The date of the last `Pass` line equals `associations.ai_pass_at`.

### Description note

**One note per version**, holding the decisions taken on that version: first the decision that created it, then the decisions taken on it later without a new version (an interactor put aside, an in-place correction, a removal). The history of a description is its notes read version by version: nothing is repeated from one version to the next. **The note is written for the next pass**, Claude's own memory for future curation and revisions: what was decided and why, what was arbitrary, what stays uncertain, and what would change the decision (e.g. `arbitrary tie: move if its strain gets an entry`). **It is empty when the curation is obvious**: no line is forced. Versions written before Claude have an empty note. In-place structure fixes (e.g. numbers stored as text, D11) get no note.

Each decision is a header line, optionally followed by `- ` detail lines:

```
[YYYY-MM-DD Claude] ACTION: summary
- Label: detail
```

| Action      | When                                                  | Example summary                                                           |
| ----------- | ----------------------------------------------------- | ------------------------------------------------------------------------- |
| `CREATED`   | New description (curation pass)                       | `anti-tag co-IP (MI:0007), Fig. 2B`                                       |
| `REVISED`   | Revision during curation                              | `method MI:0007 → MI:0096, Fig. 3A is a pull-down`                        |
| `FIXED`     | Revision of the fixing pass                           | `name1 AES → TLE5, gene name of the snapshot`                             |
| `UPDATED`   | Revision of the versioning pass                       | `UniProt 2026_03, Q77YF9 → P12520 (deleted; NL4-3 Vpr), 1–78 → 1–96`      |
| `ASIDE`     | An interactor put aside, in place on the live version | `side 2 B0FAN5 deleted, HIV-1 patient isolate, no strain in the abstract` |
| `CORRECTED` | In-place correction, no new version (not D11)         | `isoform renamed by UniProt, P01106-1 → P01106`                           |
| `REMOVED`   | Description removed, in place on its last version     | `HLA protein (§4)`                                                        |

Detail line formats:

- `Strain: <strain> (<where>) → <accession> (<strain of the entry>), closest entry: <justification>` (e.g. identity of the protein or of the mappings, same genotype). Required for every interactor that is not the publication's exact strain.
- `Mapping: <start>–<stop> (<evidence>)`; for a mapping below 90 % identity, why it is kept (e.g. `92 % on P0C6U8: closest strain`); followed by `, sequence from GenBank <accession> (<strain>)` when the mapping was extracted from a GenBank entry because UniProt has no entry for the publication's strain.

### Examples

Publication notes:

```
[2026-10-06 Claude] CURATED: from PMC1234567, 2 descriptions.
- Strain: genotype 1b, Con1 (Methods, "Plasmids").
- Not kept: NS5A × TRIM25 — only cited from ref. 12.
- Pass 2026-10-06: curated from PMC1234567.
```

```
[2026-10-20 Claude] CURATED: from PMC2345678, 1 description.
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
[2026-10-15 Claude] CURATED: from curator file run88_manual.xlsx, 4 descriptions.
- Remark: row 7 gives "ZIKV E"; the publication's strain (PRVABC59) was used for the accession.
- Pass 2026-10-05: not accessible (not open access).
- Pass 2026-10-15: curated from curator file run88_manual.xlsx.
```

```
[2026-10-06 Claude] CURATED: from PMC7654321, 0 descriptions.
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
           [2026-10-08 Claude] ASIDE: side 2 B0FAN5 deleted, HIV-1 patient isolate, no strain in the abstract.
```

## 7. Open questions for a biologist

None at the moment.

Answered on 2026-10-05: tags and fragments (§4), several regions for one pair and method (one description, its mappings list), pre-curation (§3), epitopes (not PPIs), methods (no rule taken from old notes; criteria of §4), high-throughput thresholds (the authors'), strain without information and Swiss-Prot vs TrEMBL (§4).
