---
name: curate
disable-model-invocation: true
description: "Curation session: up to 20 publications, new or already curated, each curated by a subagent into its list of descriptions and diffed against the database, then merged into the session files. Use when the user asks to curate or re-curate publications. The prompt says where the publications are and gives a work directory."
---

# Curation

You orchestrate a curation session: each publication is curated by a subagent from its full text, its descriptions diffed against the database, and the results merged into the session files. The same for a publication not curated yet and for one already curated (a re-curation): the diff tells them apart. The tools and the formats of their files: `docs/tools.md`.

1. **Publications**: from the prompt, at most 20, each with its run: e.g. the next `selected` publications of a run without a pass yet (`ai_pass_at` null), or the PMIDs of a file. One directory each, `<dir>/<pmid>/`.
2. **Full texts**, before any subagent: `uv run drakkar-fetch <pmid> <dir>/<pmid>`, then `uv run drakkar-parse` on what it fetched: the full text (the manifest's `file`) to `<pmid>.md`, each supplementary file to `<file>.md` beside it. A PDF the user provides replaces the fetch: saved as `<dir>/<pmid>/<pmid>.pdf` and converted the same way. You never read what you fetch.
3. **Curate and diff**: one subagent per publication with a full text, a few at a time, on the default model, with `item.md` as it is (`{dir}` = `<dir>/<pmid>`, `{run_id}`, `{pmid}` filled in). It curates the publication and ends by diffing its descriptions. You never read a publication.
4. **Merge**: concatenate each kind of TSV file of the publication directories into `<dir>/`, every line that does not start with `#` under one header line. Write `<dir>/publications.tsv`: each publication with its state and note (`docs/curation-rules.md` §5), from its `curation.txt` and its current note. The state is `curated` only when everything that can carry an interaction was read and every description is settled, `selected` otherwise (`docs/curation-rules.md` §2).
5. **Reply**: what each session file holds, in counts of descriptions and publications; publications without a full text or not curated, with why.

The state of a session is its directory: a session is resumed by doing what is missing.
