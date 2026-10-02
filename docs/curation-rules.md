# Curation rules (biological)

Last updated: 2026-10-02. Sources: user answers, PNAS 2024 SI appendix (doi:10.1073/pnas.2308776121, supporting text pp. 3–10). The database side (tables, versioning, invariants) is in `database.md`.

Status tags: **[confirmed]** stated by the user or the SI · **[observed]** seen in past curation, not yet confirmed · **[proposed]** my suggestion, to be validated.

## 1. Context

- Manual curation is stopped. Claude now curates and is the only writer. **[confirmed]**
- Scope: **virus–human (vh) protein–protein interactions** only. Human–human curation is discontinued. **[confirmed]**
- Full texts: **PMC open access** only, for now. Non-OA papers will be curated by humans outside the interface and handed over as Excel files to interpret and ingest (later). **[confirmed]**

## 2. Vocabulary

| Term         | Meaning                                                                                                                                       |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Interactor   | **(UniProt accession, start, stop)**. Human: always the full protein. Viral: the full protein or a mature protein cleaved from a polyprotein. |
| Description  | One interaction reported by one paper: human interactor × viral interactor × PSI-MI detection method, with optional mappings.                 |
| Mapping      | The sequence of an interaction domain, as identified in the paper.                                                                            |
| Generic name | The standard name of a viral interactor (e.g. `NS1`), independent of how UniProt or the paper names it.                                       |
| Note         | Free text attached to a paper, justifying the decision. **Very important.**                                                                   |

## 3. Process **[confirmed]**

1. A PubMed query collects new PMIDs since the last run.
1. **Pre-curation** on title and abstract: `selected` or `discarded`. The goal is to remove the query's false positives; about 10 % are selected.
1. **Curation** of each selected paper from its full text: either record descriptions and mark the paper `curated`, or record none and mark it `discarded`. Write a note in both cases.

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
1. High-throughput papers: assess the rawest data available (e.g. ORF sequences) by alignment to assign the right accession.

## 5. Conventions

| ID  | Convention                                                                                                                                                                | Status    |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| C1  | A paper × method × human interactor × viral interactor is recorded **once**.                                                                                              | confirmed |
| C2  | A viral interactor always has the same generic name. Reuse the existing name when the interactor is already known.                                                        | confirmed |
| C3  | No reference strain: record the strain the paper describes. Viral interactors are *supposed* to be equivalent across strains, but nothing enforces it.                    | confirmed |
| C4  | A new mapping must match **at least one isoform at 100 % identity**. Old mappings with tolerated mismatches (96–100 %) are left as they are.                              | confirmed |
| C5  | Only proteins from the latest UniProt release in Drakkar are used.                                                                                                        | confirmed |
| C6  | Past curators created one description per mapping when a paper showed several regions for the same pair (e.g. 21454588, HLA-A × viral epitopes), which conflicts with C1. | observed  |

## 6. Notes **[confirmed: free text, format chosen by Claude]**

The note on the paper (`associations.annotation`) explains the choices at **article level**, for a future human reviewer. There is no per-description evidence.

Format I'll use:

```
[2026-10-05 Claude] CURATED from PMC1234567.
- Kept: NS1 (P03496) × IRF3 — co-IP, Fig. 2B; pull-down, Fig. 3A. Mapping NS1 1–73 (Fig. 4, deletion mutants).
- Not kept: NS1 × TRIM25 — only cited from ref. 12.
- Strain: A/Puerto Rico/8/1934 (Methods, "Viruses").
```

```
[2026-10-05 Claude] DISCARDED: no physical interaction. Only a luciferase reporter assay (Fig. 3) and colocalization (Fig. 5).
```

New entries are appended after any existing text.

## 7. Open questions for a biologist

1. **Constructs:** same pair, same method, several interacting regions (deletion mutants, epitopes). One description with several mappings, or one description per region (C6 vs C1)?
1. **Epitopes:** is HLA presentation of a viral peptide (21454588) a virus–human PPI to curate?
1. **Methods:** which PSI-MI methods are accepted? The SI accepts complex-detection methods (co-IP, AP-MS), but some discard notes say *"No direct VH-PPI described"*. Is there a rule for "direct"? I can provide the list of methods used in vh, with counts, as a starting point.
1. **High-throughput / AP-MS:** which scoring thresholds apply? The authors' high-confidence list, or a generic rule?
1. **Tags and mutants:** are tagged proteins (GFP, FLAG, GST fusions) "wild type"? Are truncated constructs accepted as long as the region is mapped?
1. **Strain:** when a paper gives no strain, which UniProt entry should be chosen? (Practical option: the entry most used in Drakkar for the same virus species and generic name.)
1. **Swiss-Prot vs TrEMBL** for viral proteins: prefer Swiss-Prot when both exist?
1. **Pre-curation:** what makes a title and abstract good enough to be `selected`?
