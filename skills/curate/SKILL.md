---
name: curate
description: "Curation session: up to 20 selected publications of a run, curated into files of new descriptions that pass the dry run, committed on the user's go. Use when the user asks to curate a run or publications. The prompt gives a run ID and a work directory."
---

# Curation

You orchestrate a curation session as described in `docs/process.md` (§ A session); read it first.

**Done** when every publication of `<dir>/publications.tsv` has its files or is reported, the files of the session pass the dry run together, and the report is handed over. After the go: `drakkar-add`, then `drakkar-publications`, each with `--commit`, then `drakkar-check`.

- **Publications**: up to 20 `selected` publications of the run without a pass yet (`ai_pass_at` null), in PMID order, written to `<dir>/publications.tsv`. If it exists, the session is resumed.
- **Subagents**: one per publication, with `item.md` (`{dir}`, `{run_id}`, `{pmid}` filled in), on the default model: curating a full text is the hard part.
- **Report**: publications curated, with and without descriptions; without an accessible full text; too large for one subagent; descriptions added by method and by virus; unsettled cases with why.
