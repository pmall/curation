# Re-curate one publication

Sent to one subagent per publication, with `{dir}`, `{run_id}` and `{pmid}` filled in.

______________________________________________________________________

Re-curate the live virus–human descriptions of publication PMID {pmid} (run {run_id}): does each description still say what the publication shows? Read `docs/curation-rules.md` and `docs/glossary.md` first; `docs/tools.md` gives the file formats and the tools.

Decide each description from its publication and its interactors' UniProt entries (`docs/curation-rules.md` §1).

The full text is already in `{dir}/`: `{pmid}.md`, converted from the original (`{pmid}.xml`, `{pmid}.html` or `{pmid}.pdf`; beside a PMC XML, `{pmid}.pdf` is its PDF), and the supplementary files in `{pmid}.supp/`, each converted to `<file>.md` beside it. Read the converted text; open the original (the PDF's pages, the HTML) only where a table came out badly. Images are never read, nor a supplementary file that could not be converted. Never download anything.

The errors seen so far:

- the entry is right, but it carries the polyprotein's name instead of its mature protein's;
- the entry holds only part of the protein tested;
- the name designates a protein the entry does not hold;
- the coordinates are those of the construct, not of the protein;
- the human interactor is another protein.

An entry that is a truncated copy of the protein it is named after is the curator's choice and is kept.

**Done** when these files are in `{dir}/` and pass the dry run (`uv run drakkar-revise`, without `--commit`):

- `{pmid}.revise.tsv`: one row per description that changes, from `uv run drakkar-read row <stable_id>`. A fix is complete: when a field changes, so do the fields and the note it implies. Two descriptions that become identical are one: the other is a `remove` `into` the survivor, which gains its missing mapping sequences.
- `{pmid}.unsettled.tsv`, with why.

Write each file under a temporary name and rename it once it passes. Rewrite a file whole; never truncate one in place. When the dry run refuses a row, fix it or move it to unsettled. You never commit.

Reply in a few lines: revisions, removals, unsettled.
