# Tools

Descriptions and publication states are written only through these tools, from files; full texts are fetched and converted by the tools of the last section. What a write checks and does: `database.md` §2; what a right description is: `curation-rules.md`.

## Files

Tab separated. Lines starting with `#` are ignored (the header is one), so files concatenate with `cat`. Every row names its publication: a file holds one publication or many. Notes follow `curation-rules.md` §5, with `[DATE Claude]` as the date (set at commit) and `\n` for line breaks. Sequences in a list are separated by `,`.

**Descriptions to add** (`*.add.tsv`), one row per new description:

| Column                          | Content                                                                                                         |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `run_id`, `pmid`                | the publication                                                                                                 |
| `method`                        | PSI-MI ID                                                                                                       |
| `accession1`                    | human interactor; gene name and full-length coordinates come from its snapshot                                  |
| `accession2`, `start2`, `stop2` | viral interactor                                                                                                |
| `name2`                         | generic name                                                                                                    |
| `mappings1`, `mappings2`        | mapping sequences, extra end residues in lowercase (`mSTNPK`: `nter` M); occurrences are computed at write time |
| `below_threshold`               | mapping sequences kept below 90 % identity, explained in the note                                               |
| `note`                          | the description note, `CREATED`                                                                                 |

**Revisions** (`*.revise.tsv`), one row per revised description:

| Column                 | Content                                                                                                                                                                                      |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `stable_id`, `version` | the description and the live version the decision was made on; refused if it is no longer live                                                                                               |
| `run_id`, `pmid`       | its publication                                                                                                                                                                              |
| `action`               | `revise` (new version) or `remove` (no successor)                                                                                                                                            |
| `into`                 | on a `remove` that merges a duplicate: the stable ID of the survivor; the description columns may then give what the removed description was decided to become, checked against the survivor |
| description columns    | on a `revise`: the whole new description, as in `*.add.tsv`, from `method` to `below_threshold`                                                                                              |
| `note`                 | `revise`: the note of the new version, `REVISED` (`UPDATED` in a versioning pass, `FIXED` for a fix); `remove`: its `REMOVED` line                                                           |

**Publications** (`*.publications.tsv`), one row per publication whose state or note changes: `run_id`, `pmid`, `state`, `note` (the whole publication note).

## Tools

Writes go through these commands. Without `--commit`, a command is a dry run: it applies its files, checks every invariant on the whole database in the same transaction, prints the result, and rolls back. With `--commit`, it commits only if nothing is refused and the check finds no error (`database.md` §2).

- `uv run drakkar-add <file> [--commit]`: adds descriptions.
- `uv run drakkar-revise <file> [--commit]`: revisions and removals, checked on the result of all the rows, so a change that passes through an inconsistent state is fine (a rename carried by several descriptions, a fix plus a merge).
- `uv run drakkar-publications <file> [--commit]`: publication states and notes.

They take several files at once, and `--header` prints the header line of their format.

- `uv run drakkar-move <file>... [--new-run] [--commit]`: takes publications files (`*.publications.tsv`, only `run_id` and `pmid` are read) and moves those that are `selected` with a pass date in a vh run of the PubMed query to the open special run, the one with the highest number (`curation-rules.md` §2), adding its `Moved` line to each note; the others stay where they are. `--new-run` opens the next special run first, and the first move opens `special-1`. Their descriptions move with them.
- `uv run drakkar-batch <dir> [--new-run] [--commit]`: writes a curation batch from the merged files of its directory: `descriptions.revise.tsv` and `descriptions.delete.tsv` (revision rows), `descriptions.add.tsv`, and `publications.tsv`; a missing descriptions file has no rows. One transaction, in this order: the revisions and removals, the new descriptions, the publication states and notes, then the move of the publications left `selected` with a pass date, as `drakkar-move` does (`--new-run` likewise). Every invariant is checked once, on the result, so a row can rely on an earlier one (an addition on a rename). Refused rows are reported with their file and line.
- `uv run drakkar-diff <run_id> <pmid> <file>`: read-only. Diffs the descriptions of the file (`*.add.tsv` format, all of one publication) against the live descriptions of that publication, and writes beside the file `<name>.add.tsv`, the descriptions that are not live; `<name>.revise.tsv`, the live descriptions with another generic name or other mapping sequences, as `revise` rows; `<name>.delete.tsv`, the live descriptions the file does not hold, as `remove` rows. Descriptions are matched on their method and interactors, empty coordinates being the full protein; `below_threshold` follows from the mappings and is not compared. An empty file puts every live description of the publication in `<name>.delete.tsv`.
- `uv run drakkar-check <dir>`: checks every invariant, read-only.

Reading is read-only:

- `uv run drakkar-read publication <run_id> <pmid>`: title, abstract, note, live descriptions with their notes;
- `uv run drakkar-read entry <accession>`: snapshots, isoforms, names, chains and peptides, sequence;
- `uv run drakkar-read names <accession>`: the generic names used on the same strain, virus and family;
- `uv run drakkar-read curation-names <pmid> <accession>`: the same, without the descriptions of that publication, in every run;
- `uv run drakkar-read row <stable_id>...`: live descriptions as revision rows, to edit;
- `drakkar.db.connect(readonly=True)` for anything else.

## Full texts

A full text is fetched and converted by these tools, then read from the files they write; nothing else downloads it.

- `uv run drakkar-fetch <pmid> <dir>`: downloads the full text as published, from the first source that works. PMC first, on every PMCID known: the PMC open access files (the XML, its PDF and its supplementary files, the only source that holds them all), then Europe PMC `fullTextXML`, then NCBI `efetch db=pmc`, which serves a copy outside the open access files; after the last two, the supplementary files are asked for on their own from Europe PMC, and when it offers none the manifest says so (`supplements_offered`), which is not the same as a publication that has none. Then a copy elsewhere, from the open access locations of OpenAlex, Unpaywall and Crossref: the publisher at the DOI first, then the repositories (never a preprint server), an HTML full text before a PDF. Unpaywall answers only a request that carries an address, read from `UNPAYWALL_EMAIL` in the project's `.env`; without it Unpaywall is not asked at all. Failing every source, the user provides a PDF. It writes `<pmid>.xml`, `<pmid>.html` or `<pmid>.pdf`, the supplementary files in `<pmid>.supp/` (archives unpacked, videos and images left out), and last the manifest `<pmid>.json`, so a manifest means the fetch is done. The manifest holds `line`, the `Full text` line of the publication note (`curation-rules.md` §5); `file`, the full text (none when there is none, with `why`); `pdf`, the PDF beside a PMC XML; `pmcid`, `doi`, `source`, `url`, `license`; `supplements`, and `skipped_supplements` with why; `tried`, every URL tried for the full text, with its outcome.
- `uv run drakkar-parse <file> <out>`: converts one file to text, by its type: PMC XML to Markdown (title, abstract, sections, captions, tables and supplementary materials; references, acknowledgements, notes and peer reviews left out), HTML to the Markdown of its main text, a Word document (`.docx`, or `.doc` from Word 97-2003) to Markdown, a PDF to its text page by page (`--- page N ---`), a spreadsheet (`.xlsx`, `.xls`) to one TSV block per sheet, CSV and plain text as they are. A scanned PDF, a damaged file, an image or any other type is refused with the reason, and nothing is written. No network.
