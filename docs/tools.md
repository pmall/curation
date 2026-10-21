# Tools

Descriptions and publication states are written only through these tools, from files; full texts are fetched and converted by the tools of the last section. What a write checks and does: `database.md` §2; what a right description is: `curation-rules.md`.

## Files

Tab separated. Lines starting with `#` are ignored (the header is one), so files concatenate with `cat`. Every row names its publication: a file holds one publication or many. Notes follow `notes.md`, with `\n` for line breaks. Sequences in a list are separated by `,`.

**Descriptions to add** (`*.add.tsv`), one row per new description:

| Column | Content |
| -- | -- |
| `run_id`, `pmid` | the publication |
| `method` | PSI-MI ID |
| `accession1` | human interactor; gene name and full-length coordinates come from its snapshot |
| `accession2`, `start2`, `stop2` | viral interactor |
| `name2` | generic name |
| `mappings1`, `mappings2` | mapping sequences, extra end residues in lowercase (`mSTNPK`: `nter` M); occurrences are computed at write time |
| `below_threshold` | mapping sequences kept below 90 % identity, explained in the note |
| `note` | the description note |

**Revisions** (`*.revise.tsv`), one row per revised description:

| Column | Content |
| -- | -- |
| `stable_id`, `version` | the description and the live version the decision was made on; refused if it is no longer live |
| `run_id`, `pmid` | its publication |
| `action` | `revise` (new version) or `remove` (no successor) |
| `into` | on a `remove` that merges a duplicate: the stable ID of the survivor; the description columns may then give what the removed description was decided to become, checked against the survivor |
| description columns | on a `revise`: the whole new description, as in `*.add.tsv`, from `method` to `below_threshold` |
| `note` | `revise`: the note of the new version (`UPDATED` in a versioning pass, `FIXED` for a fix); `remove`: its `REMOVED` line |

**Publications** (`*.publications.tsv`), one row per publication whose state or note changes: `run_id`, `pmid`, `state`, `note` (the note of the pass, its header naming the state, `CURATED: …` or `SELECTED: …`, or the row is refused; the write dates the header and puts the note first in the publication's note, the previous notes after a line `---`).

## Tools

Writes go through these commands. Without `--commit`, a command is a dry run: it applies its files, checks every invariant on the whole database in the same transaction, prints the result, and rolls back. With `--commit`, it commits only if nothing is refused and the check finds no error (`database.md` §2).

- `uv run drakkar-add <file> [--commit]`: adds descriptions.
- `uv run drakkar-revise <file> [--commit]`: revisions and removals, checked on the result of all the rows, so a change that passes through an inconsistent state is fine (a rename carried by several descriptions, a fix plus a merge).
- `uv run drakkar-publications <file> [--commit]`: publication states and notes.

They take several files at once, and `--header` prints the header line of their format.

- `uv run drakkar-batch <dir> [--new-run] [--commit]`: writes a curation batch from the merged files of its directory: `descriptions.revise.tsv` and `descriptions.delete.tsv` (revision rows), `descriptions.add.tsv`, and `publications.tsv`; a missing descriptions file has no rows. One transaction, in this order: the revisions and removals, the new descriptions, the publication states and notes, then the move of the publications left `selected` with a pass date in a vh run of the PubMed query to the open special run, the one with the highest number (`database.md` §1, states), with a `Moved` note first in each note and their descriptions with them; `--new-run` opens the next special run first, and the first move opens `special-1`. Every invariant is checked once, on the result, so a row can rely on an earlier one (an addition on a rename). Refused rows are reported with their file and line.
- `uv run drakkar-diff <run_id> <pmid> <file>`: read-only. Diffs the descriptions of the file (`*.add.tsv` format, all of one publication) against the live descriptions of that publication, and writes beside the file `<name>.add.tsv`, the descriptions that are not live; `<name>.revise.tsv`, the live descriptions with another generic name or other mapping sequences, as `revise` rows; `<name>.delete.tsv`, the live descriptions the file does not hold, as `remove` rows. Descriptions are matched on their method and interactors, empty coordinates being the full protein; `below_threshold` follows from the mappings and is not compared. An empty file puts every live description of the publication in `<name>.delete.tsv`.
- `uv run drakkar-check <dir>`: checks every invariant, read-only.

Reading, `drakkar-read`, read-only, on the current snapshots. Each command takes many inputs; `entry` prints a block per entry, the others tab-separated lines under one `#` header line naming the columns, each line starting with the input it answers (`(none)` when nothing is found), the best first. `--limit <n>` bounds the lines per input (20); a list that is cut ends with a line `… 20 of 622`. A text matches as a substring, case aside. A taxon is given by its NCBI ID and covers its whole subtree; it is written `<ID> <name>`, a lineage `<ID> <name> < …` up to the family. A stretch of a protein is written `<accession>:<start>-<stop>`, then `obsolete` when its snapshot is (its generic name stays reusable, its entry does not). An input that cannot be read gets its own line, with why.

- `uv run drakkar-read methods <text>...`: the PSI-MI terms whose name or a synonym contains each text, the closest names first, then the detection methods (MI:0001), then the most used: PSI-MI ID, name (with the synonym matched), `is_detection`, live descriptions.
- `uv run drakkar-read taxon <text>...`: the taxa one of whose names contains each text, the closest names first: the taxon (with the name matched), its rank, its lineage.
- `uv run drakkar-read entry <accession>...`: each entry's snapshots, lineage, isoforms, names, chains and peptides; for a secondary accession, the entry that holds it.
- `uv run drakkar-read search <text>... [--taxon <ID>]`: the entries whose `search` text (accession, gene names, taxon, protein name) contains each text, under the taxon when given, Swiss-Prot first: accession, `SP` (Swiss-Prot) or `TR` (TrEMBL), gene name, protein name, taxon, length. An entry whose taxon is missing from the NCBI taxonomy is found without `--taxon`, or with its own taxon ID.
- `uv run drakkar-read seq <accession>[:<start>-<stop>]...`: the sequence of each entry or isoform, or between those coordinates (1-based, inclusive).
- `uv run drakkar-read names <taxon ID>...`: the generic names of the viral interactors of live descriptions under each taxon, the most used first, with their live descriptions and their three most used interactors, on any snapshot.
- `uv run drakkar-read sql <query>`: free SQL for what no command gives, on a read-only connection where each statement stops after 30 seconds: its rows as tab-separated lines under a `#` header of column names, bounded as the others, each cell cut at 200 characters. Written from the tables of `database.md` §1.

## Releases

A UniProt release is loaded in three commands, each in one transaction (without `--commit`, a dry run that rolls back), on a directory `data/<release>/` named after the release: `taxonomy/` (the NCBI taxdump loaded with this release), `uniprot/` (the FTP files and their parsed TSV) and `reports/`. Sources: NCBI `taxdump.tar.gz`; UniProt FTP `uniprot_sprot_human.xml.gz`, `uniprot_sprot_viruses.xml.gz`, `uniprot_trembl_viruses.xml.gz` and `uniprot_sprot_varsplic.fasta.gz` (isoforms). What a release does to the snapshots: `database.md` §3.

- `uv run drakkar-taxonomy data/<release> [--commit]`: the NCBI taxonomy, first; merged taxa are resolved with `merged.dmp`.
- `uv run drakkar-uniprot parse data/<release>`: the UniProt XML to TSV (cached).
- `uv run drakkar-uniprot upgrade data/<release> [--commit]`: the import; it writes `reports/uniprot_upgrade.md` (with the entries whose taxon is missing from the taxonomy) and `reports/obsolete_vh_descriptions.tsv`.

## Alignments

A sequence is aligned by the code of the write (`align.py`, `database.md`), on the sequences Drakkar holds: what these commands compute is what the write will. Read-only.

- `uv run drakkar-align mapping <accession>[:<start>-<stop>] <sequence>...`: what the write computes for each mapping sequence (extra end residues in lowercase) on that interactor: its extra end residues, its occurrences on each isoform with their identity (on the canonical isoform, relative to the interactor's start), and `ok`, `below 90 %` or `aligns nowhere`.
- `uv run drakkar-align closest <sequence>... --taxon <ID>`: the entries of the taxon ranked by identity with each sequence (given as is, or as `<accession>[:<start>-<stop>]`), as the write maps a sequence on a whole entry, then Swiss-Prot first: accession, `SP` or `TR`, protein name, taxon, identity, aligned region (`1-15` on the canonical isoform, `<isoform>:1-15` on another). Bounded by `--limit <n>`, as `drakkar-read`.

## NCBI sequences

A strain UniProt lacks is read at NCBI (GenBank, RefSeq), for the mappings taken from its sequence (`curation-rules.md` §3). Read-only, no database; the record used is named in the description note.

- `uv run drakkar-genbank search <query>... [--limit <n>]`: the NCBI protein records of each query, in NCBI search syntax (`JFH-1 AND polyprotein`, `"Hepatitis C virus JFH-1"[Organism]`), bounded and counted as `drakkar-read`: accession and version, title, length, NCBI taxon.
- `uv run drakkar-genbank seq <accession>[:<start>-<stop>]...`: a protein record: its accession and version, title, length and sequence, or the subsequence between those coordinates (1-based, inclusive); a nucleotide record (a genome): its coding sequences, one line each, with the protein accession to read with `seq`.

## Full texts

A full text is fetched and converted by these tools, then read from the files they write.

- `uv run drakkar-fetch <pmid> <dir>`: downloads the full text as published, in three steps. Each step is a list of routes, each route answering yes or no by one test.

  1. **Access**: the article is free when it has a PMCID, when OpenAlex or Unpaywall list a free copy, or when the publisher's page (at the DOI) declares free access (`"isAccessibleForFree": true`, `<meta name="access" content="Yes">`, `citation_fulltext_world_readable`, or a link to the article's Creative Commons license, PLOS's only declaration); a declared paywall wins. Closed otherwise. A preprint is never a copy of the article: its copies, its DOI and a PMC copy of it (known by its own DOI) are never fetched.
  2. **The article**, one file, from the first route that gives it: the PMC open access files, Europe PMC `fullTextXML`, NCBI `efetch` (each when its XML has a body); the PMC article page, which serves the PMC copies outside the open access files (when it has the body sections; one page per publication, as NCBI forbids bulk downloads); the publisher's HTML page (when it declares free access; a page that declares a paywall is never the article); then, last, the publisher's PDF (`citation_pdf_url`) and the other free copies' PDFs (when the file is a PDF).
  3. **The supplementary files**, as the article lists them: its XML, the supplementary sections of the PMC page, or else the supplementary links of the publisher's page. Each is looked for on every route that serves one, whatever route gave the article: the PMC open access files, the link the article gives (never the PMC website's, which is behind a challenge), the publisher's page, then Europe PMC's supplementary files service. Archives are unpacked. A video, an image, the Reporting Summary and the peer review file (both by their caption) are skipped, with why.

  Unpaywall is asked only with an address, `UNPAYWALL_EMAIL` in the project's `.env`. It writes the article, `<pmid>.xml`, `<pmid>.html` or `<pmid>.pdf`, and the supplementary files in `<pmid>.supp/`, each converted as `drakkar-parse` does: the article to `<pmid>.md`, a supplementary file to `<file>.md` beside it. Last, only when the article could be converted, the manifest `manifest.json`, the files the curation can use: `article`, with `file`, the original, and `text`, its text; `supplements`, each with the `name` the article gives it, `file` and `text`. Paths are relative to `<dir>`. A publication directory set up from files the user provides holds the same: each file converted with `drakkar-parse`, and the manifest in this format.

  It prints its report. First a line saying where the article comes from: `Full text: <PMCID> (<license>)` or `Full text: <source> (<license>, <URL>)`, ending with `, supplementary files missing: <names>` when some are; without the article, `Full text: closed — <why>`, or `Full text: not downloaded — <why>` when it is free but no copy could be downloaded, then every route tried with its outcome. Then one line per file that could not be converted, with why, and per supplementary file missing, with every place tried.

- `uv run drakkar-download <url> <dir>`: the file at a URL, a supplementary file the article links to: saved in `<dir>` (the type from the response when its name gives none), an archive unpacked (its videos and images left out), each file converted to `<file>.md` beside it, as `drakkar-parse` does. One line per file: its text, or why it could not be had (the HTTP outcome, skipped, not converted).

- `uv run drakkar-parse <file> <out>`: converts one file to text, by its type: PMC XML to Markdown (title, abstract, sections, captions, tables and supplementary materials; references, acknowledgements, notes and peer reviews left out), Elsevier XML from its article API the same way (references and the graphical abstract left out), a PMC article page by its structure, as its XML (the same blocks, the back matter left out), any other HTML page to the Markdown of its main text, a Word document (`.docx`, or `.doc` from Word 97-2003) to Markdown, a PDF to its text page by page (`--- page N ---`), a spreadsheet (`.xlsx`, `.xls`) to one TSV block per sheet, CSV and plain text as they are. A scanned PDF, a damaged file, an image or any other type is refused with the reason, and nothing is written. No network.
