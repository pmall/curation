"""Build the fix list from a `drakkar-check` report, without writing to the database.

One row per description with a problem: its point in `docs/02-data-fixes.md` and the invariants
it violates. A description that needs several fixes goes to the last point, fixed in a single
revision. Malformed mappings (D11) are fixed in place, without a revision: they are a separate
column, not a point.
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from drakkar.db import connect

# Point of a description that needs a single fix, in fixing order. D9 is split by protein:
# human mappings (D9h) and viral mappings (D9v) are separate fixes.
POINTS = {
    "S1": 1,
    "R3": 2,
    "D7": 3,
    "D4": 4,
    "D10": 5,
    "D6": 6,
    "D5": 7,
    "D9h": 8,
    "D9v": 9,
}
SEVERAL = 10

# Descriptions of a publication that is neither `selected` nor `curated` (S1 is reported per
# publication).
S1_DESCRIPTIONS = """
    SELECT d.stable_id, r.type FROM descriptions AS d
    JOIN associations AS a ON a.id = d.association_id
    JOIN runs AS r ON r.id = a.run_id
    WHERE d.deleted_at IS NULL AND a.state NOT IN ('selected', 'curated')
"""


def read(report: Path, invariant: str) -> list[dict[str, str]]:
    """The violations of an invariant in a check report (none if it has no TSV)."""
    path = report / f"{invariant}.tsv"
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f, delimiter="\t"))


def build(report: Path, output: Path) -> None:
    problems: dict[str, set[str]] = defaultdict(set)
    in_place: set[str] = set()
    run_types: dict[str, str] = {}

    def add(stable_id: str, run_type: str, invariant: str | None) -> None:
        run_types[stable_id] = run_type
        if invariant is None:
            in_place.add(stable_id)
        else:
            problems[stable_id].add(invariant)

    for invariant in ("R3", "D4", "D7"):
        for row in read(report, invariant):
            add(row["stable_id"], row["run_type"], invariant)
    for row in read(report, "D9"):
        add(row["stable_id"], row["run_type"], "D9h" if row["protein"] == "human" else "D9v")
    for row in read(report, "D11"):
        add(row["stable_id"], row["run_type"], None)
    for invariant in ("D5", "D6", "D10"):  # one row per group of descriptions
        for row in read(report, invariant):
            for stable_id in row["stable_ids"].split():
                add(stable_id, row["run_type"], invariant)
    with connect() as conn, conn.cursor() as cur:
        cur.execute(S1_DESCRIPTIONS)
        for stable_id, run_type in cur.fetchall():
            add(stable_id, run_type, "S1")
        conn.rollback()

    rows: list[tuple[int, str, str, str, str]] = []
    for stable_id in problems.keys() | in_place:
        invariants = problems.get(stable_id, set())
        if not invariants:
            point = 0  # no revision, only the in-place fix
        elif len(invariants) == 1:
            point = POINTS[next(iter(invariants))]
        else:
            point = SEVERAL
        malformed = "yes" if stable_id in in_place else ""
        rows.append(
            (point, stable_id, run_types[stable_id], " ".join(sorted(invariants)), malformed)
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["stable_id", "run_type", "point", "invariants", "malformed_mapping"])
        for point, stable_id, run_type, invariants, malformed in sorted(rows):
            writer.writerow([stable_id, run_type, point or "", invariants, malformed])


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the fix list from a check report.")
    parser.add_argument("report", type=Path, help="e.g. data/2021_02/reports/check-2026-10-06")
    parser.add_argument("output", type=Path, help="e.g. data/2021_02/reports/fix-list.tsv")
    args = parser.parse_args()
    build(args.report, args.output)
