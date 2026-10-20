"""Read what a curation decision needs from Drakkar, on its current snapshots (read-only).

uv run drakkar-read methods <text>...             PSI-MI terms by name or synonym
uv run drakkar-read taxon <text>...               taxa by name, with their lineage
uv run drakkar-read entry <accession>...          an entry: lineage, isoforms, names, chains
uv run drakkar-read search <text>... [--taxon <ID>]
                                                  entries by accession, gene or protein name
uv run drakkar-read seq <accession>[:<start>-<stop>]...
                                                  sequences and subsequences
uv run drakkar-read names <taxon ID>...           generic names used under each taxon
uv run drakkar-read sql <query>                   free read-only SQL

Each takes many inputs. `entry` prints a block per entry; the others print tab-separated lines
under a `#` header, each starting with the input it answers, the best first. `--limit <n>`
bounds the lines per input (20); a list that is cut ends with how many there are. A taxon is
given by its NCBI ID, and written `<ID> <name>`; a lineage `<ID> <name> < …` up to the family; a
stretch of a protein `<accession>:<start>-<stop>`, then `obsolete` on an obsolete snapshot. An
input that cannot be read gets its line, with why.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, cast

import psycopg

from drakkar.db import connect

LIMIT = 20  # lines per input by default
CELL = 200  # characters shown of an `sql` cell
LOCATION = re.compile(r"([A-Z0-9]+)(-\d+)?(?::(\d+)-(\d+))?")  # P26662-2:810-1026


@dataclass(frozen=True)
class Page:
    """At most `limit` lines per input, the best first; a list that is cut ends with how many
    there are."""

    limit: int = LIMIT

    def cut[T](self, items: list[T]) -> list[T]:
        return items[: self.limit]

    def lines(self, label: str, lines: list[str], total: int | None = None) -> list[str]:
        """An input's lines, each after its label, cut to the page; `lines` may already be the
        page, of `total` lines."""
        prefix = f"{label}\t" if label else ""
        total = len(lines) if total is None else total
        if not total:
            return [f"{prefix}(none)"]
        shown = [prefix + line for line in self.cut(lines)]
        if len(shown) < total:
            shown.append(f"{prefix}… {len(shown)} of {total}")
        return shown


DEFAULT = Page()


# --- The taxonomy ------------------------------------------------------------------------------


def subtree(cur: Any, ncbi_taxon_id: int) -> list[int]:
    """The NCBI IDs of the taxon and every taxon under it, by the nested set; the taxon itself
    even when the taxonomy lacks it, for the entries whose taxon it lacks."""
    cur.execute(
        """
        SELECT t.ncbi_taxon_id
        FROM taxon AS top
        JOIN taxon AS t ON t.left_value BETWEEN top.left_value AND top.right_value
        WHERE top.ncbi_taxon_id = %s
        """,
        (ncbi_taxon_id,),
    )
    return sorted({ncbi_taxon_id} | {r[0] for r in cur.fetchall()})


def _ancestors(cur: Any, taxon_ids: list[int]) -> dict[int, tuple[int, int, str, str]]:
    """The taxa and every taxon above them up to their family: taxon ID → (parent taxon ID, NCBI
    ID, rank, scientific name). Walked up by parent, one level per query: an ancestor is an index
    lookup, where the nested set would scan the taxa on one side of it."""
    found: dict[int, tuple[int, int, str, str]] = {}
    level = taxon_ids
    while level:
        cur.execute(
            """
            SELECT t.taxon_id, t.parent_taxon_id, t.ncbi_taxon_id, t.node_rank, n.name
            FROM taxon AS t
            LEFT JOIN taxon_name AS n
              ON n.taxon_id = t.taxon_id AND n.name_class = 'scientific name'
            WHERE t.taxon_id = ANY(%s)
            """,
            (level,),
        )
        rows = cur.fetchall()
        found.update({t: (p, i, r, n or str(i)) for t, p, i, r, n in rows})
        level = list({p for t, p, _, r, _ in rows if r != "family" and p != t} - found.keys())
    return found


def _lineage(
    nodes: dict[int, tuple[int, int, str, str]], taxon_id: int
) -> list[tuple[int, str, str]]:
    """A taxon and the taxa above it up to its family, in the nodes of `_ancestors`: NCBI ID,
    rank, scientific name."""
    walked: list[tuple[int, str, str]] = []
    node = taxon_id
    while node in nodes:
        parent, ncbi_id, rank, name = nodes[node]
        walked.append((ncbi_id, rank, name))
        if rank == "family" or parent == node:
            break
        node = parent
    return walked


def _written(lineage: list[tuple[int, str, str]]) -> str:
    return " < ".join(f"{ncbi_id} {name}" for ncbi_id, _, name in lineage)


def taxon_names(cur: Any, taxa: set[int]) -> dict[int, str]:
    cur.execute(
        """
        SELECT t.ncbi_taxon_id, n.name FROM taxon AS t
        JOIN taxon_name AS n ON n.taxon_id = t.taxon_id AND n.name_class = 'scientific name'
        WHERE t.ncbi_taxon_id = ANY(%s)
        """,
        (list(taxa),),
    )
    return dict(cur.fetchall())


# --- The lookups -------------------------------------------------------------------------------


def _like(text: str) -> str:
    """An ILIKE pattern for `text` anywhere, its wildcards escaped."""
    return "%" + re.sub(r"([\\%_])", r"\\\1", text) + "%"


def _rank(text: str, names: list[str]) -> int:
    """How closely a text matches names, case aside: 0 a name is the text, 1 a name starts with
    it, 2 a name contains it, 3 none."""
    wanted = text.casefold()
    folded = [n.casefold() for n in names]
    if wanted in folded:
        return 0
    if any(n.startswith(wanted) for n in folded):
        return 1
    return 2 if any(wanted in n for n in folded) else 3


def database(reviewed: bool) -> str:
    return "SP" if reviewed else "TR"


def methods(cur: Any, texts: list[str], page: Page = DEFAULT) -> str:
    """The PSI-MI terms whose name or a synonym contains each text, case aside: the closest names
    first, then the detection methods, then the most used."""
    cur.execute(
        """
        WITH uses AS (
            SELECT method_id, count(*) AS descriptions FROM descriptions
            WHERE deleted_at IS NULL GROUP BY method_id
        )
        SELECT m.psimi_id, m.name, m.synonyms, m.is_detection, coalesce(u.descriptions, 0)
        FROM methods AS m LEFT JOIN uses AS u ON u.method_id = m.id
        ORDER BY m.psimi_id
        """
    )
    terms = cur.fetchall()
    lines = ["#text\tpsimi_id\tname (synonym matched)\tis_detection\tlive_descriptions"]
    for text in texts:
        found = [m for m in terms if _rank(text, [m[1], *m[2]]) < 3]
        found.sort(key=lambda m: (_rank(text, [m[1], *m[2]]), not m[3], -m[4], m[0]))
        shown: list[str] = []
        for psimi_id, name, synonyms, detection, count in found:
            also = [s for s in synonyms if text.casefold() in s.casefold()]
            if also and text.casefold() not in name.casefold():
                name = f"{name} ({also[0]})"
            shown.append(f"{psimi_id}\t{name}\t{'yes' if detection else 'no'}\t{count}")
        lines += page.lines(text, shown)
    return "\n".join(lines)


def taxa(cur: Any, texts: list[str], page: Page = DEFAULT) -> str:
    """The taxa one of whose names contains each text, case aside, the closest names first: the
    taxon (with the name matched), its rank, and the taxa above it up to its family."""
    found: dict[str, list[tuple[int, list[str]]]] = {}
    for text in texts:
        cur.execute(
            "SELECT taxon_id, search FROM taxon WHERE search ILIKE %s ORDER BY ncbi_taxon_id",
            (_like(text),),
        )
        ranked = [(taxon_id, search.split(" | ")) for taxon_id, search in cur.fetchall()]
        ranked.sort(key=lambda r: _rank(text, r[1]))  # stable: NCBI ID order among equals
        found[text] = ranked
    shown = {t for rows in found.values() for t, _ in page.cut(rows)}
    nodes = _ancestors(cur, sorted(shown))

    def line(text: str, taxon_id: int, names: list[str]) -> str:
        (ncbi_id, rank, name), *above = _lineage(nodes, taxon_id)
        matched = [n for n in names if text.casefold() in n.casefold()]
        also = "" if text.casefold() in name.casefold() else f" ({matched[0]})"
        return f"{ncbi_id} {name}{also}\t{rank}\t{_written(above) or '-'}"

    lines = ["#text\ttaxon (name matched)\trank\tlineage"]
    for text, rows in found.items():
        lines += page.lines(text, [line(text, t, n) for t, n in page.cut(rows)], len(rows))
    return "\n".join(lines)


def entries(cur: Any, accessions: list[str]) -> str:
    return "\n\n".join(entry(cur, accession) for accession in accessions)


def entry(cur: Any, accession: str) -> str:
    """An entry by its accession; for a secondary accession, the current entries that hold it."""
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
        cur.execute(
            "SELECT accession FROM proteins_versions "
            "WHERE secondary_accessions @> ARRAY[%s]::varchar[] ORDER BY accession",
            (accession,),
        )
        primaries = [r[0] for r in cur.fetchall()]
        if not primaries:
            return f"# {accession}: no snapshot, and no current entry holds it as secondary"
        return "\n\n".join(
            f"# {accession} is a secondary accession of {p}\n{entry(cur, p)}" for p in primaries
        )
    current = [s for s in snapshots if s[7]]
    latest = current[0] if current else snapshots[-1]
    id_, version, type_, gene, description, taxon, sequences, is_current = latest
    isoforms = cast(dict[str, str], json.loads(sequences))
    cur.execute("SELECT taxon_id FROM taxon WHERE ncbi_taxon_id = %s", (taxon,))
    row = cur.fetchone()
    lineage = (
        _written(_lineage(_ancestors(cur, [row[0]]), row[0]))
        if row
        else f"{taxon} not in the NCBI taxonomy"
    )
    lines = [
        f"# {accession}: {description}",
        "",
        f"{'human' if type_ == 'h' else 'viral'}, taxon {lineage}"
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
    return "\n".join(lines)


def search(cur: Any, texts: list[str], taxon: int | None = None, page: Page = DEFAULT) -> str:
    """The current entries whose `search` text (accession, gene names, taxon, protein name)
    contains each text, case aside, under the taxon when given: Swiss-Prot first, then the
    closest names."""
    under = None if taxon is None else subtree(cur, taxon)
    found: dict[str, list[tuple[Any, ...]]] = {}
    for text in texts:
        cur.execute(
            """
            SELECT p.accession, v.reviewed, p.name, p.description, p.ncbi_taxon_id, v.names,
                   length(p.sequences->>p.accession)
            FROM proteins_versions AS v
            JOIN proteins AS p ON p.accession = v.accession AND p.version = v.version
            WHERE v.search ILIKE %(like)s
              AND (%(taxa)s::int[] IS NULL OR p.ncbi_taxon_id = ANY(%(taxa)s))
            """,
            {"like": _like(text), "taxa": under},
        )
        rows: list[tuple[Any, ...]] = cur.fetchall()
        rows.sort(key=lambda r: (not r[1], _rank(text, [r[2], r[3], *r[5]]), r[0]))
        found[text] = rows
    names = taxon_names(cur, {r[4] for rows in found.values() for r in page.cut(rows)})

    def line(row: tuple[Any, ...]) -> str:
        accession, is_reviewed, gene, description, taxon_id, _, length = row
        taxon_name = names.get(taxon_id, "not in the NCBI taxonomy")
        return (
            f"{accession}\t{database(is_reviewed)}\t{gene}\t{description}\t"
            f"{taxon_id} {taxon_name}\t{length}"
        )

    lines = ["#text\taccession\tdb\tgene\tprotein\ttaxon\tlength"]
    for text, rows in found.items():
        lines += page.lines(text, [line(r) for r in page.cut(rows)], len(rows))
    return "\n".join(lines)


def location(text: str) -> tuple[str, str, int | None, int | None]:
    """(entry accession, isoform accession, start, stop) of `P26662[-2][:810-1026]`."""
    match = LOCATION.fullmatch(text)
    if match is None:
        raise ValueError("not <accession>[:<start>-<stop>]")
    accession, isoform, start, stop = match.groups()
    return (
        accession,
        accession + (isoform or ""),
        None if start is None else int(start),
        None if stop is None else int(stop),
    )


def sequence_of(cur: Any, text: str) -> str:
    """The sequence of `<accession>[:<start>-<stop>]` on its current snapshot; ValueError."""
    accession, isoform, start, stop = location(text)
    cur.execute(
        """
        SELECT p.sequences->>%s FROM proteins AS p
        JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
        WHERE p.accession = %s
        """,
        (isoform, accession),
    )
    row = cur.fetchone()
    if row is None:
        raise ValueError(f"{accession} has no current snapshot")
    if row[0] is None:
        raise ValueError(f"{accession} has no isoform {isoform}")
    sequence: str = row[0]
    if start is None or stop is None:
        return sequence
    if not 1 <= start <= stop <= len(sequence):
        raise ValueError(f"{start}-{stop} is outside 1-{len(sequence)}")
    return sequence[start - 1 : stop]


def seq(cur: Any, locations: list[str]) -> str:
    """The sequence of each entry or isoform, or between its coordinates (1-based, inclusive)."""
    lines = ["#location\tsequence"]
    for text in locations:
        try:
            lines.append(f"{text}\t{sequence_of(cur, text)}")
        except ValueError as e:
            lines.append(f"{text}\t{e}")
    return "\n".join(lines)


def names(cur: Any, taxa: list[int], page: Page = DEFAULT) -> str:
    """The generic names of the viral interactors of live descriptions under each taxon: the most
    used first, each with its live descriptions and its three most used interactors, on any
    snapshot (an obsolete one marked: its generic name stays reusable, its entry does not,
    `curation-rules.md` §3)."""
    lines = ["#taxon\tgeneric_name\tlive_descriptions\tinteractors (live descriptions)"]
    for taxon in taxa:
        cur.execute(
            """
            SELECT d.name2, p.accession, d.start2, d.stop2, v.accession IS NULL AS obsolete,
                   count(*) AS descriptions
            FROM descriptions AS d
            JOIN proteins AS p ON p.id = d.protein2_id
            LEFT JOIN proteins_versions AS v
              ON v.accession = p.accession AND v.version = p.version
            WHERE d.deleted_at IS NULL AND p.type = 'v' AND p.ncbi_taxon_id = ANY(%s)
            GROUP BY d.name2, p.accession, d.start2, d.stop2, obsolete
            ORDER BY descriptions DESC, d.name2, p.accession, d.start2
            """,
            (subtree(cur, taxon),),
        )
        interactors: dict[str, list[str]] = defaultdict(list)
        totals: dict[str, int] = defaultdict(int)
        for name2, accession, start, stop, obsolete, count in cur.fetchall():
            stretch = f"{accession}:{start}-{stop}" + (" obsolete" if obsolete else "")
            interactors[name2].append(f"{stretch} ({count})")
            totals[name2] += count
        shown = [
            f"{name}\t{totals[name]}\t{', '.join(interactors[name][:3])}"
            + (f", {len(interactors[name]) - 3} more" if len(interactors[name]) > 3 else "")
            for name in sorted(interactors, key=lambda n: (-totals[n], n))
        ]
        lines += page.lines(str(taxon), shown)
    return "\n".join(lines)


def _cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= CELL else f"{text[:CELL]}…({len(text)} chars)"


def sql(cur: Any, query: str, page: Page = DEFAULT) -> str:
    """The rows of a free query, tab-separated under a `#` header of column names: a page of
    them, their total, and each cell cut at `CELL` characters. A query is run once, through a
    cursor that fetches and counts on the server; a statement no cursor takes (EXPLAIN, SHOW) is
    run as is."""
    query = query.strip().rstrip(";")
    try:
        cur.execute("SAVEPOINT lookup")
        try:
            cur.execute(f"DECLARE lookup NO SCROLL CURSOR FOR {query}")  # type: ignore[arg-type]
        except psycopg.Error:
            cur.execute("ROLLBACK TO SAVEPOINT lookup")
            cur.execute(query)  # type: ignore[arg-type]
            if cur.description is None:
                return ""
            columns = [c.name for c in cur.description]
            rows = cur.fetchall()
            total = len(rows)
        else:
            cur.execute(f"FETCH {page.limit} FROM lookup")
            columns = [c.name for c in cur.description]
            rows = cur.fetchall()
            cur.execute("MOVE FORWARD ALL IN lookup")
            total = len(rows) + cur.rowcount
    except psycopg.Error as e:
        sys.exit(f"sql: {e}".strip())
    shown = ["\t".join(_cell(v) for v in row) for row in page.cut(rows)]
    return "\n".join(["#" + "\t".join(columns), *page.lines("", shown, total)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Read what a curation decision needs.")
    commands = parser.add_subparsers(dest="command", required=True)
    limit = argparse.ArgumentParser(add_help=False)
    limit.add_argument("--limit", type=int, default=LIMIT, help=f"lines per input ({LIMIT})")
    m = commands.add_parser("methods", parents=[limit], help="PSI-MI terms by name or synonym")
    m.add_argument("texts", nargs="+")
    t = commands.add_parser("taxon", parents=[limit], help="taxa by name, with their lineage")
    t.add_argument("texts", nargs="+")
    e = commands.add_parser("entry", help="an entry: lineage, isoforms, names, chains")
    e.add_argument("accessions", nargs="+")
    s = commands.add_parser("search", parents=[limit], help="entries by accession or name")
    s.add_argument("texts", nargs="+")
    s.add_argument("--taxon", type=int, help="NCBI taxon ID: only the entries under it")
    q = commands.add_parser("seq", help="sequences, or subsequences between coordinates")
    q.add_argument("locations", nargs="+", help="<accession>[:<start>-<stop>]")
    n = commands.add_parser("names", parents=[limit], help="generic names used under each taxon")
    n.add_argument("taxa", nargs="+", type=int, help="NCBI taxon ID: its whole subtree")
    x = commands.add_parser("sql", parents=[limit], help="free read-only SQL")
    x.add_argument("query")
    args = parser.parse_args()
    with connect(readonly=True) as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '30s'")
        if args.command == "entry":
            print(entries(cur, args.accessions))
        elif args.command == "seq":
            print(seq(cur, args.locations))
        else:
            page = Page(args.limit)
            if args.command == "methods":
                print(methods(cur, args.texts, page))
            elif args.command == "taxon":
                print(taxa(cur, args.texts, page))
            elif args.command == "search":
                print(search(cur, args.texts, args.taxon, page))
            elif args.command == "names":
                print(names(cur, args.taxa, page))
            else:
                print(sql(cur, args.query, page))
