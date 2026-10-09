# Adenoviridae

Family conventions: early proteins take their transcription-unit name as the field writes it (`E1A`, `E1B-19K`, `E1B-55K`, `DBP`, `pTP`, `Pol`, the E3 proteins by their size or their conserved region, the E4 proteins by their ORF). Structural proteins take their protein name (`Hexon`, `Penton`, `Fiber`, `IIIa`, `V`, `VI`, `VII`, `IX`, `IVa2`), with the prefix `p` for the uncleaved precursor (`pVI`, `pVII`). Late non-structural proteins take their unit and size (`L1-52/55K`, `L4-22K`, `L4-100K`).

## Human adenovirus C (*Mastadenovirus caesari*, NCBI 3241411)

Serotypes used in Drakkar: 2, 5, 6.

| Generic name   | Protein (UniProt name; gene)                                   | Reference     |  Length | Also called                                           |
| -------------- | -------------------------------------------------------------- | ------------- | ------: | ----------------------------------------------------- |
| `E1A`          | Early E1A protein                                              | P03255 1–289  |     289 | Early E1A 32 kDa protein, 13S/12S E1A                 |
| `E1B-19K`      | E1B protein, small T-antigen; E1B                              | P03246 1–176  | 175–176 | E1B 19 kDa protein                                    |
| `E1B-55K`      | E1B 55 kDa protein; E1B                                        | P03243 1–496  | 495–496 | E1b55K, E1B protein large T-antigen, E1B-495R         |
| `Pol`          | DNA polymerase; POL                                            | P03261 1–1198 |    1198 | E2B polymerase                                        |
| `pTP`          | Preterminal protein; PTP                                       | P04499 1–671  |     671 | Bellett protein, precursor terminal protein           |
| `DBP`          | DNA-binding protein; DBP                                       | P03265 1–529  |     529 | Early 2A protein, E2A DNA-binding protein             |
| `IIIa`         | Pre-hexon-linking protein IIIa; L1                             | P12537 1–585  |     585 | pIIIa, protein IIIa, capsid vertex-specific component |
| `Penton`       | Penton protein; L2                                             | P12538 1–571  |     571 | CP-P, penton base protein, protein III                |
| `pVII`         | Pre-histone-like nucleoprotein; L2 (whole polyprotein)         | P68951 1–198  |     198 | pVII, pre-core protein VII                            |
| `VII`          | Histone-like nucleoprotein; L2                                 | P68951 25–198 |     174 | NP, core protein VII                                  |
| `V`            | Core-capsid bridging protein; L2                               | P24938 1–368  | 368–369 | core protein V                                        |
| `Hexon`        | Hexon protein; L3                                              | P04133 1–952  | 952–968 | CP-H, protein II                                      |
| `pVI`          | Pre-protein VI; L3                                             | P24937 1–250  |     250 | pVI                                                   |
| `L4-100K`      | Shutoff protein; L4                                            | P24933 1–807  | 805–807 | p100K, 100K-chaperone, shutoff protein 100K           |
| `Fiber`        | Fiber protein; L5                                              | P11818 1–581  | 581–582 | SPIKE, protein IV                                     |
| `IX`           | Hexon-interlacing protein IX; IX                               | P03281 1–140  |     140 | protein IX                                            |
| `E3-12.5K`     | Early E3A 12.5 kDa protein                                     | P27311 1–107  |     107 | E3-12,5K (UniProt spelling)                           |
| `E3-19K`       | Early E3 18.5 kDa glycoprotein                                 | P04494 1–160  | 159–160 | E19, gp19K, E3gp 19 kDa                               |
| `ADP`          | Adenovirus death protein                                       | P24935 1–101  |     101 | E3-11.6K, early-3 11.6 kDa glycoprotein               |
| `E3-RID-alpha` | Early 3 receptor internalization and degradation alpha protein | P15133 23–91  |      69 | RID-alpha, E3-10.4K                                   |
| `E3-14.7K`     | Early 3 14.7 kDa protein                                       | P68976 1–128  |     128 | E3-14.5K (name of the serotype 5 entry)               |
| `E4-ORF1`      | Early 4 ORF1 protein                                           | P03242 1–128  |     128 | E4 ORF1 control protein                               |
| `E4-ORF2`      | Early 4 ORF2 protein                                           | P0DJX0 1–130  | 130–148 | —                                                     |
| `E4-ORF3`      | Probable early E4 11 kDa protein                               | P04489 1–116  |     116 | E4-11K                                                |
| `E4-ORF4`      | Early 4 ORF4 protein                                           | P03240 1–114  |     114 | early E4 13 kDa protein                               |
| `E4-ORF6`      | Early 4 ORF6 protein                                           | P03239 1–294  |     294 | E4-34k                                                |
| `E4-ORF6/7`    | Early 4 ORF6/7 control protein                                 | P03238 1–150  |     150 | early E4 17 kDa protein                               |

Names:

- The E4 proteins are named by their ORF, as UniProt writes it (`E4-ORF1`, `E4-ORF2`, `E4-ORF4`, `E4-ORF6`, `E4-ORF6/7`); P04489 has no ORF name on UniProt but is the 11 kDa E4 protein, named `E4-ORF3` for consistency. In Drakkar five different E4 proteins are all called `E4-17K` today.
- `E1B-19K` and `E1B-55K` are two proteins of the same unit: in Drakkar both are called `E1B-55K`.
- `Hexon`, `Penton` and `Fiber`, the names of the UniProt entries and of the field, rather than the UniProt short names CP-H, CP-P and SPIKE.
- `Pol` from the gene name POL, written as the field does.
- The E1A products of 55 and 243 residues (E1U5L5, E1U5L4) are `E1A`; their region says which product.

## Human adenovirus D (*Mastadenovirus dominans*, NCBI 3241420)

Serotypes used in Drakkar: 9, 17, 19, 23, 24, 28, 30, 36, 37, 39, 43, 47, 49, 51, 53, 56, 58.

| Generic name  | Protein (UniProt name; gene)                 | Reference             |  Length | Also called                                 |
| ------------- | -------------------------------------------- | --------------------- | ------: | ------------------------------------------- |
| `E1A`         | Early E1A protein; E1A (no Swiss-Prot entry) | Q9YLA2 1–251 (TrEMBL) | 133–251 | E1A-14.9K                                   |
| `E3-CR1-beta` | CR1-beta; E3 (no Swiss-Prot entry)           | M0QTU7 1–417 (TrEMBL) | 385–445 | E3-49K, E3 44.5K, E3 45.8 kDa protein       |
| `E4-ORF1`     | E4-ORF1; E4                                  | P89079 1–125          |     125 | early E4 14.0 kDa protein, probable dUTPase |
| `Hexon`       | Hexon protein; L3                            | P36853 1–943          | 941–943 | CP-H, protein II                            |
| `Fiber`       | Fiber protein; L5                            | P68983 1–362          | 362–385 | SPIKE, protein IV                           |

Names: `E3-CR1-beta` for the E3 conserved-region-1 beta proteins, the TrEMBL name of most entries; they differ a lot between serotypes (several sequence groups) but are the same protein. The 133-residue E1A (Q9YLA1, "E1A 13S protein") is an E1A product.

## Human adenovirus A (*Mastadenovirus adami*, NCBI 3241402)

Serotypes used in Drakkar: 12, 18, 31.

| Generic name   | Protein (UniProt name; gene)                | Reference             |  Length | Also called                 |
| -------------- | ------------------------------------------- | --------------------- | ------: | --------------------------- |
| `E1A`          | Early E1A protein                           | P03259 1–266          |     266 | early E1A 29.5 kDa protein  |
| `E1B-19K`      | E1B protein, small T-antigen                | P04492 1–163          |     163 | E1B 19 kDa protein          |
| `E1B-55K`      | E1B 55 kDa protein                          | P04491 1–482          |     482 | E1B protein large T-antigen |
| `E3-CR1-alpha` | CR1-alpha protein; E3 (no Swiss-Prot entry) | D3JIT8 1–265 (TrEMBL) |     265 | —                           |
| `E3-CR1-beta`  | CR1-beta protein; E3 (no Swiss-Prot entry)  | D3JIT9 1–269 (TrEMBL) |     269 | —                           |
| `E4-ORF6`      | Early E4 34 kDa protein                     | P36710 1–291          |     291 | E4-34K                      |
| `Hexon`        | Hexon protein; L3                           | P19900 1–919          | 919–922 | CP-H, protein II            |
| `Fiber`        | Fiber protein; L5                           | P36711 1–587          |     587 | SPIKE, protein IV           |

Names: the "Early E4 34 kDa protein" of serotype 12 is the E4-ORF6 protein (the serotype 2 E4-ORF6 is also called E4-34k on UniProt).

## Human adenovirus B (*Mastadenovirus blackbeardi*, NCBI 3241406)

Serotypes used in Drakkar: 3, 7, 11, 14, 16, 21, 35, 55.

| Generic name | Protein (UniProt name; gene)                                                   | Reference             |  Length | Also called                            |
| ------------ | ------------------------------------------------------------------------------ | --------------------- | ------: | -------------------------------------- |
| `E1A`        | Early E1A protein; E1A                                                         | P03256 1–261          |     261 | early E1A 28 kDa protein               |
| `Penton`     | Penton protein; L2 (no Swiss-Prot entry; closest P36716, serotype 12, 73 % id) | Q65290 1–544 (TrEMBL) |     544 | CP-P, penton base protein, protein III |
| `Hexon`      | Hexon protein; L3                                                              | P36851 1–937          | 937–952 | CP-H, protein II                       |
| `Fiber`      | Fiber protein; L5                                                              | P04501 1–319          | 319–353 | SPIKE, protein IV                      |
| `E3-20.3K`   | Early E3 20.3 kDa glycoprotein                                                 | P35767 1–181          | 174–181 | E3-20.1K (serotype 3 entry)            |
| `E3-20.5K`   | Early E3 20.5 kDa glycoprotein                                                 | P11322 1–189          |     189 | —                                      |

## Human adenovirus F (*Mastadenovirus faecale*, NCBI 3241426)

Serotypes used in Drakkar: 40, 41.

| Generic name  | Protein (UniProt name; gene)              | Reference             |  Length | Also called                 |
| ------------- | ----------------------------------------- | --------------------- | ------: | --------------------------- |
| `E1A`         | Early E1A protein                         | P10541 1–249          |     249 | early E1A 27 kDa protein    |
| `E1B-55K`     | E1B 55 kDa protein                        | P10546 1–472          |     472 | E1B protein large T-antigen |
| `Penton`      | Penton protein; L2 (no Swiss-Prot entry)  | Q9QAH8 1–508 (TrEMBL) | 504–508 | CP-P, protein III           |
| `Hexon`       | Hexon protein; L3                         | P11820 2–925          | 911–924 | CP-H, protein II            |
| `Fiber-1`     | Fiber protein 1                           | P14267 1–562          |     562 | long fiber                  |
| `E3-19.4K`    | E3 19.4 kDa protein (no Swiss-Prot entry) | Q98828 1–173 (TrEMBL) |     173 | —                           |
| `E3-CR1-beta` | E3 CR1-beta1 (no Swiss-Prot entry)        | Q64861 1–276 (TrEMBL) |     276 | —                           |
| `E4-ORF4`     | E4 ORF4 (no Swiss-Prot entry)             | Q64866 1–121 (TrEMBL) |     121 | —                           |
| `E4-ORF6`     | Early E4 34 kDa protein                   | Q64865 1–289          |     289 | E4-34K                      |

Names: this serotype has two fibers; UniProt names them "Fiber protein 1" and "Fiber protein 2", hence `Fiber-1`.

## Bovine adenovirus 3 (*Mastadenovirus bostertium*, NCBI 3241409)

| Generic name | Protein (UniProt name; gene) | Reference        |  Length | Also called                                                 |
| ------------ | ---------------------------- | ---------------- | ------: | ----------------------------------------------------------- |
| `IVa2`       | Packaging protein 1; IVa2    | A0A9W3HR36 1–448 |     448 | packaging protein IVa2                                      |
| `L1-52/55K`  | Packaging protein 3; L1      | A0A9W3N2X3 1–370 | 331–370 | 52K, packaging protein 52K                                  |
| `L4-22K`     | Packaging protein 2; L4      | A0A9W3HR61 1–274 |     274 | 33K (the name used in Drakkar and in the bovine literature) |

Names: the 274-residue protein is called `33K` in Drakkar; UniProt calls it "Packaging protein 2", L4-22K. L4-22K and L4-33K are two products of the same ORF, so the four interactors are marked `check`.

## Fowl adenovirus 1 (*Aviadenovirus ventriculi*, NCBI 3426541)

| Generic name | Protein (UniProt name; gene) | Reference    | Length | Also called               |
| ------------ | ---------------------------- | ------------ | -----: | ------------------------- |
| `Gam1`       | Protein GAM-1; 8             | Q64770 1–282 |    282 | Gallus-anti morte protein |

## Human adenovirus E (*Mastadenovirus exoticum*, NCBI 3241425)

| Generic name | Protein (UniProt name; gene) | Reference    | Length | Also called              |
| ------------ | ---------------------------- | ------------ | -----: | ------------------------ |
| `E1A`        | Early E1A protein            | P10407 1–257 |    257 | early E1A 28 kDa protein |
| `Fiber`      | Fiber protein; L5            | P36844 1–426 |    426 | SPIKE, protein IV        |

## Murine adenovirus 1 (*Mastadenovirus encephalomyelitidis*, NCBI 3241422)

| Generic name | Protein (UniProt name; gene)     | Reference    | Length | Also called     |
| ------------ | -------------------------------- | ------------ | -----: | --------------- |
| `E4-33K`     | Probable early E4 33 kDa protein | P23125 1–289 |    289 | ORF A/B protein |

## Frog adenovirus 1 (*Siadenovirus ranae*, NCBI 3241308)

| Generic name | Protein (UniProt name; gene) | Reference    | Length | Also called                         |
| ------------ | ---------------------------- | ------------ | -----: | ----------------------------------- |
| `Protease`   | Protease; L3                 | Q9IIH4 1–204 |    204 | AVP, adenain, adenovirus proteinase |

## Human adenovirus 52 (*Mastadenovirus russelli*, NCBI 3241445)

| Generic name  | Protein (UniProt name; gene)           | Reference             | Length | Also called |
| ------------- | -------------------------------------- | --------------------- | -----: | ----------- |
| `E3-CR1-beta` | E3 CR1-beta1; E3 (no Swiss-Prot entry) | A0MK65 1–270 (TrEMBL) |    270 | —           |
