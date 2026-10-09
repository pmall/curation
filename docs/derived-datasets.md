# Derived datasets

Last updated: 2026-10-09. Terms are defined in `glossary.md`.

Drakkar is the curation database. Derived datasets are exported from it for other applications, which work on the latest human Swiss-Prot release. Many forms of datasets can be derived; this document gives the principles, and what they mean for curation.

## Two things curated at once [confirmed 2026-10-09]

- **The vh interactome:** which viral protein interacts with which human protein. Only up-to-date descriptions count. Consuming applications rarely care about strains: they abstract a viral protein as (a common taxon, its generic name).
- **The mappings:** the sequences of interaction domains, each recorded on a source interactor, which can be a strain. It says that this mapping was observed on this strain once. The source is kept up to date as long as possible, but viral UniProt entries are rarely updated: a new sequence usually gets a new entry, and the old one leaves UniProt. Dropping a recorded mapping because its entry left the latest release would make no sense. What consuming applications need is a human target that fits the latest Swiss-Prot.

Example of a consumer: a graph database built from Drakkar, whose viral nodes are abstracted as (common taxon, generic name), and whose mappings point to their human target nodes.

## Principles [confirmed 2026-10-09]

- **Live descriptions only.** A deleted version never counts: a version replaced by a revision is history, not data. A removed description (no live version, e.g. the HLA descriptions) never counts.
- **Obsolete is not deleted.** An obsolete description (at least one obsolete interactor) is live and counts: it was right on its snapshots when it was curated (`curation-rules.md` §1).
- **The human target is always up to date**: on a current Swiss-Prot snapshot.

## Descriptions dataset

The live descriptions with no obsolete interactor. It is always up to date.

## Mappings dataset

The mappings of the live descriptions whose human target is up to date. The interactor a mapping is recorded on may be on a current or an old snapshot: a mapping found only on a strain deleted from UniProt (e.g. a patient isolate) is kept, with its old release as its source. The same holds in hh: one human interactor up to date, the other on an old snapshot with a mapping.

Mappings with no up-to-date human target are left out.

## What it means for curation

- A description is revised whenever one of its human interactors can be updated to the latest Swiss-Prot, even when its other interactor cannot (`database.md` §3, versioning pass).
- The same viral protein has the same generic name across the strains of a virus (`curation-rules.md` C2): the datasets abstract the strains.
