"""Check the Drakkar invariants (`docs/database.md` §4) on vh and hh data, without writing.

Each invariant is a query returning its violations, one row per violation, with the stable ID and
PMID when relevant. The report is a Markdown summary plus one TSV file per violated invariant.
The exit code is 1 if any error is found.
"""

import argparse
import csv
import json
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, LiteralString, cast

from drakkar.db import connect
from drakkar.descriptions import MIN_IDENTITY, segment_identity

Rows = tuple[list[str], list[tuple[Any, ...]]]

# Live descriptions (vh and hh) with everything needed by the checks.
LIVE = """
    CREATE TEMP TABLE live AS
    SELECT d.*, r.type AS run_type, a.pmid, a.state, r.name AS run,
           p1.accession AS accession1, p1.type AS type1, p1.name AS gene1,
           p1.ncbi_taxon_id AS taxon1, length(p1.sequences->>p1.accession) AS length1,
           p2.accession AS accession2, p2.type AS type2, p2.name AS gene2,
           p2.ncbi_taxon_id AS taxon2,
           length(p2.sequences->>p2.accession) AS length2,
           EXISTS (SELECT 1 FROM proteins_versions AS v
                   WHERE v.accession = p1.accession AND v.version = p1.version) AS current1,
           EXISTS (SELECT 1 FROM proteins_versions AS v
                   WHERE v.accession = p2.accession AND v.version = p2.version) AS current2,
           m.psimi_id
    FROM descriptions AS d
    JOIN associations AS a ON a.id = d.association_id
    JOIN runs AS r ON r.id = a.run_id
    JOIN methods AS m ON m.id = d.method_id
    JOIN proteins AS p1 ON p1.id = d.protein1_id
    JOIN proteins AS p2 ON p2.id = d.protein2_id
    WHERE d.deleted_at IS NULL
"""

# All description rows (live and deleted), for the versioning checks.
VERSIONS = """
    CREATE TEMP TABLE versions AS
    SELECT d.*, r.type AS run_type FROM descriptions AS d
    JOIN associations AS a ON a.id = d.association_id
    JOIN runs AS r ON r.id = a.run_id
"""


@dataclass
class Invariant:
    id: str
    severity: str  # "error", "warning" or "upgrade" (obsolete snapshot: the upgrade job, not a fix)
    title: str
    check: LiteralString | Callable[[Any], Rows]


SQL_INVARIANTS = [
    Invariant(
        "R3",
        "error",
        "Every protein of a live description has a row in `taxon`.",
        """
        SELECT run_type, stable_id, pmid, side, accession, taxon FROM (
            SELECT run_type, stable_id, pmid, 1 AS side, accession1 AS accession,
                   taxon1 AS taxon FROM live
            UNION ALL
            SELECT run_type, stable_id, pmid, 2, accession2, taxon2 FROM live
        ) AS x
        WHERE NOT EXISTS (SELECT 1 FROM taxon AS t WHERE t.ncbi_taxon_id = x.taxon)
        ORDER BY accession, stable_id
        """,
    ),
    Invariant(
        "V2",
        "error",
        "Versions of a stable ID are contiguous from 1.",
        """
        SELECT min(run_type) AS run_type, stable_id, min(version) AS min, max(version) AS max,
               count(*) AS versions
        FROM versions GROUP BY stable_id
        HAVING min(version) <> 1 OR max(version) <> count(*)
        ORDER BY stable_id
        """,
    ),
    Invariant(
        "V3",
        "error",
        "At most one live row per stable ID, and it is the highest version.",
        """
        SELECT min(run_type) AS run_type, stable_id,
               count(*) FILTER (WHERE deleted_at IS NULL) AS live_rows,
               max(version) AS max_version,
               max(version) FILTER (WHERE deleted_at IS NULL) AS live_version
        FROM versions GROUP BY stable_id
        HAVING count(*) FILTER (WHERE deleted_at IS NULL) > 1
            OR max(version) FILTER (WHERE deleted_at IS NULL) <> max(version)
        ORDER BY stable_id
        """,
    ),
    Invariant(
        "V4",
        "error",
        "Each non-last version is deleted, no later than the next version's creation.",
        """
        SELECT v.run_type, v.stable_id, v.version, v.deleted_at, n.created_at AS next_created_at
        FROM versions AS v
        JOIN versions AS n ON n.stable_id = v.stable_id AND n.version = v.version + 1
        WHERE v.deleted_at IS NULL OR v.deleted_at > n.created_at
        ORDER BY v.stable_id, v.version
        """,
    ),
    Invariant(
        "V5",
        "error",
        "`deleted_at` is not before `created_at`.",
        """
        SELECT run_type, stable_id, version, created_at, deleted_at FROM versions
        WHERE deleted_at < created_at ORDER BY stable_id, version
        """,
    ),
    Invariant(
        "V6",
        "error",
        "All versions of a stable ID belong to the same publication.",
        """
        SELECT min(run_type) AS run_type, stable_id,
               count(DISTINCT association_id) AS associations FROM versions
        GROUP BY stable_id HAVING count(DISTINCT association_id) > 1 ORDER BY stable_id
        """,
    ),
    Invariant(
        "V7",
        "error",
        "Stable ID format: `EY` or `CW` + 8 uppercase hexadecimal characters (legacy hh bulk "
        "import: `EYUW` + 6 hexadecimal characters).",
        """
        SELECT DISTINCT run_type, stable_id FROM versions
        WHERE stable_id !~ '^((EY|CW)[0-9A-F]{8}|EYUW[0-9A-F]{6})$' ORDER BY stable_id
        """,
    ),
    Invariant(
        "D1",
        "error",
        "Protein 1 is human; protein 2 is viral in vh runs, human in hh runs.",
        """
        SELECT run_type, stable_id, pmid, accession1, type1, accession2, type2 FROM live
        WHERE type1 <> 'h' OR type2 <> (CASE run_type WHEN 'vh' THEN 'v' ELSE 'h' END)
        ORDER BY pmid, stable_id
        """,
    ),
    Invariant(
        "D2",
        "upgrade",
        "Both proteins are current snapshots (latest UniProt release).",
        """
        SELECT run_type, stable_id, pmid, side, accession FROM (
            SELECT run_type, stable_id, pmid, 1 AS side, accession1 AS accession
            FROM live WHERE NOT current1
            UNION ALL
            SELECT run_type, stable_id, pmid, 2, accession2 FROM live WHERE NOT current2
        ) AS x ORDER BY accession, stable_id
        """,
    ),
    Invariant(
        "D3",
        "error",
        "Viral interactors: 1 ≤ start ≤ stop ≤ canonical length (human ones: D4).",
        """
        SELECT run_type, stable_id, pmid, 2 AS side, accession2 AS accession,
               start2 AS start, stop2 AS stop, length2 AS length FROM live
        WHERE type2 = 'v' AND (start2 < 1 OR start2 > stop2 OR stop2 > length2)
        ORDER BY accession, stable_id
        """,
    ),
    Invariant(
        "D4",
        "error",
        "Human interactors are the full protein (start = 1, stop = canonical length).",
        """
        SELECT run_type, stable_id, pmid, side, accession, start, stop, length FROM (
            SELECT run_type, stable_id, pmid, 1 AS side, accession1 AS accession,
                   start1 AS start, stop1 AS stop, length1 AS length FROM live
            UNION ALL
            SELECT run_type, stable_id, pmid, 2, accession2, start2, stop2, length2
            FROM live WHERE type2 = 'h'
        ) AS x
        WHERE start <> 1 OR stop <> length ORDER BY accession, stable_id
        """,
    ),
    Invariant(
        "D5",
        "error",
        "One live description per (publication, method, interactor 1, interactor 2).",
        """
        SELECT run_type, pmid, psimi_id, accession1, start1, stop1, accession2, start2, stop2,
               count(*) AS descriptions, string_agg(stable_id, ' ' ORDER BY stable_id) AS stable_ids
        FROM live
        GROUP BY run_type, association_id, pmid, psimi_id, accession1, start1, stop1,
                 accession2, start2, stop2
        HAVING count(*) > 1
        ORDER BY pmid, accession1, accession2
        """,
    ),
    Invariant(
        "D6",
        "error",
        "One non-empty generic name (`name2`) per viral interactor (accession, start, stop).",
        """
        SELECT run_type, accession2, start2, stop2,
               string_agg(DISTINCT name2, ' | ') AS names, count(*) AS descriptions,
               string_agg(stable_id, ' ' ORDER BY stable_id) AS stable_ids
        FROM live WHERE run_type = 'vh'
        GROUP BY run_type, accession2, start2, stop2
        HAVING count(DISTINCT name2) > 1 OR bool_or(trim(name2) = '')
        ORDER BY accession2, start2
        """,
    ),
    Invariant(
        "D10",
        "error",
        "One viral interactor (start, stop) per generic name of a viral protein "
        "(accession, `name2`).",
        """
        SELECT run_type, accession2, name2,
               string_agg(DISTINCT start2 || '-' || stop2, ' | ') AS coordinates,
               count(*) AS descriptions,
               string_agg(stable_id, ' ' ORDER BY stable_id) AS stable_ids
        FROM live WHERE run_type = 'vh'
        GROUP BY run_type, accession2, name2
        HAVING count(DISTINCT (start2, stop2)) > 1
        ORDER BY accession2, name2
        """,
    ),
    Invariant(
        "D7",
        "warning",
        "Human names (`name1`, and `name2` in hh) are the gene name of their snapshot.",
        """
        SELECT run_type, stable_id, pmid, side, accession, name, gene FROM (
            SELECT run_type, stable_id, pmid, 1 AS side, accession1 AS accession,
                   name1 AS name, gene1 AS gene FROM live
            UNION ALL
            SELECT run_type, stable_id, pmid, 2, accession2, name2, gene2
            FROM live WHERE run_type = 'hh'
        ) AS x
        WHERE name <> gene ORDER BY accession, stable_id
        """,
    ),
    Invariant(
        "S1",
        "error",
        "A publication with a live description is `selected` (curation in progress) or `curated`.",
        """
        SELECT run_type, pmid, run, state, count(*) AS descriptions FROM live
        WHERE state NOT IN ('selected', 'curated') GROUP BY run_type, pmid, run, state
        ORDER BY pmid
        """,
    ),
    Invariant(
        "S5",
        "error",
        "Run names are unique.",
        "SELECT name, count(*) FROM runs GROUP BY name HAVING count(*) > 1 ORDER BY name",
    ),
]


AMINO_ACIDS = re.compile(r"[ACDEFGHIKLMNPQRSTVWYUOXBZJ]+")
OCCURRENCE_KEYS = ("start", "stop", "identity")
# How far below its recorded identity a slice may align: legacy gap placement, up to 0.47 point.
IDENTITY_TOLERANCE = 1.0
# The threshold legacy descriptions were curated with; `MIN_IDENTITY` applies to Claude's (`CW`).
# Both are warnings (D12), never errors.
LEGACY_MIN_IDENTITY = 96.0
NUMBER = re.compile(r"\d+(\.\d+)?")

# The description sides with mappings, with what the mapping checks need.
MAPPING_SIDES = """
    SELECT l.run_type, l.stable_id, l.pmid, x.side, x.type, x.accession, x.start, x.stop,
           x.mapping::text, p.sequences::text
    FROM live AS l
    CROSS JOIN LATERAL (VALUES
        (1, l.type1, l.accession1, l.start1, l.stop1, l.mapping1, l.protein1_id),
        (2, l.type2, l.accession2, l.start2, l.stop2, l.mapping2, l.protein2_id))
        AS x (side, type, accession, start, stop, mapping, protein_id)
    JOIN proteins AS p ON p.id = x.protein_id
    WHERE x.mapping IS NULL OR json_typeof(x.mapping) <> 'array'
       OR json_array_length(x.mapping) > 0
"""


def _number(value: Any, strict: bool = True) -> float | None:
    """A JSON number as a float; unless `strict`, a number stored as text too; None otherwise."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not strict and isinstance(value, str) and NUMBER.fullmatch(value):
        return float(value)
    return None


def mapping_structure(mappings: Any, strict: bool = True) -> list[str]:
    """Structure and type problems of a mapping column (D11), without looking at the content.

    The structure is a list of objects `{"sequence": string, "isoforms": [{"accession": string,
    "occurrences": [{"start": number, "stop": number, "identity": number}]}]}`. Unless `strict`,
    numbers stored as text are accepted, so that D9 can read the content.
    """
    if not isinstance(mappings, list):
        return ["not a list of mappings"]
    problems: set[str] = set()
    for mapping in cast(list[Any], mappings):
        if not isinstance(mapping, dict):
            problems.add("a mapping is not an object")
            continue
        fields = cast(dict[str, Any], mapping)
        if not isinstance(fields.get("sequence"), str):
            problems.add("a sequence is not a string")
        isoforms = fields.get("isoforms")
        if not isinstance(isoforms, list):
            problems.add("isoforms is not a list")
            continue
        for isoform in cast(list[Any], isoforms):
            if not isinstance(isoform, dict):
                problems.add("an isoform is not an object")
                continue
            entry = cast(dict[str, Any], isoform)
            if not isinstance(entry.get("accession"), str):
                problems.add("an isoform accession is not a string")
            occurrences = entry.get("occurrences")
            if not isinstance(occurrences, list):
                problems.add("occurrences is not a list")
                continue
            for occurrence in cast(list[Any], occurrences):
                if not isinstance(occurrence, dict):
                    problems.add("an occurrence is not an object")
                    continue
                values = cast(dict[str, Any], occurrence)
                for key in OCCURRENCE_KEYS:
                    if _number(values.get(key), strict) is not None:
                        continue
                    if _number(values.get(key), strict=False) is not None:
                        problems.add("numbers stored as text")
                    else:
                        problems.add(f"an occurrence {key} is not a number")
    return sorted(problems)


def _misfit(
    mapping: dict[str, Any],
    isoforms: dict[str, str],
    accession: str,
    start: int,
    stop: int,
) -> str:
    """Why the occurrences of a mapping do not fit the sequences of its snapshot, or "".

    Each stored occurrence is judged on its own, against the protein segment at its coordinates:
    an occurrence recorded at 100 % must be exactly the mapping; otherwise the mapping aligned end
    to end on the segment must be no more than `IDENTITY_TOLERANCE` below the recorded identity.
    Low identities are warnings (D12), not misfits. Whether the mapping could also be found
    elsewhere, or on other isoforms, is not checked.
    """
    occurrences = [
        (i["accession"], *(cast(float, _number(o[k], strict=False)) for k in OCCURRENCE_KEYS))
        for i in mapping["isoforms"]
        for o in i["occurrences"]
    ]
    if not occurrences:
        return "no occurrence"
    for isoform, first, last, stored in occurrences:
        sequence = isoforms.get(isoform)
        if sequence is None:
            return f"isoform {isoform} not in the snapshot"
        if isoform == accession:
            sequence = sequence[start - 1 : stop]
        if not 1 <= first <= last <= len(sequence):
            return f"occurrence {first:g}-{last:g} outside {isoform}"
        segment = sequence[int(first) - 1 : int(last)]
        if stored == 100 and segment != mapping["sequence"]:
            return f"100 % occurrence {first:g}-{last:g} does not match {isoform}"
        identity = segment_identity(mapping["sequence"], segment)
        if identity < stored - IDENTITY_TOLERANCE:
            return (
                f"occurrence {first:g}-{last:g} on {isoform} recorded at {stored:g} %, "
                f"{identity:g} % at its coordinates"
            )
    return ""


def _protein(type_: str) -> str:
    return {"h": "human", "v": "viral"}.get(type_, type_)


def check_d9(cur: Any) -> Rows:
    """Mapping content: an amino acid sequence, once, with an occurrence that fits (C4).

    Every stored occurrence must be true to its coordinates (`_misfit`), whatever its identity
    (low identities are D12 warnings). Occurrence positions are relative to the interactor
    region [start, stop] on the canonical isoform, to the whole sequence on other isoforms.
    Mappings whose structure cannot be read are left to D11; numbers stored as text are read as
    numbers. `protein` tells a human mapping from a viral one, which are separate fixes.
    """
    cur.execute(MAPPING_SIDES)
    rows: list[tuple[Any, ...]] = []
    for row in cur.fetchall():
        run_type, stable_id, pmid, side, type_, accession, start, stop, text, sequences = row
        mappings: Any = json.loads(text or "null")
        if mapping_structure(mappings, strict=False):
            continue
        isoforms: dict[str, str] = json.loads(sequences)
        seen: set[str] = set()
        for mapping in mappings:
            sequence = mapping["sequence"]
            problems: list[str] = []
            if not AMINO_ACIDS.fullmatch(sequence):
                problems.append("sequence is not an uppercase amino acid sequence")
            if sequence in seen:
                problems.append("duplicate mapping sequence")
            seen.add(sequence)
            if misfit := _misfit(mapping, isoforms, accession, start, stop):
                problems.append(misfit)
            if problems:
                rows.append(
                    (
                        run_type,
                        stable_id,
                        pmid,
                        side,
                        _protein(type_),
                        accession,
                        len(sequence),
                        "; ".join(problems),
                    )
                )
    header = [
        "run_type",
        "stable_id",
        "pmid",
        "side",
        "protein",
        "accession",
        "mapping_length",
        "problem",
    ]
    return header, rows


def check_d12(cur: Any) -> Rows:
    """Mapping identity (warning): the best recorded identity of a mapping is below the threshold.

    `LEGACY_MIN_IDENTITY` (96 %) for legacy descriptions, `MIN_IDENTITY` (90 %) for Claude's
    `CW` ones. A mapping below 90 % is explained in the note of its publication (C4).
    """
    cur.execute(MAPPING_SIDES)
    rows: list[tuple[Any, ...]] = []
    for row in cur.fetchall():
        run_type, stable_id, pmid, side, type_, accession, _, _, text, _ = row
        mappings: Any = json.loads(text or "null")
        if mapping_structure(mappings, strict=False):
            continue
        threshold = MIN_IDENTITY if stable_id.startswith("CW") else LEGACY_MIN_IDENTITY
        for mapping in mappings:
            identities = [
                cast(float, _number(o["identity"], strict=False))
                for i in mapping["isoforms"]
                for o in i["occurrences"]
            ]
            if identities and max(identities) < threshold:
                rows.append(
                    (
                        run_type,
                        stable_id,
                        pmid,
                        side,
                        _protein(type_),
                        accession,
                        len(mapping["sequence"]),
                        max(identities),
                        threshold,
                    )
                )
    header = [
        "run_type",
        "stable_id",
        "pmid",
        "side",
        "protein",
        "accession",
        "mapping_length",
        "best_identity",
        "threshold",
    ]
    return header, rows


def check_d11(cur: Any) -> Rows:
    """Mapping structure: the shape and the types of the JSON, not its content.

    Every version is checked, live or deleted: a structure problem is fixed in place, without a
    revision, in all the rows that have it (`docs/database.md` §2). One row per version side.
    """
    cur.execute("""
        SELECT r.type, d.stable_id, d.version, d.deleted_at IS NULL, a.pmid, x.side, p.type,
               p.accession, x.mapping::text
        FROM descriptions AS d
        JOIN associations AS a ON a.id = d.association_id
        JOIN runs AS r ON r.id = a.run_id
        CROSS JOIN LATERAL (VALUES (1, d.mapping1, d.protein1_id), (2, d.mapping2, d.protein2_id))
            AS x (side, mapping, protein_id)
        JOIN proteins AS p ON p.id = x.protein_id
    """)
    rows: list[tuple[Any, ...]] = []
    for run_type, stable_id, version, live, pmid, side, type_, accession, text in cur.fetchall():
        if problems := mapping_structure(json.loads(text or "null")):
            rows.append(
                (
                    run_type,
                    stable_id,
                    version,
                    "yes" if live else "no",
                    pmid,
                    side,
                    _protein(type_),
                    accession,
                    "; ".join(problems),
                )
            )
    header = [
        "run_type",
        "stable_id",
        "version",
        "live",
        "pmid",
        "side",
        "protein",
        "accession",
        "problem",
    ]
    return header, rows


def run(output: Path) -> int:
    start = time.time()
    output.mkdir(parents=True, exist_ok=True)
    invariants = [
        *SQL_INVARIANTS,
        Invariant(
            "D9",
            "error",
            "Mapping content: an amino acid sequence, once per side, with occurrences true to "
            "their coordinates: exact at 100 %, otherwise within 1 point of the identity at "
            "those coordinates.",
            check_d9,
        ),
        Invariant(
            "D12",
            "warning",
            "Mapping identity: the best occurrence of a mapping is below 96 % (legacy) or 90 % "
            "(CW); below 90 %, the note of the publication explains it.",
            check_d12,
        ),
        Invariant(
            "D11",
            "error",
            "Mapping structure, every version: a list of objects with the expected fields "
            "and JSON types (numbers as text are fixed in place).",
            check_d11,
        ),
    ]
    invariants.sort(key=lambda i: (i.id[0] != "R", i.id[0] != "V", i.id[0], int(i.id[1:])))
    summary: list[tuple[Invariant, int, int]] = []  # violations in vh, in hh
    # Only temporary tables are created, and the transaction is always rolled back.
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(LIVE)
        cur.execute(VERSIONS)
        cur.execute("SELECT run_type, count(*), count(DISTINCT pmid) FROM live GROUP BY 1")
        scope = {t: (n, p) for t, n, p in cur.fetchall()}
        for invariant in invariants:
            if callable(invariant.check):
                header, rows = invariant.check(cur)
            else:
                cur.execute(invariant.check)
                header = [c.name for c in cur.description or []]
                rows = cur.fetchall()
            types = [row[header.index("run_type")] for row in rows] if "run_type" in header else []
            summary.append((invariant, types.count("vh"), types.count("hh")))
            path = output / f"{invariant.id}.tsv"
            if rows:
                with path.open("w") as f:
                    writer = csv.writer(f, delimiter="\t", lineterminator="\n")
                    writer.writerow(header)
                    writer.writerows(rows)
            else:
                path.unlink(missing_ok=True)
            print(f"[{time.time() - start:6.1f}s] {invariant.id}: {len(rows)}", file=sys.stderr)
            if rows and "run_type" not in header:  # global invariant (runs)
                summary[-1] = (invariant, len(rows), 0)
        conn.rollback()

    lines = [
        f"# Drakkar check, {date.today()}",
        "",
        "Live descriptions: "
        + ", ".join(f"{t} {n} in {p} publications" for t, (n, p) in sorted(scope.items()))
        + ". One TSV per violated invariant in this directory (rows of the violations).",
        "",
        "| ID | Severity | Invariant | vh | hh |",
        "|---|---|---|---:|---:|",
    ]
    lines += [f"| {i.id} | {i.severity} | {i.title} | {v} | {h} |" for i, v, h in summary]
    (output / "check.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return int(any((v or h) and i.severity == "error" for i, v, h in summary))


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the Drakkar invariants, read-only.")
    parser.add_argument("output", type=Path, help="e.g. data/2026_03/reports/check")
    args = parser.parse_args()
    sys.exit(run(args.output))
