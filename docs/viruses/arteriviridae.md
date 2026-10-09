# Arteriviridae

Family conventions: the replicase chains are `Nsp1` to `Nsp12` with a capital N, as Swiss-Prot writes them for arteriviruses (the coronaviruses use `nsp`). The two cleavage products of Nsp1 keep their Greek letter: `Nsp1-alpha`, `Nsp1-beta`. Structural proteins: `N`, `M`, `GP3`, `GP4`.

## PRRSV-2 (*Betaarterivirus americense*, NCBI 2499685)

| Generic name | Protein (UniProt name; gene)                                    | Reference                       |  Length | Also called                                  |
| ------------ | --------------------------------------------------------------- | ------------------------------- | ------: | -------------------------------------------- |
| `Nsp1-alpha` | Nsp1-alpha papain-like cysteine proteinase; rep                 | A0MD28 1–180                    |     180 | PCP1-alpha                                   |
| `Nsp1-beta`  | Nsp1-beta papain-like cysteine proteinase; rep                  | Q9WJB2 181–383                  |     203 | PCP1-beta                                    |
| `Nsp2`       | Nsp2 cysteine proteinase; rep                                   | Q8B912 384–1579                 |   1,196 | CP, CP2                                      |
| `Nsp5`       | Non-structural protein 5; rep                                   | A6YQT5 1984–2153                |     170 | —                                            |
| `Nsp7`       | Non-structural protein 7-alpha + 7-beta; rep (joined chains)    | Q8B912 2200–2458                |     259 | Nsp7-alpha, Nsp7-beta                        |
| `Nsp12`      | Non-structural protein 12; rep                                  | Q9YN02 3809–3961                |     153 | —                                            |
| `GP3`        | Glycoprotein 3; GP3                                             | Q04567 1–265                    | 254–265 | Protein GP3, glycosylated membrane protein 3 |
| `GP4`        | Glycoprotein 4; GP4                                             | Q04568 23–183                   | 161–178 | GP4 envelope protein                         |
| `N`          | — (no Swiss-Prot entry for this species); nucleoprotein, gene N | Q04558 1–128 (nearest, PRRSV-1) |     123 | Protein N, nucleocapsid protein, NC          |

Names: `Nsp7` is used for one interactor whose region covers Nsp7-alpha and Nsp7-beta together (marked joined chains); whether such a region is acceptable is the open question, the name is not. `GP3` and `GP4` are the Swiss-Prot gene names, the names the field uses.

Unresolved: Q6SJE7 1–1463 and F1CJM8 1–1460, named `RDRP` (1 description each), are ORF1b fragments covering Nsp9 to Nsp12 — four chains, not one protein.

## PRRSV-1 (*Betaarterivirus europensis*, NCBI 3411021)

| Generic name | Protein (UniProt name; gene)                   | Reference        | Length | Also called               |
| ------------ | ---------------------------------------------- | ---------------- | -----: | ------------------------- |
| `Nsp2`       | Nsp2 cysteine proteinase; rep                  | Q04561 386–1463  |  1,078 | CP, CP2                   |
| `Nsp11`      | Uridylate-specific endoribonuclease nsp11; rep | Q04561 3480–3703 |    224 | Non-structural protein 11 |

## Equine arteritis virus (*Alphaarterivirus equid*, NCBI 2499620)

| Generic name | Protein (UniProt name; gene)              | Reference        | Length | Also called |
| ------------ | ----------------------------------------- | ---------------- | -----: | ----------- |
| `Nsp1`       | Nsp1 papain-like cysteine proteinase; rep | P19811 1–260     |    260 | PCP         |
| `Nsp9`       | RNA-directed RNA polymerase; rep          | P19811 1678–2370 |    693 | RdRp, Pol   |
| `M`          | Membrane protein; M                       | P28991 1–162     |    162 | Protein M   |

Names: equine arteritis virus has one Nsp1, not the alpha/beta pair of the PRRS viruses. The polymerase is `Nsp9`, the number Swiss-Prot gives the chain, rather than RdRp.

## Simian hemorrhagic fever virus (*Deltaarterivirus hemfev*, NCBI 2499622)

| Generic name | Protein (UniProt name; gene)  | Reference       | Length | Also called |
| ------------ | ----------------------------- | --------------- | -----: | ----------- |
| `Nsp2`       | Nsp2 cysteine proteinase; rep | Q68772 351–1236 |    886 | CP, CP2     |
