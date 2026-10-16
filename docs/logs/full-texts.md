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

## 2026-10-15, run 80 (4 publications)

| PMID     |   Fetch | Outcome                                                                                                                                |
| -------- | ------: | -------------------------------------------------------------------------------------------------------------------------------------- |
| 37478010 |  ~3 min | DiVA repository PDF (8.3 MB, about 60 KB/s), no supplementary files; Cell Reports' DOI page gave 0 words, its PDF 403, DOAJ 403        |
| 37480566 | seconds | PMC open access files: XML (NIHMS author manuscript); its 5 `.xlsx` and supplementary figures PDF are not in the PMC open access files |
| 37550507 | seconds | PMC open access files: XML, PDF, 4 supplementary files (2 `.mp4` left out)                                                             |
| 37628973 | seconds | PMC open access files: XML, PDF, 1 supplementary PDF from a zip                                                                        |

- The 30 s timeout bounds each network read, not a whole download: a slow server that keeps sending holds the fetch for minutes, and the next PMIDs wait behind it.
- One supplementary PDF of 37550507 (`MOESM2`) converted to 74 characters: no text layer to speak of.

## 2026-10-15, run 81 (20 publications)

13 full texts, all from the PMC open access files; 7 closed. The 20 fetches ran at once, in about 6 minutes.

| Closed   | Source                | Outcome                                                                                                                            |
| -------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 37656811 | Wiley, PMC10510470    | 403 on the DOI and on `pdfdirect`; the PMC copy is outside the open access files, `fullTextXML` 500                                |
| 37661566 | Wiley                 | 403 on both                                                                                                                        |
| 37658919 | Springer              | no open access location in OpenAlex: no URL was tried at all                                                                       |
| 37682346 | Springer, PMC11072444 | outside the PMC open access files, `fullTextXML` 500                                                                               |
| 37684534 | Springer              | not in OpenAlex: no URL was tried at all                                                                                           |
| 37673357 | Elsevier              | the DOI answered HTTP 200 with 0 words                                                                                             |
| 37695057 | ASM, PMC10537728      | outside the PMC open access files, `fullTextXML` 500; the HAL record holds no file (landing page 174 words, `/document` not a PDF) |

- Europe PMC answered HTTP 500, not 404, on all three PMCIDs outside the open access files: a 500 there says nothing about the article.
- Six of the seven closed publications are Springer, Wiley or Elsevier, each with a text and data mining API keyed to an institution; the seventh (ASM) is reachable only through its PMC copy.
- Conversion refused 5 supplementary files: a `.pptx` (no converter), 2 image-only PDFs (no text layer) and 2 GraphPad `.pzfx` (no converter). All five hold figures or raw curves, so none of them carries an interaction.
