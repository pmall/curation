# Hepadnaviridae

Family conventions: the names already decided for hepatitis B virus in `../viruses.md` (`HBx`, `HBcAg`, `HBeAg`, `L-HBsAg`, `M-HBsAg`, `S-HBsAg`, `P`), the UniProt alternative short names the field uses, rather than the gene names (`C` names both core and precore, `S` all three envelope proteins). The other hepadnaviruses use the same names.

## Hepatitis B virus (*Orthohepadnavirus hominoidei*, NCBI 3431302)

| Generic name | Protein (UniProt name; gene)              | Reference             |  Length | Also called                                 |
| ------------ | ----------------------------------------- | --------------------- | ------: | ------------------------------------------- |
| `HBeAg`      | External core antigen; C                  | P0C573 1–212          | 212–214 | precore protein, p25                        |
| `HBcAg`      | Capsid protein; C                         | P03146 1–183          | 183–185 | core antigen, core protein, p21.5           |
| `P`          | Protein P; P                              | P03159 1–845          | 832–845 | polymerase                                  |
| `L-HBsAg`    | Large envelope protein; S                 | P03141 1–400          | 389–400 | LHB, large S protein, major surface antigen |
| `M-HBsAg`    | Middle S protein; S (no Swiss-Prot entry) | B5TFB1 1–281 (TrEMBL) |     281 | MHB, middle surface protein                 |
| `S-HBsAg`    | Small envelope protein; S                 | P30019 1–226          |     226 | SHB, small S protein, HBsAg                 |
| `HBx`        | Protein X; X                              | P03165 1–154          |     154 | peptide X, pX                               |

Names: as decided in `../viruses.md`. `HBsAg` alone is not used: depending on the publication it names the small protein or the whole antigen.

To check:

- Seven interactors (38 descriptions) sit on precore entries of 212–214 residues but are named `C` or `HBcAg` in Drakkar: the region is the question, not the name, and it is settled from the abstracts.
- Q67953 (3 descriptions) is a large envelope protein of 445 residues, longer than any other.

Unresolved: A0A0S3IRJ8 1–40 (2 descriptions, "Precore/core protein (Fragment)"): 40 residues do not tell core from precore.

## Duck hepatitis B virus (*Avihepadnavirus anatigruidae*, NCBI 3426542)

| Generic name | Protein (UniProt name; gene) | Reference    | Length | Also called                |
| ------------ | ---------------------------- | ------------ | -----: | -------------------------- |
| `HBcAg`      | Capsid protein; C            | P0C6J7 1–262 |    262 | core antigen, core protein |

## Bat hepatitis B virus (*Orthohepadnavirus rotundifolii*, NCBI 3431461)

| Generic name | Protein (UniProt name; gene)       | Reference             | Length | Also called   |
| ------------ | ---------------------------------- | --------------------- | -----: | ------------- |
| `HBx`        | Protein X; X (no Swiss-Prot entry) | U3MBW5 1–141 (TrEMBL) |    141 | peptide X, pX |

Names: from the TrEMBL entries (gene X) and the woolly monkey hepatitis B virus protein X (53–57 % identity).

## Woodchuck hepatitis virus (*Orthohepadnavirus marmotae*, NCBI 3431307)

| Generic name | Protein (UniProt name; gene) | Reference    | Length | Also called        |
| ------------ | ---------------------------- | ------------ | -----: | ------------------ |
| `HBx`        | Protein X; X                 | P03167 1–141 |    141 | peptide X, pX, WHx |

## Woolly monkey hepatitis B virus (*Orthohepadnavirus lagothricis*, NCBI 3431303)

| Generic name | Protein (UniProt name; gene) | Reference    | Length | Also called   |
| ------------ | ---------------------------- | ------------ | -----: | ------------- |
| `HBx`        | Protein X; X                 | O71302 1–152 |    152 | peptide X, pX |
