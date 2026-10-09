# Retroviridae

Family conventions: polyproteins take their gene name (`Gag`, `Gag-Pol`, `Gag-Pro-Pol`, `Pol`, `Env`). Gag and Pol products use the UniProt short names (`MA`, `CA`, `NC`, `PR`, `IN`). Where UniProt gives a mass name, the envelope subunits use it, as the field does (`gp120`, `gp41`, `gp21`, `p15E`). Accessory and regulatory proteins keep the UniProt spelling (`Vif`, `Vpr`, `Vpx`, `Tax-1`, `p30II`).

## Human immunodeficiency virus 1 (*Lentivirus humimdef1*, NCBI 3418650)

| Generic name | Protein (UniProt name; gene)                                                      | Reference               |      Length | Also called                             |
| ------------ | --------------------------------------------------------------------------------- | ----------------------- | ----------: | --------------------------------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein)                                          | P04591 1–500            |     500–512 | Pr55Gag                                 |
| `MA`         | Matrix protein p17; gag                                                           | P04591 2–132            |         131 | p17                                     |
| `CA`         | Capsid protein p24; gag                                                           | P04591 133–363          |         231 | p24                                     |
| `CA-NC`      | Capsid protein p24 to nucleocapsid protein p7; gag (joined chains)                | P04591 133–432          |         300 | —                                       |
| `NC`         | Nucleocapsid protein p7; gag                                                      | P04591 378–432          |          55 | p7                                      |
| `SP2`        | Spacer peptide 2; gag                                                             | P03348 433–448          |          16 | p1                                      |
| `p6`         | p6-gag; gag                                                                       | P04591 449–500          |       52–64 | p6-gag                                  |
| `NC-p6`      | Nucleocapsid protein p7 to transframe region, on Gag-Pol; gag-pol (joined chains) | P04585 378–488          |         111 | —                                       |
| `Gag-Pol`    | Gag-Pol polyprotein; gag-pol (whole polyprotein)                                  | P04585 1–1435           | 1,434–1,447 | Pr160Gag-Pol                            |
| `Pol`        | Pol polyprotein; pol (no Swiss-Prot entry; whole polyprotein)                     | Q74085 1–1,015 (TrEMBL) | 1,003–1,015 | —                                       |
| `PR`         | Protease; gag-pol                                                                 | P04585 489–587          |          99 | Protease, Retropepsin                   |
| `p66 RT`     | Reverse transcriptase/ribonuclease H; gag-pol                                     | P04585 588–1147         |         560 | RT, Exoribonuclease H                   |
| `p51 RT`     | p51 RT; gag-pol                                                                   | P04585 588–1027         |         440 | RT                                      |
| `IN`         | Integrase; gag-pol                                                                | P04585 1148–1435        |         288 | Integrase                               |
| `Vif`        | Virion infectivity factor; vif                                                    | P69723 1–192            |         192 | SOR protein                             |
| `Vpr`        | Protein Vpr; vpr                                                                  | P69726 1–96             |       95–97 | Viral protein R, R ORF protein          |
| `Tat`        | Protein Tat; tat                                                                  | P04608 1–86             |      72–106 | Transactivating regulatory protein      |
| `Rev`        | Protein Rev; rev                                                                  | P04618 1–116            |         116 | ART/TRS, Anti-repression transactivator |
| `Vpu`        | Protein Vpu; vpu                                                                  | P05919 1–82             |       74–85 | Viral protein U, U ORF protein          |
| `Env`        | Envelope glycoprotein gp160; env (whole polyprotein)                              | P04578 1–856            |     847–912 | gp160, Env polyprotein                  |
| `gp120`      | Surface protein gp120; env                                                        | P04578 33–511           |     467–484 | SU                                      |
| `gp41`       | Transmembrane protein gp41; env                                                   | P04578 512–856          |     343–346 | TM                                      |
| `Nef`        | Protein Nef; nef                                                                  | P04601 1–206            |     200–239 | Negative factor, F-protein, 3'ORF       |
| `ASP`        | Antisense protein; asp (no Swiss-Prot entry)                                      | I3QK15 1–189 (TrEMBL)   |         189 | —                                       |

Names:

- `Env`, not `gp160`: the gene name, like `Gag` and `Gag-Pol`. `gp120` and `gp41` (UniProt alternative names), not `SU` and `TM`: the names the field uses.
- `p66 RT` and `p51 RT`: the UniProt names of the two RT chains (p51 is the N-terminal 440 residues of p66). `PR`: UniProt alternative name.
- `SP2`, not `p1`: UniProt short name. `p6`: UniProt full name "p6-gag", the field says p6.
- `Pol` and `ASP`: no Swiss-Prot entry; TrEMBL gene names.
- `NC-p6` on Gag-Pol (P04585 378–488) covers NC and the Gag-Pol transframe region, not the p6 of Gag.
- `Tat`: one-exon (86) and two-exon (101) forms are the same protein.

## Human T-cell leukemia virus 1 (*Deltaretrovirus priTlym1*, NCBI 3428212)

| Generic name  | Protein (UniProt name; gene)                             | Reference        |  Length | Also called                               |
| ------------- | -------------------------------------------------------- | ---------------- | ------: | ----------------------------------------- |
| `Gag`         | Gag polyprotein; gag (whole polyprotein)                 | P03345 1–429     |     429 | Pr53Gag                                   |
| `MA`          | Matrix protein p19; gag                                  | P03345 2–130     |     129 | p19                                       |
| `Gag-Pro-Pol` | Gag-Pro-Pol polyprotein; gag-pro-pol (whole polyprotein) | P14078 1–1462    |   1,462 | Pr160Gag-Pro-Pol                          |
| `IN`          | Integrase; gag-pro-pol                                   | P03362 1168–1462 |     295 | Integrase                                 |
| `Env`         | Envelope glycoprotein gp62; env (whole polyprotein)      | P23064 1–488     |     488 | gp62, Env polyprotein                     |
| `gp21`        | Transmembrane protein; env                               | P23064 313–488   | 176–177 | TM, Glycoprotein 21                       |
| `Tax-1`       | Protein Tax-1; tax                                       | P03409 1–353     | 352–353 | Tax, Tax1, p40, Protein PX, Protein X-LOR |
| `Rex`         | Protein Rex                                              | P0C205 1–189     |     189 | Rex-1, p27Rex                             |
| `p12I`        | Accessory protein p12I                                   | P0C215 1–99      |      99 | p12                                       |
| `p30II`       | Accessory protein p30II                                  | P0C214 1–241     |     241 | p30                                       |
| `HBZ`         | HTLV-1 basic zipper factor; HBZ                          | P0C746 1–209     | 172–209 | —                                         |

Names:

- `Tax-1`: UniProt writes "Tax-1" (and "Tax-2", "Tax-3"), with a hyphen; Drakkar writes `Tax1`.
- `Rex`: the full name ends in "Rex"; Rex-1 is an alternative name only.
- `p12I`, `p30II`: the UniProt names; the field often says p12 and p30. p8 is a cleavage product of p12I with no chain in UniProt.
- `gp21`, like `gp41` in HIV-1.

## Simian immunodeficiency virus (*Lentivirus simimdef*, NCBI 3418654)

| Generic name | Protein (UniProt name; gene)                         | Reference        |  Length | Also called                       |
| ------------ | ---------------------------------------------------- | ---------------- | ------: | --------------------------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein)             | Q02843 1–513     |     513 | Pr55Gag                           |
| `MA`         | Matrix protein p17; gag-pol                          | P05896 2–135     |     134 | p17                               |
| `CA`         | Capsid protein p24; gag                              | P19505 136–365   | 229–230 | p24                               |
| `NC`         | Nucleocapsid protein p7; gag-pol                     | P05895 377–443   |      67 | p7                                |
| `IN`         | Integrase; gag-pol                                   | P05896 1156–1448 | 236–293 | Integrase                         |
| `Vif`        | Virion infectivity factor; vif                       | P05902 1–214     | 214–238 | Q protein, SOR protein            |
| `Vpx`        | Protein Vpx; vpx                                     | P05917 1–112     |  99–119 | Viral protein X, X ORF protein    |
| `Vpr`        | Protein Vpr; vpr                                     | P12521 1–89      |  89–135 | Viral protein R, R ORF protein    |
| `Vpu`        | Protein Vpu; vpu                                     | Q1A244 1–79      |   76–79 | Viral protein U, U ORF protein    |
| `Env`        | Envelope glycoprotein gp160; env (whole polyprotein) | P19503 1–889     | 854–889 | gp160, Env polyprotein            |
| `Nef`        | Protein Nef; nef                                     | P05861 1–247     |  92–263 | Negative factor, F-protein, 3'ORF |

Names: several SIV lineages in one species. Some TrEMBL Vpx entries are named "Protein Vpr" with gene vpx (Q6EZD7, E1ANU0, E1ANU9, Q7ZB17): gene and closest Swiss-Prot say Vpx.

## Human T-cell leukemia virus 2 (*Deltaretrovirus priTlym2*, NCBI 3428213)

| Generic name | Protein (UniProt name; gene)                                  | Reference             |  Length | Also called           |
| ------------ | ------------------------------------------------------------- | --------------------- | ------: | --------------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein)                      | P03346 1–433          |     433 | Pr53Gag               |
| `Pol`        | Pol polyprotein; pol (no Swiss-Prot entry; whole polyprotein) | Q82441 1–982 (TrEMBL) |     982 | —                     |
| `IN`         | Integrase; gag-pro-pol                                        | P03363 1167–1461      |     295 | Integrase             |
| `Env`        | Envelope glycoprotein gp63; env (whole polyprotein)           | P03383 1–486          |     486 | gp63, Env polyprotein |
| `gp21`       | Transmembrane protein; env                                    | P03383 309–486        | 178–195 | TM, Glycoprotein 21   |
| `Tax-2`      | Protein Tax-2; tax                                            | P03410 1–331          |     331 | Tax, Tax2             |
| `Rex`        | Protein Rex                                                   | Q85601 1–170          |     170 | Rex-2                 |
| `p28II`      | Protein 28 xII; xII (no Swiss-Prot entry)                     | Q80824 1–216 (TrEMBL) |     216 | p28, p28xII           |

Names: `p28II` has no Swiss-Prot entry; spelled like its HTLV-1 counterpart `p30II`.

## Human immunodeficiency virus 2 (*Lentivirus humimdef2*, NCBI 3418651)

| Generic name | Protein (UniProt name; gene)                         | Reference        |  Length | Also called                        |
| ------------ | ---------------------------------------------------- | ---------------- | ------: | ---------------------------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein)             | P18095 1–521     |     521 | Pr55Gag                            |
| `CA`         | Capsid protein p24; gag                              | P04590 136–365   |     230 | p24                                |
| `p6`         | p6-gag; gag                                          | P18095 446–521   |      76 | p6-gag                             |
| `IN`         | Integrase; gag-pol                                   | P04584 1172–1464 |     293 | Integrase                          |
| `Vif`        | Virion infectivity factor; vif                       | P04595 1–215     | 215–216 | Q protein, SOR protein             |
| `Vpx`        | Protein Vpx; vpx                                     | P06939 1–112     | 112–113 | Viral protein X                    |
| `Vpr`        | Protein Vpr; vpr                                     | P06938 1–105     |  87–105 | Viral protein R                    |
| `Tat`        | Protein Tat; tat                                     | P18098 1–130     |     130 | Transactivating regulatory protein |
| `Rev`        | Protein Rev; rev                                     | P04615 1–100     |     100 | —                                  |
| `Env`        | Envelope glycoprotein gp160; env (whole polyprotein) | P04577 1–858     | 858–860 | gp160, Env polyprotein             |
| `gp41`       | Transmembrane protein gp41; env                      | P04577 512–858   |     347 | TM                                 |
| `Nef`        | Protein Nef; nef                                     | P18092 1–257     | 256–257 | Negative factor                    |

## Murine leukemia virus (*Gammaretrovirus murleu*, NCBI 3428959)

| Generic name | Protein (UniProt name; gene)             | Reference           |  Length | Also called               |
| ------------ | ---------------------------------------- | ------------------- | ------: | ------------------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein) | P03332 1–538        | 536–538 | Pr65gag, Core polyprotein |
| `MA`         | Matrix protein p15; gag                  | Q2F7I9 2–129 (XMRV) | 128–134 | p15                       |
| `p12`        | RNA-binding phosphoprotein p12; gag      | P03332 132–215      |   84–85 | pp12                      |
| `CA`         | Capsid protein p30; gag                  | P03332 216–478      |     263 | p30                       |
| `IN`         | Integrase; gag-pol                       | P03355 1331–1738    |     408 | p46                       |
| `p15E`       | Transmembrane protein; env               | P03385 470–649      | 180–187 | TM, Envelope protein p15E |

Names: `p15E` (UniProt alternative name), the name the field uses, like `gp41` and `gp21`. The MA reference is the XMRV entry (98 % identity), the only matrix chain in the packet.

## Bovine immunodeficiency virus (*Lentivirus bovimdef*, NCBI 3418645)

| Generic name | Protein (UniProt name; gene)                     | Reference        | Length | Also called     |
| ------------ | ------------------------------------------------ | ---------------- | -----: | --------------- |
| `Gag-Pol`    | Gag-Pol polyprotein; gag-pol (whole polyprotein) | P19560 1–1475    |  1,475 | Pr170Gag-Pol    |
| `IN`         | Integrase; gag-pol                               | P19560 1194–1475 |    282 | Integrase       |
| `Vif`        | Virion infectivity factor; vif                   | P19563 1–198     |    198 | Q protein       |
| `Rev`        | Protein Rev; rev                                 | P24097 1–186     |    186 | —               |
| `Env`        | Envelope glycoprotein; env (whole polyprotein)   | P19557 1–904     |    904 | Env polyprotein |

## Equine infectious anemia virus (*Lentivirus equinfane*, NCBI 3418648)

| Generic name | Protein (UniProt name; gene)                   | Reference            |      Length | Also called     |
| ------------ | ---------------------------------------------- | -------------------- | ----------: | --------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein)       | P69732 1–486         |     486–512 | —               |
| `CA`         | Capsid protein p26; gag                        | P69732 125–354       |         230 | p26             |
| `p9`         | p9; gag                                        | P69732 436–486       |          51 | —               |
| `Pol`        | Pol polyprotein; pol (whole polyprotein)       | P32542 1–1146        | 1,138–1,146 | —               |
| `IN`         | Integrase; pol                                 | P03371 914–1145      |      31–232 | Integrase       |
| `S2`         | S2 protein; s2 (no Swiss-Prot entry)           | Q992K0 1–68 (TrEMBL) |          68 | —               |
| `Rev`        | Protein Rev; rev                               | P32543 1–165         |     135–165 | 3'-ORF protein  |
| `Env`        | Envelope glycoprotein; env (whole polyprotein) | P11306 1–859         |         859 | Env polyprotein |

Names: EIAV has a separate Pol polyprotein in Swiss-Prot. `S2`: TrEMBL gene name.

## Visna-maedi virus (*Lentivirus ovivismae*, NCBI 3418652)

| Generic name | Protein (UniProt name; gene)   | Reference        | Length | Also called                 |
| ------------ | ------------------------------ | ---------------- | -----: | --------------------------- |
| `IN`         | Integrase; pol                 | P23426 1226–1506 |    281 | Integrase                   |
| `Vif`        | Virion infectivity factor; vif | P69716 1–230     |    230 | Q protein                   |
| `Tat`        | Probable Vpr-like protein; tat | P35958 1–94      |     94 | Protein S, Vpr-like protein |
| `Rev`        | Protein Rev; rev               | P35957 1–167     |    167 | —                           |

Names: `Tat`, the gene name and a UniProt alternative name, the name the field uses; UniProt's full name is "Probable Vpr-like protein".

## Simian foamy virus (NCBI 11642)

| Generic name | Protein (UniProt name; gene)                         | Reference    |  Length | Also called                                    |
| ------------ | ---------------------------------------------------- | ------------ | ------: | ---------------------------------------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein)             | P14349 1–648 |     648 | Pr71Gag                                        |
| `Env`        | Envelope glycoprotein gp130; env (whole polyprotein) | P14351 1–989 |     989 | gp130, Env polyprotein                         |
| `Tas`        | Protein Bel-1; bel1, tas                             | P14353 1–300 |     300 | Bel-1, bel1, Taf, Transactivator of spumavirus |
| `Bet`        | Protein Bet; bet                                     | P89873 1–482 | 482–490 | —                                              |

Names: `Tas`, UniProt alternative name and gene, the name the field now uses; `Bel-1` is the older name. References are the "Human spumaretrovirus" entries (prototype foamy virus).

## Bovine leukemia virus (*Deltaretrovirus bovleu*, NCBI 3428211)

| Generic name | Protein (UniProt name; gene)                   | Reference    |  Length | Also called     |
| ------------ | ---------------------------------------------- | ------------ | ------: | --------------- |
| `Env`        | Envelope glycoprotein; env (whole polyprotein) | P51519 1–515 |     515 | Env polyprotein |
| `Tax`        | Putative uncharacterized protein PXBL-I        | P03412 1–308 | 308–309 | p34, PXBL-I     |

Names: `Tax`: the Swiss-Prot entry has no usable name; TrEMBL gene tax, the field's name.

## Avian leukosis virus (*Alpharetrovirus avileu*, NCBI 3426267)

| Generic name | Protein (UniProt name; gene)                                   | Reference        | Length | Also called |
| ------------ | -------------------------------------------------------------- | ---------------- | -----: | ----------- |
| `p2B`        | p2B; gag-pol                                                   | Q04095 167–177   |     11 | —           |
| `IN`         | Integrase; pol                                                 | Q7SQ98 1281–1567 |    287 | pp32        |
| `Ski`        | Transforming protein Ski; V-SKI (avian erythroblastosis virus) | P17863 1–437     |    437 | v-Ski       |

Names: `Ski`: the full name ends in "Ski"; UniProt gives no "v-Ski".

## Walleye dermal sarcoma virus (*Epsilonretrovirus waldersar*, NCBI 3428561)

| Generic name | Protein (UniProt name; gene) | Reference    | Length | Also called                  |
| ------------ | ---------------------------- | ------------ | -----: | ---------------------------- |
| `Rv-cyclin`  | Retroviral cyclin; orfA      | Q88939 1–297 |    297 | ORF-A protein, orfA, vCyclin |
| `ORF-B`      | ORF-B protein                | Q88940 1–306 |    306 | ORFB                         |

## Feline immunodeficiency virus (*Lentivirus felimdef*, NCBI 3418649)

| Generic name | Protein (UniProt name; gene)                         | Reference       |      Length | Also called            |
| ------------ | ---------------------------------------------------- | --------------- | ----------: | ---------------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein)             | P16087 1–450    |         450 | —                      |
| `CA`         | Capsid protein p24; gag                              | P16087 136–357  |         222 | p24                    |
| `Pol`        | Pol polyprotein; pol (whole polyprotein)             | P31822 1–1124   | 1,123–1,124 | —                      |
| `IN`         | Integrase; pol                                       | P16088 844–1124 |         281 | Integrase              |
| `Rev`        | Probable protein Rev; rev                            | P19032 1–153    |         153 | ART/TRS, ORF4, ORFH    |
| `Env`        | Envelope glycoprotein gp150; env (whole polyprotein) | P16090 1–856    |         856 | gp150, Env polyprotein |

## Feline leukemia virus (*Gammaretrovirus felleu*, NCBI 3428951)

| Generic name | Protein (UniProt name; gene)             | Reference        |  Length | Also called      |
| ------------ | ---------------------------------------- | ---------------- | ------: | ---------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein) | P10262 1–506     |     506 | Core polyprotein |
| `p12`        | RNA-binding phosphoprotein p12; gag      | P10262 128–197   |      70 | pp12             |
| `IN`         | Integrase; pol                           | P10273 1298–1712 | 415–416 | Integrase        |

## Human T-cell leukemia virus 3 (*Deltaretrovirus priTlym3*, NCBI 3428214)

| Generic name | Protein (UniProt name; gene)                        | Reference    | Length | Also called           |
| ------------ | --------------------------------------------------- | ------------ | -----: | --------------------- |
| `Env`        | Envelope glycoprotein gp63; env (whole polyprotein) | Q09SZ7 1–493 |    493 | gp63, Env polyprotein |
| `Tax-3`      | Protein Tax-3; tax                                  | Q4U0X7 1–350 |    350 | Tax, Tax3             |

## Mason-Pfizer monkey virus (*Betaretrovirus maspfimon*, NCBI 3427294)

| Generic name | Protein (UniProt name; gene)                     | Reference    | Length | Also called            |
| ------------ | ------------------------------------------------ | ------------ | -----: | ---------------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein)         | P07567 1–657 |    657 | Pr78, Core polyprotein |
| `MA`         | Matrix protein p10; gag                          | P07567 2–100 |     99 | p10                    |
| `Gag-Pro`    | Gag-Pro polyprotein; gag-pro (whole polyprotein) | P07570 1–911 |    911 | Pr95                   |

Names: `MA` as in the rest of the family; this entry gives no short name.

## Rous sarcoma virus (*Alpharetrovirus avirousar*, NCBI 3426270)

| Generic name | Protein (UniProt name; gene)                            | Reference    | Length | Also called             |
| ------------ | ------------------------------------------------------- | ------------ | -----: | ----------------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein)                | P03322 1–701 |    701 | —                       |
| `v-Src`      | Tyrosine-protein kinase transforming protein Src; V-SRC | P00526 1–526 |    526 | p60-Src, pp60v-src, src |

Names: `v-Src`, UniProt alternative name, the field's name.

## Gibbon ape leukemia virus (*Gammaretrovirus gibleu*, NCBI 3428953)

| Generic name | Protein (UniProt name; gene)             | Reference      | Length | Also called |
| ------------ | ---------------------------------------- | -------------- | -----: | ----------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein) | P21416 2–520   |    519 | —           |
| `p12`        | RNA-binding phosphoprotein p12; gag      | P21416 126–195 |     70 | pp12        |

## Koala retrovirus (*Gammaretrovirus koa*, NCBI 3428957)

| Generic name | Protein (UniProt name; gene)             | Reference      | Length | Also called |
| ------------ | ---------------------------------------- | -------------- | -----: | ----------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein) | Q9TTC2 2–521   |    520 | —           |
| `p12`        | RNA-binding phosphoprotein p12; gag      | Q9TTC2 129–196 |     68 | pp12        |

## Moloney murine sarcoma virus (*Gammaretrovirus momursar*, NCBI 3428958)

| Generic name | Protein (UniProt name; gene)             | Reference    |  Length | Also called      |
| ------------ | ---------------------------------------- | ------------ | ------: | ---------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein) | P03334 2–538 | 468–537 | Core polyprotein |

## Jembrana disease virus (*Lentivirus bovjem*, NCBI 3418646)

| Generic name | Protein (UniProt name; gene) | Reference    | Length | Also called |
| ------------ | ---------------------------- | ------------ | -----: | ----------- |
| `Tat`        | Protein Tat; tat             | Q82854 1–114 | 97–114 | jTat        |

## Bovine foamy virus (*Bovispumavirus bostau*, NCBI 3427599)

| Generic name | Protein (UniProt name; gene) | Reference             | Length | Also called |
| ------------ | ---------------------------- | --------------------- | -----: | ----------- |
| `Borf-1`     | Borf-1 (no Swiss-Prot entry) | Q86342 1–249 (TrEMBL) |    249 | ORF1, BTas  |

Names: `Borf-1`: TrEMBL name (Q86342); the bovine foamy virus transactivator, counterpart of `Tas`.

## Human immunodeficiency virus (NCBI 12721)

| Generic name | Protein (UniProt name; gene) | Reference              | Length | Also called           |
| ------------ | ---------------------------- | ---------------------- | -----: | --------------------- |
| `PR`         | Protease; gag-pol            | P12497 489–587 (HIV-1) |     99 | Protease, Retropepsin |

Names: the sequence is HIV-1 protease (99 % identity), named as in HIV-1.

## Jaagsiekte sheep retrovirus (*Betaretrovirus ovijaa*, NCBI 3427296)

| Generic name | Protein (UniProt name; gene)                   | Reference    | Length | Also called     |
| ------------ | ---------------------------------------------- | ------------ | -----: | --------------- |
| `Env`        | Envelope glycoprotein; env (whole polyprotein) | P31621 1–615 |    615 | Env polyprotein |

## Y73 avian sarcoma virus (*Alpharetrovirus aviY73sar*, NCBI 3426273)

| Generic name | Protein (UniProt name; gene)                 | Reference    | Length | Also called |
| ------------ | -------------------------------------------- | ------------ | -----: | ----------- |
| `Gag-yes`    | Gag-yes polyprotein; gag (whole polyprotein) | P03327 1–284 |    284 | —           |

## Caprine arthritis encephalitis virus (*Lentivirus capartenc*, NCBI 3418647)

| Generic name | Protein (UniProt name; gene)   | Reference    | Length | Also called                 |
| ------------ | ------------------------------ | ------------ | -----: | --------------------------- |
| `Vif`        | Virion infectivity factor; vif | P33462 1–229 |    229 | Q protein, SOR protein      |
| `Tat`        | Probable Vpr-like protein; tat | P21125 1–87  |     87 | Protein S, Vpr-like protein |

Names: `Tat` as in visna-maedi virus.

## UR2 avian sarcoma virus (*Alpharetrovirus aviUR2sar*, NCBI 3426272)

| Generic name | Protein (UniProt name; gene) | Reference    | Length | Also called     |
| ------------ | ---------------------------- | ------------ | -----: | --------------- |
| `p19`        | Core protein p19; gag        | P03324 1–150 |    150 | Gag protein p19 |

## Xenotropic MuLV-related virus (*Murine leukemia-related retroviruses*, NCBI 99182)

| Generic name | Protein (UniProt name; gene)             | Reference      | Length | Also called               |
| ------------ | ---------------------------------------- | -------------- | -----: | ------------------------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein) | Q2F7I9 1–536   |    536 | Pr65gag, Core polyprotein |
| `p12`        | RNA-binding phosphoprotein p12; gag      | Q2F7I9 130–213 |     84 | pp12                      |

## Simian-human immunodeficiency virus (NCBI 57667)

| Generic name | Protein (UniProt name; gene)             | Reference            |  Length | Also called |
| ------------ | ---------------------------------------- | -------------------- | ------: | ----------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein) | P05893 1–506 (SIV)   | 506–510 | Pr55Gag     |
| `Rev`        | Protein Rev; rev                         | P04618 1–116 (HIV-1) |     116 | ART/TRS     |

Names: a chimera: Gag is SIV, Rev is HIV-1.

## Abelson murine leukemia virus (NCBI 11788)

| Generic name | Protein (UniProt name; gene)             | Reference    | Length | Also called |
| ------------ | ---------------------------------------- | ------------ | -----: | ----------- |
| `Gag`        | Gag polyprotein; gag (whole polyprotein) | P03333 1–235 |    235 | —           |
