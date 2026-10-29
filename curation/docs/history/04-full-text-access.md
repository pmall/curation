# Full-text access, measured on run 87 (2026-10-05)

Run 87: 2,328 PMIDs.

| Category | PMIDs | `selected` | What Claude can download |
| -- | -: | -: | -- |
| PMC, open access subset | 1,289 | 114 | Structured XML through the APIs (Europe PMC `fullTextXML`, NCBI BioC, PMC OA). |
| PMC, not open access (incl. manuscripts) | 58 | 2 | Readable on the web only; text mining not allowed, so not accessible. |
| PMC, bioRxiv preprint | 134 | 1 | Not peer-reviewed: discarded at pre-curation anyway. |
| Not in PMC, open access elsewhere | 322 | 25 | Publisher, repository or preprint copy; plain download worked for 6 of the 25. |
| Not in PMC, not open access | 525 | 27 | Abstract only. |

Open access status outside PMC comes from OpenAlex. Most failed downloads were Elsevier (redirect pages; Elsevier has a text-mining API with a free key), PNAS and Taylor & Francis (HTTP 403).

Publications reach PMC with a lag: 75–84 % of the publications of runs 70–79 (2022–2023) are in PMC today, against 60–67 % for runs 80–87.
