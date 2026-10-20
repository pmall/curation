---
name: curate
disable-model-invocation: true
description: "Curation batch: up to 20 publications, new or already curated, each curated by a subagent into its list of descriptions and diffed against the database, then merged into the batch files. Use when the user asks to curate or re-curate publications. The prompt may say which publications and give a work directory; without them, the batch takes the next ones."
---

# Curation

You orchestrate a curation batch: each publication is curated by a `curator` agent from its full text, its descriptions diffed against Drakkar, and the results merged into the batch files, written after the user's go. The same for a publication not curated yet and for one already curated (a re-curation): the publication is curated from its full text whatever Drakkar holds for it, and the diff turns the result into additions, revisions and removals. You never read a publication, and you read no doc: this skill holds the whole process.

1. **Publications**: at most 20, each with its run, as the prompt gives them (e.g. a run, or the PMIDs of a file). When the prompt gives none, take the next ones: the `selected` publications without a pass yet (`ai_pass_at` null) of the oldest vh run that still has some. The work directory is the prompt's, or else `data/sessions/run<run>/batch<n>/`, `<n>` numbering the batches of that run. One directory per publication, `<dir>/<pmid>/`.

2. **Full texts**, before any agent: `uv run drakkar-fetch <pmid> <dir>/<pmid>`. Its manifest, `<pmid>.json`, records the article (`file`), or why there is none (`why`), each supplementary file found (`supplements`), skipped (`skipped_supplements`) or missing (`missing_supplements`), and `line`, the `Full text` line of the publication note.

   - No article: fetch once more, as a route that failed for a passing reason (a rate limit, a server error) can answer the second time. Still none: no agent; the publication is reported with the manifest's `why`, and is left `selected`.
   - An article: `uv run drakkar-parse <file> <out>` on it (the manifest's `file`) to `<pmid>.md`, and on each supplementary file to `<file>.md` beside it.

   A PDF the user provides replaces the fetch: saved as `<dir>/<pmid>/<pmid>.pdf` and converted the same way. You read the manifests, never what you fetch.

3. **Curate and diff**: one `curator` agent per publication with the article, a few at a time, on the default model (in Claude Code, the agent tool with the agent type `curator`), sent only this message: `dir: <dir>/<pmid>`, `run_id: <run>`, `pmid: <pmid>`. Its agent file, `prompts/agents/curator.md`, holds its prompt: never send it yourself. Where the harness has no agent files, send the body of `curator.md` (below its frontmatter) followed by the message to a subagent that has only the shell and the file tools. The agent writes `descriptions.tsv`, `curation.txt` and the diff files `descriptions.add.tsv`, `descriptions.revise.tsv` and `descriptions.delete.tsv` in its directory. An agent that ends without these files is run once more; still without them, its publication is reported as not curated and left out of the batch files. Its reply gives the state the publication earns, the `best-effort` values a reviewer should see, the supplementary files it asked for, found or missing (check them against the manifest, where they are marked `asked`), and what the tools could not do.

4. **Merge**: concatenate each kind of TSV file of the publication directories into `<dir>/`, every line that does not start with `#` under one header line. Then `<dir>/publications.tsv`, with the columns `run_id`, `pmid`, `state` and `note` (`uv run drakkar-publications --header`), one row per publication, `\n` for the line breaks of its note:

   - **The state**: `curated` when all its relevant files were explored and all its descriptions extracted, with or without descriptions; `selected` when a relevant file is missing (a `Not read: … — relevant, …` line in `curation.txt`), or without the article.

   - **The note**: `CURATED: from <source>, <the Summary line of curation.txt>` (`SELECTED: …, <files> missing` when selected), then `- Full text: <the manifest's line, as it stands after the curation>`, then the other lines of `curation.txt`, then `- Pass <curation date>: <outcome>` (`curated from <source>`, `re-curated from <source>`, `partial from <source>, <files> missing`), the curation date being the day the agents curated. `<source>` is the PMCID, the URL, or `a PDF provided by the user` (then the line is `Full text: PDF provided by the user`). Without the article: `SELECTED: no full text, <the manifest's why>`, the `Full text` line and `- Pass <date>: not accessible (<why>)`. The write puts it first in the publication's note, the previous notes after a line `---`.

5. **Dry run**: `uv run drakkar-batch <dir>`: the batch files applied in one transaction, every invariant checked, then rolled back. Its refused rows and errors, inconsistencies between publications among them (two names for one interactor), are reported as they are, not fixed.

6. **Reply**: what each batch file holds, in counts of descriptions and publications; the refused rows and errors of the dry run; the publications without the article, or with a relevant file missing, with why; the `best-effort` values the agents report; the supplementary files they asked for, found or missing; what the tools could not do. The publications left `selected` move to the special run after the go.

7. **Commit**, after the go, for new and re-curated publications alike: `uv run drakkar-batch <dir> --commit`. It writes the revisions and removals, the new descriptions, the publication states and notes (with the date of the pass in `ai_pass_at`), and last moves the publications left `selected` to the open special run, with a `Moved` note first in their notes: the run they leave can be complete, and their manual pass happens there. `--new-run` opens a new special run, only when the user says so.
