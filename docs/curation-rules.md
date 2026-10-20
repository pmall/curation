# Curation rules

The biological rules of curation: what is curated, and how each value of a description is identified. The method is the one published in the PNAS 2024 SI appendix (doi:10.1073/pnas.2308776121, supporting text pp. 3–10).

## 1. Principles

- **Scope**: virus–human (vh) protein–protein interactions. Human–human (hh) descriptions get no new curation.
- **Full texts**: a publication is read in its full text, with its supplementary files, from any copy at hand (PMC, the publisher, a repository, a PDF the user provides); never a preprint, which is not peer-reviewed (01). Images are never read.
- **Relevant files**: a supplementary file is relevant when it can hold interactions. A file that was read is judged by its content; a file that could not be read (not fetched, held by no copy, failed to convert) by what the text, its caption or its name show: a table of hits, a figure of an interaction experiment, data the text cites for an interaction. Irrelevant, for instance: an image, a video, a reporting summary, a peer review file, a checklist, a figure of non-interaction data, a file of raw source data whose values are already in a table that was read.
- **The publications are the truth**: only what the publication demonstrates is recorded, never what is concluded from it. A description says what its publication shows, read in its full text, on its interactors' own UniProt entries (their names, chains and sequences). A description already in Drakkar is held to the same: anything that does not match its publication (a name, a region, a strain, an entry, a sequence) is curated again. A curation mistake is never assumed from Drakkar alone.
- **Every description is written**: a pair the publication shows is either a description, or not kept because a criterion fails, with the reason. Each value of a description is identified by the first tier that gives it (§4), from the most direct to the most inferred; a value from another database is allowed, and cited. A value read from free text (e.g. a name in an entry's description) is stated as Claude's reading, never as the source's.
- **Each description is judged on its own**: against its own publication and its own UniProt entries, never by comparison with how another description was decided. A difference between two comparable descriptions only points at rows to look at again.
- **Exact curation, not grouping**: each description is exactly right (accessions, coordinates, generic names, mappings). How the data is grouped (species, taxonomy levels, strains abstracted into one interactor) is the concern of the derived datasets (`derived-datasets.md`). Grouping is only a tool to spot curation errors.
- **Names**: the generic name of a viral interactor names the protein the publication tested, written as Drakkar already names it: the names already used for the strain, then the virus, then the family are followed, the existing name of that protein reused rather than the publication's spelling (`orf6`, not `orf-6`), and a new protein named in the form its neighbours use. Generic names are enforced on the entry: one name per region of an entry, one region per name. The same name across the strains of a virus is followed when it can be, not enforced.

## 2. Acceptance criteria

01. Peer-reviewed article with a PMID. Reviews without experimental evidence are not curated.
02. Host protein is **human and wild type** (check cell lines, plasmids, cDNA library origin, primers); without evidence, not kept. A protein carrying a changed residue is not wild type, whatever the purpose of the change (a catalytically dead enzyme included), and an experiment that uses it is not kept. A fragment (11) and a tag (10) are not changes.
03. Human identifier from the **Swiss-Prot human reference proteome**.
04. Viral taxon clearly identified, viral protein **wild type** (as in 02). Strain recorded when clearly described.
05. Viral protein identified in UniProt, with a **standard generic name** (all "non-structural protein 1" variants → `NS1`).
06. Mature proteins from polyproteins are interactors with coordinates (e.g. DENV1 NS5 = `B5AGU1[2494-3392]`).
07. The method detects a **physical** interaction. Excluded: colocalization, functional interaction, citing an interaction shown elsewhere. Included: binary methods (co-crystal, Y2H) and complex-detection methods (co-IP…). A description is a bait, a prey and the method that detected their binding, recorded once per publication × method × human interactor × viral interactor. Any experiment in which the method detects the bait bound to the prey is evidence, even when the experiment was designed to test something else: in an inhibition assay, for example, the inhibitor is the variable, and the condition without it is the method detecting the bait bound to the prey, so that condition is evidence of the description. What the experiment adds without being detected bound (an inhibitor, a competitor, a blocking peptide) is neither an interactor nor a mapping.
08. Method from the PSI-MI **interaction detection method** branch (MI:0001).
09. **Mappings**: the fragments of the bait or the prey the publication shows bound (§3).
10. **Tagged proteins** (GFP, FLAG, HA, GST fusions…) are curated as the wild-type protein: the interactor never carries the tag, while a mapping keeps it as extra end residues (§3).
11. **Fragments** (truncated constructs) are accepted: the interactor is the protein, the fragment a mapping (§3).
12. High-throughput publications: assess the rawest data available (e.g. ORF sequences) by alignment to assign the right accession. **Scoring thresholds are the authors' own**: a measured affinity is an interaction, whatever its value, and a screen is curated no further than its authors went: their thresholds, and the subset they retain as their result when they narrow their list.
13. **No HLA proteins**: a description involving an HLA protein (any `HLA-` gene, vh or hh) is not curated.
14. **Swiss-Prot over TrEMBL** whenever both fit.
15. Existing notes are not a source of rules: they can be outdated or wrong. Only the criteria written here apply.

## 3. The values of a description

A description records, for each interactor, its UniProt entry and, for a mature protein, its coordinates; and, on each side, its mappings.

### The UniProt entry

Each interactor is an entry of the current UniProt release in Drakkar: for a human protein, an entry of the Swiss-Prot human reference proteome (03); for a viral protein, the entry of the publication's strain, or the closest entry when UniProt does not have it. The interactor is the protein the experiment tested, never its construct: a tag (10) or a truncation (11) leaves it the same protein. When the publication names only a protein family or a complex (e.g. "Sec61", "14-3-3") where an experiment tested one protein, the interactor is the member the evidence points to (the construct, the primers, the antibody, the cited source).

### The coordinates of a mature protein

A human interactor is always its whole protein. A viral interactor is a whole protein, or a mature protein cleaved from a polyprotein (06): the polyprotein's entry, with the start and stop of the mature protein on it. Two mature proteins of one polyprotein are two interactors.

### The mappings

A mapping is a fragment of the bait or the prey that the publication shows bound: the part of the interactor its construct carried, recorded as the exact sequence that was tested. It is what is demonstrated, and only that: a region concluded from the results is not shown to bind on its own, and is no mapping; neither is what the experiment adds without being detected bound (07). The interactor stays the whole protein, or the mature protein. A mapping belongs to one side of one description, so to its method; a description holds every mapping its publication shows for it, or none. A mapping is at least 4 residues, and the short ones, of 20 residues or less, get special attention.

The sequence is the one of the experiment, from the publication's own sequence, never adapted to UniProt: the downstream work uses these sequences. The alignment links it to the interactor: the mapping is aligned on the interactor and its isoforms, which verifies that it belongs to the protein, finds all its occurrences and gives their positions, and never changes it. Its identity should reach 90 % on at least one isoform, to tolerate the differences between strains, as UniProt keeps few of them: a mapping of 10 residues or more can have one mismatch or gap, a shorter one must match exactly. Below 90 %, it is kept with its best alignment only when the description note says why. A mapping may differ from its interactor for one reason only: the UniProt sequence is not the one of the experiment (viral: the entry is the closest strain, not the publication's; human: the Swiss-Prot sequence changed since). Any other difference is an error, in the mapping, the interactor or the alignment.

The tested sequence can carry, at its N- or C-terminal end, residues that are not on its interactor: the protein's own residues just outside it (the initiator methionine before a mature protein, residues of the polyprotein past its end) or residues of the construct (a tag, a linker). The mapping keeps them, named `nter` (at its start) and `cter` (at its end), and only the rest is aligned. A fragment across the cleavage site between two mature proteins cannot be recorded: it is not kept.

## 4. How each value is identified

Each value is identified by the first tier that gives it, in the three lists below, from the most direct to the most inferred; the last tier of each list is any way possible. The lists apply to the human and the viral interactors alike.

### The UniProt entry

1. A current UniProt accession the publication gives.
2. An identifier of another database the publication gives (a GenBank or RefSeq accession, a PDB code, a clone, a plasmid, a commercial construct): the current entry it cross-references, or the current entry identical by sequence.
3. The protein named, with the strain for a viral protein (for a human protein, its gene name): its current entry.
4. The protein's sequence, from the publication or from another database: the closest current entry by sequence, of the same virus for a viral protein.
5. A viral protein whose strain is not given: a Swiss-Prot entry of the virus, otherwise the entry most used in Drakkar for that virus and generic name.
6. A viral protein whose virus has no current entry: the closest current entry by sequence, whatever its virus.
7. Any way possible.

### The coordinates of a mature protein

1. The chain of the mature protein on the entry (UniProt chain feature).
2. The mature protein's boundaries given by the publication, on the entry or aligned on it from the publication's sequence.
3. The mature peptide features of the entry's GenBank or RefSeq record.
4. The chain of the same mature protein on another entry (another strain), aligned on the entry.
5. Any way possible.

### The mappings

1. The sequence the publication writes (text, figure, table, supplementary file).
2. Coordinates on the publication's sequence (its strain, its clone): the subsequence of that sequence, from UniProt or another database.
3. Coordinates on another sequence the publication names (a reference strain, a numbering it states): the region they designate on that sequence, carried over to the publication's sequence when it is known, else that subsequence.
4. A construct the publication names without coordinates (a deletion mutant, primers, a commercial or deposited construct, a construct of a cited publication): its boundaries as that construct's own record gives them (the primers, the supplier, the plasmid record, the cited publication), on the publication's sequence.
5. Any way possible that gives the sequence the construct carried.
