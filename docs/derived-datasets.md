# Derived datasets

Terms are defined in `glossary.md`.

Drakkar is the curation database. Derived datasets are exported from it for other applications. This document gives what they are, and what they mean for curation.

## Drakkar is consistent at the UniProt entry level

Each description is exact on its UniProt entries, whatever their version: the snapshot it points to keeps the interactions and the mappings as they were recorded at the time of curation. Drakkar does not reconcile entries or strains: the derived datasets do, when they need to.

## How the datasets reconcile the entries

- **Human interactors** count only on the latest ingested Swiss-Prot release.
- **Viral interactors** count on the latest snapshot they can be on, which may be an old one when the entry left UniProt (e.g. a patient isolate).
- **Live descriptions only.** A deleted version is history, not data; a removed description never counts.

## The four datasets

| Dataset         | What it holds                                                                                                                                                                             |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| hh descriptions | The pairs of human interactors, both up to date.                                                                                                                                          |
| vh descriptions | The up-to-date human interactor and the generic viral protein: (the NCBI taxon ID of the species, one generic name), whatever the strain and the UniProt version of the viral interactor. |
| hh mappings     | Both human interactors up to date; the mapping sequences, with all the isoforms as their source.                                                                                          |
| vh mappings     | The up-to-date human interactor as the target, and the viral source of the mapping, whatever its UniProt version, strain or isoform.                                                      |

**Generic viral proteins.** The vh descriptions dataset needs one generic name per viral protein of a species, across its strains (e.g. `orf14` and `orf9c` for the same protein). This is a viral curation pass of its own: list the species present in Drakkar and group their viral interactors under a single generic protein name. It is never done in the descriptions: curation keeps the names of Drakkar (`curation-rules.md` §1).

## What it means for curation

- Every UniProt upgrade works on all the obsolete interactors: each one is moved to the latest snapshot it can be on, a human one whenever it can be (`database.md` §3, versioning pass).
- A description with an obsolete interactor is live and counts: it was right on its snapshots when it was curated (`curation-rules.md` §1).

## Open questions

1. Licenses: Drakkar is curated from any full text, whatever its license (`curation-rules.md` §1), and the license of each is in its publication note (`Full text` line). Many are under non-commercial licenses (CC BY-NC, BY-NC-ND). What do they allow for the published datasets?
