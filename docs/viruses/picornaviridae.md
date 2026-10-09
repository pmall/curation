# Picornaviridae

Family conventions: every protein is a chain of the genome polyprotein. The generic name is the letter/number ending the UniProt chain name (`VP1`, `2A`, `3D`), not UniProt's short names `P2A`, `P2C`, `P3A`, `RdRp`. Joined chains keep both names (`2BC`, `3AB`, `3CD`), capsid precursors keep the UniProt chain name (`VP0`, `P1`). The leader is `L` where UniProt names it "Leader protein" and `Lpro` where UniProt names it "Leader protease".

## Enterovirus A (*Enterovirus alphacoxsackie*, NCBI 3428500)

| Generic name | Protein (UniProt name; gene)               | Reference        | Length | Also called             |
| ------------ | ------------------------------------------ | ---------------- | -----: | ----------------------- |
| `VP0`        | Capsid protein VP0 (joined chains VP4-VP2) | Q66478 2–323     |    322 | VP4-VP2                 |
| `VP2`        | Capsid protein VP2                         | Q66478 70–323    |    254 | P1B, Virion protein 2   |
| `VP3`        | Capsid protein VP3                         | Q66478 324–565   |    242 | P1C, Virion protein 3   |
| `VP1`        | Capsid protein VP1                         | Q66478 566–862   |    297 | P1D, Virion protein 1   |
| `2A`         | Protease 2A                                | Q66478 863–1012  |    150 | P2A, Picornain 2A       |
| `2B`         | Protein 2B                                 | Q66478 1013–1111 |     99 | P2B                     |
| `2C`         | Protein 2C                                 | Q66478 1112–1440 |    329 | P2C                     |
| `2BC`        | Protein 2B + 2C (joined chains)            | Q66478 1013–1440 |    428 | —                       |
| `3A`         | Protein 3A                                 | Q66478 1441–1526 |     86 | P3A                     |
| `3AB`        | Protein 3AB (joined chains 3A + 3B)        | Q66478 1441–1548 |    108 | —                       |
| `3C`         | Protease 3C                                | Q66478 1549–1731 |    183 | P3C, Picornain 3C       |
| `3D`         | RNA-directed RNA polymerase                | Q66478 1732–2193 |    462 | 3Dpol, RdRp, Protein 3D |

Names: EV-A71 (Q66478, strain BrCr) is the reference; coxsackievirus A16, A6 and A10 interactors of the same species carry the same names with their own coordinates.

Unresolved: none. L7QIJ0 1–191 (coxsackievirus A10, "VP1 (Fragment)") is named `VP1` but is only 65 % identical over a 191-residue fragment: marked `check`.

## Coxsackievirus B (*Enterovirus betacoxsackie*, NCBI 3428502)

| Generic name | Protein (UniProt name; gene) | Reference        | Length | Also called             |
| ------------ | ---------------------------- | ---------------- | -----: | ----------------------- |
| `VP4`        | Capsid protein VP4           | P03313 2–69      |     68 | P1A, Virion protein 4   |
| `VP3`        | Capsid protein VP3           | P03313 333–570   |    238 | P1C, Virion protein 3   |
| `VP1`        | Capsid protein VP1           | P03313 571–851   |    281 | P1D, Virion protein 1   |
| `2A`         | Protease 2A                  | P03313 852–1001  |    150 | P2A, Picornain 2A       |
| `2B`         | Protein 2B                   | P03313 1002–1100 |     99 | P2B                     |
| `2C`         | Protein 2C                   | P03313 1101–1429 |    329 | P2C                     |
| `3A`         | Protein 3A                   | P03313 1430–1518 |     89 | P3A                     |
| `3B`         | Viral protein genome-linked  | P03313 1519–1540 |     22 | VPg, P3B, Protein 3B    |
| `3C`         | Protease 3C                  | P03313 1541–1723 |    183 | P3C, Picornain 3C       |
| `3D`         | RNA-directed RNA polymerase  | P03313 1724–2185 |    462 | 3Dpol, RdRp, Protein 3D |

Names: `3B` rather than `VPg`, to stay with the family numbering (UniProt gives both).

## Rhinovirus C (*Enterovirus cerhino*, NCBI 3428504)

| Generic name | Protein (UniProt name; gene)                         | Reference      | Length | Also called        |
| ------------ | ---------------------------------------------------- | -------------- | -----: | ------------------ |
| `P1`         | P1 (capsid precursor, joined chains VP4-VP2-VP3-VP1) | E5D8F2 2–846   |    845 | Capsid polyprotein |
| `2A`         | Protease 2A                                          | E5D8F2 847–988 |    142 | P2A, Picornain 2A  |

Names: `P1` is the UniProt chain name of the capsid precursor; Drakkar calls it `C15a` (the strain name C15), which is not a protein name.

## Encephalomyocarditis virus (*Cardiovirus rueckerti*, NCBI 3427730)

| Generic name | Protein (UniProt name; gene) | Reference        | Length | Also called            |
| ------------ | ---------------------------- | ---------------- | -----: | ---------------------- |
| `L`          | Leader protein               | P03304 1–67      |     67 | —                      |
| `2A`         | Protein 2A                   | P03304 900–1042  |    143 | P2A, G                 |
| `2C`         | Protein 2C                   | P03304 1193–1517 |    325 | P2C, C                 |
| `3A`         | Protein 3A                   | P03304 1518–1605 |     88 | P3A                    |
| `3C`         | Protease 3C                  | P03304 1626–1830 |    205 | P3C, Picornain 3C, p22 |
| `3D`         | RNA-directed RNA polymerase  | P03304 1831–2290 |    460 | 3Dpol, RdRp, E         |

Names: EMCV (P03304) is the reference; Mengo virus (P12296) interactors are the same proteins, three residues further along the polyprotein.

## Enterovirus D68 (*Enterovirus deconjuncti*, NCBI 3428506)

| Generic name | Protein (UniProt name; gene) | Reference        | Length | Also called           |
| ------------ | ---------------------------- | ---------------- | -----: | --------------------- |
| `VP3`        | Capsid protein VP3           | Q68T42 318–552   |    235 | P1C, Virion protein 3 |
| `2A`         | Protease 2A                  | Q68T42 862–1008  |    147 | P2A, Picornain 2A     |
| `2B`         | Protein 2B                   | Q68T42 1009–1107 |     99 | P2B                   |
| `2C`         | Protein 2C                   | Q68T42 1108–1437 |    330 | P2C                   |
| `3A`         | Protein 3A                   | Q68T42 1438–1526 |     89 | P3A                   |
| `3C`         | Protease 3C                  | Q68T42 1549–1731 |    183 | P3C, Picornain 3C     |
| `3D`         | RNA-directed RNA polymerase  | Q68T42 1732–2188 |    457 | 3Dpol, RdRp           |

## Rhinovirus A (*Enterovirus alpharhino*, NCBI 3428501)

| Generic name | Protein (UniProt name; gene) | Reference        | Length | Also called           |
| ------------ | ---------------------------- | ---------------- | -----: | --------------------- |
| `VP1`        | Capsid protein VP1           | P04936 562–850   |    289 | P1D, Virion protein 1 |
| `2A`         | Protease 2A                  | P04936 851–992   |    142 | P2A, Picornain 2A     |
| `3A`         | Protein 3A                   | Q82122 1413–1489 |     77 | P3A                   |
| `3C`         | Protease 3C                  | Q82122 1511–1693 |    183 | P3C, Picornain 3C     |

Names: two reference entries, rhinovirus A2 (P04936) and A16 (Q82122), each the one used by the interactors of that row.

## Poliovirus (*Enterovirus coxsackiepol*, NCBI 3428505)

| Generic name  | Protein (UniProt name; gene)           | Reference        |      Length | Also called       |
| ------------- | -------------------------------------- | ---------------- | ----------: | ----------------- |
| `Polyprotein` | Genome polyprotein (whole polyprotein) | P03300 1–2209    | 2,209–2,214 | —                 |
| `2A`          | Protease 2A                            | P03300 882–1030  |         149 | P2A, Picornain 2A |
| `2C`          | Protein 2C                             | P03300 1128–1456 |         329 | P2C               |
| `3A`          | Protein 3A                             | P03300 1457–1543 |          87 | P3A               |
| `3C`          | Protease 3C                            | P03300 1566–1748 |         183 | P3C, Picornain 3C |
| `3D`          | RNA-directed RNA polymerase            | P03300 1749–2209 |         461 | 3Dpol, RdRp       |

Names: `Polyprotein` is the whole uncleaved product (two descriptions, poliovirus 1 and coxsackievirus A24); whether a whole polyprotein is an acceptable region is the open question of `viruses.md` §3.

## Foot-and-mouth disease virus (*Aphthovirus vesiculae*, NCBI 3426401)

| Generic name | Protein (UniProt name; gene)               | Reference        |  Length | Also called                      |
| ------------ | ------------------------------------------ | ---------------- | ------: | -------------------------------- |
| `Lpro`       | Leader protease                            | P03305 1–201     |     201 | L, Lab, Lb                       |
| `VP3`        | Capsid protein VP3                         | P03305 505–724   | 220–221 | P1C, 1C, Virion protein 3        |
| `VP1`        | Capsid protein VP1                         | P03305 725–935   | 210–214 | P1D, 1D, Virion protein 1        |
| `2C`         | Protein 2C                                 | P03305 1108–1425 |     318 | P2C                              |
| `3A`         | Protein 3A                                 | P03305 1426–1578 |     153 | P3A                              |
| `3B`         | Protein 3B-1 + 3B-2 + 3B-3 (joined chains) | P03305 1579–1649 |      71 | VPg1-VPg3, 3B1-3B3               |
| `3C`         | Protease 3C                                | P03305 1650–1862 |     213 | P3C, Picornain 3C, Protease P20B |
| `3D`         | RNA-directed RNA polymerase 3D-POL         | P03305 1863–2332 |     470 | P3D-POL, 3Dpol, P56A             |

Names: the serotype O entry P03305 is the reference; serotype A and C interactors (P03306–P03311, P49303) are the same proteins. `3B` covers the three tandem VPg copies of this family: marked `check` in the assignment table.

## Aichi virus (*Kobuvirus aichi*, NCBI 72149)

| Generic name | Protein (UniProt name; gene)    | Reference        | Length | Also called |
| ------------ | ------------------------------- | ---------------- | -----: | ----------- |
| `2B`         | Protein 2B                      | O91464 1153–1317 |    165 | P2B         |
| `2C`         | Protein 2C                      | O91464 1318–1652 |    335 | P2C         |
| `2BC`        | Protein 2B + 2C (joined chains) | O91464 1153–1652 |    500 | —           |
| `3A`         | Protein 3A                      | O91464 1653–1747 |     95 | P3A         |
| `3AB`        | Protein 3A + 3B (joined chains) | O91464 1653–1774 |    122 | —           |

## Theiler's murine encephalomyelitis virus (*Cardiovirus theileri*, NCBI 3427732)

| Generic name | Protein (UniProt name; gene) | Reference   | Length | Also called |
| ------------ | ---------------------------- | ----------- | -----: | ----------- |
| `L`          | Leader protein               | P13899 1–76 |     76 | Leader      |

Names: `L`, the UniProt short name, as in the other cardioviruses; 20 descriptions call it `Leader`.

## Seneca Valley virus (*Senecavirus valles*, NCBI 3241303)

| Generic name | Protein (UniProt name; gene) | Reference        | Length | Also called            |
| ------------ | ---------------------------- | ---------------- | -----: | ---------------------- |
| `VP1`        | Capsid protein VP1           | Q155Z9 674–937   |    264 | Alpha, P1D             |
| `2B`         | Protein 2B                   | Q155Z9 947–1074  |    128 | P2B                    |
| `3C`         | Protease 3C                  | Q155Z9 1508–1719 |    212 | P3C, Picornain 3C, p22 |

Unresolved: none, but A0A1I9WAH6 1655–1689 (7 descriptions) is named `VP1` while its 35 residues lie inside 3C: marked `check`.

## Porcine kobuvirus (*Kobuvirus bejaponia*, NCBI 194965)

| Generic name | Protein (UniProt name; gene)                                                                       | Reference                   | Length | Also called |
| ------------ | -------------------------------------------------------------------------------------------------- | --------------------------- | -----: | ----------- |
| `3A`         | Protein 3A (no Swiss-Prot entry for this species; named from Aichi virus O91464 3A, 46 % identity) | Q8BES6 1,679–1,772 (TrEMBL) |     94 | P3A         |

## Aichivirus C (*Kobuvirus cebes*, NCBI 1298633)

| Generic name | Protein (UniProt name; gene)                                                                       | Reference                   | Length | Also called |
| ------------ | -------------------------------------------------------------------------------------------------- | --------------------------- | -----: | ----------- |
| `3A`         | Protein 3A (no Swiss-Prot entry for this species; named from Aichi virus O91464 3A, 45 % identity) | B8R1T8 1,705–1,794 (TrEMBL) |     90 | P3A         |

Unresolved: none; D2WF18 1705–1738 (2 descriptions) is a 34-residue piece at the start of the same 3A region, too short to confirm on its own: marked `check`.

## Salivirus A (*Salivirus aklasse*, NCBI 3432241)

| Generic name | Protein (UniProt name; gene) | Reference        | Length | Also called |
| ------------ | ---------------------------- | ---------------- | -----: | ----------- |
| `3A`         | Protein 3A                   | C5MSH2 1600–1676 |     77 | P3A         |

## Hepatitis A virus (*Hepatovirus ahepa*, NCBI 3407641)

| Generic name | Protein (UniProt name; gene)        | Reference        | Length | Also called           |
| ------------ | ----------------------------------- | ---------------- | -----: | --------------------- |
| `VP1`        | Capsid protein VP1                  | P08617 492–764   |    273 | P1D, Virion protein 1 |
| `2A`         | Assembly signal 2A                  | P08617 765–836   |     72 | pX                    |
| `3A`         | Protein 3A                          | P08617 1423–1496 |     74 | P3A                   |
| `3CD`        | Protein 3CD (joined chains 3C + 3D) | P08617 1520–2227 |    708 | —                     |

Names: `2A` keeps the family numbering; UniProt's alternative name `pX` (used by the two descriptions) is the name of the same chain. The single `VP1` description is a 56-residue fragment of the VP1-2A chain (P0C5S8): marked `check`.

## Human parechovirus (*Parechovirus ahumpari*, NCBI 3431395)

| Generic name | Protein (UniProt name; gene) | Reference        |  Length | Also called            |
| ------------ | ---------------------------- | ---------------- | ------: | ---------------------- |
| `VP0`        | Capsid protein VP0           | O73556 1–289     | 289–290 | P1AB, Virion protein 0 |
| `3A`         | Protein 3A                   | Q66578 1375–1491 |     117 | P3A                    |

## Rhinovirus B (*Enterovirus betarhino*, NCBI 3428503)

| Generic name | Protein (UniProt name; gene) | Reference        | Length | Also called |
| ------------ | ---------------------------- | ---------------- | -----: | ----------- |
| `3A`         | Protein 3A                   | P03303 1430–1514 |     85 | P3A         |

## Saffold virus (*Cardiovirus saffoldi*, NCBI 3427731)

| Generic name | Protein (UniProt name; gene)                                                                                    | Reference   | Length | Also called |
| ------------ | --------------------------------------------------------------------------------------------------------------- | ----------- | -----: | ----------- |
| `L`          | Leader protein (the interactor is on a TrEMBL entry; closest Swiss-Prot is Saffold virus C0MHL9, 83 % identity) | C0MHL9 1–71 |  71–76 | Leader      |

## Bovine enterovirus (*Enterovirus eibovi*, NCBI 3428507)

| Generic name | Protein (UniProt name; gene)        | Reference        | Length | Also called |
| ------------ | ----------------------------------- | ---------------- | -----: | ----------- |
| `3AB`        | Protein 3AB (joined chains 3A + 3B) | P12915 1420–1531 |    112 | —           |

## Enterovirus F (*Enterovirus fitauri*, NCBI 3428508)

| Generic name | Protein (UniProt name; gene)                                                                                            | Reference        |  Length | Also called |
| ------------ | ----------------------------------------------------------------------------------------------------------------------- | ---------------- | ------: | ----------- |
| `3D`         | RNA-directed RNA polymerase (no Swiss-Prot entry for this species; named from bovine enterovirus P12915, 84 % identity) | P12915 1715–2175 | 453–461 | 3Dpol, RdRp |
