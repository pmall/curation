"""Read what a curation decision needs, complete and short (read-only).

uv run drakkar-read publication <run_id> <pmid>   title, abstract, note, live descriptions
uv run drakkar-read entry <accession>             snapshots, sequences, names, chains
uv run drakkar-read names <accession>             generic names used near a viral protein
uv run drakkar-read row <stable_id>...            live descriptions as revision rows
"""

import argparse
import json
import sys
from collections import defaultdict
from typing import Any, cast

from drakkar.db import connect
from drakkar.files import REVISE, format_revision, header
from drakkar.write import live_revisions


def _text(value: Any) -> str:
    """PubMed XML as JSON: a string, or a structure whose strings are the text."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_text(v) for v in cast(list[Any], value))
    if isinstance(value, dict):
        fields = cast(dict[str, Any], value)
        return " ".join(_text(v) for k, v in fields.items() if k != "@attributes")
    return "" if value is None else str(value)


def publication(cur: Any, run_id: int, pmid: int) -> str:
    cur.execute(
        """
        SELECT r.type, a.state, a.annotation, a.ai_pass_at,
               p.metadata->'PubmedArticle'->'MedlineCitation'->'Article'
        FROM associations AS a JOIN runs AS r ON r.id = a.run_id
        JOIN publications AS p ON p.pmid = a.pmid
        WHERE a.run_id = %s AND a.pmid = %s
        """,
        (run_id, pmid),
    )
    row = cur.fetchone()
    if row is None:
        sys.exit(f"publication {pmid} is not in run {run_id}")
    run_type, state, note, ai_pass_at, article = row
    article = cast(dict[str, Any], article or {})
    pass_at = f", Claude's pass {ai_pass_at:%Y-%m-%d}" if ai_pass_at else ""
    lines = [
        f"# PMID {pmid}, run {run_id} ({run_type.strip()}), {state}{pass_at}",
        "",
        f"Title: {_text(article.get('ArticleTitle'))}",
        "",
        f"Abstract: {_text(article.get('Abstract')) or '(none)'}",
        "",
        "Note:" + (f"\n{note}" if note else " (empty)"),
    ]
    cur.execute(
        """
        SELECT d.stable_id, d.version, m.psimi_id, d.name1, p1.accession, d.name2, p2.accession,
               d.start2, d.stop2, d.mapping1::text, d.mapping2::text, d.annotation
        FROM descriptions AS d
        JOIN associations AS a ON a.id = d.association_id
        JOIN methods AS m ON m.id = d.method_id
        JOIN proteins AS p1 ON p1.id = d.protein1_id
        JOIN proteins AS p2 ON p2.id = d.protein2_id
        WHERE a.run_id = %s AND a.pmid = %s AND d.deleted_at IS NULL
        ORDER BY p2.accession, d.start2, d.name1, d.stable_id
        """,
        (run_id, pmid),
    )
    rows = cur.fetchall()
    lines += ["", f"## Live descriptions: {len(rows)}", ""]
    for stable_id, version, method, n1, a1, n2, a2, s2, e2, m1, m2, annotation in rows:
        mappings = [_mapping_lengths(m) for m in (m1, m2)]
        line = f"- {stable_id} v{version} {method}: {n1} ({a1}) – {n2} {a2}[{s2}-{e2}]"
        if any(mappings):
            line += f"; mappings {mappings[0] or '-'} / {mappings[1] or '-'}"
        lines.append(line)
        lines += [f"  {n}" for n in annotation.split("\n") if annotation]
    return "\n".join(lines)


def _mapping_lengths(text: str) -> str:
    mappings = cast(list[dict[str, Any]], json.loads(text))
    return ", ".join(f"{len(m['sequence'])} aa" for m in mappings)


def entry(cur: Any, accession: str) -> str:
    cur.execute(
        """
        SELECT p.id, p.version, p.type, p.name, p.description, p.ncbi_taxon_id,
               p.sequences::text, v.accession IS NOT NULL
        FROM proteins AS p
        LEFT JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
        WHERE p.accession = %s ORDER BY p.id
        """,
        (accession,),
    )
    snapshots = cur.fetchall()
    if not snapshots:
        sys.exit(f"{accession}: no snapshot")
    current = [s for s in snapshots if s[7]]
    latest = current[0] if current else snapshots[-1]
    id_, version, type_, gene, description, taxon, sequences, is_current = latest
    isoforms = cast(dict[str, str], json.loads(sequences))
    kind = "human" if type_ == "h" else "viral"
    lines = [
        f"# {accession}: {description}",
        "",
        f"{kind}, taxon {taxon} ({_taxon_name(cur, taxon)})"
        + (f", gene name {gene}" if type_ == "h" else ""),
        f"Snapshot {id_} ({version}), {'current' if is_current else 'obsolete: no current one'}; "
        f"length {len(isoforms.get(accession, ''))}",
    ]
    others = [f"{s[0]} ({s[1]})" for s in snapshots if s is not latest]
    if others:
        lines.append(f"Other snapshots (obsolete): {', '.join(others)}")
    if len(isoforms) > 1:
        lines.append(
            "Isoforms: " + ", ".join(f"{k} ({len(v)})" for k, v in sorted(isoforms.items()))
        )
    cur.execute(
        "SELECT names, features::text FROM proteins_versions WHERE accession = %s "
        "ORDER BY current_version DESC LIMIT 1",
        (accession,),
    )
    row = cur.fetchone()
    if row:
        names, features = row
        names = [n for n in names if n and n != "N/A"]
        if names:
            lines.append(f"Names: {', '.join(names)}")
        parts = [
            f for f in json.loads(features) if f.get("type") in ("chain", "peptide", "propeptide")
        ]
        if parts:
            lines += ["", "Chains and peptides:"]
            lines += [
                f"- {f['start']}-{f['stop']} {f['type']}: {f.get('description', '')}"
                for f in sorted(parts, key=lambda f: (f["start"], -f["stop"]))
            ]
    lines += ["", f"Sequence ({accession}):", isoforms.get(accession, "")]
    return "\n".join(lines)


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
    return row[0] if row else "not in the NCBI taxonomy"


def _lineages(cur: Any, taxa: set[int]) -> dict[int, dict[str, tuple[int, str]]]:
    """Species and family (NCBI ID, scientific name) of each taxon, one walk up the tree."""
    cur.execute(
        """
        WITH RECURSIVE lineage AS (
            SELECT ncbi_taxon_id AS leaf, taxon_id, parent_taxon_id, ncbi_taxon_id, node_rank
            FROM taxon WHERE ncbi_taxon_id = ANY(%s)
            UNION ALL
            SELECT l.leaf, t.taxon_id, t.parent_taxon_id, t.ncbi_taxon_id, t.node_rank
            FROM lineage AS l JOIN taxon AS t ON t.taxon_id = l.parent_taxon_id
            WHERE l.node_rank <> 'family'      -- stop at the family
              AND t.taxon_id <> l.taxon_id     -- the root is its own parent
        )
        SELECT l.leaf, l.node_rank, l.ncbi_taxon_id, n.name
        FROM lineage AS l
        LEFT JOIN taxon_name AS n ON n.taxon_id = l.taxon_id AND n.name_class = 'scientific name'
        WHERE l.node_rank IN ('species', 'family')
        """,
        (list(taxa),),
    )
    lineages: dict[int, dict[str, tuple[int, str]]] = defaultdict(dict)
    for leaf, rank, ncbi_id, name in cur.fetchall():
        lineages[leaf].setdefault(rank, (ncbi_id, name or str(ncbi_id)))
    return lineages


LEVELS = (("strain", None), ("virus", "species"), ("family", "family"))


def names(cur: Any, accession: str) -> str:
    """The generic names of the live vh descriptions on the same strain, virus and family.

    Viral interactors on current snapshots only.

    Strain: the NCBI taxon of the entry; virus: its species; family: its family. Each name with
    its descriptions and viral interactors, the most used first.
    """
    cur.execute(
        """
        SELECT p.ncbi_taxon_id, p.description FROM proteins AS p
        LEFT JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
        WHERE p.accession = %s AND p.type = 'v'
        ORDER BY v.accession IS NOT NULL DESC, p.id DESC LIMIT 1
        """,
        (accession,),
    )
    row = cur.fetchone()
    if row is None:
        sys.exit(f"{accession}: no viral protein with this accession")
    taxon, description = row
    cur.execute(
        """
        SELECT p.ncbi_taxon_id, p.accession, d.start2, d.stop2, d.name2, count(*)
        FROM descriptions AS d
        JOIN associations AS a ON a.id = d.association_id
        JOIN runs AS r ON r.id = a.run_id
        JOIN proteins AS p ON p.id = d.protein2_id
        JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
        WHERE d.deleted_at IS NULL AND r.type = 'vh'
        GROUP BY p.ncbi_taxon_id, p.accession, d.start2, d.stop2, d.name2
        """
    )
    uses = cur.fetchall()
    lineages = _lineages(cur, {u[0] for u in uses} | {taxon})
    own = lineages.get(taxon, {})

    def level(use_taxon: int) -> str | None:
        if use_taxon == taxon:
            return "strain"
        other = lineages.get(use_taxon, {})
        for label, rank in LEVELS[1:]:
            if rank in own and other.get(rank) == own[rank]:
                return label
        return None

    found: dict[str, dict[str, dict[str, int]]] = {label: defaultdict(dict) for label, _ in LEVELS}
    for use_taxon, acc, start, stop, name, count in uses:
        if (label := level(use_taxon)) is not None:
            found[label][name][f"{acc}[{start}-{stop}]"] = count

    lines = [f"# Generic names near {accession} ({description})"]
    for label, rank in LEVELS:
        if rank is None:
            head = f"{_taxon_name(cur, taxon)} ({taxon})"
        elif rank in own:
            ncbi_id, scientific_name = own[rank]
            others = "other viruses" if rank == "family" else "other strains"
            head = f"{scientific_name} ({ncbi_id}), {others}"
        else:
            lines += ["", f"{label.capitalize()}: not in the NCBI lineage"]
            continue
        lines += ["", f"{label.capitalize()}: {head}"]
        if not found[label]:
            lines.append("- no generic name")
        ranked = sorted(found[label].items(), key=lambda kv: (-sum(kv[1].values()), kv[0]))
        for name, interactors in ranked:
            listed = sorted(interactors.items(), key=lambda kv: -kv[1])
            shown = ", ".join(f"{i} ({c})" for i, c in listed[:3])
            more = f", {len(listed) - 3} more" if len(listed) > 3 else ""
            lines.append(f"- `{name}` {sum(interactors.values())}: {shown}{more}")
    return "\n".join(lines)


def rows(cur: Any, stable_ids: list[str]) -> str:
    cur.execute(
        "SELECT DISTINCT d.stable_id, a.run_id, a.pmid FROM descriptions AS d "
        "JOIN associations AS a ON a.id = d.association_id "
        "WHERE d.stable_id = ANY(%s) AND d.deleted_at IS NULL",
        (stable_ids,),
    )
    found = {s: (r, p) for s, r, p in cur.fetchall()}
    if missing := [s for s in stable_ids if s not in found]:
        sys.exit(f"no live description: {', '.join(missing)}")
    by_id = {
        r.stable_id: r
        for run_id, pmid in set(found.values())
        for r in live_revisions(cur, run_id, pmid)
    }
    return "\n".join([header(REVISE), *(format_revision(by_id[s]) for s in stable_ids)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Read what a curation decision needs.")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("publication", help="title, abstract, note, live descriptions")
    p.add_argument("run_id", type=int)
    p.add_argument("pmid", type=int)
    e = commands.add_parser("entry", help="snapshots, sequences, names, chains of an accession")
    e.add_argument("accession")
    n = commands.add_parser("names", help="generic names used near a viral protein")
    n.add_argument("accession")
    r = commands.add_parser("row", help="live descriptions as revision rows, to edit")
    r.add_argument("stable_ids", nargs="+")
    args = parser.parse_args()
    with connect(readonly=True) as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '30s'")
        if args.command == "publication":
            print(publication(cur, args.run_id, args.pmid))
        elif args.command == "entry":
            print(entry(cur, args.accession))
        elif args.command == "names":
            print(names(cur, args.accession))
        else:
            print(rows(cur, args.stable_ids))
