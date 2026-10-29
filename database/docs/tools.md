# Tools

Descriptions and publication states are written only through these tools, from files. What a write checks and does: `database.md` §2.

## Files

JSON Lines: one JSON object per line, with every key of its format and no other, its values in JSON types. No header: an empty file has no row. Every row names its publication by its PMID: a file holds one publication or many, and files concatenate with `cat`. In a value, JSON escapes only `"` (`\"`), `\` (`\\`) and line breaks (`\n`). A line with a missing or unknown key, or a value of the wrong type, is refused with its file and line. Notes follow `database.md` §1, notes.

**Descriptions to add** (`*.jsonl`), one line per new description:

| Key | Content |
| -- | -- |
| `pmid` | the publication, a number, in its vh run |
| `method` | PSI-MI ID |
| `accession1` | human interactor; gene name and full-length coordinates come from its snapshot |
| `accession2`, `start2`, `stop2` | viral interactor; `start2` and `stop2` numbers, or null for the full protein |
| `name2` | generic name |
| `mappings1`, `mappings2` | lists of mapping sequences, extra end residues in lowercase (`mSTNPK`: `nter` M); occurrences are computed at write time |
| `note` | the description note |

```json
{"pmid": 35939498, "method": "MI:0007", "accession1": "Q13501", "accession2": "P29990", "start2": null, "stop2": null, "name2": "C", "mappings1": [], "mappings2": ["mSTNPK", "mDREMA"], "note": "..."}
```

**Revisions** (`*.revise.jsonl`, `*.delete.jsonl`), one line per revised or removed description:

| Key | Content |
| -- | -- |
| `stable_id`, `version` | the description and the live version the decision was made on, a number; refused if it is no longer live |
| `pmid` | its publication, a number |
| `action` | `revise` (new version) or `remove` (no successor) |
| `into` | on a `remove` that merges a duplicate: the stable ID of the survivor, otherwise null; the description keys may then give what the removed description was decided to become, checked against the survivor |
| description keys | on a `revise`: the whole new description, the keys of the descriptions to add from `method` to `mappings2`; on a `remove`, null |
| `note` | `revise`: the note of the new version (the curation's note from `database-diff`, `UPDATED` in a versioning pass, `FIXED` for a fix); `remove`: its `REMOVED` line |

**Publications** (`*.jsonl`), one line per publication whose state or note changes: `pmid`, a number, the publication in its vh run; `state`, `selected` or `curated`; `note`, the note of the pass. The write puts it first in the publication's note, after the date (`[2026-10-22] CURATED …`), the previous notes after a line `---`.

```json
{"pmid": 35939498, "state": "curated", "note": "CURATED ..."}
```

## Tools

Writes go through these commands. Without `--commit`, a command is a dry run: it applies its files, checks every invariant on the whole database in the same transaction, prints the result, and rolls back. With `--commit`, it commits only if nothing is refused and the check finds no error (`database.md` §2).

- `uv run database-add <file> [--commit]`: adds descriptions.
- `uv run database-revise <file> [--commit]`: revisions and removals, checked on the result of all the rows, so a change that passes through an inconsistent state is fine (a rename carried by several descriptions, a fix plus a merge).
- `uv run database-publications <file> [--commit]`: publication states and notes.

They take several files at once.

- `uv run database-batch <dir> [--commit]`: writes a batch from the files of its directory: `descriptions.jsonl`, the descriptions to add; `descriptions.add.jsonl`, `descriptions.revise.jsonl` and `descriptions.delete.jsonl`, the files `database-diff` writes beside a `descriptions.jsonl`, the first read in place of `descriptions.jsonl` when it is there; and `publications.jsonl`. A missing descriptions file has no rows. One transaction, in this order: the revisions and removals, the new descriptions, the publication states and notes. Every invariant is checked once, on the result, so a row can rely on an earlier one (an addition on a rename). Refused rows are reported with their file and line.
- `uv run database-diff <pmid> <file>`: read-only. Diffs the descriptions of the file (descriptions to add, all of one publication) against the live descriptions of that publication in its vh run, and writes beside the file `<name>.add.jsonl`, the descriptions that are not live; `<name>.revise.jsonl`, the live descriptions with another generic name or other mapping sequences, as `revise` rows; `<name>.delete.jsonl`, the live descriptions the file does not hold, as `remove` rows. Descriptions are matched on their method and interactors, empty coordinates being the full protein. An empty file puts every live description of the publication in `<name>.delete.jsonl`.
- `uv run database-check <dir>`: checks every invariant, read-only.

Reading, `database-read`, read-only, on the current snapshots. Each command takes many inputs; `entry` prints a block per entry, the others tab-separated lines under one `#` header line naming the columns, each line starting with the input it answers (`(none)` when nothing is found), the best first. `--limit <n>` bounds the lines per input (20), except in `names`, never cut; a list that is cut ends with a line `… 20 of 622 shown, cut by --limit 20`. A text matches as a substring, case aside, except in `methods`. `search` and `entry` identify entries: they take an accession as publications write it, an old (secondary) accession, an isoform's (`P30875-2`), a sequence version (`P04637.2`), a group (`P09913; O14879`, `Q15646;`, each of its accessions), case aside; it names its current entry, or, for an old accession, the current entries that hold it (one after a merge, several after a split), never an obsolete one. `seq` and `database-mapping` take an accession the same way, then its stretch (`<accession>:<start>-<stop>`); `database-mapping` refuses an isoform. A taxon is given by its NCBI ID and covers its whole subtree; it is written `<ID> <name>`, a lineage `<ID> <name> < …` up to the family. A stretch of a protein is written `<accession>:<start>-<stop>`. An input that cannot be read gets its own line, with why.

- `uv run database-read methods <text>...`: the PSI-MI terms with a name or a synonym that holds a word of the text, case and punctuation aside (`biolayer interferometry` finds `bio-layer interferometry`, `GST pull-down` finds `pull down`), the closest names first (the most words held), then the detection methods (MI:0001), then the most used: PSI-MI ID, name (with the synonym matched), `is_detection`, live descriptions.
- `uv run database-read taxon <text>...`: the taxa one of whose names contains each text and that hold a current entry (theirs or under them), the closest names first (a name that is the text, then one that starts with it as a word, holds it as a word, holds it inside a word): the taxon (with the name matched), its rank, its lineage.
- `uv run database-read entry <accession>...`: each entry's lineage, gene names, length, isoforms, chains, peptides, propeptides, domains, zinc fingers and regions, and for a viral entry the generic names of the live descriptions on its current snapshot, each with its span and its live descriptions; for an old accession, the current entries that hold it.
- `uv run database-read search <text>... [--taxon <ID>]`: the entries each text names, under the taxon when given, Swiss-Prot first: an accession, its current entries, or, when it names none, the entries with a gene name that is the text (`B3GAT1` has an accession's shape); any other text, the entries whose `search` text (accession, gene names, taxon, protein name) contains it. Each line: the accession to write, `SP` (Swiss-Prot) or `TR` (TrEMBL), gene name, protein name, taxon, length. An entry whose taxon is missing from the NCBI taxonomy is found without `--taxon`, or with its own taxon ID.
- `uv run database-read seq <accession>[:<start>-<stop>]...`: the sequence of each entry or isoform, or between those coordinates (1-based, inclusive).
- `uv run database-read closest <sequence>... --taxon <ID>`: the entries of the taxon closest to each amino acid sequence (an accession is refused), by a database search: every isoform is aligned on the sequence (Smith-Waterman, BLOSUM62, gap open 11, extension 1, by pyopal), and each entry is ranked by the score of its best isoform, then Swiss-Prot first: each entry as `search` shows it, then identity (identical residues over the aligned columns, gaps included), coverage (the part of the sequence aligned), aligned region (`1-15` on the canonical isoform, `<isoform>:1-15` on another).
- `uv run database-read names <taxon ID>...`: the generic names of the viral interactors of live descriptions under each taxon, on current snapshots, the most used first, with their live descriptions and their three most used interactors; never cut.
- `uv run database-read sql <query>`: free SQL for what no command gives, on a read-only connection where each statement stops after 30 seconds: its rows, whole, as tab-separated lines under a `#` header of column names. The query bounds its own rows and columns; past 10 kB of output, a guard of the context, the rest is left out, with a line `… cut at 10 kB: select fewer columns or rows`; an error, as PostgreSQL gives it. Written from the tables of `database.md` §1.

## Releases

A UniProt release is loaded in three commands, each in one transaction (without `--commit`, a dry run that rolls back), on a directory `_data/<release>/` named after the release: `taxonomy/` (the NCBI taxdump loaded with this release), `uniprot/` (the FTP files and their parsed TSV) and `reports/`. Sources: NCBI `taxdump.tar.gz`; UniProt FTP `uniprot_sprot_human.xml.gz`, `uniprot_sprot_viruses.xml.gz`, `uniprot_trembl_viruses.xml.gz` and `uniprot_sprot_varsplic.fasta.gz` (isoforms). What a release does to the snapshots: `database.md` §3.

- `uv run database-taxonomy _data/<release> [--commit]`: the NCBI taxonomy, first; merged taxa are resolved with `merged.dmp`.
- `uv run database-uniprot parse _data/<release>`: the UniProt XML to TSV (cached).
- `uv run database-uniprot upgrade _data/<release> [--commit]`: the import; it writes `reports/uniprot_upgrade.md` (with the entries whose taxon is missing from the taxonomy) and `reports/obsolete_vh_descriptions.tsv`.

## Mapping

Read-only, on an identified entry.

- `uv run database-mapping <accession>[:<start>-<stop>] <sequence>...`: what the write computes for each mapping sequence (extra end residues in lowercase) on that interactor, by its own code (`align.py`, `database.md`): its extra end residues, its occurrences on each isoform with their identity, in the entry's numbering, and `ok`, `below 90 %` or `aligns nowhere`; a sequence over 20 residues is shown by its first 20 and its length, as in `closest`. One interactor per call: an accession among the sequences gets its own line; an interactor that cannot be read (an isoform, coordinates outside the entry), a message alone.

## Generic viral proteins

The generic viral proteins of the vh descriptions dataset (`datasets.md`) are three files of `database/generic/`, versioned in git, tab-separated under a header line:

| File | Columns |
| -- | -- |
| `species.tsv` | `family_ncbi_taxon_id` (empty when the NCBI taxonomy places the taxon in no family), `ncbi_taxon_id`, `name` (the virus name readers use, not the NCBI binomial), `publications` (the publications of its live vh descriptions): the species, one line each, sorted by family, then species (a species in no family last). A person writes `ncbi_taxon_id` and `name`; the tool fills the others. |
| `placed.tsv` | `ncbi_taxon_id`, `species_ncbi_taxon_id`, `name`: a taxon of viral interactors placed in its species, with its subtree: one missing from the NCBI taxonomy, or one the taxonomy keeps outside the species its virus is (an old species beside its successor, an unclassified taxon of a known virus); sorted by species, then taxon. |
| `proteins.tsv` | `ncbi_taxon_id` (the species), `generic_name`, `protein`, `note`: one line per generic name of the dataset in its species, the label of the generic viral protein it is shown as, and why when it is not obvious; sorted as `species.tsv`, then by name. |

The species of a viral interactor is given by the deepest taxon at or above its taxon in `species.tsv` (that taxon) or `placed.tsv` (the species it is placed in).

- `uv run database-generic sync <dir>`: read-only on the database. Rewrites the three files of the directory, sorted, and from Drakkar the families and publications of `species.tsv` and the names of `proteins.tsv`: the names the dataset no longer has are removed, the new ones added with an empty `protein`. Prints the counts, the names removed, then what a person decides, or `nothing`: a species missing from the NCBI taxonomy; a placed taxon now under its species in it (its line can go); a taxon under no species, with its lineage and its names; a name with no protein; a name whose protein is a name of the species mapped to another protein. A file whose header is not its format is refused.

## Derived datasets

The derived datasets (`datasets.md`) are five, each written as a `.tsv` file, tab-separated under a header line, and an `.xlsx` file, the same lines; each name ends with `run` and the name of the last vh run exported by ID, special runs aside, each character other than a letter, a digit or `-` made a `-` (`descriptions_vh_run87.tsv`):

| Dataset | Columns |
| -- | -- |
| `descriptions_hh` | `stable_id`, `version`, `pmid`, `psimi_id`, `method`; each human interactor: `release1` (the release its snapshot first appeared in), `accession1`, `gene_name1`, then `release2`, `accession2`, `gene_name2`. One line per description, sorted by stable ID. |
| `descriptions_vh` | `stable_id`, `version`, `pmid`, `psimi_id`, `method`; the human interactor: `release1` (the release its snapshot first appeared in), `accession1`, `gene_name1`; the viral interactor, from the most general to the most specific: `species_ncbi_taxon_id`, `species`, `protein` (from `database/generic/`), `strain_ncbi_taxon_id`, `strain` (its scientific name, empty when the taxon is missing from the NCBI taxonomy), `release2`, `accession2`, `uniprot_name2` (the UniProt protein name), `generic_name2`, `start2`, `stop2`. One line per description, sorted by stable ID. |
| `interactors_viral` | `release`, `accession`, `start`, `stop`, `sequence` (the canonical sequence from start to stop): one line per viral interactor of `descriptions_vh` (`release2`, `accession2`, `start2`, `stop2`), sorted by its columns. |
| `mappings_h` | `stable_id`, `sequence` (as the experiment used it, its extra end residues included, in lowercase: `mSTNPK`), the interactor: `release`, `accession`; `isoform` (the isoform it is found on: the canonical one, the accession, when the mapping occurs on it, else its other isoform with the lowest number), `target` (`h` or `v`, the kind of the other interactor), `nter`, `cter` (the extra end residues, mostly empty). The mappings of the human interactors of `descriptions_hh` (both sides) and `descriptions_vh`, one line per (stable ID, sequence, isoform): a homodimer's mapping on both sides is one line. Sorted by its columns. |
| `mappings_v` | `stable_id`, `sequence`, the interactor: `release`, `accession`, `start`, `stop`; `isoform`, `nter`, `cter`, as in `mappings_h`: the mappings of the viral interactors of `descriptions_vh`. |

- `uv run database-export <generic> <dir> [--run <id>] [--special-run <id>]`: read-only on the database. Writes the five datasets to the directory, from the live descriptions whose human interactors are on their current snapshots, in Swiss-Prot: of the vh runs up to `--run`, special runs aside, and of the special runs up to `--special-run`, all by default; of every hh run. A run is given by its ID (`runs.id`), not its name, so that an export can stop before a run in progress; a cut that is not the ID of a run of its kind is refused. The species and generic viral proteins are read from `<generic>`, the directory of their files, in step with Drakkar (the `export` skill): a taxon under no species, a species not in `species.tsv` or a name with no protein is reported, and nothing is written. Prints the runs exported and the lines of each dataset, then checks the `.tsv` files, read back: each description on one line in one file; the viral interactors of `descriptions_vh`, each on one line of `interactors_viral`, its sequence as long as its coordinates; each mapping on one line, on an interactor of its description, in the file of its target; and the numbers, each from its own query: the live descriptions of the runs exported, those exported and those left out (a human interactor not up to date); the mappings of the descriptions exported, the lines written and those merged in homodimers. It ends with `ok`, or with the failures and an error, the files left for a look.
