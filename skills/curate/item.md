# Curate one publication

Sent by the `curate` skill to one subagent per publication, as it is, with `{dir}` (the publication directory), `{run_id}` and `{pmid}` filled in.

______________________________________________________________________

Curate publication PMID {pmid} (run {run_id}): read its full text and record every virus–human interaction it shows that meets the criteria of `docs/curation-rules.md`. Read that file and `docs/glossary.md` first; `docs/tools.md` gives the file formats and the tools.

The full text is already in `{dir}/`: `{pmid}.md`, converted from the original (`{pmid}.xml`, `{pmid}.html` or `{pmid}.pdf`; beside a PMC XML, `{pmid}.pdf` is its PDF), and the supplementary files in `{pmid}.supp/`, each converted to `<file>.md` beside it. Read the converted text; open the original (the PDF's pages, the HTML) only where a table came out badly. Images are never read, nor a supplementary file that could not be converted. Never download anything: a supplementary file the publication needs but that is missing is said in the curation notes.

The publication is curated from its full text and its interactors' UniProt entries (`uv run drakkar-read entry <accession>`), never from its record in the database: no `drakkar-read publication` or `drakkar-read row` on it. Generic names: `uv run drakkar-read curation-names {pmid} <accession>`.

A high-throughput screen is curated from its supplementary tables, with the authors' own thresholds (`curation-rules.md` §3). If it holds more than you can decide well, write no file and say so.

**Done** when these files are in `{dir}/`:

- `descriptions.tsv`: every description of the publication, in the format of `*.add.tsv` (`uv run drakkar-add --header` gives the header line); only the header line when there is none.
- `descriptions.unsettled.tsv`, only when a description cannot be settled: one row per description, the columns of `descriptions.tsv` filled as far as settled and empty otherwise, then `as_published` (the interaction in the publication's own words: both proteins, the strain, the experiment, the figure or table) and `why` (which value is missing and what was tried, e.g. `no UniProt entry for JFH1; closest: P26662 (NS3 at 98 %), Q99IB8 (96 %)`); its header line is that of `descriptions.tsv` followed by `as_published` and `why`.
- `curation.txt`: the curation notes, as detail lines of the publication note (`curation-rules.md` §5); with no description, why.
- `descriptions.add.tsv`, `descriptions.revise.tsv` and `descriptions.delete.tsv`: written by `uv run drakkar-diff {run_id} {pmid} {dir}/descriptions.tsv`, run last, once your files above are complete. What the diff finds is not yours to act on.

Write each of your files under a temporary name and rename it once it is complete. You never write to the database.

Reply in a few lines: descriptions, unsettled descriptions, anything you could not do.
