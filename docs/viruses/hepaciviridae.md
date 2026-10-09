# Hepaciviridae

Family conventions: the mature products of the genome polyprotein take the UniProt short names `Core`, `E1`, `E2`, `p7`, `NS2`, `NS3`, `NS4A`, `NS4B`, `NS5A`, `NS5B`; `p7` is written in lowercase, as UniProt writes it. Joined chains take the names of their parts, hyphenated, the second one short: `NS3-4A`, `NS5A-5B`, `E1-E2`.

## Hepatitis C virus (*Orthohepacivirus hominis*, NCBI 3052230)

| Generic name | Protein (UniProt name; gene) | Reference        |  Length | Also called                                                             |
| ------------ | ---------------------------- | ---------------- | ------: | ----------------------------------------------------------------------- |
| `Core`       | Core protein precursor       | P27958 2–191     |     190 | Capsid protein C, p23                                                   |
| `F`          | F protein                    | P0C045 1–162     |     162 | ARFP/F, alternate reading frame protein, frameshifted protein, p16, p17 |
| `E1`         | Envelope glycoprotein E1     | P27958 192–383   |     192 | gp32, gp35                                                              |
| `E1-E2`      | E1 + E2 (joined chains)      | P27958 192–746   |     555 | —                                                                       |
| `E2`         | Envelope glycoprotein E2     | P27958 384–746   | 363–367 | NS1, gp68, gp70                                                         |
| `p7`         | Viroporin p7                 | P27958 747–809   |      63 | —                                                                       |
| `NS2`        | Protease NS2                 | P27958 810–1026  |     217 | p23, non-structural protein 2                                           |
| `NS3`        | Serine protease/helicase NS3 | P27958 1027–1657 |     631 | Hepacivirin, NS3 protease, NS3 helicase, NS3P                           |
| `NS3-4A`     | NS3 + NS4A (joined chains)   | P27958 1027–1711 |     685 | —                                                                       |
| `NS4A`       | Non-structural protein 4A    | P27958 1658–1711 |      54 | p8                                                                      |
| `NS4B`       | Non-structural protein 4B    | P27958 1712–1972 |     261 | p27                                                                     |
| `NS5A`       | Non-structural protein 5A    | P27958 1973–2420 | 445–466 | p56/58                                                                  |
| `NS5A-5B`    | NS5A + NS5B (joined chains)  | Q99IB8 1977–3033 |   1,057 | —                                                                       |
| `NS5B`       | RNA-directed RNA polymerase  | P27958 2421–3011 |     591 | NS5B, p68                                                               |

Names: H77 (P27958, genotype 1a) is the reference; lengths are the range over the genotypes used in Drakkar. `Core` is the UniProt core precursor chain (191 residues), not the mature 177-residue core. `p7`, not `P7`: UniProt writes "Viroporin p7". `F` is the alternate reading frame product, a protein of its own, not a region of the polyprotein.

To check: 328 interactors named `NS2-3` carry the region of the NS2 chain alone (Q99IB8 814–1030, P26662 810–1026). The name or the region is wrong; settled from the abstracts.

## Hepatitis C virus (*Hepacivirus C*, NCBI 11103)

| Generic name | Protein (UniProt name; gene) | Reference        | Length | Also called                   |
| ------------ | ---------------------------- | ---------------- | -----: | ----------------------------- |
| `NS2`        | Protease NS2                 | P27958 810–1026  |    217 | p23, non-structural protein 2 |
| `NS4A`       | Non-structural protein 4A    | P27958 1658–1711 |     54 | p8                            |
| `NS5A`       | Non-structural protein 5A    | P27958 1973–2420 |    448 | p56/58                        |
| `NS5B`       | RNA-directed RNA polymerase  | P27958 2421–3011 |    591 | NS5B, p68                     |

Names: the 17 descriptions under this older NCBI species are hepatitis C virus and take the same names as *Orthohepacivirus hominis*; all four interactors are TrEMBL fragments pointing to obsolete snapshots.

## GB virus B (*Orthohepacivirus platyrrhini*, NCBI 3052236)

| Generic name | Protein (UniProt name; gene) | Reference        | Length | Also called |
| ------------ | ---------------------------- | ---------------- | -----: | ----------- |
| `NS5A`       | Non-structural protein 5A    | Q69422 1864–2274 |    411 | —           |

Names: the two interactors named `NS51` are the NS5A chain; `NS51` looks like a typing of `NS5A`.
