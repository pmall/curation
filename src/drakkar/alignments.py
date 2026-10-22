"""Align sequences on the sequences Drakkar holds.

uv run drakkar-align mapping <accession>[:<start>-<stop>] <sequence>...
    what the write computes for each mapping sequence on that interactor (`align.py`)
uv run drakkar-align closest <sequence>... --taxon <ID>
    the current entries of a taxon closest to each sequence, by a database search

Read-only. `closest` prints the best lines per sequence, bounded by `--limit <n>` (20), as
`drakkar-read`.
"""

import argparse
import json
import sys
from typing import Any, cast

import pyopal

from drakkar.align import MIN_IDENTITY, UNSCORED, best_identity, map_sequence, read_written
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
from drakkar.write import InvalidRow, snapshot_of

# The database search of `closest`: Smith-Waterman on every sequence, BLAST's protein scoring.
# Its alphabet lacks U, O and J, aligned as X (`align.py`).
SEARCH: Any = pyopal.Aligner("BLOSUM62", gap_open=11, gap_extend=1)  # pyopal is not typed


def _label(text: str) -> str:
    """An input as its line shows it: whitespace as one space, cut at 20 characters."""
    text = " ".join(text.split())
    return text if len(text) <= 20 else f"{text[:20]}…({len(text)} characters)"


def _spaced(text: str) -> str | None:
    """Why an input holding whitespace is not one sequence: several sequences in one argument
    (an unquoted shell variable, in zsh), or one with whitespace around it (a line of a file);
    every letter is an amino acid, so a name with spaces is told the same."""
    if len(text.split()) > 1:
        return f"{len(text.split())} parts separated by whitespace: one sequence per argument"
    if text != text.strip():
        return "leading or trailing whitespace around the argument"
    return None


def _queries(cur: Any, texts: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """The sequences to search, by their label, and the inputs that are none, with why."""
    queries: dict[str, str] = {}
    unread: dict[str, str] = {}
    for text in texts:
        if why := _spaced(text):
            unread[_label(text)] = why
        elif any(c.isdigit() for c in text):  # an accession, never a sequence
            try:
                queries[text] = sequence_of(cur, text)
            except ValueError as e:
                unread[text] = str(e)
        elif AMINO_ACIDS.fullmatch(text.upper()):
            queries[text if len(text) <= 20 else f"{text[:20]}…({len(text)} aa)"] = text.upper()
        else:
            unread[_label(text)] = "neither an accession nor an amino acid sequence"
    return queries, unread


def _hit(alignment: Any, accession: str, isoform: str) -> str:
    """Identity, coverage of the query and region on the isoform of a full alignment: identity
    is identical residues over the aligned columns, gaps included (`M` in pyopal's alignment)."""
    columns: str = alignment.alignment or ""
    if not columns:
        return "0.0 %\t0.0 %\taligns nowhere"
    identity = 100 * columns.count("M") / len(columns)
    coverage = 100 * (alignment.query_end - alignment.query_start + 1) / alignment.query_length
    region = f"{alignment.target_start + 1}-{alignment.target_end + 1}"
    return (
        f"{identity:.1f} %\t{coverage:.1f} %\t"
        + ("" if isoform == accession else f"{isoform}:")
        + region
    )


def closest(cur: Any, sequences: list[str], taxon: int, page: Page = DEFAULT) -> str:
    """The current entries of the taxon closest to each sequence: every isoform is aligned
    (Smith-Waterman), each entry ranked by the score of its best isoform, then Swiss-Prot
    first."""
    queries, unread = _queries(cur, sequences)
    cur.execute(
        """
        SELECT p.accession, v.reviewed, p.description, p.ncbi_taxon_id, p.sequences::text
        FROM proteins_versions AS v
        JOIN proteins AS p ON p.accession = v.accession AND v.version = p.version
        WHERE p.ncbi_taxon_id = ANY(%s)
        ORDER BY p.accession
        """,
        (subtree(cur, taxon),),
    )
    entries: list[tuple[str, bool, str, int]] = []
    isoforms: list[tuple[int, str, str]] = []  # entry index, isoform accession, sequence
    for accession, is_reviewed, description, taxon_id, text in cur.fetchall():
        for isoform, sequence in sorted(cast(dict[str, str], json.loads(text)).items()):
            isoforms.append((len(entries), isoform, sequence.translate(UNSCORED)))
        entries.append((accession, is_reviewed, description, taxon_id))
    targets = pyopal.Database([s for _, _, s in isoforms], alphabet=SEARCH.alphabet)
    names = taxon_names(cur, {e[3] for e in entries})
    lines = ["#sequence\taccession\tdb\tprotein\ttaxon\tidentity\tcoverage\tregion"]
    for label, query in queries.items():
        query = query.translate(UNSCORED)
        best: dict[int, tuple[int, int]] = {}  # entry index → score, isoform index
        scores = SEARCH.align(query, targets, mode="score", algorithm="sw")
        for index, ((owner, isoform, _), result) in enumerate(zip(isoforms, scores, strict=True)):
            canonical = isoform == entries[owner][0]
            # the best score, the canonical isoform among equals (isoforms are in name order)
            if (
                owner not in best
                or result.score > best[owner][0]
                or (result.score == best[owner][0] and canonical)
            ):
                best[owner] = (result.score, index)
        ranked = sorted(best, key=lambda e: (-best[e][0], not entries[e][1], entries[e][0]))
        shown = page.cut(ranked)
        aligned = SEARCH.align(
            query,
            pyopal.Database([isoforms[best[e][1]][2] for e in shown], alphabet=SEARCH.alphabet),
            mode="full",
            algorithm="sw",
        )
        rows: list[str] = []
        for e, alignment in zip(shown, aligned, strict=True):
            accession, is_reviewed, description, taxon_id = entries[e]
            taxon_name = names.get(taxon_id, "not in the NCBI taxonomy")
            rows.append(
                f"{accession}\t{database(is_reviewed)}\t{description}\t{taxon_id} {taxon_name}"
                f"\t{_hit(alignment, accession, isoforms[best[e][1]][1])}"
            )
        lines += page.lines(label, rows, len(ranked))
    lines += [f"{label}\t{why}" for label, why in unread.items()]
    return "\n".join(lines)


def _occurrences(aligned: dict[str, Any], canonical: str, start: int) -> str:
    """The occurrences of a mapping JSON on each isoform, in the entry's numbering: the write's
    positions on the canonical isoform are relative to the interactor's start."""
    return "; ".join(
        f"{i['accession']} "
        + ", ".join(
            f"{o['start'] + shift}-{o['stop'] + shift} ({o['identity']:g} %)"
            for o in i["occurrences"]
        )
        for i in aligned["isoforms"]
        for shift in [start - 1 if i["accession"] == canonical else 0]
    )


def mapping(cur: Any, interactor: str, sequences: list[str]) -> str:
    """What the write computes for each mapping sequence on the interactor (its current
    snapshot): extra end residues, occurrences on each isoform with their identity, in the
    entry's numbering, and whether it is below 90 %."""
    for text in sequences:
        if not _spaced(text) and any(c.isdigit() for c in text):  # an accession, not a sequence
            sys.exit(f"{text}: an accession where a sequence is expected: one interactor per call")
    try:
        accession, isoform, start, stop = location(interactor)
        if isoform != accession:
            raise ValueError("an interactor is an entry, not an isoform")
        snapshot = snapshot_of(cur, accession)
    except (ValueError, InvalidRow) as e:
        sys.exit(f"{interactor}: {e}")
    length = snapshot.length
    start, stop = start or 1, stop or length
    if not 1 <= start <= stop <= length:
        sys.exit(f"{interactor}: {start}-{stop} is outside 1-{length}")
    lines = ["#sequence\tnter\tcter\toccurrences\tverdict"]
    for text in sequences:
        if why := _spaced(text):
            lines.append(f"{_label(text)}\t{why}")
            continue
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
        occurrences = _occurrences(aligned, accession, start)
        lines.append(f"{text}\t{nter or '-'}\t{cter or '-'}\t{occurrences or '-'}\t{verdict}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Align sequences on Drakkar's sequences.")
    commands = parser.add_subparsers(dest="command", required=True)
    m = commands.add_parser("mapping", help="what the write computes for mappings")
    m.add_argument("interactor", help="<accession>[:<start>-<stop>]")
    m.add_argument("sequences", nargs="+", help="extra end residues in lowercase")
    c = commands.add_parser("closest", help="the current entries of a taxon closest to sequences")
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
