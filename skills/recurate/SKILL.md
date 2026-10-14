---
name: recurate
description: "Re-curation session: up to 20 curated publications, their descriptions checked against the publications themselves and turned into a file of revisions that passes the dry run, committed on the user's go. Use when the user asks to re-curate, re-check or validate curated publications. The prompt gives a work directory holding publications.tsv."
---

# Re-curation

You orchestrate a re-curation session as described in `docs/process.md` (§ A session); read it first.

**Done** when every publication of `<dir>/publications.tsv` has its files or is reported, the files of the session pass the dry run together, and the report is handed over. After the go: `drakkar-revise --commit`, then `drakkar-check`.

- **Publications**: given in `<dir>/publications.tsv`, at most 20; if it is missing or longer, ask.
- **Subagents**: one per publication, with `item.md` (`{dir}`, `{run_id}`, `{pmid}` filled in), on Sonnet: checking curated descriptions against their publication is mostly reading.
- **Report**: decisions by kind, each with its count of descriptions and publications and one example; removals; unsettled cases with why.
