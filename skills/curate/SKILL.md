---
name: curate
disable-model-invocation: true
description: "Curation batch: up to 20 publications, new or already curated, each curated by a subagent into its list of descriptions and diffed against the database, then merged into the batch files. Use when the user asks to curate or re-curate publications. The prompt may say which publications and give a work directory; without them, the batch takes the next ones."
---

# Curation

You orchestrate a curation batch: each publication is curated by a subagent from its full text, its descriptions diffed against the database, and the results merged into the batch files. The same for a publication not curated yet and for one already curated (a re-curation): the diff tells them apart. The tools and the formats of their files: `docs/tools.md`.

1. **Publications**: at most 20, each with its run, as the prompt gives them (e.g. a run, or the PMIDs of a file). When the prompt gives none, take the next ones: the `selected` publications without a pass yet (`ai_pass_at` null) of the oldest vh run that still has some. The work directory is the prompt's, or else `data/sessions/run<run>/batch<n>/`, `<n>` numbering the batches of that run. One directory per publication, `<dir>/<pmid>/`.

2. **Full texts**, before any subagent: `uv run drakkar-fetch <pmid> <dir>/<pmid>`. Its manifest, `<pmid>.json`, says by its `outcome` what came (`docs/tools.md`):

   - `closed`: no subagent. The publication is reported as closed, with the manifest's `line`, and is left `selected` after the go, waiting for a PDF from the user.
   - `incomplete` without the article (no `file`): fetch once more, as a route that failed for a passing reason (a rate limit, a server error) can answer the second time. Still without it: no subagent; the publication is reported as incomplete, with every route tried (`tried`), and is left `selected` after the go.
   - With the article, `complete` or `incomplete` with supplementary files missing: `uv run drakkar-parse` on the article (the manifest's `file`) to `<pmid>.md`, and on each supplementary file to `<file>.md` beside it.

   A PDF the user provides replaces the fetch: saved as `<dir>/<pmid>/<pmid>.pdf` and converted the same way. You read the manifests, never what you fetch.

3. **Curate and diff**: one subagent per publication with the article, a few at a time, on the default model, with `item.md` as it is (`{dir}` = `<dir>/<pmid>`, `{run_id}`, `{pmid}` filled in, and `{missing}`: the names of the manifest's `missing_supplements`, or `none`). It curates the publication, fetching a missing file it needs with `drakkar-fetch --supplement`, and ends by diffing its descriptions. You never read a publication. Its reply lists the files it asked for, found or missing: check them against the manifest (`supplements` and `missing_supplements` marked `asked`) when you build the report.

4. **Merge**: concatenate each kind of TSV file of the publication directories into `<dir>/`, every line that does not start with `#` under one header line. Write `<dir>/publications.tsv`: each publication with its state and note (`docs/curation-rules.md` §5), from its `curation.txt`, its current note, and the `line` of its manifest as it stands after the curation. The state is `curated` only when all the relevant files were explored and all the descriptions extracted, none unsettled, with or without descriptions; `selected` otherwise (`docs/curation-rules.md` §2).

5. **Dry run**: `uv run drakkar-batch <dir>`: the batch files applied in one transaction, every invariant checked, then rolled back. Its refused rows and errors, inconsistencies between publications among them, are reported as they are, not fixed.

6. **Reply**: what each batch file holds, in counts of descriptions and publications; the refused rows and errors of the dry run; publications closed, incomplete without the article, or not curated, with why; the supplementary files the subagents asked for, found or missing: the publications left `selected` move to the special run after the go.

7. **Commit**, after the go, for new and re-curated publications alike: `uv run drakkar-batch <dir> --commit`, which writes the descriptions, then the publications, and last moves the publications of the batch left `selected` to the open special run (`docs/curation-rules.md` §2); `--new-run` only when the user says to open a new one.
