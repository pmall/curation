# Hepeviridae

Family conventions: the proteins are named by their open reading frame, as UniProt names them (`ORF1`, `ORF2`, `ORF3`, `ORF4`), without the `p` of the UniProt short names (pORF1, pORF2, pORF3). The domains of ORF1 used as interactors take the form `ORF1-<domain>`.

## Hepatitis E virus (*Paslahepevirus balayani*, NCBI 1678143)

| Generic name | Protein (UniProt name; gene)                               | Reference       |      Length | Also called             |
| ------------ | ---------------------------------------------------------- | --------------- | ----------: | ----------------------- |
| `ORF1`       | Non-structural polyprotein pORF1; ORF1 (whole polyprotein) | P29324 1–1693   | 1,693–1,708 | pORF1                   |
| `ORF1-MET`   | Methyltransferase domain of pORF1                          | Q6J8G2 60–240   |         181 | Met                     |
| `ORF1-Y`     | Y domain of pORF1                                          | Q6J8G2 239–439  |         201 | —                       |
| `ORF1-PCP`   | Papain-like protease domain of pORF1                       | Q6J8G2 440–610  |         171 | PCP                     |
| `ORF1-V`     | Hypervariable (V) region of pORF1                          | Q6J8G2 714–793  |          80 | HVR, polyproline region |
| `ORF1-X`     | X (macro) domain of pORF1                                  | Q6J8G2 800–957  |         158 | Macro domain            |
| `ORF1-Macro` | X (macro) domain of pORF1                                  | Q9WC28 775–921  |         147 | X domain                |
| `ORF1-Hel`   | Helicase domain of pORF1                                   | Q6J8G2 975–1219 |         245 | Hel                     |
| `ORF2`       | Pro-secreted protein ORF2; ORF2                            | P29326 1–660    |     658–660 | pORF2, capsid protein   |
| `ORF3`       | Protein ORF3; ORF3                                         | P69616 1–114    |     112–114 | pORF3, Vp13             |

Names: `ORF1`, `ORF2`, `ORF3` are the UniProt gene names and the names the field uses; the interactors carry the whole protein including the ORF2 signal peptide.

To check: the seven `ORF1-…` interactors are domains of pORF1, not UniProt chains (UniProt annotates no mature products on pORF1). Their boundaries come from the publications, not from UniProt; `ORF1-X` and `ORF1-Macro` are the same domain on two entries, with different boundaries.

## Rat hepatitis E virus (*Rocahepevirus ratti*, NCBI 1678145)

| Generic name | Protein (UniProt name; gene)                                                    | Reference                 | Length | Also called |
| ------------ | ------------------------------------------------------------------------------- | ------------------------- | -----: | ----------- |
| `ORF4`       | ORF4 protein (no Swiss-Prot entry; TrEMBL A0A0S3QNZ2, ferret hepatitis E virus) | A0A0S3QNZ2 1–183 (TrEMBL) |    183 | —           |

Names: no Swiss-Prot entry; the TrEMBL protein name gives the name, which follows the family convention.

## Avian hepatitis E virus (*Avihepevirus magniiecur*, NCBI 1678144)

| Generic name | Protein (UniProt name; gene) | Reference   | Length | Also called |
| ------------ | ---------------------------- | ----------- | -----: | ----------- |
| `ORF3`       | Protein ORF3; ORF3           | Q913Y8 1–87 |     87 | pORF3       |
