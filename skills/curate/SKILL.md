---
name: curate
description: "Curation session: up to 20 selected publications of a run, curated into files of new descriptions that pass the dry run, committed on the user's go. Use when the user asks to curate a run or publications. The prompt gives a run ID and a work directory."
---

# Curation

You orchestrate a curation session: selected publications turned into files of descriptions to add (`*.add.tsv`), which pass the dry run and are committed together on the user's go. The files and the tools: `docs/tools.md`.

**Done** when every publication of `<dir>/publications.tsv` has its files or is reported, the files of the session pass the dry run together, and the report is handed over.

1. **Publications**: up to 20 `selected` publications of the run without a pass yet (`ai_pass_at` null), in PMID order, written to `<dir>/publications.tsv` (`run_id`, `pmid`). Everything the session produces goes in `<dir>`. If `publications.tsv` exists, the session is resumed.
1. **Full texts**, before any subagent: for each publication, `uv run drakkar-fetch <pmid> <dir>`, then `uv run drakkar-parse` on what it fetched: the full text (the manifest's `file`) to `<dir>/<pmid>.md`, each supplementary file to `<file>.md` beside it (`docs/tools.md`). A PDF the user provides for a publication, named in the prompt, replaces its fetch: saved as `<dir>/<pmid>.pdf` and converted the same way, with no manifest. A supplementary file that cannot be converted stays as it is, unread. You never read what you fetch.
1. **No full text** (a manifest without `file` and no PDF provided, or a full text that cannot be converted, such as a scanned PDF): the publication gets no subagent. Write `<dir>/<pmid>.publications.tsv` yourself from `uv run drakkar-read publication`: still `selected`, its note rewritten whole (`docs/curation-rules.md` §5) with the summary of its Claude note (else one line from its title), the `Full text` line of the manifest (`Full text: closed — <why>` for a full text that cannot be converted), a new `Pass` line `not accessible (<why>)` after the earlier ones, and the curator note kept verbatim; it passes the dry run.
1. **One subagent per publication with a full text**, a few at a time, with `item.md` (`{dir}`, `{run_id}`, `{pmid}` filled in), on the default model: curating a full text is the hard part. Each subagent decides its publication alone: you never read a publication, and a full text is only ever read by the subagent of its publication. A publication is done when its files (`<dir>/<pmid>.*.tsv`) exist: the subagent writes them under a temporary name and renames them once they pass the dry run, so a file that exists has passed. A publication too large for one subagent (a high-throughput screen with more than it can decide) is reported as such, with no file: it gets a session of its own.
1. **Reconcile**: dry-run all the files of the session together. Files that pass alone can contradict each other, e.g. two publications naming the same region of an entry differently. Each contradiction goes back to the subagent of one of its publications, to be decided again or left unsettled.
1. **Report**: publications curated, with and without descriptions; without an accessible full text, with why; too large for one subagent; descriptions added by method and by virus, by kind of decision with an example each; unsettled cases with why.
1. **After the go**: `uv run drakkar-add <dir>/*.add.tsv --commit`, then `uv run drakkar-publications <dir>/*.publications.tsv --commit`, then `uv run drakkar-check <dir>/check-after`, and save the report as `<dir>/report.md`.

The state of a session is its directory: a publication without a manifest is still to fetch (unless the user provided its PDF), one with a full text but no `<pmid>.md` still to convert, one without files still to do, and `report.md` means committed. A session is resumed by doing what is missing.
