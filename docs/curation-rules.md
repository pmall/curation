# Curation rules (biological)

Last updated: 2026-10-05. Sources: user answers, PNAS 2024 SI appendix (doi:10.1073/pnas.2308776121, supporting text pp. 3–10). The database side (tables, versioning, invariants) is in `database.md`.

Status tags: **[confirmed]** stated by the user or the SI · **[observed]** seen in past curation, not yet confirmed · **[proposed]** my suggestion, to be validated.

## 1. Context

- Manual curation is stopped. Claude now curates and is the only writer. **[confirmed]**
- Scope: **virus–human (vh) protein–protein interactions** only. Human–human curation is discontinued. **[confirmed]**
- Full texts, in order of priority: **PMC open access** (structured XML, no parsing needed), then **other legal open access copies** (publisher, repository, preprint server; Claude parses HTML or PDF). For other papers, curators may hand over Excel files describing interactions; Claude interprets and inserts them (later). **[confirmed]**
- Claude inserts every new description, whatever its source (full text or curator file), with a `CW` stable ID. `EY` IDs came from the web interface, which is retired. **[confirmed]**
- Papers whose full text Claude cannot access need a human intervention (or a curator file). **[confirmed]**

## 2. Vocabulary

| Term         | Meaning                                                                                                                                       |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Interactor   | **(UniProt accession, start, stop)**. Human: always the full protein. Viral: the full protein or a mature protein cleaved from a polyprotein. |
| Description  | One interaction reported by one paper: human interactor × viral interactor × PSI-MI detection method, with optional mappings.                 |
| Mapping      | The sequence of an interaction domain, as close as possible to what the paper describes. It is the reference and is never adapted to UniProt. |
| Generic name | The standard name of a viral interactor (e.g. `NS1`), independent of how UniProt or the paper names it.                                       |
| Note         | Free text attached to a paper, justifying the decision. **Very important.**                                                                   |

## 3. Process **[confirmed]**

1. A PubMed query collects new PMIDs since the last run. One run per batch. Every paper starts `pending` (not pre-curated).

1. **Pre-curation** on title and abstract, by Claude, for every paper: `selected` or `discarded`. The goal is to remove the query's false positives; about 10 % are selected. A paper is `selected` as soon as the abstract suggests it may contain a virus–human PPI: **the goal is exhaustiveness**, so in doubt, select. **[confirmed]** `discarded` is a pre-curation decision only.

1. **Curation pass** by Claude on each selected paper, from its full text when Claude can get one: first the PMC open access XML (no parsing needed), otherwise another legal open access copy that Claude parses. Once the full text has been read, the paper is `curated`, **whether descriptions were found or not**. A curated paper with zero descriptions is a valid outcome: the paper was reviewed and reports no interaction that meets the criteria. The note says why.

1. Every selected paper Claude went through gets the date of the pass in `associations.ai_pass_at` (`database.md` §5), curated or not. A paper still `selected` with a date needs a **manual pass**: curated by hand, or handed to Claude as a curator file. Its note says why Claude could not curate it (e.g. no accessible full text, with the URL when there is one).

**Tracking \[confirmed\]:**

| State + `ai_pass_at` | Meaning                                  |
| -------------------- | ---------------------------------------- |
| `pending`            | Not pre-curated yet.                     |
| `selected`, null     | Waiting for Claude's curation pass.      |
| `selected`, date     | Claude could not curate it: manual pass. |
| `curated`            | Done (by Claude if dated).               |
| `discarded`          | Rejected at pre-curation.                |

A run is **complete** when every paper is `discarded` or `curated`. Claude is **done with a run** when no paper is `pending` and every `selected` paper has a date. Papers in PMC outside the open access subset cannot be text-mined: Claude uses them only if an open access copy exists elsewhere.

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
1. Interaction domains (mappings) are collected when clearly identified in the article.
1. **Tagged proteins** (GFP, FLAG, HA, GST fusions…) are curated as the wild-type protein: only the protein sequence is kept, never the tag. **[confirmed]**
1. **Fragments** (truncated constructs used to locate the binding region) are accepted: the interactor is the protein, the fragment is recorded as a mapping. **[confirmed]**
1. High-throughput papers: assess the rawest data available (e.g. ORF sequences) by alignment to assign the right accession. **Scoring thresholds are the authors' own** (their high-confidence list or cut-off). **[confirmed]**
1. **No HLA proteins**: a description involving an HLA protein (any `HLA-` gene, vh or hh) is not curated. The existing ones (241 vh, 835 hh) were removed on 2026-10-06 (`02-data-fixes.md` point 7). **[confirmed 2026-10-06, by the biologists]**
1. Viral strain: when the paper gives none, the choice is arbitrary: prefer a **Swiss-Prot** entry; if still undecided, the entry most used in Drakkar for the same virus and generic name. **[confirmed]**
1. **Swiss-Prot over TrEMBL** whenever both fit. **[confirmed]**
1. Existing notes are not a source of rules: they can be outdated or wrong. Only the criteria written here apply. **[confirmed]**

## 5. Conventions

| ID  | Convention                                                                                                                                                                                                                                                                                         | Status    |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| C1  | A paper × method × human interactor × viral interactor is recorded **once**; several regions found for it are several mappings of that description. Several live descriptions for the same paper, method, human interactor and viral interactor are an error, fixed by merging them into one (D5). | confirmed |
| C2  | A viral interactor always has the same generic name. Reuse the existing name when the interactor is already known.                                                                                                                                                                                 | confirmed |
| C3  | The interactor is the UniProt entry **closest** to the paper's protein: the exact strain when it exists (about 96 % of cases), otherwise the closest entry of the same virus, documented and justified in the note (`Strain` line, §6).                                                            | confirmed |
| C4  | The mapping is aligned on the interactor and its isoforms, to verify it belongs to the protein, find all occurrences and get positions. It must reach **≥ 96 % identity** on at least one isoform; no match or a lower identity flags the description for deeper review instead of inserting it.   | confirmed |
| C5  | Only proteins from the latest UniProt release in Drakkar are used.                                                                                                                                                                                                                                 | confirmed |

## 6. Notes **[confirmed: free text, format chosen by Claude]**

The note on the paper (`associations.annotation`) explains the choices at **article level**, for a future human reviewer. There is no per-description evidence.

**The note holds the latest state** **[confirmed]**: each time Claude acts on a paper, it rewrites the whole note, so it always describes the current state and descriptions. The only exception is the **pass history** at the end: one short `Pass` line per curation pass, kept across rewrites, so the note stays short while the passes stay traceable. The history of descriptions is in their versions. **Curator note \[confirmed\]:** on Claude's first pass (`ai_pass_at` null), a non-empty existing note was written by a curator (e.g. a past curation Claude now reviews). Claude keeps it **verbatim** in a final block, never edited, and kept across every rewrite.

### Template

A header line, optional `- ` detail lines, the pass history (oldest first), then the curator note if there was one:

```
[YYYY-MM-DD Claude] STATE: summary
- Label: detail
- Pass YYYY-MM-DD: outcome
--- Curator note (before Claude) ---
<previous note, verbatim>
```

The header is fixed so the check script can parse it: the date of the last rewrite, `Claude`, the association state in capitals, then a one-line summary. The state in the header must match `associations.state`.

| State       | Summary                                                                                            | Detail lines                                                          |
| ----------- | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `SELECTED`  | What the abstract suggests.                                                                        | `Full text` once checked; `Pass`.                                     |
| `DISCARDED` | `<reason code>`, then a short why.                                                                 | —                                                                     |
| `CURATED`   | Source and count: `from PMC1234567, 3 descriptions` or `from curator file <name>, N descriptions`. | `Kept`, `Not kept`, `Strain`, `Mapping`, `Revised`, `Remark`; `Pass`. |

Pre-curation discard reason codes \[confirmed\]: `no-viral-protein`, `no-human-protein`, `no-ppi` (no physical interaction suggested), `non-human-host`, `review`, `preprint`, `not-research` (editorial, erratum, protocol…), `other`.

Detail line formats:

- `Full text: PMC open access (PMCID)`, `Full text: <source> (<license>, <URL>)` for another open access copy, or `Full text: closed — <why>` (not open access anywhere, or open access at <URL> but download blocked)
- `Kept: <generic name> (<accession>[start-stop]) × <gene> (<accession>) — <method> (MI:xxxx), Fig. 2B[; <method>, Fig. 3A]`
- `Not kept: <pair or claim> — <reason>`
- `Strain: <strain> (<where in the paper>)`. When the paper's strain has no UniProt entry: `Strain: <strain> (<where>) → <accession> (<strain of the entry>), closest entry: <justification>` (e.g. identity of the protein or of the mappings, same genotype). Required for every interactor that is not the paper's exact strain.
- `Mapping: <interactor> <start>–<stop> (<evidence>)`
- `Revised: <stable IDs> — <reason>` (UniProt upgrade, invariant fix; only the latest revision)
- `Remark: <anything a reviewer should know>` (for a curator file: how ambiguous rows were interpreted)
- `Pass YYYY-MM-DD: <outcome>`, one per curation pass, e.g. `not accessible (not open access)`, `curated from PMC1234567`, `curated from curator file <name>`. The date of the last `Pass` line equals `associations.ai_pass_at`.

### Examples

Review of a past curation (the note was `Co-IP fig 2, NS1 only` before Claude's first pass):

```
[2026-10-20 Claude] CURATED: from PMC2345678, 1 description.
- Kept: NS1 (P03496) × TRIM25 (Q14258) — anti-tag co-IP (MI:0007), Fig. 2.
- Revised: EY1A2B3C4D — UniProt 2026_04 upgrade, new snapshot of P03496.
- Pass 2026-10-20: reviewed, curated from PMC2345678.
--- Curator note (before Claude) ---
Co-IP fig 2, NS1 only
```

```
[2026-10-06 Claude] CURATED: from PMC1234567, 2 descriptions.
- Kept: NS5A (P26662[1973-2419]) × EIF2AK2 (P19525) — anti-tag co-IP (MI:0007), Fig. 2B; pull-down (MI:0096), Fig. 3A.
- Not kept: NS5A × TRIM25 — only cited from ref. 12.
- Strain: genotype 1b, Con1 (Methods, "Plasmids").
- Mapping: NS5A 2209–2274 (Fig. 4, deletion mutants).
- Pass 2026-10-06: curated from PMC1234567.
```

```
[2026-10-05 Claude] DISCARDED: no-ppi — viral protein–RNA interaction, no host protein.
```

```
[2026-10-05 Claude] SELECTED: Y2H screen of ZIKV proteins against a human library.
- Full text: closed — not open access anywhere.
- Pass 2026-10-05: not accessible (not open access).
```

The same paper after a curator file:

```
[2026-10-15 Claude] CURATED: from curator file run88_manual.xlsx, 4 descriptions.
- Kept: …
- Remark: row 7 gives "ZIKV E"; the paper's strain (PRVABC59) was used for the accession.
- Pass 2026-10-05: not accessible (not open access).
- Pass 2026-10-15: curated from curator file run88_manual.xlsx.
```

```
[2026-10-06 Claude] CURATED: from PMC7654321, 0 descriptions.
- Remark: no physical interaction. Only a luciferase reporter assay (Fig. 3) and colocalization (Fig. 5).
- Pass 2026-10-06: curated from PMC7654321.
```

## 7. Open questions for a biologist

None at the moment.

Answered on 2026-10-05: tags and fragments (§4), several regions for one pair and method (one description, its mappings list), pre-curation (§3), epitopes (not PPIs), methods (no rule taken from old notes; criteria of §4), high-throughput thresholds (the authors'), strain without information and Swiss-Prot vs TrEMBL (§4).
