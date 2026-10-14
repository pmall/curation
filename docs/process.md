# Curation process

How curation and re-curation sessions run. What a right description is: `curation-rules.md`; what a write checks and does: `database.md` §2.

## Goal

Curation and re-curation produce files, not writes. **Curation** turns selected publications into files of descriptions to add. **Re-curation** turns curated publications into files of revisions; it never adds descriptions. A file is done when it passes the dry run; the files of a session are committed together, on the user's go.

## A session

A session is at most 20 publications, handled in one Claude session and chosen before it starts: choosing them is not the session's job. Each publication gets its own subagent, which decides it alone: the orchestrator never reads a publication, and a full text is only ever read by the subagent of its publication.

1. **Start**: the work directory `<dir>` holds `publications.tsv` (`run_id`, `pmid`); everything the session produces goes in it.
1. **One subagent per publication**, a few at a time, following the item instructions of the skill. A publication is **done** when its files (`<dir>/<pmid>.*.tsv`) exist and pass the dry run: the subagent that decided runs it and settles what it refuses, because only it has the evidence. It writes each file under a temporary name and renames it once it passes, so a file that exists has passed. A publication too large for one subagent (a high-throughput screen with more than it can decide) is reported as such, with no file: it gets a session of its own.
1. **Reconcile**: dry-run all the files of the session together. Files that pass alone can contradict each other, e.g. two publications naming the same region of an entry differently. Each contradiction goes back to the subagent of one of its publications, to be decided again or left unsettled.
1. **Report, then commit on the go**: the report covers the descriptions that pass, by kind of decision, with an example and a count each, the unsettled cases with why, and the publications without files. After the go: commit, then `uv run drakkar-check <dir>/check-after`, and save the report as `<dir>/report.md`.

The state of a session is its directory: what has no file yet is still to do, and `report.md` means committed. A session is resumed by doing what is missing.

## Files

Tab separated. Lines starting with `#` are ignored (the header is one), so files concatenate with `cat`. Every row names its publication: a file holds one publication or many. Notes follow `curation-rules.md` §5, with `[DATE Claude]` as the date (set at commit) and `\n` for line breaks. Sequences in a list are separated by `,`.

**Descriptions to add** (`*.add.tsv`), one row per new description:

| Column                          | Content                                                                        |
| ------------------------------- | ------------------------------------------------------------------------------ |
| `run_id`, `pmid`                | the publication                                                                |
| `method`                        | PSI-MI ID                                                                      |
| `accession1`                    | human interactor; gene name and full-length coordinates come from its snapshot |
| `accession2`, `start2`, `stop2` | viral interactor                                                               |
| `name2`                         | generic name                                                                   |
| `mappings1`, `mappings2`        | mapping sequences; occurrences are computed at write time                      |
| `below_threshold`               | mapping sequences kept below 90 % identity, explained in the note              |
| `note`                          | the description note, `CREATED`                                                |

**Revisions** (`*.revise.tsv`), one row per revised description:

| Column                 | Content                                                                                                                                                                                      |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `stable_id`, `version` | the description and the live version the decision was made on; refused if it is no longer live                                                                                               |
| `run_id`, `pmid`       | its publication                                                                                                                                                                              |
| `action`               | `revise` (new version) or `remove` (no successor)                                                                                                                                            |
| `into`                 | on a `remove` that merges a duplicate: the stable ID of the survivor; the description columns may then give what the removed description was decided to become, checked against the survivor |
| description columns    | on a `revise`: the whole new description, as in `*.add.tsv`, from `method` to `below_threshold`                                                                                              |
| `note`                 | `revise`: the note of the new version, `REVISED` (`UPDATED` in a versioning pass, `FIXED` for a fix); `remove`: its `REMOVED` line                                                           |

**Publications** (`*.publications.tsv`), one row per publication whose state or note changes: `run_id`, `pmid`, `state`, `note` (the whole publication note).

**Unsettled** (`*.unsettled.tsv`): `run_id`, `pmid`, `stable_id` (empty for a claim that is not a description), `why`. Not written to the database; it feeds the report.

## Tools

Writes go through these commands. Without `--commit`, a command is a dry run: it applies its files, checks every invariant on the whole database in the same transaction, prints the result, and rolls back. With `--commit`, it commits only if nothing is refused and no invariant fails (`database.md` §2).

- `uv run drakkar-add <file> [--commit]`: adds descriptions.
- `uv run drakkar-revise <file> [--commit]`: revisions and removals, checked on the result of all the rows, so a change that passes through an inconsistent state is fine (a rename carried by several descriptions, a fix plus a merge).
- `uv run drakkar-publications <file> [--commit]`: publication states and notes.

They take several files at once, and `--header` prints the header line of their format. `uv run drakkar-check <dir>` checks every invariant, read-only.

Reading is read-only:

- `uv run drakkar-read publication <run_id> <pmid>`: title, abstract, note, live descriptions with their notes;
- `uv run drakkar-read entry <accession>`: snapshots, isoforms, names, chains and peptides, sequence;
- `uv run drakkar-read names <accession>`: the generic names used on the same strain, virus and family;
- `uv run drakkar-read row <stable_id>...`: live descriptions as revision rows, to edit;
- `drakkar.db.connect(readonly=True)` for anything else.
