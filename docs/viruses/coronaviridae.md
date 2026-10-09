# Coronaviridae

Family conventions: the replicase chains are `nsp1` to `nsp16`, lowercase, as Swiss-Prot writes them for coronaviruses (not the arterivirus `Nsp`). Accessory proteins take the name Swiss-Prot gives them in that virus: `ORF3a`, `ORF6`, `ORF8` style for the SARS viruses and MERS, `ns3a`, `ns4a`, `ns2a` style for 229E, NL63, MHV, PEDV, HKU5 and HKU9. Structural proteins: `S`, `E`, `M`, `N`, `HE`.

## SARS-CoV-2 and SARS-CoV (*Betacoronavirus pandemicum*, NCBI 3418604)

| Generic name | Protein (UniProt name; gene)                   | Reference                 |                 Length | Also called                            |
| ------------ | ---------------------------------------------- | ------------------------- | ---------------------: | -------------------------------------- |
| `nsp1`       | Host translation inhibitor nsp1; rep           | P0DTD1 1–180              |                    180 | Leader protein                         |
| `nsp2`       | Non-structural protein 2; rep                  | P0DTD1 181–818            |                    638 | p65 homolog                            |
| `nsp3`       | Papain-like protease nsp3; rep                 | P0DTD1 819–2763           |            1,922–1,945 | PL-PRO, PL2-PRO                        |
| `nsp4`       | Non-structural protein 4; rep                  | P0DTD1 2764–3263          |                    500 | —                                      |
| `nsp5`       | 3C-like proteinase nsp5; rep                   | P0DTD1 3264–3569          |                    306 | 3CL-PRO, Mpro, main protease           |
| `nsp6`       | Non-structural protein 6; rep                  | P0DTD1 3570–3859          |                    290 | —                                      |
| `nsp7`       | Non-structural protein 7; rep                  | P0DTD1 3860–3942          |                     83 | —                                      |
| `nsp8`       | Non-structural protein 8; rep                  | P0DTD1 3943–4140          |                    198 | —                                      |
| `nsp9`       | Viral protein genome-linked nsp9; rep          | P0DTD1 4141–4253          |                    113 | RNA-capping enzyme subunit nsp9        |
| `nsp10`      | Non-structural protein 10; rep                 | P0DTD1 4254–4392          |                    139 | GFL, growth factor-like peptide        |
| `nsp11`      | Non-structural protein 11; 1a                  | P0DTC1 4393–4405          |                     13 | —                                      |
| `nsp12`      | RNA-directed RNA polymerase nsp12; rep         | P0DTD1 4393–5324          |                    932 | RdRp, Pol                              |
| `nsp13`      | Helicase nsp13; rep                            | P0DTD1 5325–5925          |                    601 | Hel                                    |
| `nsp14`      | Guanine-N7 methyltransferase nsp14; rep        | P0DTD1 5926–6452          |                    527 | ExoN, proofreading exoribonuclease     |
| `nsp15`      | Uridylate-specific endoribonuclease nsp15; rep | P0DTD1 6453–6798          |                    346 | NendoU                                 |
| `nsp16`      | 2'-O-methyltransferase nsp16; rep              | P0DTD1 6799–7096          |                    298 | —                                      |
| `S`          | Spike glycoprotein; S (whole polyprotein)      | P0DTC2 1–1273             |            1,255–1,273 | S glycoprotein, E2, peplomer protein   |
| `ORF3a`      | ORF3a protein; 3a                              | P0DTC3 1–275              |                274–275 | Accessory protein 3a, protein U274, X1 |
| `ORF3b`      | ORF3b protein; 3b                              | P59633 1–154; P0DTF1 1–22 | 154 (22 in SARS-CoV-2) | ns3b, accessory protein 3b, protein X2 |
| `E`          | Envelope small membrane protein; E             | P0DTC4 1–75               |                  75–76 | sM protein                             |
| `M`          | Membrane protein; M                            | P0DTC5 1–222              |                221–222 | E1 glycoprotein, matrix glycoprotein   |
| `ORF6`       | ORF6 protein; 6                                | P0DTC6 1–61               |                  61–63 | ns6, accessory protein 6, protein X3   |
| `ORF7a`      | ORF7a protein; 7a                              | P0DTC7 1–121              |                121–122 | Accessory protein 7a, protein U122, X4 |
| `ORF7b`      | ORF7b protein; 7b                              | P0DTD8 1–43               |                  43–44 | ns7b, accessory protein 7b             |
| `ORF8`       | ORF8 protein; 8                                | P0DTC8 1–121              |                121–122 | ns8, accessory protein 8               |
| `ORF8a`      | ORF8a protein; 8a                              | Q7TFA0 1–39               |                     39 | ns8a                                   |
| `ORF8b`      | ORF8b protein; 8b                              | Q80H93 1–84               |                     84 | ns8b                                   |
| `N`          | Nucleoprotein; N                               | P0DTC9 1–419              |                419–422 | Nucleocapsid protein, NC               |
| `ORF9b`      | ORF9b protein; 9b                              | P0DTD2 1–97               |                  97–98 | Accessory protein 9b, ORF-9b           |
| `ORF9c`      | Putative ORF9c protein; 9c                     | P0DTD3 1–73               |                  70–73 | ORF14, uncharacterized protein 14      |
| `ORF10`      | Putative ORF10 protein; ORF10                  | A0A663DJA2 1–38           |                     38 | —                                      |

Names: the Swiss-Prot short names, with the capital `ORF` spelling of these entries; Drakkar's lowercase `orf3a`, `orf6`… are renamed. `ORF9c` covers the SARS-CoV protein that Swiss-Prot calls ORF14 (same protein group). `ORF8` is the full-length ORF8, `ORF8a` and `ORF8b` the two products of the SARS-CoV strains carrying the 29-nucleotide deletion. The 63-residue Q6VA95, named `N` in Drakkar, is ORF6.

Unresolved: Q6SRE2 1–312 (named `nsp15`, 1 description) is a replicase fragment lying across the nsp14/nsp15 junction; which of the two it is cannot be told.

## MERS-CoV (*Betacoronavirus cameli*, NCBI 3433633)

| Generic name | Protein (UniProt name; gene)                   | Reference        |      Length | Also called                          |
| ------------ | ---------------------------------------------- | ---------------- | ----------: | ------------------------------------ |
| `nsp1`       | Host translation inhibitor nsp1; rep           | K9N7C7 1–193     |         193 | Leader protein                       |
| `nsp2`       | Non-structural protein 2; rep                  | K9N7C7 194–853   |         660 | p65 homolog                          |
| `nsp3`       | Papain-like protease nsp3; rep                 | K9N7C7 854–2740  |       1,887 | PL-PRO                               |
| `nsp4`       | Non-structural protein 4; rep                  | K9N7C7 2741–3247 |         507 | —                                    |
| `nsp5`       | 3C-like proteinase nsp5; rep                   | K9N7C7 3248–3553 |         306 | 3CL-PRO, main protease               |
| `nsp6`       | Non-structural protein 6; rep                  | K9N7C7 3554–3845 |         292 | —                                    |
| `nsp7`       | Non-structural protein 7; rep                  | K9N7C7 3846–3928 |          83 | —                                    |
| `nsp8`       | Non-structural protein 8; rep                  | K9N7C7 3929–4127 |         199 | —                                    |
| `nsp9`       | Viral protein genome-linked nsp9; rep          | K9N7C7 4128–4237 |         110 | p12, RNA-capping enzyme subunit nsp9 |
| `nsp10`      | Non-structural protein 10; rep                 | K9N7C7 4238–4377 |         140 | GFL                                  |
| `nsp11`      | Non-structural protein 11; 1a                  | K9N638 4378–4391 |          14 | —                                    |
| `nsp13`      | Helicase nsp13; rep                            | K9N7C7 5311–5908 |         598 | Hel                                  |
| `nsp14`      | Guanine-N7 methyltransferase nsp14; rep        | K9N7C7 5909–6432 |         524 | ExoN                                 |
| `nsp15`      | Uridylate-specific endoribonuclease nsp15; rep | K9N7C7 6433–6775 |         343 | NendoU                               |
| `nsp16`      | 2'-O-methyltransferase nsp16; rep              | K9N7C7 6776–7078 |         303 | —                                    |
| `S`          | Spike glycoprotein; S (whole polyprotein)      | K9N5Q8 1–1353    | 1,322–1,353 | S glycoprotein, E2, peplomer protein |
| `S1`         | Spike protein S1; S (chain)                    | K9N5Q8 18–751    |         734 | —                                    |
| `ORF3`       | Non-structural protein ORF3; ORF3              | K9N796 1–103     |         103 | —                                    |
| `ORF4a`      | Non-structural protein ORF4a; ORF4a            | K9N4V0 1–109     |         109 | NS3b protein (TrEMBL)                |
| `ORF4b`      | Non-structural protein ORF4b; ORF4b            | K9N643 1–246     |         246 | —                                    |
| `ORF5`       | Non-structural protein ORF5; ORF5              | K9N7D2 1–224     |         224 | NS3D protein (TrEMBL)                |
| `E`          | Envelope small membrane protein; E             | K9N5R3 1–82      |          82 | sM protein                           |
| `M`          | Membrane protein; M                            | K9N7A1 1–219     |         219 | E1 glycoprotein, matrix glycoprotein |
| `N`          | Nucleoprotein; N                               | K9N4V7 1–411     |     411–433 | Nucleocapsid protein, NC             |
| `ORF8b`      | — (no Swiss-Prot entry); TrEMBL gene orf8b     | R9UNW8 1–112     |         112 | —                                    |

Names: the Swiss-Prot `ORF` short names of this virus; `ORF8b`, the internal ORF of the N gene, has no Swiss-Prot entry and takes its TrEMBL gene name. `S1` is the mature chain, `S` the whole protein.

## Human coronavirus 229E (*Alphacoronavirus chicagoense*, NCBI 3433756)

| Generic name | Protein (UniProt name; gene)              | Reference        |      Length | Also called                          |
| ------------ | ----------------------------------------- | ---------------- | ----------: | ------------------------------------ |
| `nsp1`       | Non-structural protein 1; 1a              | P0C6U2 1–111     |         111 | p9                                   |
| `nsp3`       | Papain-like protease nsp3; rep            | P0C6X1 898–2484  |       1,587 | PLP1/PLP2, p195                      |
| `nsp4`       | Non-structural protein 4; rep             | P0C6X1 2485–2965 |         481 | Peptide HD2                          |
| `nsp5`       | 3C-like proteinase; rep                   | P0C6X1 2966–3267 |         302 | 3CL-PRO, M-PRO, p34                  |
| `nsp6`       | Non-structural protein 6; rep             | P0C6X1 3268–3546 |         279 | —                                    |
| `nsp8`       | Non-structural protein 8; rep             | P0C6X1 3630–3824 |         195 | p23                                  |
| `nsp14`      | Exoribonuclease; rep                      | P0C6X1 5593–6110 |         518 | ExoN                                 |
| `S`          | Spike glycoprotein; S                     | P15423 1–1173    | 1,170–1,173 | S glycoprotein, E2, peplomer protein |
| `ns4a`       | Non-structural protein 4a; 4a             | P19739 1–133     |         133 | Accessory protein 4a                 |
| `ns4`        | — (no Swiss-Prot entry); TrEMBL gene ORF4 | A2ICY9 1–219     |         219 | ORF4 protein                         |
| `N`          | Nucleoprotein; N                          | P15130 1–389     |         389 | Nucleocapsid protein, NC             |

Names: 229E accessories are `ns…` on Swiss-Prot, so Drakkar's `orf4a` becomes `ns4a`. `ns4` is the full-length ORF4 product (219 residues), which Swiss-Prot has only as the split ns4a/ns4b: to check whether the publications studied the full-length protein.

## Human coronavirus NL63 (*Alphacoronavirus amsterdamense*, NCBI 3433809)

| Generic name | Protein (UniProt name; gene)   | Reference        | Length | Also called                          |
| ------------ | ------------------------------ | ---------------- | -----: | ------------------------------------ |
| `nsp1`       | Non-structural protein 1; rep  | P0C6X5 1–110     |    110 | p9                                   |
| `nsp3`       | Papain-like protease nsp3; rep | P0C6X5 899–2462  |  1,564 | PLP1/PLP2, p195                      |
| `nsp6`       | Non-structural protein 6; rep  | P0C6X5 3243–3521 |    279 | —                                    |
| `nsp7`       | Non-structural protein 7; rep  | P0C6X5 3522–3604 |     83 | p5                                   |
| `nsp13`      | Helicase; rep                  | P0C6X5 4971–5567 |    597 | Hel, p66                             |
| `nsp14`      | Exoribonuclease; rep           | P0C6X5 5568–6085 |    518 | ExoN                                 |
| `S`          | Spike glycoprotein; S          | Q6Q1S2 1–1356    |  1,356 | S glycoprotein, E2, peplomer protein |
| `ns3`        | Non-structural protein 3; 3    | Q6Q1S1 1–225     |    225 | Protein 3, accessory protein 3a      |
| `M`          | Membrane protein; M            | Q6Q1R9 1–226     |    226 | E1 glycoprotein, matrix glycoprotein |
| `N`          | Nucleoprotein; N               | Q6Q1R8 1–377     |    377 | Nucleocapsid protein, NC             |

Names: `ns3` is the accessory protein (gene 3), not the replicase chain `nsp3`.

## Avian infectious bronchitis virus (*Gammacoronavirus galli*, NCBI 3433766)

| Generic name | Protein (UniProt name; gene)              | Reference        |      Length | Also called                             |
| ------------ | ----------------------------------------- | ---------------- | ----------: | --------------------------------------- |
| `nsp3`       | Papain-like protease nsp3; rep            | P0C6Y3 674–2267  | 1,592–1,594 | PL-PRO, p195                            |
| `nsp13`      | Helicase; rep                             | P0C6Y2 4869–5468 |         600 | Hel, p68                                |
| `nsp14`      | Proofreading exoribonuclease; rep         | P0C6Y2 5469–5989 |         521 | ExoN, guanine-N7 methyltransferase, p58 |
| `S`          | Spike glycoprotein; S (whole polyprotein) | P11223 1–1162    |       1,162 | S glycoprotein, E2, peplomer protein    |
| `E`          | Envelope small membrane protein; E        | Q89894 1–108     |         108 | sM protein                              |
| `M`          | Membrane protein; M                       | P69601 1–225     |     225–230 | E1 glycoprotein, matrix glycoprotein    |
| `N`          | Nucleoprotein; N                          | P69596 1–409     |         409 | Nucleocapsid protein, NC                |

Names: the interactor named `papain-like_protease` in Drakkar is the nsp3 chain, so `nsp3`.

## Human coronavirus OC43 (*Betacoronavirus gravedinis*, NCBI 3433757)

| Generic name | Protein (UniProt name; gene)                   | Reference        |  Length | Also called                          |
| ------------ | ---------------------------------------------- | ---------------- | ------: | ------------------------------------ |
| `nsp1`       | Non-structural protein 1; 1a                   | P0C6U7 1–246     |     246 | p28                                  |
| `nsp4`       | Non-structural protein 4; 1a                   | P0C6U7 2751–3246 |     496 | Peptide HD2, p44                     |
| `nsp15`      | Uridylate-specific endoribonuclease nsp15; rep | P0C6X0 6422–6795 |     374 | NendoU, p35                          |
| `S`          | Spike glycoprotein; S (whole polyprotein)      | P36334 1–1353    |   1,353 | S glycoprotein, E2, peplomer protein |
| `E`          | Envelope small membrane protein; E             | P0C2Q3 1–84      |      84 | sM protein                           |
| `M`          | Membrane protein; M                            | P69703 1–230     |     230 | E1 glycoprotein, matrix glycoprotein |
| `N`          | Nucleoprotein; N                               | P33469 1–448     | 446–448 | Nucleocapsid protein, NC             |

## Human coronavirus HKU1 (*Betacoronavirus hongkongense*, NCBI 3433758)

| Generic name | Protein (UniProt name; gene)                   | Reference        | Length | Also called                          |
| ------------ | ---------------------------------------------- | ---------------- | -----: | ------------------------------------ |
| `nsp1`       | Non-structural protein 1; 1a                   | P0C6U4 1–222     |    222 | p28                                  |
| `nsp3`       | Papain-like protease nsp3; rep                 | P0C6X4 810–2788  |  1,979 | PL-PRO, p210                         |
| `nsp4`       | Non-structural protein 4; rep                  | P0C6X4 2789–3284 |    496 | Peptide HD2, p44                     |
| `nsp5`       | 3C-like proteinase nsp5; rep                   | P0C6X2 3335–3637 |    303 | 3CL-PRO, M-PRO, p27                  |
| `nsp6`       | Non-structural protein 6; rep                  | P0C6X4 3588–3874 |    287 | —                                    |
| `nsp7`       | Non-structural protein 7; rep                  | P0C6X4 3875–3966 |     92 | p10                                  |
| `nsp14`      | Guanine-N7 methyltransferase nsp14; rep        | P0C6X4 5939–6459 |    521 | ExoN                                 |
| `nsp15`      | Uridylate-specific endoribonuclease nsp15; rep | P0C6X4 6460–6833 |    374 | NendoU, p35                          |
| `S`          | Spike glycoprotein; S (whole polyprotein)      | Q5MQD0 1–1356    |  1,356 | S glycoprotein, E2, peplomer protein |
| `M`          | Membrane protein; M                            | Q14EA7 1–223     |    223 | E1 glycoprotein, matrix glycoprotein |
| `N`          | Nucleoprotein; N                               | Q5MQC6 1–441     |    441 | Nucleocapsid protein, NC             |

To check: the single `nsp5` interactor is curated on P0C6X2 3335–3627, ten residues short of the nsp5 chain (3335–3637).

## Bat coronavirus HKU5 (*Betacoronavirus pipistrelli*, NCBI 3433775)

| Generic name | Protein (UniProt name; gene)              | Reference        | Length | Also called                          |
| ------------ | ----------------------------------------- | ---------------- | -----: | ------------------------------------ |
| `nsp3`       | Papain-like protease nsp3; 1a             | P0C6T5 852–2830  |  1,979 | PL-PRO, PL2-PRO                      |
| `nsp4`       | Non-structural protein 4; 1a              | P0C6T5 2831–3338 |    508 | —                                    |
| `nsp6`       | Non-structural protein 6; 1a              | P0C6T5 3645–3936 |    292 | —                                    |
| `nsp7`       | Non-structural protein 7; 1a              | P0C6T5 3937–4019 |     83 | —                                    |
| `nsp8`       | Non-structural protein 8; 1a              | P0C6T5 4020–4218 |    199 | —                                    |
| `nsp9`       | RNA-capping enzyme subunit nsp9; 1a       | P0C6T5 4219–4328 |    110 | Viral protein genome-linked nsp9     |
| `nsp10`      | Non-structural protein 10; 1a             | P0C6T5 4329–4467 |    139 | GFL                                  |
| `S`          | Spike glycoprotein; S (whole polyprotein) | A3EXD0 1–1352    |  1,352 | S glycoprotein, E2, peplomer protein |
| `ns3a`       | Non-structural protein 3a; 3a             | A3EXD1 1–121     |    121 | Accessory protein 3a                 |
| `ns3d`       | Non-structural protein 3d; 3d             | A3EXD4 1–223     |    223 | Accessory protein 3d                 |
| `ORF4b`      | Non-structural protein ORF4b; ORF4b       | A3EXD3 1–256     |    256 | —                                    |
| `E`          | Envelope small membrane protein; E        | A3EXD5 1–82      |     82 | sM protein                           |
| `M`          | Membrane protein; M                       | A3EXD6 1–220     |    220 | E1 glycoprotein, matrix glycoprotein |
| `N`          | Nucleoprotein; N                          | A3EXD7 1–427     |    427 | Nucleocapsid protein, NC             |

Names: Swiss-Prot mixes the two styles in this virus: `ns3a` and `ns3d` for the gene-3 accessories, `ORF4b` for the ORF4b protein. Drakkar's `orf3a` and `orf5` are `ns3a` and `ns3d`.

## Transmissible gastroenteritis virus and relatives (*Alphacoronavirus suis*, NCBI 3433814)

| Generic name | Protein (UniProt name; gene)       | Reference        |      Length | Also called                          |
| ------------ | ---------------------------------- | ---------------- | ----------: | ------------------------------------ |
| `nsp3`       | Papain-like protease nsp3; rep     | P0C6Y5 880–2388  | 1,509–1,534 | PLP1/PLP2, p195                      |
| `nsp4`       | Non-structural protein 4; rep      | P0C6Y5 2389–2878 |         490 | Peptide HD2                          |
| `nsp6`       | Non-structural protein 6; rep      | P0C6Y5 3181–3474 |         294 | —                                    |
| `nsp7`       | Non-structural protein 7; rep      | P0C6Y5 3475–3557 |          83 | p5                                   |
| `nsp8`       | Non-structural protein 8; rep      | P0C6Y5 3558–3752 |         195 | p23                                  |
| `nsp11`      | Non-structural protein 11; 1a      | P0C6V2 3999–4017 |          19 | —                                    |
| `nsp14`      | Exoribonuclease; rep               | P0C6Y5 5527–6045 |         519 | ExoN                                 |
| `S`          | Spike glycoprotein; S              | P07946 1–1447    | 1,225–1,447 | S glycoprotein, E2, peplomer protein |
| `E`          | Envelope small membrane protein; E | P69611 1–82      |          82 | sM protein                           |
| `N`          | Nucleoprotein; N                   | P04134 1–382     |     381–382 | Nucleocapsid protein, NC             |

Names: one species gathers TGEV, porcine respiratory coronavirus, feline coronavirus and canine coronavirus; the names are the same in all four, the lengths differ (the porcine respiratory spike is 1,225 residues).

## Murine hepatitis virus (*Betacoronavirus muris*, NCBI 3433759)

| Generic name | Protein (UniProt name; gene)            | Reference        |      Length | Also called                          |
| ------------ | --------------------------------------- | ---------------- | ----------: | ------------------------------------ |
| `nsp1`       | Host translation inhibitor nsp1; rep    | P0C6X9 1–247     |         247 | p28                                  |
| `nsp3`       | Papain-like protease nsp3; rep          | P0C6X9 833–2837  | 1,951–2,005 | PL-PRO, p210                         |
| `nsp4`       | Non-structural protein 4; rep           | P0C6X9 2838–3333 |         496 | Peptide HD2, p44                     |
| `nsp14`      | Guanine-N7 methyltransferase nsp14; rep | P0C6X9 5983–6503 |         521 | ExoN                                 |
| `ns2a`       | Non-structural protein 2a; 2a           | P19738 1–261     |         261 | ns2, p30, 30 kDa accessory protein   |
| `HE`         | Hemagglutinin-esterase; HE              | P31615 1–428     |     428–439 | HE protein, E3 glycoprotein          |
| `ns4`        | Non-structural protein 4; 4             | P0C5A8 1–128     |         128 | Accessory protein 4                  |
| `M`          | Membrane protein; M                     | P03415 1–228     |         228 | E1 glycoprotein, matrix glycoprotein |
| `N`          | Nucleoprotein; N                        | P03416 1–454     |         454 | Nucleocapsid protein, NC             |

Names: `ns4` is the 128-residue accessory protein of gene 4 (named `nsp4` in Drakkar), not the replicase chain `nsp4`.

## Porcine epidemic diarrhea virus (*Alphacoronavirus porci*, NCBI 3433789)

| Generic name | Protein (UniProt name; gene)            | Reference        |      Length | Also called                                      |
| ------------ | --------------------------------------- | ---------------- | ----------: | ------------------------------------------------ |
| `nsp3`       | Papain-like protease nsp3; rep          | P0C6Y4 896–2516  |       1,621 | PL-PRO, PLP1/PLP2, p195                          |
| `nsp14`      | Guanine-N7 methyltransferase nsp14; rep | P0C6Y4 5547–6141 |         595 | ExoN                                             |
| `S`          | Spike glycoprotein; S                   | Q91AV1 1–1383    | 1,383–1,386 | S glycoprotein, E2, peplomer protein             |
| `ns3`        | Non-structural protein 3; 3             | Q91AV0 1–224     |         224 | Accessory protein 3a, accessory membrane protein |
| `N`          | Nucleoprotein; N                        | Q07499 1–441     |         441 | Nucleocapsid protein, NC                         |

To check: A0A068JC22 1–409, named `N` (2 descriptions), is a nucleoprotein fragment of 409 residues out of 441.

## Bat coronavirus HKU9 (*Betacoronavirus rousetti*, NCBI 3418615)

| Generic name | Protein (UniProt name; gene)              | Reference        | Length | Also called                          |
| ------------ | ----------------------------------------- | ---------------- | -----: | ------------------------------------ |
| `nsp3`       | Papain-like protease nsp3; rep            | P0C6W5 773–2609  |  1,837 | PL-PRO                               |
| `nsp4`       | Non-structural protein 4; rep             | P0C6W5 2610–3103 |    494 | —                                    |
| `nsp8`       | Non-structural protein 8; 1a              | P0C6T6 3783–3982 |    200 | —                                    |
| `nsp14`      | Guanine-N7 methyltransferase nsp14; rep   | P0C6W5 5767–6296 |    530 | ExoN                                 |
| `S`          | Spike glycoprotein; S (whole polyprotein) | A3EXG6 1–1274    |  1,274 | S glycoprotein, E2, peplomer protein |
| `ns3`        | Non-structural protein 3; 3               | A3EXG7 1–220     |    220 | Accessory protein 3                  |
| `E`          | Envelope small membrane protein; E        | A3EXG8 1–79      |     79 | sM protein                           |
| `N`          | Nucleoprotein; N                          | A3EXH0 1–468     |    468 | Nucleocapsid protein, NC             |

Names: the 220-residue A3EXG7, named `nsp3` in Drakkar, is the accessory protein of gene 3: `ns3`.

## Bat coronavirus HKU4 (*Betacoronavirus tylonycteridis*, NCBI 3433776)

| Generic name | Protein (UniProt name; gene)              | Reference     |      Length | Also called                          |
| ------------ | ----------------------------------------- | ------------- | ----------: | ------------------------------------ |
| `S`          | Spike glycoprotein; S (whole polyprotein) | A3EX94 1–1352 | 1,350–1,352 | S glycoprotein, E2, peplomer protein |
| `E`          | Envelope small membrane protein; E        | A3EX99 1–82   |          82 | sM protein                           |

## Pangolin coronavirus (NCBI 2708335)

| Generic name | Protein (UniProt name; gene)                                                | Reference               |      Length | Also called          |
| ------------ | --------------------------------------------------------------------------- | ----------------------- | ----------: | -------------------- |
| `S`          | — (no Swiss-Prot entry); spike glycoprotein, 92 % identical to SARS-CoV-2 S | P0DTC2 1–1273 (nearest) | 1,265–1,267 | Surface glycoprotein |

## Bat SARS CoV Rs806/2006 (NCBI 663565)

| Generic name | Protein (UniProt name; gene)                  | Reference                  | Length | Also called |
| ------------ | --------------------------------------------- | -------------------------- | -----: | ----------- |
| `nsp13`      | — (no Swiss-Prot entry); helicase nsp13 chain | P0C6W6 5300–5900 (nearest) |    601 | Hel         |

## Porcine deltacoronavirus (*Deltacoronavirus suis*, NCBI 3433742)

| Generic name | Protein (UniProt name; gene)                | Reference                 | Length | Also called          |
| ------------ | ------------------------------------------- | ------------------------- | -----: | -------------------- |
| `S`          | — (no Swiss-Prot entry); spike glycoprotein | X2G836 1–1,160 (TrEMBL)   |  1,160 | Spike glycoprotein   |
| `NS6`        | — (no Swiss-Prot entry); TrEMBL gene NS6    | A0A0E3Y5V9 1–94 (TrEMBL)  |     94 | NS6 protein          |
| `N`          | — (no Swiss-Prot entry); nucleoprotein      | A0A0E3N3M9 1–342 (TrEMBL) |    342 | Nucleocapsid protein |

Names: no Swiss-Prot entry for any deltacoronavirus protein of this virus; `S` and `N` follow the family, `NS6` its TrEMBL gene name.

## Swine acute diarrhea syndrome coronavirus (NCBI 2032731)

| Generic name | Protein (UniProt name; gene)           | Reference                 | Length | Also called          |
| ------------ | -------------------------------------- | ------------------------- | -----: | -------------------- |
| `N`          | — (no Swiss-Prot entry); nucleoprotein | A0A2P1G739 1–375 (TrEMBL) |    375 | Nucleocapsid protein |

## Swine enteric alphacoronavirus (NCBI 2045491)

| Generic name | Protein (UniProt name; gene)           | Reference                                    | Length | Also called          |
| ------------ | -------------------------------------- | -------------------------------------------- | -----: | -------------------- |
| `N`          | — (no Swiss-Prot entry); nucleoprotein | A0A5B9Y683 1–375 (obsolete snapshot 2020_05) |    375 | Nucleocapsid protein |

## Bat coronavirus (*Alphacoronavirus rhinolophi*, NCBI 3433795)

| Generic name | Protein (UniProt name; gene)           | Reference                 | Length | Also called          |
| ------------ | -------------------------------------- | ------------------------- | -----: | -------------------- |
| `N`          | — (no Swiss-Prot entry); nucleoprotein | A0A2S1WCF9 1–375 (TrEMBL) |    375 | Nucleocapsid protein |

## SARS-like coronavirus BatCoV/BB9904/BGR/2008 (NCBI 1737344)

| Generic name | Protein (UniProt name; gene)                | Reference                | Length | Also called        |
| ------------ | ------------------------------------------- | ------------------------ | -----: | ------------------ |
| `S`          | — (no Swiss-Prot entry); spike glycoprotein | P59594 14–1255 (nearest) |  1,262 | Spike glycoprotein |
