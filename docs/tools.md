# Tools

Descriptions and publication states are written only through these tools, from files; full texts are fetched and converted by the tools of the last section. What a write checks and does: `database.md` §2; what a right description is: `curation-rules.md`.

## Files

JSON Lines: one JSON object per line, with every key of its format and no other, its values in JSON types. No header: an empty file has no row. Every row names its publication by its PMID: a file holds one publication or many, and files concatenate with `cat`. In a value, JSON escapes only `"` (`\"`), `\` (`\\`) and line breaks (`\n`). A line with a missing or unknown key, or a value of the wrong type, is refused with its file and line. Notes follow `notes.md`.

**Descriptions to add** (`*.jsonl`), one line per new description:

| Key | Content |
| -- | -- |
| `pmid` | the publication, a number, in its vh run |
| `method` | PSI-MI ID |
| `accession1` | human interactor; gene name and full-length coordinates come from its snapshot |
| `accession2`, `start2`, `stop2` | viral interactor; `start2` and `stop2` numbers, or null for the full protein |
| `name2` | generic name |
| `mappings1`, `mappings2` | lists of mapping sequences, extra end residues in lowercase (`mSTNPK`: `nter` M); occurrences are computed at write time |
| `below_threshold` | list of the mapping sequences kept below 90 % identity, explained in the note |
| `note` | the description note |

```json
{"pmid": 35939498, "method": "MI:0007", "accession1": "Q13501", "accession2": "P29990", "start2": null, "stop2": null, "name2": "C", "mappings1": [], "mappings2": ["mSTNPK", "mDREMA"], "below_threshold": [], "note": "anti-tag co-IP (MI:0007), Fig. 2B and 5C\n- Entry: ..."}
```

**Revisions** (`*.revise.jsonl`, `*.delete.jsonl`), one line per revised or removed description:

| Key | Content |
| -- | -- |
| `stable_id`, `version` | the description and the live version the decision was made on, a number; refused if it is no longer live |
| `pmid` | its publication, a number |
| `action` | `revise` (new version) or `remove` (no successor) |
| `into` | on a `remove` that merges a duplicate: the stable ID of the survivor, otherwise null; the description keys may then give what the removed description was decided to become, checked against the survivor |
| description keys | on a `revise`: the whole new description, the keys of the descriptions to add from `method` to `below_threshold`; on a `remove`, null |
| `note` | `revise`: the note of the new version (the curation's note from `drakkar-diff`, `UPDATED` in a versioning pass, `FIXED` for a fix); `remove`: its `REMOVED` line |

**Publications** (`*.jsonl`), one line per publication whose state or note changes: `pmid`, a number, the publication in its vh run; `state`, `selected` or `curated`; `note`, the note of the pass. The write puts it first in the publication's note, after the date (`[2026-10-22] CURATED: …`), the previous notes after a line `---`.

```json
{"pmid": 35939498, "state": "curated", "note": "CURATED: co-IP of HSV-1 gE with ANXA1\n- Not kept: ..."}
```

## Tools

Writes go through these commands. Without `--commit`, a command is a dry run: it applies its files, checks every invariant on the whole database in the same transaction, prints the result, and rolls back. With `--commit`, it commits only if nothing is refused and the check finds no error (`database.md` §2).

- `uv run drakkar-add <file> [--commit]`: adds descriptions.
- `uv run drakkar-revise <file> [--commit]`: revisions and removals, checked on the result of all the rows, so a change that passes through an inconsistent state is fine (a rename carried by several descriptions, a fix plus a merge).
- `uv run drakkar-publications <file> [--commit]`: publication states and notes.

They take several files at once.

- `uv run drakkar-notes <dir>`: writes `<dir>/publications.jsonl` from the publication notes of a curation batch, each `<dir>/<pmid>/curation.txt`, plain text, as written: one row per note, the PMID its directory's name, the state `selected` when the note starts with `SELECTED`, `curated` otherwise; an empty note gives no row. It never refuses a note.
- `uv run drakkar-batch <dir> [--commit]`: writes a batch from the files of its directory: `descriptions.jsonl`, the descriptions to add of a curation batch; `descriptions.add.jsonl`, `descriptions.revise.jsonl` and `descriptions.delete.jsonl`, the files `drakkar-diff` writes beside a `descriptions.jsonl`, the first read in place of `descriptions.jsonl` when it is there; and `publications.jsonl`. A missing descriptions file has no rows. One transaction, in this order: the revisions and removals, the new descriptions, the publication states and notes. Every invariant is checked once, on the result, so a row can rely on an earlier one (an addition on a rename). Refused rows are reported with their file and line.
- `uv run drakkar-diff <pmid> <file>`: read-only. Diffs the descriptions of the file (descriptions to add, all of one publication) against the live descriptions of that publication in its vh run, and writes beside the file `<name>.add.jsonl`, the descriptions that are not live; `<name>.revise.jsonl`, the live descriptions with another generic name or other mapping sequences, as `revise` rows; `<name>.delete.jsonl`, the live descriptions the file does not hold, as `remove` rows. Descriptions are matched on their method and interactors, empty coordinates being the full protein; `below_threshold` follows from the mappings and is not compared. An empty file puts every live description of the publication in `<name>.delete.jsonl`.
- `uv run drakkar-check <dir>`: checks every invariant, read-only.

Reading, `drakkar-read`, read-only, on the current snapshots. Each command takes many inputs; `entry` prints a block per entry, the others tab-separated lines under one `#` header line naming the columns, each line starting with the input it answers (`(none)` when nothing is found), the best first. `--limit <n>` bounds the lines per input (20); a list that is cut ends with a line `… 20 of 622 shown, cut by --limit 20`. A text matches as a substring, case aside, except in `methods`. A taxon is given by its NCBI ID and covers its whole subtree; it is written `<ID> <name>`, a lineage `<ID> <name> < …` up to the family. A stretch of a protein is written `<accession>:<start>-<stop>`, then `obsolete` when its snapshot is (its generic name stays reusable, its entry does not). An input that cannot be read gets its own line, with why.

- `uv run drakkar-read methods <text>...`: the PSI-MI terms with a name or a synonym that holds each word of the text, case and punctuation aside (`biolayer interferometry` finds `bio-layer interferometry`), the closest names first, then the detection methods (MI:0001), then the most used: PSI-MI ID, name (with the synonym matched), `is_detection`, live descriptions.
- `uv run drakkar-read taxon <text>...`: the taxa one of whose names contains each text, the closest names first: the taxon (with the name matched), its rank, its lineage.
- `uv run drakkar-read entry <accession>...`: each entry's snapshots, lineage, isoforms, UniProt names, chains, peptides, propeptides and regions, and for a viral entry the generic names of its live descriptions, each with its span and its live descriptions, snapshot by snapshot; for a secondary accession, the entry that holds it.
- `uv run drakkar-read search <text>... [--taxon <ID>]`: the entries whose `search` text (accession, gene names, taxon, protein name) contains each text, under the taxon when given, Swiss-Prot first: accession, `SP` (Swiss-Prot) or `TR` (TrEMBL), gene name, protein name, taxon, length. An entry whose taxon is missing from the NCBI taxonomy is found without `--taxon`, or with its own taxon ID.
- `uv run drakkar-read seq <accession>[:<start>-<stop>]...`: the sequence of each entry or isoform, or between those coordinates (1-based, inclusive).
- `uv run drakkar-read names <taxon ID>...`: the generic names of the viral interactors of live descriptions under each taxon, the most used first, with their live descriptions and their three most used interactors, on any snapshot.
- `uv run drakkar-read sql <query> --limit <n>`: free SQL for what no command gives, on a read-only connection where each statement stops after 30 seconds: its rows as tab-separated lines under a `#` header of column names, each cell cut at 200 characters. Never cut: `--limit` is required, and a query that returns more rows is refused, with no row printed. Written from the tables of `database.md` §1.

## Releases

A UniProt release is loaded in three commands, each in one transaction (without `--commit`, a dry run that rolls back), on a directory `data/<release>/` named after the release: `taxonomy/` (the NCBI taxdump loaded with this release), `uniprot/` (the FTP files and their parsed TSV) and `reports/`. Sources: NCBI `taxdump.tar.gz`; UniProt FTP `uniprot_sprot_human.xml.gz`, `uniprot_sprot_viruses.xml.gz`, `uniprot_trembl_viruses.xml.gz` and `uniprot_sprot_varsplic.fasta.gz` (isoforms). What a release does to the snapshots: `database.md` §3.

- `uv run drakkar-taxonomy data/<release> [--commit]`: the NCBI taxonomy, first; merged taxa are resolved with `merged.dmp`.
- `uv run drakkar-uniprot parse data/<release>`: the UniProt XML to TSV (cached).
- `uv run drakkar-uniprot upgrade data/<release> [--commit]`: the import; it writes `reports/uniprot_upgrade.md` (with the entries whose taxon is missing from the taxonomy) and `reports/obsolete_vh_descriptions.tsv`.

## Alignments

Read-only, on the sequences Drakkar holds.

- `uv run drakkar-align mapping <accession>[:<start>-<stop>] <sequence>...`: what the write computes for each mapping sequence (extra end residues in lowercase) on that interactor, by its own code (`align.py`, `database.md`): its extra end residues, its occurrences on each isoform with their identity, in the entry's numbering, and `ok`, `below 90 %` or `aligns nowhere`. One interactor per call: an accession among the sequences is refused.
- `uv run drakkar-align closest <sequence>... --taxon <ID>`: the entries of the taxon closest to each sequence (given as is, or as `<accession>[:<start>-<stop>]`), by a database search: every isoform is aligned on the sequence (Smith-Waterman, BLOSUM62, gap open 11, extension 1, by pyopal), and each entry is ranked by the score of its best isoform, then Swiss-Prot first: accession, `SP` or `TR`, protein name, taxon, identity (identical residues over the aligned columns, gaps included), coverage (the part of the sequence aligned), aligned region (`1-15` on the canonical isoform, `<isoform>:1-15` on another). Bounded by `--limit <n>`, as `drakkar-read`.

## NCBI sequences

A strain UniProt lacks is read at NCBI (GenBank, RefSeq), for the mappings taken from its sequence (`curation-rules.md` §3). Read-only, no database; the record used is named in the description note.

- `uv run drakkar-genbank search <query>... [--limit <n>]`: the NCBI protein records of each query, in NCBI search syntax (`JFH-1 AND polyprotein`, `"Hepatitis C virus JFH-1"[Organism]`), or of a nucleotide accession (a genome: the proteins it codes for), bounded and counted as `drakkar-read`: accession and version, title, length, NCBI taxon.
- `uv run drakkar-genbank seq <accession>[:<start>-<stop>]...`: a protein record: its accession and version, title, length and sequence, or the subsequence between those coordinates (1-based, inclusive); a nucleotide record (a genome): its coding sequences, one line each, with the protein accession to read with `seq`.

## Full texts

A full text is fetched and converted by these tools, then read from the files they write.

- `uv run drakkar-fetch <pmid> <dir>`: downloads the full text as published, in three steps. Each step is a list of routes, each route answering yes or no by one test.

  1. **Access**: the article is free when it has a PMCID, when OpenAlex or Unpaywall list a free copy, or when the publisher's page (at the DOI) declares free access (`"isAccessibleForFree": true`, `<meta name="access" content="Yes">`, `citation_fulltext_world_readable`, or a link to the article's Creative Commons license, PLOS's only declaration); a declared paywall wins. Closed otherwise. A preprint is never a copy of the article: its copies, its DOI and a PMC copy of it (known by its own DOI) are never fetched.
  2. **The article**, one file, from the first route that gives it: the PMC open access files, Europe PMC `fullTextXML`, NCBI `efetch` (each when its XML has a body); the PMC article page, which serves the PMC copies outside the open access files (when it has the body sections; one page per publication, as NCBI forbids bulk downloads); the publisher's HTML page (when it declares free access; a page that declares a paywall is never the article); then, last, the publisher's PDF (`citation_pdf_url`) and the other free copies' PDFs (when the file is a PDF).
  3. **The supplementary files**, as the article lists them: its XML, the supplementary sections of the PMC page, or else the supplementary links of the publisher's page. Each is looked for on every route that serves one, whatever route gave the article: the PMC open access files, the link the article gives (never the PMC website's, which is behind a challenge), the publisher's page, then Europe PMC's supplementary files service. Archives are unpacked. A video, an image, the Reporting Summary and the peer review file (both by their caption) are skipped.

  Unpaywall is asked only with an address, `UNPAYWALL_EMAIL` in the project's `.env`. It writes the article, `<pmid>.xml`, `<pmid>.html` or `<pmid>.pdf`, and the supplementary files in `<pmid>.supp/`, each converted as `drakkar-parse` does: the article to `<pmid>.md`, a supplementary file to `<file>.md` beside it. Last, only when the article could be converted, the manifest `manifest.json`, the files the curation can use: `article`, with `file`, the original, `text`, its text, and `bytes`, the size of the text; `supplements`, each with the `name` the article gives it, `file`, `text` and `bytes`. Paths are relative to `<dir>`. A publication directory set up from files the user provides holds the same: each file converted with `drakkar-parse`, and the manifest in this format, `bytes` optional.

  It prints its report. First a line saying where the article comes from: `Full text: <PMCID> (<license>)` or `Full text: <source> (<license>, <URL>)`, ending with `, supplementary files missing: <names>` when some are; without the article, `Full text: closed — <why>`, or `Full text: not downloaded — <why>` when it is free but no copy could be downloaded, then every route tried with its outcome. Then one line per file that could not be converted, with why, and per supplementary file missing, with every place tried.

- `uv run drakkar-download <url> <dir>`: the file at a URL, a supplementary file the article links to: saved in `<dir>` (the type from the response when its name gives none), an archive unpacked (its videos and images left out), each file converted to `<file>.md` beside it, as `drakkar-parse` does. One line per file: its text, or why it could not be had (the HTTP outcome, not converted).

- `uv run drakkar-parse <file> <out>`: converts one file to text, by its type: PMC XML to Markdown (title, abstract, sections, captions, tables and supplementary materials; references, acknowledgements, notes and peer reviews left out), a PMC article page by its structure, as its XML (the same blocks, the back matter left out), any other HTML page to the Markdown of its main text, a Word document (`.docx`, or `.doc` from Word 97-2003) to Markdown, a PDF to its text page by page (`--- page N ---`), a spreadsheet (`.xlsx`, `.xls`) to one TSV block per sheet, CSV and plain text as they are. A scanned PDF, a damaged file, an image or any other type is refused with the reason, and nothing is written. No network.
