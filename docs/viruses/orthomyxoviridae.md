# Orthomyxoviridae

Family conventions: influenza proteins by their UniProt short or gene names in capitals (`PB2`, `PB1`, `PA`, `HA`, `NP`, `NA`, `M1`, `M2`, `NS1`, `NS2`); accessory proteins as UniProt writes them (`PB1-F2`, `PA-X`). Thogotoviruses follow their own UniProt entries.

## Influenza A virus (*Alphainfluenzavirus influenzae*, NCBI 2955291)

| Generic name | Protein (UniProt name; gene)                       | Reference    |  Length | Also called                            |
| ------------ | -------------------------------------------------- | ------------ | ------: | -------------------------------------- |
| `PB2`        | Polymerase basic protein 2; PB2                    | P03428 1–759 |     759 | RNA-directed RNA polymerase subunit P3 |
| `PB1`        | RNA-directed RNA polymerase catalytic subunit; PB1 | P03431 1–757 |     757 | Polymerase basic protein 1, subunit P1 |
| `PB1-F2`     | Protein PB1-F2; PB1                                | P0C0U1 1–87  |   79–90 | —                                      |
| `PA`         | Polymerase acidic protein; PA                      | P03433 1–716 |     716 | RNA-directed RNA polymerase subunit P2 |
| `PA-X`       | Protein PA-X; PA                                   | P0CK64 1–252 |     252 | —                                      |
| `HA`         | Hemagglutinin; HA (whole precursor)                | P03452 1–565 | 560–568 | chains HA1 (18–342), HA2 (344–565)     |
| `NP`         | Nucleoprotein; NP                                  | P03466 1–498 |     498 | Protein N, nucleocapsid protein        |
| `NA`         | Neuraminidase; NA                                  | P03468 1–454 | 449–469 | —                                      |
| `M1`         | Matrix protein 1; M                                | P03485 1–252 |     252 | —                                      |
| `M2`         | Matrix protein 2; M                                | P06821 1–97  |      97 | Proton channel protein M2              |
| `NS1`        | Non-structural protein 1; NS                       | P03496 1–230 | 215–237 | NS1A                                   |
| `NS2`        | Nuclear export protein; NS                         | P03508 1–121 |     121 | NEP, non-structural protein 2          |

Names:

- `NS2`, not `NEP`: both are UniProt names and both are used in the field; `NS2` is the one already used in Drakkar (§2, tie-break).
- `PB1`: UniProt's full name is "RNA-directed RNA polymerase catalytic subunit"; `PB1` is its gene and alternative name.

Unresolved:

- Q67020 1–93 (obsolete TrEMBL snapshot, "Protein PA-X", named `PA-X`): its first ~53 residues are the PA/PA-X N-terminus, the remaining 40 match neither PA nor PA-X.

## Influenza B virus (*Betainfluenzavirus influenzae*, NCBI 2955465)

| Generic name | Protein (UniProt name; gene)                       | Reference    | Length | Also called                |
| ------------ | -------------------------------------------------- | ------------ | -----: | -------------------------- |
| `PB2`        | Polymerase basic protein 2; PB2                    | O36431 1–770 |    770 | —                          |
| `PB1`        | RNA-directed RNA polymerase catalytic subunit; PB1 | P13871 1–752 |    752 | Polymerase basic protein 1 |
| `PA`         | Polymerase acidic protein; PA                      | O36432 1–726 |    726 | —                          |
| `HA`         | Hemagglutinin; HA (whole precursor)                | P22092 1–585 |    585 | chains HA1, HA2            |
| `NP`         | Nucleoprotein; NP                                  | O36433 1–560 |    560 | —                          |
| `M1`         | Matrix protein 1; M                                | P03489 1–248 |    248 | —                          |
| `BM2`        | Matrix protein 2; M                                | P03493 1–109 |    109 | M2                         |
| `NS1`        | Non-structural protein 1; NS                       | P03502 1–281 |    281 | —                          |

Names: `BM2` (UniProt alternative name), the name the field uses for the influenza B M2 protein, distinct from influenza A `M2`.

## Influenza C virus (*Gammainfluenzavirus influenzae*, NCBI 2955935)

| Generic name | Protein (UniProt name; gene)                       | Reference    | Length | Also called                                      |
| ------------ | -------------------------------------------------- | ------------ | -----: | ------------------------------------------------ |
| `PB2`        | Polymerase basic protein 2; PB2                    | Q9IMP3 1–774 |    774 | —                                                |
| `PB1`        | RNA-directed RNA polymerase catalytic subunit; PB1 | Q9IMP4 1–754 |    754 | —                                                |
| `PA`         | Polymerase acidic protein; PA                      | Q9IMP5 1–709 |    709 | P3                                               |
| `NP`         | Nucleoprotein; NP                                  | Q6I7C0 1–565 |    565 | —                                                |
| `p42`        | Polyprotein p42; M (whole polyprotein)             | Q6I7B9 1–374 |    374 | M polyprotein; chains M1' (1–259), CM2 (260–374) |
| `NS1`        | Non-structural protein 1; NS                       | Q01639 1–246 |    246 | —                                                |

Names: `p42`, the number ending the UniProt name, for the uncleaved M polyprotein (named `M` in Drakkar, which is the gene).

## Thogoto virus (*Thogotovirus thogotoense*, NCBI 11569)

| Generic name | Protein (UniProt name; gene)     | Reference    | Length | Also called             |
| ------------ | -------------------------------- | ------------ | -----: | ----------------------- |
| `GP`         | Envelope glycoprotein; segment 4 | P28977 1–512 |    512 | Surface glycoprotein 75 |
| `N`          | Nucleoprotein; segment 5         | P89216 1–454 |    454 | Nucleocapsid protein    |
| `ML`         | Protein ML; segment 6            | Q80A33 1–304 |    304 | —                       |

Names: `N` from "Protein N" (UniProt gives no `NP` here). `GP`: UniProt gives no short name; the field's name for it (named `E` in Drakkar).

## Influenza D virus (*Deltainfluenzavirus influenzae*, NCBI 2955744)

| Generic name | Protein (UniProt name; gene)                 | Reference                 | Length | Also called |
| ------------ | -------------------------------------------- | ------------------------- | -----: | ----------- |
| `NP`         | Nucleoprotein (no Swiss-Prot entry)          | A0A0E3VZU8 1–552 (TrEMBL) |    552 | —           |
| `NS2`        | Nuclear export protein (no Swiss-Prot entry) | A0A088CK81 1–184 (TrEMBL) |    184 | NEP         |

Names: no Swiss-Prot entry; named after the influenza C proteins (Q9IMP6 NP, Q9ENX7 NS2), the closest by sequence (39 % and 30 % identity).

## Dhori virus (*Thogotovirus dhoriense*, NCBI 11318)

| Generic name | Protein (UniProt name; gene)                      | Reference    | Length | Also called                            |
| ------------ | ------------------------------------------------- | ------------ | -----: | -------------------------------------- |
| `P2`         | RNA-directed RNA polymerase catalytic subunit; P2 | P27153 1–716 |    716 | RNA-directed RNA polymerase subunit P2 |
| `P4`         | Envelope glycoprotein; P4                         | P27427 1–521 |    521 | —                                      |

Names: the gene names, as UniProt gives them for Dhori virus.
