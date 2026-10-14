"""The files of a pass (`docs/tools.md`) and the commands that write them.

Tab separated, one row per item; lines starting with `#` are ignored, so files concatenate.
In a note, `\\n` is a line break. Lists (mappings, below_threshold) are separated by `,`.

    uv run drakkar-add <file>... [--commit]
    uv run drakkar-revise <file>... [--commit]
    uv run drakkar-publications <file>... [--commit]

Without `--commit`, a dry run: everything is applied and checked, then rolled back.
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, cast

from drakkar.db import connect
from drakkar.write import (
    Description,
    NewDescription,
    Outcome,
    PublicationUpdate,
    Revision,
    add_descriptions,
    revise_descriptions,
    update_publications,
)

DESCRIPTION = [
    "method",
    "accession1",
    "accession2",
    "start2",
    "stop2",
    "name2",
    "mappings1",
    "mappings2",
    "below_threshold",
]
ADD = ["run_id", "pmid", *DESCRIPTION, "note"]
REVISE = ["stable_id", "version", "run_id", "pmid", "action", "into", *DESCRIPTION, "note"]
PUBLICATIONS = ["run_id", "pmid", "state", "note"]


class FileError(ValueError):
    pass


def _unescape(text: str) -> str:
    return text.replace("\\\\", "\0").replace("\\n", "\n").replace("\0", "\\")


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("\n", "\\n")


def read_rows(paths: Sequence[Path], columns: list[str]) -> list[tuple[str, dict[str, str]]]:
    """Rows of the files as (where, {column: value}); a `#` header, if any, must be `columns`."""
    rows: list[tuple[str, dict[str, str]]] = []
    for path in paths:
        for number, line in enumerate(path.read_text().splitlines(), 1):
            where = f"{path}:{number}"
            if not line.strip():
                continue
            if line.startswith("#"):
                fields = line[1:].split("\t")
                if fields[0] in ("run_id", "stable_id") and fields != columns:
                    raise FileError(f"{where}: header is not {' '.join(columns)}")
                continue
            values = line.split("\t")
            if len(values) != len(columns):
                raise FileError(f"{where}: {len(values)} fields, expected {len(columns)}")
            rows.append((where, dict(zip(columns, values, strict=True))))
    return rows


def header(columns: list[str]) -> str:
    return "#" + "\t".join(columns)


def _int(where: str, row: dict[str, str], column: str) -> int:
    try:
        return int(row[column])
    except ValueError:
        raise FileError(f"{where}: {column} is not a number: {row[column]!r}") from None


def _list(text: str) -> tuple[str, ...]:
    return tuple(s.strip() for s in text.split(",") if s.strip())


def _description(where: str, row: dict[str, str]) -> Description:
    return Description(
        method=row["method"].strip(),
        accession1=row["accession1"].strip(),
        accession2=row["accession2"].strip(),
        start2=_int(where, row, "start2") if row["start2"].strip() else None,
        stop2=_int(where, row, "stop2") if row["stop2"].strip() else None,
        name2=row["name2"].strip(),
        mappings1=_list(row["mappings1"]),
        mappings2=_list(row["mappings2"]),
        below_threshold=_list(row["below_threshold"]),
    )


def new_description(where: str, row: dict[str, str]) -> NewDescription:
    return NewDescription(
        _int(where, row, "run_id"),
        _int(where, row, "pmid"),
        _description(where, row),
        _unescape(row["note"]),
    )


def revision(where: str, row: dict[str, str]) -> Revision:
    action = row["action"].strip()
    if action not in ("revise", "remove"):
        raise FileError(f"{where}: action is {action!r}, not revise or remove")
    described = any(row[c].strip() for c in DESCRIPTION)
    return Revision(
        stable_id=row["stable_id"].strip(),
        version=_int(where, row, "version"),
        run_id=_int(where, row, "run_id"),
        pmid=_int(where, row, "pmid"),
        action=action,
        description=_description(where, row) if described else None,
        into=row["into"].strip(),
        note=_unescape(row["note"]),
    )


def publication(where: str, row: dict[str, str]) -> PublicationUpdate:
    state = row["state"].strip()
    if state not in ("selected", "curated"):
        raise FileError(f"{where}: state is {state!r}, not selected or curated")
    return PublicationUpdate(
        _int(where, row, "run_id"), _int(where, row, "pmid"), state, _unescape(row["note"])
    )


def format_revision(item: Revision) -> str:
    """A revision as a row of a revision file (the inverse of `revision`)."""
    d = item.description
    values: dict[str, Any] = {
        "stable_id": item.stable_id,
        "version": item.version,
        "run_id": item.run_id,
        "pmid": item.pmid,
        "action": item.action,
        "into": item.into,
        "note": _escape(item.note),
    }
    if d is not None:
        values |= {
            "method": d.method,
            "accession1": d.accession1,
            "accession2": d.accession2,
            "start2": "" if d.start2 is None else d.start2,
            "stop2": "" if d.stop2 is None else d.stop2,
            "name2": d.name2,
            "mappings1": ",".join(d.mappings1),
            "mappings2": ",".join(d.mappings2),
            "below_threshold": ",".join(d.below_threshold),
        }
    return "\t".join(str(values.get(c, "")) for c in REVISE)


# --- Commands -----------------------------------------------------------------------------------


def report(outcome: Outcome, rows: list[tuple[str, dict[str, str]]]) -> str:
    """What happened, short: refused rows, check errors, warnings on what was written."""
    lines = [f"refused {rows[number - 1][0]}: {why}" for number, why in outcome.problems]
    for result in outcome.errors:
        lines.append(f"error {result.invariant.id}: {result.invariant.title}")
        lines.append("  " + "\t".join(result.header))
        lines += ["  " + "\t".join(str(v) for v in row) for row in result.rows[:20]]
        if len(result.rows) > 20:
            lines.append(f"  … {len(result.rows) - 20} more")
    written = set(outcome.written)
    for result in outcome.results:
        if result.invariant.severity != "warning" or "stable_id" not in result.header:
            continue
        column = result.header.index("stable_id")
        if mine := [row for row in result.rows if row[column] in written]:
            lines.append(f"warning {result.invariant.id}: {result.invariant.title}")
            lines.append("  " + "\t".join(result.header))
            lines += ["  " + "\t".join(str(v) for v in row) for row in mine]
    if outcome.committed:
        verdict = "committed"
    elif outcome.ok:
        verdict = "dry run passed, rolled back"
    else:
        verdict = "failed, rolled back"
    lines.append(f"{len(rows)} rows, {len(outcome.written)} applied: {verdict}")
    return "\n".join(lines)


def _command(
    description: str,
    columns: list[str],
    parse: Callable[[str, dict[str, str]], Any],
    write: Callable[..., Outcome],
) -> None:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("files", type=Path, nargs="*", help="files of the format of docs/tools.md")
    parser.add_argument("--commit", action="store_true", help="commit if everything passes")
    parser.add_argument("--header", action="store_true", help="print the header line and exit")
    args = parser.parse_args()
    if args.header:
        print(header(columns))
        return
    try:
        rows = read_rows(cast(list[Path], args.files), columns)
        items = [parse(where, row) for where, row in rows]
        with connect() as conn:
            outcome = write(conn, items, commit=args.commit)
    except ValueError as e:  # a file error, or a stable ID given twice
        sys.exit(str(e))
    print(report(outcome, rows))
    sys.exit(0 if outcome.ok else 1)


def add_main() -> None:
    _command("Add new descriptions.", ADD, new_description, add_descriptions)


def revise_main() -> None:
    _command("Revise or remove live descriptions.", REVISE, revision, revise_descriptions)


def publications_main() -> None:
    _command(
        "Set the state and note of publications.", PUBLICATIONS, publication, update_publications
    )
