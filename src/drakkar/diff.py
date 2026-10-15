"""Diff the descriptions of one publication, as curated, against its live descriptions.

A curation gives the whole list of a publication's descriptions; the diff says what writing it
would change (`docs/tools.md`). Descriptions are matched on what makes them one description
(`glossary.md`): method, human accession, viral accession and coordinates, empty
coordinates being the full protein. A matched description whose generic name or mapping
sequences differ is revised; `below_threshold` is not compared, it follows from the mappings.
A curated description without a match is added, a live one without a match is deleted. The
publication is given, so an empty list deletes every live description.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from drakkar.write import DATE, Description, NewDescription, Revision, live_revisions

CREATED = re.compile(re.escape(DATE) + r" CREATED: (.+)")

Key = tuple[str, str, str, int | None, int | None]


@dataclass(frozen=True)
class Diff:
    same: list[str]  # stable IDs of the live descriptions the curation leaves as they are
    added: list[NewDescription]
    revised: list[Revision]
    deleted: list[Revision]


def _label(d: Description) -> str:
    region = "" if d.start2 is None and d.stop2 is None else f"[{d.start2}-{d.stop2}]"
    return f"{d.method} {d.accession1} × {d.accession2}{region}"


def _full_length(cur: Any, accession: str) -> int | None:
    """The length of the current snapshot of an accession, if it has one."""
    cur.execute(
        """
        SELECT length(p.sequences->>p.accession) FROM proteins AS p
        JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
        WHERE p.accession = %s
        """,
        (accession,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def _key(cur: Any, d: Description) -> Key:
    """Method and interactors; empty coordinates are the full current protein."""
    start2 = 1 if d.start2 is None else d.start2
    stop2 = _full_length(cur, d.accession2) if d.stop2 is None else d.stop2
    return d.method, d.accession1, d.accession2, start2, stop2


def _changes(live: Description, curated: Description) -> list[str]:
    changes: list[str] = []
    if live.name2 != curated.name2:
        changes.append(f"name2 {live.name2} → {curated.name2}")
    for side, old, new in (
        (1, live.mappings1, curated.mappings1),
        (2, live.mappings2, curated.mappings2),
    ):
        added, removed = len(set(new) - set(old)), len(set(old) - set(new))
        if added or removed:
            changes.append(f"mappings{side} {added} added, {removed} removed")
    return changes


def _revised_note(changes: list[str], note: str) -> str:
    """The `REVISED` note of a matched description: what changed, then the curation's evidence."""
    lines = note.strip().split("\n") if note.strip() else []
    evidence = ""
    if lines and (created := CREATED.fullmatch(lines[0])):
        evidence, lines = f"; {created[1]}", lines[1:]
    details = [line for line in lines if line.startswith("- ")]
    return "\n".join([f"{DATE} REVISED: re-curation, {', '.join(changes)}{evidence}", *details])


def diff_descriptions(cur: Any, run_id: int, pmid: int, curated: Sequence[NewDescription]) -> Diff:
    """What writing `curated`, the whole curation of a publication, would change."""
    cur.execute("SELECT 1 FROM associations WHERE run_id = %s AND pmid = %s", (run_id, pmid))
    if cur.fetchone() is None:
        raise ValueError(f"publication {pmid} is not in run {run_id}")
    by_key: dict[Key, NewDescription] = {}
    for item in curated:
        if (item.run_id, item.pmid) != (run_id, pmid):
            raise ValueError(
                f"{_label(item.description)} is in publication {item.pmid} of run {item.run_id}, "
                f"not {pmid} of run {run_id}"
            )
        key = _key(cur, item.description)
        if key in by_key:
            raise ValueError(f"{_label(item.description)} is curated twice")
        by_key[key] = item

    diff = Diff([], [], [], [])
    for live in live_revisions(cur, run_id, pmid):
        assert live.description is not None
        item = by_key.pop(_key(cur, live.description), None)
        if item is None:
            note = f"{DATE} REMOVED: not found by the re-curation"
            diff.deleted.append(replace(live, action="remove", description=None, note=note))
        elif changes := _changes(live.description, item.description):
            note = _revised_note(changes, item.note)
            diff.revised.append(replace(live, description=item.description, note=note))
        else:
            diff.same.append(live.stable_id)
    diff.added.extend(by_key.values())
    return diff
