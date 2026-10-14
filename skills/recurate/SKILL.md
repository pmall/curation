---
name: recurate
description: "Re-curation session: up to 20 curated publications, their descriptions checked against the publications themselves and turned into a file of revisions that passes the dry run, committed on the user's go. Use when the user asks to re-curate, re-check or validate curated publications. The prompt gives a work directory holding publications.tsv."
---

# Re-curation

You orchestrate a re-curation session: curated publications turned into files of revisions (`*.revise.tsv`), which pass the dry run and are committed together on the user's go. Re-curation never adds descriptions. The files and the tools: `docs/tools.md`.

**Done** when every publication of `<dir>/publications.tsv` has its files or is reported, the files of the session pass the dry run together, and the report is handed over.

1. **Publications**: given in `<dir>/publications.tsv` (`run_id`, `pmid`), at most 20; if it is missing or longer, ask. Everything the session produces goes in `<dir>`.
1. **Full texts**, before any subagent: for each publication, `uv run drakkar-fetch <pmid> <dir>`, then `uv run drakkar-parse` on what it fetched: the full text (the manifest's `file`) to `<dir>/<pmid>.md`, each supplementary file to `<file>.md` beside it (`docs/tools.md`). A PDF the user provides for a publication, named in the prompt, replaces its fetch: saved as `<dir>/<pmid>.pdf` and converted the same way, with no manifest. A supplementary file that cannot be converted stays as it is, unread. You never read what you fetch.
1. **No full text** (a manifest without `file` and no PDF provided, or a full text that cannot be converted, such as a scanned PDF): the publication gets no subagent and no file; it is reported, with why.
1. **One subagent per publication with a full text**, a few at a time, with `item.md` (`{dir}`, `{run_id}`, `{pmid}` filled in), on Sonnet: checking curated descriptions against their publication is mostly reading. Each subagent decides its publication alone: you never read a publication, and a full text is only ever read by the subagent of its publication. A publication is done when its files (`<dir>/<pmid>.*.tsv`) exist: the subagent writes them under a temporary name and renames them once they pass the dry run, so a file that exists has passed. A publication too large for one subagent is reported as such, with no file: it gets a session of its own.
1. **Reconcile**: dry-run all the files of the session together. Files that pass alone can contradict each other, e.g. two publications renaming the same region of an entry differently. Each contradiction goes back to the subagent of one of its publications, to be decided again or left unsettled.
1. **Report**: decisions by kind, each with its count of descriptions and publications and one example; removals; unsettled cases with why; publications without a full text, with why; publications without files.
1. **After the go**: `uv run drakkar-revise <dir>/*.revise.tsv --commit`, then `uv run drakkar-check <dir>/check-after`, and save the report as `<dir>/report.md`.

The state of a session is its directory: a publication without a manifest is still to fetch (unless the user provided its PDF), one with a full text but no `<pmid>.md` still to convert, one without files still to do, and `report.md` means committed. A session is resumed by doing what is missing.
