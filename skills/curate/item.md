# Curate one publication

Sent to one subagent per publication, with `{dir}`, `{run_id}` and `{pmid}` filled in.

______________________________________________________________________

Curate publication PMID {pmid} (run {run_id}): read its full text and record every virus–human interaction it shows that meets the criteria of `docs/curation-rules.md`. Read that file and `docs/glossary.md` first; `docs/tools.md` gives the file formats and the tools.

The full text is already in `{dir}/`: `{pmid}.md`, converted from the original (`{pmid}.xml`, `{pmid}.html` or `{pmid}.pdf`; beside a PMC XML, `{pmid}.pdf` is its PDF), and the supplementary files in `{pmid}.supp/`, each converted to `<file>.md` beside it. Read the converted text; open the original (the PDF's pages, the HTML) only where a table came out badly. Images are never read, nor a supplementary file that could not be converted. Never download anything: a supplementary file the publication needs but that is missing is said in the note. The `Full text` line of the note is `line` in `{pmid}.json`; without `{pmid}.json`, the PDF was provided by the user: `Full text: PDF provided by the user`.

**Done** when these files are in `{dir}/` and pass the dry run (`uv run drakkar-add`, `uv run drakkar-publications`, without `--commit`):

- `{pmid}.add.tsv`: one row per description; a header only when there is none.
- `{pmid}.publications.tsv`: the publication `curated` with its note, or still `selected` with why when its full text cannot be read.
- `{pmid}.unsettled.tsv`, when a claim cannot be settled; its `Not kept` line goes in the publication note too.

A high-throughput screen is curated from its supplementary tables, with the authors' own thresholds (`curation-rules.md` §3). If it holds more than you can decide well, write no file and say so.

Write each file under a temporary name and rename it once it passes. When the dry run refuses a row, fix it or move it to unsettled. You never commit.

Reply in a few lines: descriptions, unsettled claims, anything you could not do.
