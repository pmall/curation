"""Align sequences as the write does (`align.py`), on the sequences Drakkar holds.

uv run drakkar-align mapping <accession>[:<start>-<stop>] <sequence>...
    what the write computes for each mapping sequence on that interactor
uv run drakkar-align closest <sequence>... --taxon <ID>
    the current entries of a taxon ranked by identity with each sequence

Read-only. `closest` prints the best lines per sequence, bounded by `--limit <n>` (20), as the
lookups of `drakkar-read`.
"""

import argparse
import json
import sys
from typing import Any, cast

from drakkar.align import MIN_IDENTITY, best_identity, map_sequence, read_written
from drakkar.check import AMINO_ACIDS
from drakkar.db import connect
from drakkar.read import (
    DEFAULT,
    LIMIT,
    Page,
    database,
    location,
    sequence_of,
    subtree,
    taxon_names,
)
from drakkar.write import (
    InvalidRow,
    _snapshot,  # pyright: ignore[reportPrivateUsage]
)


def _region(aligned: dict[str, Any], canonical: str) -> str:
    """The occurrences of a mapping: `1-15` on the canonical isoform, `P04439-2:1-15` on another,
    each with its identity when below the best."""
    best = best_identity(aligned)
    return ", ".join(
        ("" if i["accession"] == canonical else f"{i['accession']}:")
        + f"{o['start']}-{o['stop']}"
        + ("" if o["identity"] == best else f" ({o['identity']:g} %)")
        for i in aligned["isoforms"]
        for o in i["occurrences"]
    )


def _map_entry(query: str, accession: str, sequences: str) -> dict[str, Any]:
    """A sequence mapped on a whole entry, its isoforms given as JSON."""
    isoforms = cast(dict[str, str], json.loads(sequences))
    return map_sequence(query, isoforms, accession, 1, len(isoforms[accession]))


def closest(cur: Any, sequences: list[str], taxon: int, page: Page = DEFAULT) -> str:
    """The current entries of the taxon ranked by identity with each sequence, as the write
    computes it for a mapping on the whole entry, then Swiss-Prot first."""
    queries: dict[str, str] = {}
    unread: dict[str, str] = {}  # an input that is no sequence, and why
    for text in sequences:
        if any(c.isdigit() for c in text):  # an accession, never a sequence
            try:
                queries[text] = sequence_of(cur, text)
            except ValueError as e:
                unread[text] = str(e)
        elif AMINO_ACIDS.fullmatch(text.upper()):
            queries[text if len(text) <= 20 else f"{text[:20]}…({len(text)} aa)"] = text.upper()
        else:
            unread[text[:20]] = "neither an accession nor an amino acid sequence"
    cur.execute(
        """
        SELECT p.accession, v.reviewed, p.description, p.ncbi_taxon_id, p.sequences::text
        FROM proteins_versions AS v
        JOIN proteins AS p ON p.accession = v.accession AND v.version = p.version
        WHERE p.ncbi_taxon_id = ANY(%s)
        """,
        (subtree(cur, taxon),),
    )
    entries = cur.fetchall()
    names = taxon_names(cur, {e[3] for e in entries})
    lines = ["#sequence\taccession\tdb\tprotein\ttaxon\tidentity\tregion"]
    for label, query in queries.items():
        ranked: list[tuple[float, bool, str, str]] = []
        for accession, is_reviewed, description, taxon_id, isoforms in entries:
            aligned = _map_entry(query, accession, isoforms)
            identity = best_identity(aligned)
            taxon_name = names.get(taxon_id, "not in the NCBI taxonomy")
            ranked.append(
                (
                    identity,
                    is_reviewed,
                    accession,
                    f"{accession}\t{database(is_reviewed)}\t{description}\t{taxon_id} {taxon_name}"
                    f"\t{identity:.1f} %\t{_region(aligned, accession) or 'aligns nowhere'}",
                )
            )
        ranked.sort(key=lambda r: (-r[0], not r[1], r[2]))
        lines += page.lines(label, [r[3] for r in ranked])
    lines += [f"{label}\t{why}" for label, why in unread.items()]
    return "\n".join(lines)


def mapping(cur: Any, interactor: str, sequences: list[str]) -> str:
    """What the write computes for each mapping sequence on the interactor (its current
    snapshot): extra end residues, occurrences on each isoform with their identity (on the
    canonical isoform, relative to the interactor's start), and whether it is below 90 %."""
    try:
        accession, isoform, start, stop = location(interactor)
        if isoform != accession:
            raise ValueError("an interactor is an entry, not an isoform")
        snapshot = _snapshot(cur, accession)
    except (ValueError, InvalidRow) as e:
        sys.exit(f"{interactor}: {e}")
    length = len(snapshot.sequences[accession])
    start, stop = start or 1, stop or length
    if not 1 <= start <= stop <= length:
        sys.exit(f"{interactor}: {start}-{stop} is outside 1-{length}")
    lines = ["#sequence\tnter\tcter\toccurrences\tverdict"]
    for text in sequences:
        try:
            sequence, nter, cter = read_written(text)
        except ValueError as e:
            lines.append(f"{text}\t{e}")
            continue
        if not AMINO_ACIDS.fullmatch(sequence):
            lines.append(f"{text}\tnot an amino acid sequence")
            continue
        aligned = map_sequence(sequence, snapshot.sequences, accession, start, stop, nter, cter)
        identity = best_identity(aligned)
        verdict = (
            "aligns nowhere"
            if not aligned["isoforms"]
            else f"below {MIN_IDENTITY:g} %"
            if identity < MIN_IDENTITY
            else "ok"
        )
        occurrences = "; ".join(
            f"{i['accession']} "
            + ", ".join(f"{o['start']}-{o['stop']} ({o['identity']:g} %)" for o in i["occurrences"])
            for i in aligned["isoforms"]
        )
        lines.append(f"{text}\t{nter or '-'}\t{cter or '-'}\t{occurrences or '-'}\t{verdict}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Align sequences as the write does.")
    commands = parser.add_subparsers(dest="command", required=True)
    m = commands.add_parser("mapping", help="what the write computes for mappings")
    m.add_argument("interactor", help="<accession>[:<start>-<stop>]")
    m.add_argument("sequences", nargs="+", help="extra end residues in lowercase")
    c = commands.add_parser("closest", help="the current entries of a taxon by identity")
    c.add_argument("sequences", nargs="+", help="a sequence, or <accession>[:<start>-<stop>]")
    c.add_argument("--taxon", type=int, required=True, help="NCBI taxon ID: its whole subtree")
    c.add_argument("--limit", type=int, default=LIMIT, help=f"lines per sequence ({LIMIT})")
    args = parser.parse_args()
    with connect(readonly=True) as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '30s'")
        if args.command == "mapping":
            print(mapping(cur, args.interactor, args.sequences))
            return
        print(closest(cur, args.sequences, args.taxon, Page(args.limit)))
