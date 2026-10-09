# Viruses with no family in NCBI

The species of these interactors has no family in NCBI, or the taxon itself is missing from NCBI (the packet calls that family "None"). The proteins are named by the same rules as everywhere else.

## Epstein-Barr virus (species missing in NCBI, NCBI None)

Herpesvirus rule (`viruses.md` §3, same choice as for the other herpesviruses): a protein widely known by a protein name keeps it (`EBNA-1`, `EBNA-LP`, `gL`, `gN`, `gp42`), the others keep their gene/ORF name (`BZLF1`, `BALF5`, `BDLF2`, `BLLF2`, `BLLF3`, `BLRF2`, `BMRF2`, `BNLF2a`). The nuclear antigens are hyphenated as UniProt writes them: `EBNA-1`, `EBNA-3A`, `EBNA-3B`, `EBNA-3C`, `EBNA-LP`.

| Generic name | Protein (UniProt name; gene)                                 | Reference     | Length | Also called                         |
| ------------ | ------------------------------------------------------------ | ------------- | -----: | ----------------------------------- |
| `EBNA-LP`    | Epstein-Barr nuclear antigen leader protein; EBNA-LP         | Q8AZK7 1–506  |    506 | EBNA-5, EBNA5                       |
| `BZLF1`      | Lytic switch protein BZLF1; BZLF1                            | Q3KSS8 1–245  |    245 | Zta, ZEBRA, EB1, Protein Z          |
| `gN`         | Envelope glycoprotein N; gN, BLRF1                           | P0C6Z3 1–102  |    102 | BLRF1                               |
| `EBNA-3B`    | Epstein-Barr nuclear antigen 4; EBNA4                        | Q3KST1 1–938  |    938 | EBNA-4, EBNA4, BERF2A-BERF2B        |
| `BDLF2`      | Protein BDLF2; BDLF2                                         | Q3KSQ7 1–420  |    420 | —                                   |
| `BLLF3`      | Deoxyuridine 5'-triphosphate nucleotidohydrolase; DUT, BLLF3 | Q3KST7 1–278  |    278 | dUTPase                             |
| `BNLF2a`     | Protein BNLF2a; BNLF2a                                       | P0C737 1–60   |     60 | —                                   |
| `EBNA-3A`    | Epstein-Barr nuclear antigen 3; EBNA3                        | Q3KST2 1–935  |    935 | EBNA-3, EBNA3, BLRF3-BERF1          |
| `BLRF2`      | Tegument protein BLRF2; BLRF2                                | Q3KST5 1–162  |    162 | VCA-p23                             |
| `gL`         | Envelope glycoprotein L; gL, BKRF2                           | Q3KSS3 1–137  |    137 | BKRF2                               |
| `gp42`       | Glycoprotein 42; BZLF2                                       | P03205 1–223  |    223 | BZLF2                               |
| `BMRF2`      | Protein BMRF2; BMRF2                                         | Q3KSU2 1–357  |    357 | —                                   |
| `BLLF2`      | Uncharacterized protein BLLF2; BLLF2                         | Q3KST3 1–148  |    148 | —                                   |
| `EBNA-3C`    | Epstein-Barr nuclear antigen 6; EBNA6                        | Q3KST0 1–1009 |  1,009 | EBNA-6, EBNA-4B, EBNA6, BERF3-BERF4 |
| `BALF5`      | DNA polymerase catalytic subunit; BALF5                      | Q3KSP1 1–1015 |  1,015 | viral DNA polymerase                |
| `EBNA-1`     | Epstein-Barr nuclear antigen 1; EBNA1                        | Q3KSS4 1–641  |    641 | EBNA1, BKRF1                        |

Names: the glycoproteins take their protein names (`gL`, `gN`, `gp42`), not `BKRF2`, `BLRF1`, `BZLF2`, as for gB and gH in the other herpesviruses; the four descriptions that use the gene names are renamed. `BLLF3` keeps the ORF name (UniProt's gene names are DUT and BLLF3): the enzyme name dUTPase names an activity shared with the host.

Unresolved: none, but the species of these 255 descriptions is missing in NCBI: the entries are Epstein-Barr virus strains GD1, B95-8 and AG876.

## Clostridium botulinum D phage (*Clostridium botulinum D phage*, NCBI 29342)

| Generic name | Protein (UniProt name; gene)       | Reference    | Length | Also called                  |
| ------------ | ---------------------------------- | ------------ | -----: | ---------------------------- |
| `C3`         | Mono-ADP-ribosyltransferase C3; C3 | P15879 1–251 |    251 | Exoenzyme C3, C3 transferase |

## Bacillus phage PBS2 (*Bacillus phage PBS2*, NCBI 10684)

| Generic name | Protein (UniProt name; gene)          | Reference   | Length | Also called |
| ------------ | ------------------------------------- | ----------- | -----: | ----------- |
| `UGI`        | Uracil-DNA glycosylase inhibitor; UGI | P14739 1–84 |     84 | Ugi         |

## Reovirus sp. (*Reovirus sp.*, NCBI 10891)

| Generic name | Protein (UniProt name; gene)     | Reference    |  Length | Also called                                         |
| ------------ | -------------------------------- | ------------ | ------: | --------------------------------------------------- |
| `Sigma1`     | Outer capsid protein sigma-1; S1 | P04507 1–462 | 454–462 | sigma-1, S1, Cell attachment protein, Hemagglutinin |

Names: `Sigma1` with the spelling of the other reovirus proteins (see `spinareoviridae.md`); the description uses the segment name `S1`.
