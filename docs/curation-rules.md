# Curation rules

The biological rules of curation: what is curated, and how each value of a description is identified. The method is the one published in the PNAS 2024 SI appendix (doi:10.1073/pnas.2308776121, supporting text pp. 3–10).

## 1. Principles

- **Scope**: virus–human (vh) protein–protein interactions. Human–human (hh) descriptions get no new curation.
- **Full texts**: a publication is read in its full text, with its supplementary files, from any copy at hand (PMC, the publisher, a repository, a PDF the user provides); never a preprint, which is not peer-reviewed (01). Images are never read.
- **Relevant files**: a supplementary file is relevant when it can hold interactions. A file that was read is judged by its content; a file that could not be read (not fetched, held by no copy, failed to convert) by what the text, its caption or its name show: a table of hits, a figure of an interaction experiment, data the text cites for an interaction. Irrelevant, for instance: an image, a video, a reporting summary, a peer review file, a checklist, a figure of non-interaction data, a file of raw source data whose values are already in a table that was read.
- **The publications are the truth**: a description records what its publication demonstrates, never what is concluded from it, on its interactors' own UniProt entries (their names, chains and sequences).
- **Every description is written**: a pair the publication shows is either a description, or not kept because a criterion fails, with the reason. Each value is identified by its tier (§4); a value from another database is allowed, and cited. A value read from free text (e.g. a name in an entry's description) is stated as Claude's reading, never as the source's.
- **Right is not the same as not wrong**: a value the publication determines, with no doubt and no judgement call, is right, and is recorded as it is. Where no right value exists — the publication does not determine it, or its authors err or contradict themselves — a value that is not wrong is recorded: one the publication supports and that can be defended, with the description note saying what could not be determined and why. Such a value is not an error: the curator chooses it, and justifies it if a reviewer asks. A value the publication contradicts, and a value that was never verified, are wrong.
- **Each description is judged on its own**: against its own publication and its own UniProt entries, never by comparison with how another description was decided. A difference between two comparable descriptions only points at rows to look at again.
- **Exact curation, not grouping**: each description is exactly right (accessions, coordinates, generic names, mappings). How the data is grouped (species, taxonomy levels, strains abstracted into one interactor) is the concern of the derived datasets (`derived-datasets.md`). Grouping is only a tool to spot curation errors.
- **Names**: the generic name of a viral interactor names the protein the publication tested, as Drakkar already names it: follow the names used for the strain, then the virus, then the family; reuse the existing name of that protein rather than the publication's spelling (`orf6`, not `orf-6`); name a new protein in the form its neighbours use. On one entry, one name per region and one region per name: this is enforced. Across the strains of a virus, the same name is used when it can be: this is not enforced.

## 2. Acceptance criteria

01. Peer-reviewed article with a PMID. Reviews without experimental evidence are not curated.
02. Host protein is **human and wild type** (check cell lines, plasmids, cDNA library origin, primers); without evidence, not kept. A protein carrying a changed residue anywhere in its sequence is not wild type, whatever the purpose of the change (a catalytically dead enzyme included), and an experiment that uses it is not kept. A natural post-translational modification (a phosphorylation, an acetylation, a glycosylation) changes no residue: the protein is still wild type, and the description note names the modification. A fragment (11) and a tag (10) are not changes either.
03. Human identifier from the **Swiss-Prot human reference proteome**.
04. Viral taxon clearly identified, viral protein **wild type** (as in 02). Strain recorded when clearly described.
05. Viral protein identified in UniProt, with a **standard generic name** (all "non-structural protein 1" variants → `NS1`).
06. A **mature protein** is an interactor with coordinates (§3), cleaved from a polyprotein (DENV1 NS5 = `B5AGU1[2494-3392]`) or from a protein cleaved into subunits (SARS-CoV-2 S1 = `P0DTC2[14-685]`, influenza HA2 = `Q8QPL1[347-568]`). It always takes precedence over a mapping (§3).
07. The method detects a **physical** interaction. Excluded: colocalization, functional interaction, citing an interaction shown elsewhere. Included: binary methods (co-crystal, Y2H) and complex-detection methods (co-IP…). A description is a bait, a prey and the method that detected their binding, recorded once per publication × method × human interactor × viral interactor. Any experiment in which the method detects the bait bound to the prey is evidence, even one designed to test something else: in an inhibition assay, the condition without the inhibitor detects the bait bound to the prey, and is evidence. What the experiment adds without being detected bound (an inhibitor, a competitor, a blocking peptide) is neither an interactor nor a mapping.
08. Method from the PSI-MI **interaction detection method** branch (MI:0001). When no term describes the assay, the closest term of the branch is used and the description note says what the assay was.
09. **Mappings**: the fragments of the bait or the prey the publication shows bound (§3).
10. **Tagged proteins** (GFP, FLAG, HA, GST fusions…) are curated as the wild-type protein: a tag is only ever on a mapping, as extra end residues (§3), never on an interactor.
11. **Fragments** (truncated constructs) are accepted: the interactor is the protein, the fragment a mapping (§3).
12. High-throughput publications: the accession is assigned from the rawest data available (e.g. ORF sequences), by alignment. **Scoring thresholds are the authors' own**: a measured affinity is an interaction, whatever its value; a screen is curated as far as its authors went, no further: with their thresholds, and only the subset they keep as their result when they narrow their list.
13. **No HLA proteins**: a description involving an HLA protein (any `HLA-` gene, vh or hh) is not curated.
14. **Swiss-Prot over TrEMBL** whenever both fit.
15. Existing notes are not a source of rules: they can be outdated or wrong. Only the criteria written here apply.

## 3. The values of a description

A description records, for each interactor, its UniProt entry and, for a mature protein, its coordinates; and, on each side, its mappings.

### The UniProt entry

Each interactor is an entry of the current UniProt release in Drakkar: for a human protein, an entry of the Swiss-Prot human reference proteome (03); for a viral protein, the entry of the publication's strain, or the closest entry of the same virus when UniProt does not have it. The interactor is the protein the experiment tested, never its construct: a tag (10) or a truncation (11) leaves it the same protein. When the publication names only a protein family or a complex (e.g. "Sec61", "14-3-3") where an experiment tested one protein, the interactor is the member the evidence points to (the construct, the primers, the antibody, the cited source).

### The coordinates of a mature protein

A human interactor is always its whole protein. A viral interactor is a whole protein, or a mature protein (06): the entry of the protein it is cleaved from, with the start and stop of the mature protein on it. Two mature proteins of one cleaved protein are two interactors.

### The mappings

A mapping is a fragment of the bait or the prey that the publication shows bound: the part of the interactor its construct carried, recorded as the exact sequence that was tested. It is always a strict subsequence of its interactor, never the whole of it. The interactor is identified first — the whole protein, or the mature protein the fragment belongs to — then the mapping within it. A mapping is only what is demonstrated: a region concluded from the results is not a mapping, nor is what the experiment adds without being detected bound (07). A mapping belongs to one side of one description, so to its method; a description holds every mapping its publication shows for it, or none. A mapping is at least 4 residues: a short one, a peptide of 20 residues or less, is a mapping like any other, and easy to miss.

The sequence is the one tested, from the publication's own sequence, never adapted to UniProt: the downstream work uses these sequences. The mapping is aligned on the interactor and its isoforms: the alignment verifies that it belongs to the protein, finds all its occurrences and gives their positions, and never changes the mapping. Its identity should reach 90 % on at least one isoform, which tolerates the differences between strains (UniProt holds few strains): a mapping of 10 to 19 residues can have one mismatch or gap, a shorter one must match exactly. Below 90 %, it is kept with its best alignment only when the description note says why. A mapping may differ from its interactor for one reason only: the UniProt sequence is not the one of the experiment (viral: the entry is the closest strain, not the publication's; human: the Swiss-Prot sequence changed since). Any other difference is an error, in the mapping, the interactor or the alignment.

The tested sequence can carry, at its N- or C-terminal end, residues that are not on its interactor: the protein's own residues just outside it (the initiator methionine before a mature protein, residues of the cleaved protein past its end) or residues of the construct (a tag, a linker). The mapping keeps them, named `nter` (at its start) and `cter` (at its end), and only the rest is aligned. A fragment across the cleavage site between two mature proteins belongs to neither, and Drakkar has no way to record it: the pair is not kept, and the publication note says so.

## 4. How each value is identified

Each value is identified by the first tier that gives it, in the three lists below, from the most direct to the most inferred. Each tier gives its label, the case it applies to, and how it identifies the value; a description note names the tier of a value by its label (`notes.md`). The lists of the entry and of the mappings apply to the human and the viral interactors alike.

- A tier whose case does not apply, or that gives no value, passes to the next: a UniProt accession the publication gives that is not in Drakkar passes to `reference`.
- A tier that would give a value the criteria forbid (a human entry outside the Swiss-Prot human reference proteome, a TrEMBL entry where Swiss-Prot fits) gives no value, and passes to the next.
- When two sources of the publication disagree, the value of the earlier tier is used; within one tier, the curator chooses by judgement. The description note records the disagreement.
- When a tier leaves several values equally supported, and nothing in the publication breaks the tie, the curator chooses by judgement, and the description note says the tie could not be broken (§1, right and not wrong).

### The UniProt entry

1. `accession`: when the publication gives a UniProt accession, its current entry.
2. `reference`: when the publication gives another identifier or a name — a GenBank, RefSeq or PDB accession, a clone, a plasmid, a commercial construct, a human gene name, a viral protein with its strain — the current entry it designates.
3. `sequence`: when the protein's sequence is known, from the publication or another database (e.g. the GenBank record of a strain UniProt does not have), the current entry closest to it by sequence, of the same virus for a viral protein (e.g. isolate HCV-N, not in UniProt: its GenBank sequence AF139594 is closest to P26662, strain H77). The whole sequence of the protein is aligned, never a part of it (a fragment, a peptide).
4. `virus`: when the strain of a viral protein is not given and its sequence is not known, the Swiss-Prot entry of the virus for that protein, otherwise the entry most used in Drakkar for that virus and generic name.
5. `best-effort`: in any other case, any way possible. When there is none (UniProt has the protein of no strain of that virus), the pair is not kept (03, 05): an entry of another virus, however close its sequence, is wrong.

### The coordinates of a mature protein (viral interactors only)

1. `publication`: the boundaries the publication gives, only when the entry has the sequence the publication used (same strain or clone; a shift in numbering is corrected).
2. `annotation`: when the entry has a chain or a region feature for the mature protein, that feature.
3. `drakkar`: when Drakkar already records a span for that entry and that generic name, that span.
4. `GenBank`: when the entry's GenBank or RefSeq record has a mature peptide feature for it, that feature.
5. `best-effort`: in any other case, any way possible, for instance the chain of another strain's entry, carried over by alignment.

### The mappings

1. `written`: when the publication writes the sequence (in its text, a figure, a table, a supplementary file), that sequence.
2. `coordinates`: when the publication gives coordinates on its own sequence (its strain, its clone), the subsequence at those coordinates, from UniProt or another database.
3. `other-numbering`: when the publication gives coordinates on another sequence it names (a reference strain, a numbering it states), the region they designate on that sequence, carried over to the publication's sequence when it is known, otherwise the subsequence of that other sequence.
4. `construct`: when the publication names a construct without coordinates (a deletion mutant, primers, a commercial or deposited construct, a construct of a cited publication), the subsequence of the publication's sequence within the boundaries that construct's own record gives (the primers, the supplier, the plasmid record, the cited publication).
5. `best-effort`: in any other case, any way possible that gives the sequence the construct carried.
