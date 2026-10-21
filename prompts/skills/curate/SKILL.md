---
name: curate
disable-model-invocation: true
description: "Curation batch: up to 20 publications, new or already curated, each curated by a subagent into its list of descriptions and diffed against the database, then merged into the batch files. Use when the user asks to curate or re-curate publications. The prompt may say which publications and give a work directory; without them, the batch takes the next ones."
---

# Curation

You orchestrate a curation batch: each publication is curated by a `curator` agent from its full text, its descriptions diffed against Drakkar, and the results merged into the batch files, written after the user's go. The same for a publication not curated yet and for one already curated (a re-curation): the publication is curated from its full text whatever Drakkar holds for it, and the diff turns the result into additions, revisions and removals. You never read a publication, and you read no doc: this skill holds the whole process.

1. **Publications**: at most 20, each with its run, as the prompt gives them (e.g. a run, or the PMIDs of a file). When the prompt gives none, take the next ones: the `selected` publications without a pass yet (`ai_pass_at` null) of the oldest vh run that still has some. The work directory is the prompt's, or else `data/sessions/run<run>/batch<n>/`, `<n>` numbering the batches of that run. One directory per publication, `<dir>/<pmid>/`.

2. **Full texts**, before any agent. A publication directory that already holds its manifest, `manifest.json`, is ready (files the user provides). Each other publication is fetched: `mkdir -p <dir>/<pmid> && uv run drakkar-fetch <pmid> <dir>/<pmid> > <dir>/<pmid>/fetch.txt`. Its report starts with a line saying where the article comes from, or why there is none; the manifest is written only when the article could be had and converted.

   - `Full text: not downloaded` (free, but no copy could be downloaded): fetch once more, as a route that failed for a passing reason (a rate limit, a server error) can answer the second time. Still none: no agent, and the publication is left out of the batch files, to be fetched again in a later batch.
   - `Full text: closed`, or an article that could not be converted: no agent; the publication is reported with why, and is left `selected`.

   You read the reports, never the full texts.

3. **Curate and diff**: one `curator` agent per publication with its manifest, a few at a time, on the default model (in Claude Code, the agent tool with the agent type `curator`), sent only this message: `dir: <dir>/<pmid>`, `run_id: <run>`, `pmid: <pmid>`. Its agent file, `prompts/agents/curator.md`, holds its prompt: never send it yourself. Where the harness has no agent files, send the body of `curator.md` (below its frontmatter) followed by the message to a subagent that has only the shell and the file tools. The agent writes `descriptions.tsv`, `curation.txt` and the diff files `descriptions.add.tsv`, `descriptions.revise.tsv` and `descriptions.delete.tsv` in its directory. An agent that ends without these files is run once more; still without them, its publication is reported as not curated and left out of the batch files. Its reply gives the `best-effort` values a reviewer should see, the supplementary files it downloaded or could not get, and what the tools could not do.

4. **Merge**: concatenate each kind of TSV file of the publication directories into `<dir>/`, every line that does not start with `#` under one header line. Then `<dir>/publications.tsv`, with the columns `run_id`, `pmid`, `state` and `note` (`uv run drakkar-publications --header`), one row per publication, `\n` for the line breaks of its note:

   - **The state**: the state of the header of `curation.txt`, `curated` or `selected`; without the article, `selected`.
   - **The note**: `curation.txt` as it is; without the article, `SELECTED: no full text, <the why of the first line of fetch.txt>`. The write dates its header and puts it first in the publication's note, the previous notes after a line `---`.

5. **Dry run**: `uv run drakkar-batch <dir>`: the batch files applied in one transaction, every invariant checked, then rolled back. Its refused rows and errors, inconsistencies between publications among them (two names for one interactor), are reported as they are, not fixed.

6. **Reply**: what each batch file holds, in counts of descriptions and publications; the refused rows and errors of the dry run; the publications without the article, closed or not downloaded, or with a relevant file missing, with why; the `best-effort` values the agents report; the supplementary files they downloaded or could not get; what the tools could not do. The publications left `selected` move to the special run after the go.

7. **Commit**, after the go, for new and re-curated publications alike: `uv run drakkar-batch <dir> --commit`. It writes the revisions and removals, the new descriptions, the publication states and notes (with the date of the pass in `ai_pass_at`), and last moves the publications left `selected` to the open special run, with a `Moved` note first in their notes: the run they leave can be complete, and their manual pass happens there. `--new-run` opens a new special run, only when the user says so.
