# Viral proteins reference

Last updated: 2026-10-09. The generic name of each viral protein, decided once and used everywhere: curation, fixes, reviews. Before writing a viral interactor, its generic name is taken from here. A protein that is not here yet gets its entry first, with the reason for its name.

This file holds the rules; the names are in one file per virus family, in `viruses/` (index in §4). Claude is the curator: the names are Claude's decisions, kept up to date at every UniProt release (§5). The reference covers every virus and protein used by a live vh description on 2026-10-09; how Drakkar compares with it is a separate review.

## 1. Identifying a protein

- A protein is identified by its **sequence**, never by the name it carries in Drakkar, and never by the most common name: the majority can be wrong.
- **UniProt says what the protein is**: the name of its Swiss-Prot entry, or of its chain when it is a mature protein. For a TrEMBL entry, whose names are often automatic, the Swiss-Prot entry of the same protein (closest by sequence, same virus, else same family) decides.
- Example: in measles, A4URT5 1–186 is named `V` in Drakkar. UniProt calls this entry "C protein", gene C, and it has the length of the C protein (186 residues; V has 299). It is C.

## 2. Choosing the generic name

1. The name the field uses for the protein, among the names UniProt gives it on the Swiss-Prot entry: short name, alternative short name, gene or ORF name, or the letter or number ending the full name (e.g. "Capsid protein C" → `C`).
1. **Spelling as UniProt writes it**, exactly \[decided 2026-10-09\]: UniProt names, not the names Drakkar used before, because they make maintenance mechanical (§5); the existing descriptions are renamed once, whatever the number of revisions: case, hyphens, primes. A protein with no Swiss-Prot entry takes the spelling of the closest Swiss-Prot protein of the same virus or family (e.g. `nsp1` for coronaviruses, `nsP1` for alphaviruses, `NS1` for flaviviruses).
1. **Tie-break:** when UniProt gives several names that the field uses equally, the one already used in Drakkar is kept, to avoid needless renames (influenza `NS2`, not `NEP`).
1. Large DNA viruses (herpesviruses, poxviruses): the gene or ORF name of the virus, as UniProt writes it (EBV `BPLF1`, HSV-1 `UL36`, vaccinia `A46`), except proteins widely known by a protein name (`gB`, `LANA1`, `EBNA-1`, `LMP1`, `CrmA`). Each family file states its convention.
1. **One protein, one name, in every strain of the virus.** Different species keep their own names when UniProt differs (vaccinia `A46`, ectromelia `EVM145`).
1. Each family file writes its choices in one line when UniProt offers several names, and lists under **Unresolved** what the evidence does not settle.
1. **The name follows the region.** When the region of a Drakkar interactor is another protein than its name says (e.g. a core protein curated on the precore entry), the region is the question, not the name: settled from the abstracts.

## 3. Regions (open)

Conventions to decide, one at a time. Until then, the family files name what Drakkar uses, marked `joined chains` or `whole polyprotein`:

1. A whole protein whose UniProt chain lacks the signal peptide (e.g. spike, gB, HA): keep the whole protein, or the chain?
1. Two adjacent chains joined (NS2B-3, NS4A-2K, NS3-4A, prM-E): kept as interactors in their own right?
1. A whole polyprotein used as one interactor (Gag, Gag-Pol, Env gp160): when is it right?
1. A region 1 to 10 residues away from a UniProt chain: moved to the chain?

## 4. Index

One section per NCBI species, most described first. Each row is a **target**: one protein of the virus, with one reference sequence, so the reference alone is enough to place any interactor (search its sequence against the targets of its virus) and to maintain Drakkar. Its reference is a UniProt entry and region: Swiss-Prot when there is one, else a current TrEMBL entry (with the Swiss-Prot protein it is named after), else an obsolete snapshot still in Drakkar (marked with its release). A target is added when curation meets a new protein; the reference does not list whole proteomes.

| Family                         | File                                                               | Species |
| ------------------------------ | ------------------------------------------------------------------ | ------: |
| Adenoviridae                   | [`viruses/adenoviridae.md`](viruses/adenoviridae.md)               |      11 |
| Alloherpesviridae              | [`viruses/alloherpesviridae.md`](viruses/alloherpesviridae.md)     |       1 |
| Ambiguiviridae                 | [`viruses/ambiguiviridae.md`](viruses/ambiguiviridae.md)           |       1 |
| Anelloviridae                  | [`viruses/anelloviridae.md`](viruses/anelloviridae.md)             |       3 |
| Arenaviridae                   | [`viruses/arenaviridae.md`](viruses/arenaviridae.md)               |      14 |
| Arteriviridae                  | [`viruses/arteriviridae.md`](viruses/arteriviridae.md)             |       4 |
| Ascoviridae                    | [`viruses/ascoviridae.md`](viruses/ascoviridae.md)                 |       1 |
| Asfarviridae                   | [`viruses/asfarviridae.md`](viruses/asfarviridae.md)               |       1 |
| Astroviridae                   | [`viruses/astroviridae.md`](viruses/astroviridae.md)               |       5 |
| Baculoviridae                  | [`viruses/baculoviridae.md`](viruses/baculoviridae.md)             |      12 |
| Birnaviridae                   | [`viruses/birnaviridae.md`](viruses/birnaviridae.md)               |       1 |
| Bornaviridae                   | [`viruses/bornaviridae.md`](viruses/bornaviridae.md)               |       2 |
| Caliciviridae                  | [`viruses/caliciviridae.md`](viruses/caliciviridae.md)             |       5 |
| Circoviridae                   | [`viruses/circoviridae.md`](viruses/circoviridae.md)               |       1 |
| Coronaviridae                  | [`viruses/coronaviridae.md`](viruses/coronaviridae.md)             |      20 |
| Filoviridae                    | [`viruses/filoviridae.md`](viruses/filoviridae.md)                 |       9 |
| Flaviviridae                   | [`viruses/flaviviridae.md`](viruses/flaviviridae.md)               |      12 |
| Fuselloviridae                 | [`viruses/fuselloviridae.md`](viruses/fuselloviridae.md)           |       2 |
| Hafunaviridae                  | [`viruses/hafunaviridae.md`](viruses/hafunaviridae.md)             |       1 |
| Hantaviridae                   | [`viruses/hantaviridae.md`](viruses/hantaviridae.md)               |       6 |
| Hepaciviridae                  | [`viruses/hepaciviridae.md`](viruses/hepaciviridae.md)             |       3 |
| Hepadnaviridae                 | [`viruses/hepadnaviridae.md`](viruses/hepadnaviridae.md)           |       5 |
| Hepeviridae                    | [`viruses/hepeviridae.md`](viruses/hepeviridae.md)                 |       3 |
| Iridoviridae                   | [`viruses/iridoviridae.md`](viruses/iridoviridae.md)               |       5 |
| Kolmioviridae                  | [`viruses/kolmioviridae.md`](viruses/kolmioviridae.md)             |       1 |
| Matonaviridae                  | [`viruses/matonaviridae.md`](viruses/matonaviridae.md)             |       1 |
| Nairoviridae                   | [`viruses/nairoviridae.md`](viruses/nairoviridae.md)               |       4 |
| Nimaviridae                    | [`viruses/nimaviridae.md`](viruses/nimaviridae.md)                 |       1 |
| Orthoherpesviridae             | [`viruses/orthoherpesviridae.md`](viruses/orthoherpesviridae.md)   |      30 |
| Orthomyxoviridae               | [`viruses/orthomyxoviridae.md`](viruses/orthomyxoviridae.md)       |       6 |
| Papillomaviridae               | [`viruses/papillomaviridae.md`](viruses/papillomaviridae.md)       |      32 |
| Paramyxoviridae                | [`viruses/paramyxoviridae.md`](viruses/paramyxoviridae.md)         |      26 |
| Parvoviridae                   | [`viruses/parvoviridae.md`](viruses/parvoviridae.md)               |      10 |
| Peribunyaviridae               | [`viruses/peribunyaviridae.md`](viruses/peribunyaviridae.md)       |       4 |
| Pestiviridae                   | [`viruses/pestiviridae.md`](viruses/pestiviridae.md)               |       4 |
| Phenuiviridae                  | [`viruses/phenuiviridae.md`](viruses/phenuiviridae.md)             |       7 |
| Phycodnaviridae                | [`viruses/phycodnaviridae.md`](viruses/phycodnaviridae.md)         |       3 |
| Picobirnaviridae               | [`viruses/picobirnaviridae.md`](viruses/picobirnaviridae.md)       |       1 |
| Picornaviridae                 | [`viruses/picornaviridae.md`](viruses/picornaviridae.md)           |      20 |
| Pneumoviridae                  | [`viruses/pneumoviridae.md`](viruses/pneumoviridae.md)             |       6 |
| Polydnaviriformidae            | [`viruses/polydnaviriformidae.md`](viruses/polydnaviriformidae.md) |       1 |
| Polyomaviridae                 | [`viruses/polyomaviridae.md`](viruses/polyomaviridae.md)           |      10 |
| Potyviridae                    | [`viruses/potyviridae.md`](viruses/potyviridae.md)                 |       1 |
| Poxviridae                     | [`viruses/poxviridae.md`](viruses/poxviridae.md)                   |      20 |
| Retroviridae                   | [`viruses/retroviridae.md`](viruses/retroviridae.md)               |      31 |
| Rhabdoviridae                  | [`viruses/rhabdoviridae.md`](viruses/rhabdoviridae.md)             |      15 |
| Sedoreoviridae                 | [`viruses/sedoreoviridae.md`](viruses/sedoreoviridae.md)           |       7 |
| Spinareoviridae                | [`viruses/spinareoviridae.md`](viruses/spinareoviridae.md)         |       4 |
| Tobaniviridae                  | [`viruses/tobaniviridae.md`](viruses/tobaniviridae.md)             |       1 |
| Togaviridae                    | [`viruses/togaviridae.md`](viruses/togaviridae.md)                 |      12 |
| Tombusviridae                  | [`viruses/tombusviridae.md`](viruses/tombusviridae.md)             |       1 |
| Virgaviridae                   | [`viruses/virgaviridae.md`](viruses/virgaviridae.md)               |       3 |
| Zimmerviridae                  | [`viruses/zimmerviridae.md`](viruses/zimmerviridae.md)             |       1 |
| Viruses with no family in NCBI | [`viruses/unclassified.md`](viruses/unclassified.md)               |       4 |
| **Total**                      |                                                                    | **395** |

## 5. Maintenance

The reference follows UniProt. Its targets point to UniProt entries, which change at every release, so it is maintained at each upgrade, as a step of the upgrade job: after the taxonomy and UniProt are loaded, before the versioning pass (`database.md` §3), which uses it to move viral interactors and settle their names.

The upgrade keeps a viral snapshot when its sequences and taxon are unchanged, whatever happened to its names and chains. So the reference is compared with the new release itself (the loaded current snapshots and their chain features, and the release XML for the short names), not only with the snapshots that changed.

For each target, in this order:

1. **Reference entry gone** (deleted, merged, demerged): a new reference is chosen by sequence among the current entries of the same species, Swiss-Prot first, then the closest sequence, as for a new target. The name stays unless the new entry says otherwise (step 3).
1. **Reference region changed**: the sequence of the region, or the chain it is, changed in the new entry. The target follows its chain (new coordinates); if the chain is gone, the region is found again by sequence (one best match), else the target goes to Unresolved with the reason.
1. **Name changed in UniProt**: a new short or alternative name, a new gene name, or a TrEMBL target that now has a Swiss-Prot entry (it becomes the reference). The target is renamed when the rules of §2 give another name; the old name goes to *Also called*. A rename of a target is a rename of every Drakkar interactor on it: one revision per description, the name only.
1. **Better reference available**: a TrEMBL or obsolete reference that now has a Swiss-Prot or current entry of the same protein is replaced (steps 2 and 3 apply to the new one).

Then:

- Targets on obsolete snapshots (marked with their release) are tried again at each release: a current entry with the same protein replaces them.
- Every change is written in the family file, and the date at the top of this file is updated. The changes of a release (targets moved, renamed, set aside) are recorded in the history of its versioning pass.
- Steps 1, 2 and 4 are mechanical: a script parses the target tables of `viruses/` and lists, per target, what changed in the new release. Step 3 is a curation decision, recorded in the family file (`Names:` line).
- New targets come from curation, not from upgrades: a target is added when a new description needs a protein the reference does not have (§4).
