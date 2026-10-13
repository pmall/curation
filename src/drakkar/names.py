"""Generic names already used near a viral protein, to name it as Drakkar does.

Read-only. For a viral accession, lists the generic names of the live vh descriptions on the
same strain (NCBI taxon of the entry), then on the other strains of its virus (NCBI species),
then on the other viruses of its family: per name, its viral interactors and descriptions.
"""

import argparse
import sys
from collections import defaultdict
from typing import Any

from drakkar.db import connect

LEVELS = ("strain", "virus", "family")


def _snapshot(cur: Any, accession: str) -> tuple[int, str] | None:
    """Taxon and description of the current snapshot, else of the latest one."""
    cur.execute(
        """
        SELECT p.ncbi_taxon_id, p.description
        FROM proteins AS p
        LEFT JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
        WHERE p.accession = %s AND p.type = 'v'
        ORDER BY v.accession IS NOT NULL DESC, p.id DESC
        LIMIT 1
        """,
        (accession,),
    )
    row = cur.fetchone()
    return (row[0], row[1]) if row else None


def _uses(cur: Any) -> list[tuple[int, str, int, int, str, int]]:
    """Live vh viral interactors on current snapshots, with their taxon and description count."""
    cur.execute(
        """
        SELECT p.ncbi_taxon_id, p.accession, d.start2, d.stop2, d.name2, count(*)
        FROM descriptions AS d
        JOIN associations AS a ON a.id = d.association_id
        JOIN runs AS r ON r.id = a.run_id AND r.type = 'vh'
        JOIN proteins AS p ON p.id = d.protein2_id
        JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
        WHERE d.deleted_at IS NULL
        GROUP BY 1, 2, 3, 4, 5
        """
    )
    return cur.fetchall()


def _lineages(cur: Any, taxa: set[int]) -> dict[int, dict[str, tuple[int, str]]]:
    """Species and family (NCBI ID, scientific name) of each taxon, one walk up the tree."""
    cur.execute(
        """
        WITH RECURSIVE walk AS (
            SELECT t.ncbi_taxon_id AS leaf, t.taxon_id, t.parent_taxon_id, t.node_rank
            FROM taxon AS t WHERE t.ncbi_taxon_id = ANY(%s)
            UNION ALL
            SELECT w.leaf, t.taxon_id, t.parent_taxon_id, t.node_rank
            FROM walk AS w JOIN taxon AS t ON t.taxon_id = w.parent_taxon_id
            WHERE w.node_rank <> 'family' AND t.taxon_id <> w.taxon_id
        )
        SELECT w.leaf, w.node_rank, t.ncbi_taxon_id, n.name
        FROM walk AS w
        JOIN taxon AS t ON t.taxon_id = w.taxon_id
        LEFT JOIN taxon_name AS n ON n.taxon_id = w.taxon_id AND n.name_class = 'scientific name'
        WHERE w.node_rank IN ('species', 'family')
        """,
        (list(taxa),),
    )
    lineages: dict[int, dict[str, tuple[int, str]]] = defaultdict(dict)
    for leaf, rank, ncbi_id, name in cur.fetchall():
        lineages[leaf].setdefault(rank, (ncbi_id, name or str(ncbi_id)))
    return lineages


def _taxon_name(cur: Any, ncbi_taxon_id: int) -> str:
    cur.execute(
        """
        SELECT n.name FROM taxon AS t
        JOIN taxon_name AS n ON n.taxon_id = t.taxon_id AND n.name_class = 'scientific name'
        WHERE t.ncbi_taxon_id = %s
        """,
        (ncbi_taxon_id,),
    )
    row = cur.fetchone()
    return row[0] if row else f"taxon {ncbi_taxon_id} (not in the NCBI taxonomy)"


def names(accession: str) -> str:
    with connect(readonly=True) as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '30s'")
        snapshot = _snapshot(cur, accession)
        if snapshot is None:
            sys.exit(f"{accession}: no viral protein with this accession")
        taxon, description = snapshot
        uses = _uses(cur)
        lineages = _lineages(cur, {u[0] for u in uses} | {taxon})
        own = lineages.get(taxon, {})

        def level(use_taxon: int) -> str | None:
            if use_taxon == taxon:
                return "strain"
            other = lineages.get(use_taxon, {})
            for rank, label in (("species", "virus"), ("family", "family")):
                if rank in own and other.get(rank) == own[rank]:
                    return label
            return None

        # level -> name -> interactor -> descriptions
        found: dict[str, dict[str, dict[str, int]]] = {lv: defaultdict(dict) for lv in LEVELS}
        for use_taxon, acc, start, stop, name, count in uses:
            lv = level(use_taxon)
            if lv is not None:
                found[lv][name][f"{acc} [{start}-{stop}]"] = count

        heads = {
            "strain": f"{_taxon_name(cur, taxon)} ({taxon})",
            "virus": "{1} ({0})".format(*own["species"]) if "species" in own else None,
            "family": "{1} ({0})".format(*own["family"]) if "family" in own else None,
        }
    lines = [f"# Generic names near {accession} ({description})", ""]
    for lv in LEVELS:
        head = heads[lv]
        others = (
            " (other strains)" if lv == "virus" else " (other viruses)" if lv == "family" else ""
        )
        if head is None:
            lines += [f"## {lv.capitalize()}: no {lv} in the NCBI lineage", ""]
            continue
        lines += [f"## {lv.capitalize()}: {head}{others}", ""]
        if not found[lv]:
            lines += ["No generic name.", ""]
            continue
        lines += ["| Generic name | Descriptions | Viral interactors |", "| --- | ---: | --- |"]
        for name in sorted(found[lv], key=lambda n: (n.lower(), n)):
            interactors = found[lv][name]
            listed = ", ".join(f"{i} ({c})" for i, c in sorted(interactors.items()))
            lines.append(f"| `{name}` | {sum(interactors.values())} | {listed} |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List the generic names already used for the strain, virus and family "
        "of a viral protein (read-only)."
    )
    parser.add_argument("accession", help="UniProt accession of the viral protein")
    args = parser.parse_args()
    print(names(args.accession))


if __name__ == "__main__":
    main()
