---
name: curate
disable-model-invocation: true
description: "Curation batch: publications each curated by a curator agent, merged into batch files written after the user's go. Use when the user asks to curate publications; the prompt may name the publications and the work directory."
---

# Curation

You run a curation batch. A `curator` agent curates each publication from its full text; you merge the results, dry-run them, report, and write them after the user's go. Read no publication and no doc: this skill is the whole process.

1. **Work directory**: the prompt's; otherwise `data/sessions/run<run>/batch<n>/` when the publications are of one run (its name, not its `id`), `data/sessions/batch<n>/` when they are of several; one directory per publication, `<dir>/<pmid>/`.

2. **Full texts**: a publication directory with its `manifest.json` is ready (files the user provided). Fetch the others: `mkdir -p <dir>/<pmid> && uv run drakkar-fetch <dir>/<pmid> <pmid> > <dir>/<pmid>/fetch.txt`. The report's first line says where the article comes from, or why there is none; the manifest is written only when the article could be had and converted. Read the reports, never the full texts.

   - `Full text: not downloaded` (free, but no copy could be downloaded): fetch once more, as the failure may pass. Still none: leave the publication out of the batch; a later batch fetches it again.
   - `Full text: closed`, or the article not converted: no curator; write its note in `<dir>/<pmid>/curation.txt`: `SELECTED`, then why there is no full text.

3. **Curate**: one `curator` agent per publication with a manifest, a few at a time, on the default model, sent only `dir: <dir>/<pmid>`, `pmid: <pmid>`. Its prompt is `prompts/agents/curator.md`: in Claude Code, the agent type `curator`; elsewhere, that file below its frontmatter, then the message, sent to a subagent with the shell, a tool to read files and a web search. It writes `descriptions.jsonl` and `curation.txt`. Without them, run it once more; still without them, report the publication as not curated and leave it out.

4. **Merge**: `cat <dir>/*/descriptions.jsonl > <dir>/descriptions.jsonl`, then `uv run drakkar-notes <dir>`, which writes `<dir>/publications.jsonl` from the notes, each `<dir>/<pmid>/curation.txt`, the state from its first word. The write dates the note.

5. **Dry run**: `uv run drakkar-batch <dir>` applies and checks everything in one transaction, then rolls it back. Report its refused rows and errors as they are, without fixing them.

6. **Reply**: what each batch file holds, in descriptions and publications; the refused rows and errors; the publications without the article or with a relevant file missing, with why; from the notes, the `best-effort` values and the supplementary files downloaded or not; from the agents' replies, the tool errors.

7. **Commit**, after the go: `uv run drakkar-batch <dir> --commit` writes the new descriptions, the publication states and notes.
