---
name: curate
disable-model-invocation: true
description: "Curation batch: up to 20 publications, each curated by a curator agent, merged into batch files written after the user's go. Use when the user asks to curate publications; the prompt may name the publications and the work directory."
---

# Curation

You run a curation batch. A `curator` agent curates each publication from its full text; you merge the results, dry-run them, report, and write them after the user's go. Read no publication and no doc: this skill is the whole process.

1. **Publications**: at most 20, each with its run, as the prompt gives them; otherwise the `selected` publications without a pass (`ai_pass_at` null) of the oldest vh run that has some. A run is given by its name, not its `id`. The work directory is the prompt's, or `data/sessions/run<run>/batch<n>/`, with one directory per publication, `<dir>/<pmid>/`.

2. **Full texts**: a publication directory with its `manifest.json` is ready (files the user provided). Fetch the others: `mkdir -p <dir>/<pmid> && uv run drakkar-fetch <pmid> <dir>/<pmid> > <dir>/<pmid>/fetch.txt`. The report's first line says where the article comes from, or why there is none; the manifest is written only when the article could be had and converted. Read the reports, never the full texts.

   - `Full text: not downloaded` (free, but no copy could be downloaded): fetch once more, as the failure may pass. Still none: leave the publication out of the batch; a later batch fetches it again.
   - `Full text: closed`, or the article not converted: no curator; its note is `SELECTED: no full text, <why, from the report>`.

3. **Curate**: one `curator` agent per publication with a manifest, a few at a time, on the default model, sent only `dir: <dir>/<pmid>`, `run_id: <run id>`, `pmid: <pmid>`. Its prompt is `prompts/agents/curator.md`: in Claude Code, the agent type `curator`; elsewhere, that file below its frontmatter, then the message, sent to a subagent with the shell and the file tools. It writes `descriptions.tsv` and `curation.txt`. Without them, run it once more; still without them, report the publication as not curated and leave it out.

4. **Merge**: `cat <dir>/*/descriptions.tsv > <dir>/descriptions.tsv` (the header lines start with `#` and are skipped). Then `<dir>/publications.tsv`, under the header `uv run drakkar-publications --header` prints: one row per publication, its state the header of its note (`curated` or `selected`), its note `curation.txt` as it is, or the note of step 2, `\n` for its line breaks. The write dates the note.

5. **Dry run**: `uv run drakkar-batch <dir>` applies and checks everything in one transaction, then rolls it back. Report its refused rows and errors as they are, without fixing them.

6. **Reply**: what each batch file holds, in descriptions and publications; the refused rows and errors; the publications without the article or with a relevant file missing, with why; from the agents' replies, the `best-effort` values, the supplementary files downloaded or not, and the tool errors. The `selected` publications move to the special run on commit.

7. **Commit**, after the go: `uv run drakkar-batch <dir> --commit` writes the new descriptions, the publication states and notes, then moves the `selected` publications to the open special run. `--new-run` opens a new special run, only when the user says so.
