---
name: curate
disable-model-invocation: true
description: "Curation batch: publications, one or many, each curated by a curator agent, merged into batch files written after the user's go. Use when the user asks to curate publications; the prompt names them (one PMID, several, or a run's selected publications) and may name the work directory."
---

# Curation batch

You run a curation batch, of one publication or many. A `curator` agent curates each publication from its full text; you merge the results, dry-run them, report, and write them after the user's go. Read no publication and no doc: this skill is the whole process.

1. **Work directory**: the prompt's; otherwise `_data/sessions/run<run>/batch<n>/` when the publications are of one run (its name, not its `id`), `_data/sessions/batch<n>/` when they are of several; one directory per publication, `<dir>/<pmid>/`.

2. **Full texts**: a publication directory with its `manifest.json` is ready (files the user provided). Fetch the others: `mkdir -p <dir>/<pmid> && uv run curation-fetch <dir>/<pmid> <pmid> > <dir>/<pmid>/fetch.txt`. The report's first line says where the article comes from, or why there is none; the manifest is written only when the article could be had and converted. Read the reports, never the full texts.

   - `Full text: not downloaded` (free, but no copy could be downloaded): fetch once more, as the failure may pass. Still none: leave the publication out of the batch; a later batch fetches it again.
   - `Full text: closed`, or the article not converted: no curator; write its note in `<dir>/<pmid>/curation.txt`: `SELECTED`, then why there is no full text.

3. **Curate**: one `curator` agent per publication with a manifest, a few at a time, sent only `dir: <dir>/<pmid>`, `pmid: <pmid>`. It writes `descriptions.jsonl` and `curation.txt`. Without them, run it once more; still without them, report the publication as not curated and leave it out.

4. **Merge**: `cat <dir>/*/descriptions.jsonl > <dir>/descriptions.jsonl`, then `uv run curation-notes <dir>`, which writes `<dir>/publications.jsonl` from the notes, each `<dir>/<pmid>/curation.txt`, the state from its first word. The write dates the note.

5. **Dry run**: `uv run database-batch <dir>` applies and checks everything in one transaction, then rolls it back. Report its refused rows and errors as they are, without fixing them.

6. **Reply**: what each batch file holds, in descriptions and publications; the refused rows and errors; the publications without the article or with a relevant file missing, with why; from the notes, the `best-effort` values and the supplementary files downloaded or not; from the agents' replies, the tool errors.

7. **Commit**, after the go: `uv run database-batch <dir> --author "<model> (effort $CLAUDE_EFFORT, $AI_AGENT)" --commit` writes the new descriptions, the publication states and notes, each note after its date and its author: your model ID, as your system prompt gives it, `$CLAUDE_EFFORT`, your effort, and `$AI_AGENT`, the Claude Code running you; the curators run on the same model and effort (`[2026-10-29, claude-opus-5-5 (effort high, claude-code_2-1-312_agent)] CURATED …`).
