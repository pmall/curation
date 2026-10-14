# Full texts: the fetch and the conversion at work

Cases spotted with `drakkar-fetch` and `drakkar-parse` on real publications: failures, wrong conversions, timings, dated. The tools are improved from them.

## 2026-10-14, first runs (by hand)

| PMID     | Fetch | Outcome                                                                                       |
| -------- | ----: | --------------------------------------------------------------------------------------------- |
| 22046132 | 6.6 s | PMC open access files: XML, PDF, 6 supplementary `.doc` (3 `.tif` left out)                   |
| 41542592 | 5.9 s | PMC open access files: XML, PDF, 1 supplementary PDF (an archive of movies left out)          |
| 40060511 | 2.0 s | closed: eLife's page is rendered by JavaScript; its PMC copy is outside the open access files |
| 41279199 | 1.4 s | closed: Cell Reports, the DOI leads to an Elsevier redirect page                              |
| 42678594 | 2.6 s | Springer PDF                                                                                  |
| 42687756 | 1.3 s | closed: Oxford University Press refuses the download (403)                                    |
| 40455154 | 0.7 s | closed: not open access anywhere                                                              |

- Conversion: 0.4 to 0.7 s per file, the 12 files fetched above. Size of the text against the original, in characters: PMC XML 136,687 → 52,507 (62 % shorter) and 196,346 → 51,412 (74 %); a PLOS HTML page 282,348 → 65,459 (77 %).
- Old `.doc` tables: rows are cut where Word ends them, from the paragraph properties (some stored in the Data stream); a cell spanning two columns is aligned on the cell edges of the fullest row. The 6 `.doc` of PMID 22046132: every row has its table's width (88 rows of 9 columns for the Y2H table).
- Europe PMC's supplementary files service sends about 50 KB/s (a 5 MB archive took minutes): PMC files come from the PMC open access files on AWS instead.
- The PMC website refuses downloads; MDPI refused one (403); bioRxiv answered 429 to repeated requests, before preprints were left out.
- OpenAlex's version labels are unreliable (a bioRxiv copy labelled accepted, PMC copies labelled submitted).
