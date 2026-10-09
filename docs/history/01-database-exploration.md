# Database exploration — first pass

> Note: the workflow and some interpretations below are superseded by `../curation-rules.md` (biology) and `../database.md` (structure, versioning, invariants).

Database: `drakkar_2026_09_09_curation_ai` (PostgreSQL 18.6, schema `public`). Date: 2026-10-02. All queries were run in a read-only session (`default_transaction_read_only=on`).

## 1. Data model as I understand it

```
runs (74)  ──<  associations (109,885)  >──  publications (109,432)
                     │  state: selected | discarded | curated  (+ 'pending', unused)
                     │
                     └──<  descriptions (425,135 rows, 418,014 stable_ids)
                              │  protein1_id ──> proteins (always human, type 'h')
                              │  protein2_id ──> proteins (human for 'hh' runs, viral for 'vh' runs)
                              │  method_id   ──> methods  (full PSI-MI ontology, 1,328 terms)
                              └──< peptides (955, viral only, keyed by stable_id)

proteins (4.96M, UniProt snapshots 2019_01 / 2020_05 / 2021_02)
   └── proteins_versions (accession, version) -> current_version (all = 2021_02)
   └── ncbi_taxon_id ──> taxon / taxon_name (NCBI taxonomy, nested sets left/right_value)

keywords (232): 'g' = interaction terms (interact, bind…), 'v' = virus terms/acronyms
dataset: materialized view joining everything (the export / analysis view)
```

### Workflow inferred from the data

1. A **run** is a batch of PubMed hits from a keyword search (`keywords`: interaction term × virus term). Runs are numbered (`name` = "81", "82", …), typed `vh` (virus–human) or `hh` (human–human).
1. Each hit is an **association** (run, pmid) — triage state: `selected` (to curate), `discarded` (with an optional free-text reason in `annotation`), `curated` (done).
1. Curating a publication = creating **descriptions**: one binary interaction = (human protein + region, partner protein + region, PSI-MI detection method).
1. Edits are **versioned**: the old row gets `deleted_at`, a new row with the same `stable_id` and `version + 1` is created. Deleting an interaction = setting `deleted_at` with no successor.
1. Polyproteins: `name2` + `start2/stop2` give the mature chain (e.g. `NS3` 1503–2119 of a flavivirus genome polyprotein). `mapping1/2` hold peptide/fragment sequences mapped onto isoforms (10,491 rows non-empty).
1. `peptides` carry extra info for short viral peptides (free-text `info`, affinity, hotspots — mostly empty).

### Volumes

| Type | Curated pubs | Live descriptions | Deleted versions | Notes                                                                        |
| ---- | -----------: | ----------------: | ---------------: | ---------------------------------------------------------------------------- |
| vh   |        6,042 |           117,457 |            7,782 | manual curation, median 2 PPIs / paper                                       |
| hh   |        9,363 |           299,446 |              450 | dominated by large screens (HuRI 32296183: 57,742; BioPlex 28514442: 56,903) |

- Triage: 93,731 discarded vs 15,405 curated (≈ 14 % acceptance in `vh`).
- **Backlog**: 749 `selected` associations, 744 of them in recent runs 81–87 (2025–2026).
- Top viruses: SARS-CoV-2 (16.5k), Zika (12.5k across strains), Influenza A, EBV, HCMV, HBV, HCV, HIV-1, HPV16.
- Methods most used (vh): MS of complexes (MI:0069), anti-tag co-IP (MI:0007), pull-down (MI:0096), two-hybrid (MI:0018), affinity chromatography (MI:0004), TAP (MI:0676), proximity labelling (MI:1313).

## 2. Integrity observations (first pass)

### Schema-level

- **No foreign keys** on `descriptions` (→ associations, methods, proteins) nor on `peptides` (→ descriptions). In practice there are **zero orphans** today, but nothing enforces it.
- No triggers; versioning and state logic live in the application.
- `dataset` hardcodes protein1 as *Homo sapiens* (taxon name and nested-set bounds) and **inner-joins** `taxon` for protein2: any description whose protein2 taxon is missing silently disappears from the view.
- `methods` contains the whole PSI-MI ontology (incl. non-detection-method terms such as `reactome`, `rho tag`); nothing restricts descriptions to *interaction detection method* (MI:0001 subtree).
- `proteins` frozen at UniProt **2021_02**, yet curation continued through 2026 — SARS-CoV-2 / new viral entries created after 2021 cannot be referenced.

### Data-level findings

| #   | Check                                                                             | Result                                                                                                           |
| --- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 1   | At most one live version per `stable_id`, and it is the max version               | holds (1,108 stable_ids fully deleted)                                                                           |
| 2   | Live descriptions on non-`curated` associations                                   | **25** (10 `discarded`, 15 `selected`; e.g. pmid 41586518, 41902231, 10603321)                                   |
| 3   | `curated` association with no live description                                    | **1** (assoc 51058, pmid 37097169, run 78)                                                                       |
| 4   | Description absent from `dataset` (missing taxon)                                 | **1** (EY05645BC3, G8EFI1, taxon 1559366); 2,742 proteins have no taxon row                                      |
| 5   | `stop > sequence length`                                                          | **417** (e.g. Q9NVV5 stop 245 vs canonical 238: coordinates seem to refer to another isoform / sequence version) |
| 6   | Exact duplicate live descriptions (same pub, proteins, method, regions, mappings) | **69 groups / 195 rows**, all `vh`                                                                               |
| 7   | Live descriptions on obsolete protein versions                                    | 13,756 (mostly created in 2019)                                                                                  |
| 8   | `name1` ≠ current protein name                                                    | 1,121 (old gene symbols, e.g. AES → TLE5, AARS → AARS1)                                                          |
| 9   | `hh` symmetric duplicates (A–B and B–A, same pub & method)                        | 0; no canonical ordering of the pair though                                                                      |
| 10  | Dates: `deleted_at < created_at`                                                  | 0                                                                                                                |

## 3. Questions for you

### Scope and semantics

1. **Is `hh` in scope?** Should I focus only on `vh`, or are human–human interactions also curated manually now (last `hh` run is from 2020)?
1. **Unit of a description**: one row = one (protein pair × method × publication)? If a paper shows the same pair by co-IP and pull-down, is that two rows? And the same pair by co-IP with two different constructs (regions)?
1. **Direct vs indirect**: does a co-IP / AP-MS association count, or only "direct" interactions? Discard reasons like *"No direct VH-PPI described"* suggest a rule — what exactly is it?
1. **Bait/prey or host/viral orientation**: protein1 is always human; for `hh` is there any meaning to which protein is 1 vs 2?
1. **Regions**: when the paper uses full-length proteins, is `start=1, stop=length` the rule? For a mature viral chain, should the coordinates match the UniProt `chain` feature exactly?
1. **`name2`**: is it free text or should it follow a controlled vocabulary (UniProt chain name, gene name)?
1. **`mapping1/2` and `peptides`**: when are they required? Only for synthetic peptides / fragments shorter than a domain?
1. **Large-scale screens (AP-MS, proteomics)**: what thresholds do you apply (e.g. *"threshold at difference = 4"*)? Is there a generic rule or is it decided per paper?

### Triage

9. What are the selection criteria between `selected` and `discarded`? Is there a list of standard discard reasons (paper unavailable, non-human host, no direct PPI, structure-only, …)?
1. Are the 25 live descriptions on `selected`/`discarded` associations work in progress, or errors?
1. Is `pending` still used? Today no association is in that state.

### Proteins and versions

12. How do you plan to handle proteins newer than UniProt 2021_02? Should I propose an update of `proteins` / `proteins_versions`, or must I only use what exists?
01. Should a description be migrated to a new `proteins.id` when UniProt changes (the 2019 rows on obsolete entries), and is that what versions 2+ mostly represent?
01. For viral proteins, which strain/entry do you pick when the paper only says "ZIKV NS5"? Reference proteome? Swiss-Prot first?

### Operations

15. Is there an application (web UI / API) writing to this DB? I'd like to know how it generates `stable_id` (`EY` + 8 hex; `EYU` prefix only for 58k `hh` rows) and refreshes `dataset`.
01. This database name has a date (2026-09-09): is it a copy dedicated to me? Am I allowed to write in it, and should my descriptions be distinguishable (e.g. a dedicated run, a marker column, a curator field)?
01. Do you have access to full texts (PMC OA, institutional access), or should I work from abstracts only to start?

## 4. Proposed next steps (to discuss)

1. **Invariants**: turn section 2 + your answers into a written list of invariants, then a `uv` Python tool (`ruff`, `pyright`, `mdformat`) that checks them read-only and produces a report.
1. **Benchmark**: use the 6,042 curated `vh` publications as a gold standard — re-curate a sample blindly and measure precision/recall on (pair, method, region) to calibrate the automatic curation.
1. **Ingestion**: start on the 744 `selected` publications of runs 81–87, producing *proposals* (in a staging table or files) that you validate before anything goes into `descriptions`.
