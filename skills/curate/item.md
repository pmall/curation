# Curate one publication

Sent by the `curate` skill to one subagent per publication, as it is, with `{dir}` (the publication directory), `{run_id}`, `{pmid}` and `{missing}` (the supplementary files the fetch could not download, or `none`) filled in.

______________________________________________________________________

Curate publication PMID {pmid} (run {run_id}): read its full text and record every virus–human interaction it shows that meets the criteria of `docs/curation-rules.md`. Read that file and `docs/glossary.md` first; `docs/tools.md` gives the file formats and the tools.

The full text is already in `{dir}/`: `{pmid}.md`, converted from the original (`{pmid}.xml`, `{pmid}.html` or `{pmid}.pdf`; beside a PMC XML, `{pmid}.pdf` is its PDF), and the supplementary files in `{pmid}.supp/`, each converted to `<file>.md` beside it. Supplementary files the fetch could not download: {missing}. Read the converted text; open the original (the PDF's pages, the HTML) only where a table came out badly. Images are never read, nor a supplementary file that could not be converted. A publication's file is downloaded only with `drakkar-fetch --supplement`, never the article.

**Relevant files.** A file not read is relevant only when the text, its caption or its name shows it can hold interactions: a table of hits, a figure of an interaction experiment, data the text cites for an interaction. A file that cannot hold one (a reporting summary, a peer review file, a checklist, a figure of non-interaction data) is not fetched and does not keep the publication selected; the curation notes name it and say why it is not relevant.

**A missing file.** When a relevant file is missing (cited in the text and absent from `{dir}`, or listed above as missing), run, before writing your descriptions, `uv run drakkar-fetch --supplement {pmid} {dir} <url or file name>...` for all of them in one call, with any URL or file name the text gives (a label such as `Table S1` is looked for too). It prints one line per file. Found: read its converted file and go on. Still missing: go on without it; the curation notes name the missing file and the places tried, and the publication stays `selected`.

The publication is curated from its full text and its interactors' UniProt entries (`uv run drakkar-read entry <accession>`), never from its record in the database: no `drakkar-read publication` or `drakkar-read row` on it. Generic names: `uv run drakkar-read curation-names {pmid} <accession>`.

**The database** is read with these lookups (`docs/tools.md`), each taking many inputs at once, so ask everything you need in one call. A text matches as a substring, case aside: give its spelling variants as more inputs (`JFH1 JFH-1`, `NS2B-NS3 NS2B/NS3`). They print the first 10 results per input, the closest first; when some are left out, the last line says how many and how to see them: read on with `--offset`, or narrow (a closer text, `--taxon`, `--reviewed`, `--min-identity`) rather than `--all`. Never decide from a cut list without checking that what you look for is not further down.

- `uv run drakkar-read methods <text>...`: the PSI-MI ID of a method, by name or synonym, and whether it is a detection method: `methods coimmuno "two hybrid" "pull down"`. A term PSI-MI does not hold is looked for by its technique: `pull down` for a GST pull-down, `affinity` for AP-MS, `electron microscopy` for cryo-EM, `proximity labelling` for APEX, `non denaturing gel` for a native gel.
- `uv run drakkar-read search <text>... [--taxon <taxon>] [--human | --viral] [--reviewed]`: the entries of a gene or protein name, or a virus's whole proteome: `search TRIM25 DDX3X --human --reviewed`, `search "non-structural protein 4A" --taxon 3052230`, `search --taxon 3052230`. A mature protein is a chain of its polyprotein: `entry` lists them. An accession is read with `entry`, secondary ones too. An entry whose taxon is missing from the NCBI taxonomy is found without `--taxon` only.
- `uv run drakkar-read taxon <text>...`: the taxon of a strain or a virus: `taxon JFH1 "Puerto Rico/8"`.
- `uv run drakkar-read closest <sequence>... --taxon <taxon>`: the publication's strain, or the closest entry when UniProt lacks it: `closest MSTNPKPQRKTKRNT --taxon 3052230 --min-identity 100`.
- `uv run drakkar-read seq <accession>[:<start>-<stop>]...`: a mapping from coordinates: `seq P26662:810-830`.
- `uv run drakkar-read map <accession>[:<start>-<stop>] <sequence>...`: your mappings checked before writing them: `map P26662:810-1026 mDREMAASCGG`.
- `uv run drakkar-read used <taxon> [<generic name>...] --exclude {pmid}`: the generic names already used for a virus, and the entry most used for a virus and generic name: `used 3052230 NS3 NS5A --exclude {pmid}`.
- `uv run drakkar-genbank search <query>...` and `uv run drakkar-genbank seq <accession>[:<start>-<stop>]...`: the publication's strain at NCBI when UniProt lacks it, for the mappings taken from its sequence: `drakkar-genbank search "JFH-1 AND polyprotein"`, `drakkar-genbank seq BAB32872.1:2-191`; a genome accession lists its coding sequences.

`--exclude {pmid}` is always given: the curation never sees the descriptions of the publication it curates.

What none of them gives: `uv run drakkar-read sql "<query>"`, written from the tables of `docs/database.md` §1, then go on with the curation.

A high-throughput screen is curated from its supplementary tables, with the authors' own thresholds (`curation-rules.md` §3). If it holds more than you can decide well, write no file and say so.

**Done** when these files are in `{dir}/`:

- `descriptions.tsv`: every description of the publication, in the format of `*.add.tsv` (`uv run drakkar-add --header` gives the header line); only the header line when there is none.
- `descriptions.unsettled.tsv`, only when a description cannot be settled: one row per description, the columns of `descriptions.tsv` filled as far as settled and empty otherwise, then `as_published` (the interaction in the publication's own words: both proteins, the strain, the experiment, the figure or table) and `why` (which value is missing and what was tried, e.g. `no UniProt entry for JFH1; closest: P26662 (NS3 at 98 %), Q99IB8 (96 %)`); its header line is that of `descriptions.tsv` followed by `as_published` and `why`.
- `curation.txt`: the curation notes, as detail lines of the publication note (`curation-rules.md` §5); with no description, why.
- `descriptions.add.tsv`, `descriptions.revise.tsv` and `descriptions.delete.tsv`: written by `uv run drakkar-diff {run_id} {pmid} {dir}/descriptions.tsv`, run last, once your files above are complete. What the diff finds is not yours to act on.

Write each of your files under a temporary name and rename it once it is complete. You never write to the database.

Reply in a few lines: descriptions, unsettled descriptions, anything you could not do; each file you asked for with `--supplement`: the name the publication gives it, where it is cited, found or missing; and each `drakkar-read sql` query, with what it was for.
