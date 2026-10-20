"""Read what a curation decision needs, complete and short (read-only).

uv run drakkar-read publication <run_id> <pmid>   title, abstract, note, live descriptions
uv run drakkar-read entry <accession>             snapshots, names, chains (also by a secondary
                                                  accession)
uv run drakkar-read names <accession>             generic names used near a viral protein
uv run drakkar-read curation-names <pmid> <accession>
                                                  the same, for the curation of a publication
uv run drakkar-read row <stable_id>...            live descriptions as revision rows

The lookups, on the current snapshots: each takes many inputs and prints a page of lines per
input (`--limit`, `--offset`, `--all`), each starting with the input it answers, and says what
it leaves out:

uv run drakkar-read methods [<text>...]           PSI-MI terms by name or synonym
uv run drakkar-read search [<text>...] [--taxon <taxon>] [--human | --viral] [--reviewed]
                                                  entries by gene names, taxon, protein name
uv run drakkar-read taxon <text>... [--taxon <taxon>]
                                                  taxa by name
uv run drakkar-read closest <sequence>... --taxon <taxon>
                                                  the entries of a taxon by identity
uv run drakkar-read seq <accession>[:<start>-<stop>]...
                                                  sequences and subsequences
uv run drakkar-read map <accession>[:<start>-<stop>] <sequence>...
                                                  the occurrences the write would compute
uv run drakkar-read used <taxon> [<generic name>...] [--exclude <pmid>]
                                                  viral interactors of live descriptions
uv run drakkar-read sql <query>                   free read-only SQL, as tab-separated rows
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from multiprocessing import Pool
from typing import Any, cast

import psycopg

from drakkar.align import MIN_IDENTITY, best_identity, map_sequence, read_written
from drakkar.check import AMINO_ACIDS
from drakkar.db import connect
from drakkar.files import REVISE, format_revision, header
from drakkar.write import (
    InvalidRow,
    _snapshot,  # pyright: ignore[reportPrivateUsage]
    live_revisions,
)


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
        f"# PMID {pmid}, run {run_id} ({run_type}), {state}{pass_at}",
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
            sys.exit(f"{accession}: no snapshot, and no current entry holds it as secondary")
        return "\n\n".join(
            f"# {accession} is a secondary accession of {p}\n{entry(cur, p)}" for p in primaries
        )
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
    lines += ["", f"Sequence: drakkar-read seq {accession}[:<start>-<stop>]"]
    return "\n".join(lines)


def _taxon_name(cur: Any, ncbi_taxon_id: int) -> str:
    return _taxon_names(cur, {ncbi_taxon_id}).get(ncbi_taxon_id, "not in the NCBI taxonomy")


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


def names(cur: Any, accession: str, exclude: int | None = None) -> str:
    """The generic names of the live vh descriptions on the same strain, virus and family.

    Viral interactors on obsolete snapshots are included, marked: their generic names stay
    reusable, their entries do not (`curation-rules.md` §3). `exclude` leaves out the
    descriptions of that PMID, in every run: a curation sees the names of the other
    publications, never those of the publication it curates (curated again blind in a
    re-curation).

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
        SELECT p.ncbi_taxon_id, p.accession, d.start2, d.stop2, d.name2,
               v.accession IS NULL AS obsolete, count(*)
        FROM descriptions AS d
        JOIN associations AS a ON a.id = d.association_id
        JOIN runs AS r ON r.id = a.run_id
        JOIN proteins AS p ON p.id = d.protein2_id
        LEFT JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
        WHERE d.deleted_at IS NULL AND r.type = 'vh' AND a.pmid IS DISTINCT FROM %s
        GROUP BY p.ncbi_taxon_id, p.accession, d.start2, d.stop2, d.name2, obsolete
        """,
        (exclude,),
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
    for use_taxon, acc, start, stop, name, obsolete, count in uses:
        if (label := level(use_taxon)) is not None:
            found[label][name][f"{acc}[{start}-{stop}]" + (" obsolete" if obsolete else "")] = count

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


# --- lookups ----------------------------------------------------------------------------------

LIMIT = 10  # lines per input of a lookup by default; the footer says when there are more
CELL = 200  # characters shown of an `sql` cell
LOCATION = re.compile(r"([A-Z0-9]+)(-\d+)?(?::(\d+)-(\d+))?")  # P26662-2:810-1026


@dataclass(frozen=True)
class Page:
    """Which lines of each input a lookup prints, in its order: `limit` from `offset` (all of
    them when `limit` is None)."""

    offset: int = 0
    limit: int | None = LIMIT

    def cut[T](self, items: list[T]) -> list[T]:
        """The items of the page."""
        return items[self.offset : None if self.limit is None else self.offset + self.limit]

    def lines(
        self, label: str, lines: list[str], narrow: str, total: int | None = None
    ) -> list[str]:
        """The page of an input's lines, each after its label, then a footer when some are not
        shown: which ones are, out of how many, and how to see the others. `lines` may already
        be the page, of `total` lines."""
        prefix = f"{label}\t" if label else ""
        if total is None:
            total = len(lines)
            lines = self.cut(lines)
        if not total:
            return [f"{prefix}(none)"]
        shown = [prefix + line for line in lines]
        if len(lines) < total:
            first, last = self.offset + 1, self.offset + len(lines)
            span = f"{first}-{last}" if lines else "none"
            more = f" --offset {last} for the next;" if last < total else ""
            shown.append(f"{prefix}… {span} of {total} shown:{more} narrow with {narrow}, or --all")
        return shown


DEFAULT = Page()


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


def _db(reviewed: bool) -> str:
    return "SP" if reviewed else "TR"


def _taxon(cur: Any, text: str) -> int:
    """The NCBI taxon ID given as is, or of the one taxon with that name, case aside."""
    if text.isdigit():
        return int(text)
    cur.execute(
        """
        SELECT DISTINCT t.ncbi_taxon_id, s.name
        FROM taxon AS t
        JOIN taxon_name AS n ON n.taxon_id = t.taxon_id
        LEFT JOIN taxon_name AS s ON s.taxon_id = t.taxon_id AND s.name_class = 'scientific name'
        WHERE t.search ILIKE %s AND lower(n.name) = lower(%s)
        ORDER BY t.ncbi_taxon_id
        """,
        (_like(text), text),
    )
    found = cur.fetchall()
    if not found:
        sys.exit(f"{text}: no taxon has this name (drakkar-read taxon finds names)")
    if len(found) > 1:
        sys.exit(f"{text}: several taxa, give the ID: " + ", ".join(f"{i} {n}" for i, n in found))
    return found[0][0]


def _descend(cur: Any, taxon_ids: list[int]) -> dict[int, tuple[int, int]]:
    """The taxa and every taxon under them: taxon ID → (parent taxon ID, NCBI ID). Walked one
    level per query (a recursive query is planned as a scan of the whole taxonomy per level)."""
    cur.execute(
        "SELECT taxon_id, parent_taxon_id, ncbi_taxon_id FROM taxon WHERE taxon_id = ANY(%s)",
        (taxon_ids,),
    )
    found = {t: (parent, ncbi_id) for t, parent, ncbi_id in cur.fetchall()}
    level = list(found)
    while level:
        cur.execute(
            "SELECT taxon_id, parent_taxon_id, ncbi_taxon_id FROM taxon "
            "WHERE parent_taxon_id = ANY(%s) AND taxon_id <> parent_taxon_id",  # the root
            (level,),
        )
        new = {t: (parent, ncbi_id) for t, parent, ncbi_id in cur.fetchall() if t not in found}
        found.update(new)
        level = list(new)
    return found


def _ascend(cur: Any, taxon_ids: list[int]) -> dict[int, tuple[int, int, str, str]]:
    """The taxa and every taxon above them up to their family: taxon ID → (parent taxon ID,
    NCBI ID, rank, scientific name). Walked one level per query, as `_descend`."""
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


def _subtree_taxa(cur: Any, ncbi_taxon_id: int) -> dict[int, tuple[int, int]]:
    """`_descend` from the taxon of that NCBI ID."""
    cur.execute("SELECT taxon_id FROM taxon WHERE ncbi_taxon_id = %s", (ncbi_taxon_id,))
    return _descend(cur, [r[0] for r in cur.fetchall()])


def _subtree(cur: Any, ncbi_taxon_id: int) -> list[int]:
    """The NCBI IDs of the taxon and every taxon under it."""
    below = _subtree_taxa(cur, ncbi_taxon_id)
    return sorted({ncbi_taxon_id} | {i for _, i in below.values()})


def _taxon_names(cur: Any, taxa: set[int]) -> dict[int, str]:
    cur.execute(
        """
        SELECT t.ncbi_taxon_id, n.name FROM taxon AS t
        JOIN taxon_name AS n ON n.taxon_id = t.taxon_id AND n.name_class = 'scientific name'
        WHERE t.ncbi_taxon_id = ANY(%s)
        """,
        (list(taxa),),
    )
    return dict(cur.fetchall())


def _fetch(cur: Any, query: str, params: dict[str, Any]) -> list[tuple[Any, ...]]:
    cur.execute(query, params)  # type: ignore[arg-type]
    return cur.fetchall()


def methods(cur: Any, texts: list[str], page: Page = DEFAULT) -> str:
    """The PSI-MI terms whose name or a synonym contains each text, case aside (all of them
    without text): the closest names first, then the detection methods, then the most used."""
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

    def line(psimi_id: str, name: str, synonyms: list[str], detection: bool, count: int) -> str:
        return f"{psimi_id}\t{name}\t{'yes' if detection else 'no'}\t{count}"

    columns = "psimi_id\tname (synonym matched)\tis_detection\tlive_descriptions"
    if not texts:
        return "\n".join([f"#{columns}", *page.lines("", [line(*m) for m in terms], "a text")])
    lines = [f"#text\t{columns}"]
    for text in texts:
        found = [m for m in terms if _rank(text, [m[1], *m[2]]) < 3]
        found.sort(key=lambda m: (_rank(text, [m[1], *m[2]]), not m[3], -m[4], m[0]))
        shown: list[str] = []
        for psimi_id, name, synonyms, detection, count in found:
            also = [s for s in synonyms if text.casefold() in s.casefold()]
            if also and text.casefold() not in name.casefold():
                name = f"{name} ({also[0]})"
            shown.append(line(psimi_id, name, synonyms, detection, count))
        lines += page.lines(text, shown, "a closer text")
    return "\n".join(lines)


def search(
    cur: Any,
    texts: list[str],
    taxon: str | None = None,
    kind: str | None = None,
    reviewed: bool = False,
    page: Page = DEFAULT,
) -> str:
    """The current entries whose `search` text (accession, gene names, taxon, protein name)
    contains each text, case aside; every current entry of the taxon without text. Swiss-Prot
    first, then the closest names."""
    if not texts and taxon is None:
        sys.exit("search: give a text or a taxon")
    params: dict[str, Any] = {
        "taxa": _subtree(cur, _taxon(cur, taxon)) if taxon is not None else None,
        "type": kind,
        "reviewed": reviewed,
    }
    query = """
        SELECT p.accession, v.reviewed, p.name, p.description, p.ncbi_taxon_id, v.names,
               length(p.sequences->>p.accession)
        FROM proteins_versions AS v
        JOIN proteins AS p ON p.accession = v.accession AND p.version = v.version
        WHERE (%(taxa)s::int[] IS NULL OR p.ncbi_taxon_id = ANY(%(taxa)s))
          AND (%(type)s::char IS NULL OR p.type = %(type)s)
          AND (v.reviewed OR NOT %(reviewed)s)
    """
    results = {
        text: _fetch(cur, query + " AND v.search ILIKE %(like)s", {**params, "like": _like(text)})
        for text in texts
    } or {"": _fetch(cur, query, params)}
    pages: dict[str, list[tuple[Any, ...]]] = {}
    for text, found in results.items():
        found.sort(key=lambda r: (not r[1], _rank(text, [r[2], r[3], *r[5]]), r[0]))
        pages[text] = page.cut(found)
    names = _taxon_names(cur, {r[4] for rows in pages.values() for r in rows})

    def line(row: tuple[Any, ...]) -> str:
        accession, is_reviewed, gene, description, taxon_id, _, length = row
        taxon_name = names.get(taxon_id, "not in the NCBI taxonomy")
        return (
            f"{accession}\t{_db(is_reviewed)}\t{gene}\t{description}\t"
            f"{taxon_id} {taxon_name}\t{length}"
        )

    narrow = "--taxon, --reviewed, --human or --viral" + (", or a closer text" if texts else "")
    columns = "accession\tdb\tgene\tprotein\ttaxon\tlength"
    lines = [f"#text\t{columns}" if texts else f"#{columns}"]
    for text, found in results.items():
        lines += page.lines(text, [line(r) for r in pages[text]], narrow, len(found))
    return "\n".join(lines)


def taxa(cur: Any, texts: list[str], taxon: str | None = None, page: Page = DEFAULT) -> str:
    """The taxa whose `search` text (all their names) contains each text, case aside (under the
    taxon, when given): rank and lineage up to the family, the closest names first."""
    within = set(_subtree_taxa(cur, _taxon(cur, taxon))) if taxon is not None else None
    found: dict[str, list[tuple[int, str]]] = {}
    for text in texts:
        cur.execute(
            "SELECT taxon_id, search FROM taxon WHERE search ILIKE %s ORDER BY ncbi_taxon_id",
            (_like(text),),
        )
        found[text] = [r for r in cur.fetchall() if within is None or r[0] in within]
    pages: dict[str, list[tuple[int, list[str]]]] = {}
    for text, rows in found.items():
        ranked = [(t, s.split(" | ")) for t, s in rows]
        ranked.sort(key=lambda r: _rank(text, r[1]))  # stable: NCBI ID order among equals
        pages[text] = page.cut(ranked)
    nodes = _ascend(cur, sorted({t for rows in pages.values() for t, _ in rows}))

    def line(text: str, taxon_id: int, names: list[str]) -> str:
        """NCBI ID, scientific name (with the name matched), rank, lineage up to the family."""
        walked: list[tuple[int, str, str]] = []
        node = taxon_id
        while node in nodes:
            parent, ncbi_id, rank, name = nodes[node]
            walked.append((ncbi_id, rank, name))
            if rank == "family" or parent == node:
                break
            node = parent
        (ncbi_id, rank, name), *above = walked
        matched = [n for n in names if text.casefold() in n.casefold()]
        also = "" if text.casefold() in name.casefold() else f" ({matched[0]})"
        return f"{ncbi_id}\t{name}{also}\t{rank}\t{' < '.join(n for *_, n in above) or '-'}"

    lines = ["#text\ttaxon\tname (name matched)\trank\tlineage"]
    for text, rows in found.items():
        shown = [line(text, t, names) for t, names in pages[text]]
        lines += page.lines(text, shown, "--taxon or a closer text", len(rows))
    return "\n".join(lines)


def _location(text: str) -> tuple[str, str, int | None, int | None]:
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


def _sequence(cur: Any, text: str) -> str:
    """The sequence of `<accession>[:<start>-<stop>]` on its current snapshot; ValueError."""
    accession, isoform, start, stop = _location(text)
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
    lines: list[str] = []
    for text in locations:
        try:
            lines.append(f"{text}\t{_sequence(cur, text)}")
        except ValueError as e:
            lines.append(f"{text}\t{e}")
    return "\n".join(lines)


def _region(mapping: dict[str, Any], canonical: str) -> str:
    """The occurrences of a mapping: `1-15` on the canonical isoform, `P04439-2:1-15` on another,
    each with its identity when below the best."""
    best = best_identity(mapping)
    return ", ".join(
        ("" if i["accession"] == canonical else f"{i['accession']}:")
        + f"{o['start']}-{o['stop']}"
        + ("" if o["identity"] == best else f" ({o['identity']:g} %)")
        for i in mapping["isoforms"]
        for o in i["occurrences"]
    )


def _map_entry(query: str, accession: str, sequences: str) -> dict[str, Any]:
    """A sequence mapped on a whole entry, its isoforms given as JSON."""
    isoforms = cast(dict[str, str], json.loads(sequences))
    return map_sequence(query, isoforms, accession, 1, len(isoforms[accession]))


def closest(
    cur: Any,
    sequences: list[str],
    taxon: str,
    min_identity: float = 0.0,
    page: Page = DEFAULT,
) -> str:
    """The current entries of the taxon ranked by identity with each sequence, as the write
    computes it for a mapping on the whole entry, then Swiss-Prot first."""
    queries: dict[str, str] = {}
    for text in sequences:
        if any(c.isdigit() for c in text):  # an accession, never a sequence
            try:
                queries[text] = _sequence(cur, text)
            except ValueError as e:
                sys.exit(f"{text}: {e}")
        elif AMINO_ACIDS.fullmatch(text.upper()):
            queries[text if len(text) <= 20 else f"{text[:20]}…({len(text)} aa)"] = text.upper()
        else:
            sys.exit(f"{text[:20]}: neither an accession nor an amino acid sequence")
    cur.execute(
        """
        SELECT p.accession, v.reviewed, p.description, p.ncbi_taxon_id, p.sequences::text
        FROM proteins_versions AS v
        JOIN proteins AS p ON p.accession = v.accession AND v.version = p.version
        WHERE p.ncbi_taxon_id = ANY(%s)
        """,
        (_subtree(cur, _taxon(cur, taxon)),),
    )
    entries = cur.fetchall()
    names = _taxon_names(cur, {e[3] for e in entries})
    lines = ["#sequence\taccession\tdb\tprotein\ttaxon\tidentity\tregion"]
    for label, query in queries.items():
        with Pool() as pool:  # one alignment per entry: thousands for a virus
            mappings = pool.starmap(_map_entry, [(query, e[0], e[4]) for e in entries], 64)
        ranked: list[tuple[float, bool, str, str]] = []
        for (accession, is_reviewed, description, taxon_id, _), mapping in zip(
            entries, mappings, strict=True
        ):
            identity = best_identity(mapping)
            if identity < min_identity:
                continue
            taxon_name = names.get(taxon_id, "not in the NCBI taxonomy")
            ranked.append(
                (
                    identity,
                    is_reviewed,
                    accession,
                    f"{accession}\t{_db(is_reviewed)}\t{description}\t{taxon_id} {taxon_name}"
                    f"\t{identity:.1f} %\t{_region(mapping, accession) or 'aligns nowhere'}",
                )
            )
        ranked.sort(key=lambda r: (-r[0], not r[1], r[2]))
        lines += page.lines(label, [r[3] for r in ranked], "--taxon or --min-identity")
    return "\n".join(lines)


def map_(cur: Any, interactor: str, sequences: list[str]) -> str:
    """What the write computes for each mapping sequence on the interactor (its current
    snapshot): extra end residues, occurrences on each isoform with their identity (on the
    canonical isoform, relative to the interactor's start), and whether it is below 90 %."""
    try:
        accession, isoform, start, stop = _location(interactor)
        if isoform != accession:
            raise ValueError("an interactor is an entry, not an isoform")
        snapshot = _snapshot(cur, accession)
    except (ValueError, InvalidRow) as e:
        sys.exit(f"{interactor}: {e}")
    length = len(snapshot.sequences[accession])
    start, stop = start or 1, stop or length
    if not 1 <= start <= stop <= length:
        sys.exit(f"{interactor}: {start}-{stop} is outside 1-{length}")
    lines = [f"# on {accession}[{start}-{stop}]", "#sequence\tnter\tcter\toccurrences\tverdict"]
    for text in sequences:
        try:
            sequence, nter, cter = read_written(text)
        except ValueError as e:
            lines.append(f"{text}\t{e}")
            continue
        if not AMINO_ACIDS.fullmatch(sequence):
            lines.append(f"{text}\tnot an amino acid sequence")
            continue
        mapping = map_sequence(sequence, snapshot.sequences, accession, start, stop, nter, cter)
        identity = best_identity(mapping)
        verdict = (
            "aligns nowhere"
            if not mapping["isoforms"]
            else f"below {MIN_IDENTITY:g} %"
            if identity < MIN_IDENTITY
            else "ok"
        )
        occurrences = "; ".join(
            f"{i['accession']} "
            + ", ".join(f"{o['start']}-{o['stop']} ({o['identity']:g} %)" for o in i["occurrences"])
            for i in mapping["isoforms"]
        )
        lines.append(f"{text}\t{nter or '-'}\t{cter or '-'}\t{occurrences or '-'}\t{verdict}")
    return "\n".join(lines)


def used(
    cur: Any, taxon: str, names: list[str], exclude: int | None = None, page: Page = DEFAULT
) -> str:
    """The viral interactors of live descriptions under the taxon, on any snapshot (an obsolete
    one marked: its generic name stays reusable, its entry does not, `curation-rules.md` §3),
    without those of the PMID excluded. Without generic names, one line per generic name, the
    most used first, with its most used interactors; with generic names (case aside), one line
    per interactor of each."""
    cur.execute(
        """
        SELECT d.name2, p.accession, d.start2, d.stop2, v.accession IS NULL AS obsolete,
               count(*) AS descriptions
        FROM descriptions AS d
        JOIN associations AS a ON a.id = d.association_id
        JOIN proteins AS p ON p.id = d.protein2_id
        LEFT JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
        WHERE d.deleted_at IS NULL AND p.type = 'v' AND p.ncbi_taxon_id = ANY(%s)
          AND a.pmid IS DISTINCT FROM %s
        GROUP BY d.name2, p.accession, d.start2, d.stop2, obsolete
        ORDER BY descriptions DESC, d.name2, p.accession, d.start2
        """,
        (_subtree(cur, _taxon(cur, taxon)), exclude),
    )
    found = cur.fetchall()
    if not names:
        by_name: dict[str, list[str]] = defaultdict(list)
        totals: dict[str, int] = defaultdict(int)
        for name2, accession, start, stop, obsolete, count in found:
            mark = ", obsolete snapshot" if obsolete else ""
            by_name[name2].append(f"{accession} {start}-{stop} ({count}{mark})")
            totals[name2] += count
        ranked = sorted(by_name, key=lambda n: (-totals[n], n))
        shown = [
            f"{n}\t{totals[n]}\t{', '.join(by_name[n][:3])}"
            + (f", {len(by_name[n]) - 3} more" if len(by_name[n]) > 3 else "")
            for n in ranked
        ]
        lines = ["#generic_name\tlive_descriptions\tinteractors (live descriptions)"]
        return "\n".join(lines + page.lines("", shown, "generic names"))
    lines = ["#generic_name\tname\taccession\tcoordinates\tsnapshot\tlive_descriptions"]
    for name in names:
        rows = [
            f"{n}\t{accession}\t{start}-{stop}\t{'obsolete' if obsolete else 'current'}\t{count}"
            for n, accession, start, stop, obsolete, count in found
            if n.casefold() == name.casefold()
        ]
        lines += page.lines(name, rows, "a closer taxon")
    return "\n".join(lines)


def _cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= CELL else f"{text[:CELL]}…({len(text)} chars)"


def sql(cur: Any, query: str, page: Page = DEFAULT) -> str:
    """The rows of a free query, tab-separated under a header of column names: a page of them,
    their total, and each cell cut at `CELL` characters. A query is run once, through a cursor
    that skips, fetches and counts on the server; a statement no cursor takes (EXPLAIN, SHOW)
    is run as is."""
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
            rows = page.cut(rows)
        else:
            skipped = 0
            if page.offset:
                cur.execute(f"MOVE FORWARD {page.offset} IN lookup")
                skipped = cur.rowcount
            cur.execute(f"FETCH {'ALL' if page.limit is None else page.limit} FROM lookup")
            columns = [c.name for c in cur.description]
            rows = cur.fetchall()
            cur.execute("MOVE FORWARD ALL IN lookup")
            total = skipped + len(rows) + cur.rowcount
    except psycopg.Error as e:
        sys.exit(f"sql: {e}".strip())
    shown = ["\t".join(_cell(v) for v in row) for row in rows]
    return "\n".join(["\t".join(columns), *page.lines("", shown, "WHERE", total)])


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
    c = commands.add_parser(
        "curation-names", help="the same, without the descriptions of the publication curated"
    )
    c.add_argument("pmid", type=int)
    c.add_argument("accession")
    r = commands.add_parser("row", help="live descriptions as revision rows, to edit")
    r.add_argument("stable_ids", nargs="+")
    paged = argparse.ArgumentParser(add_help=False)
    paged.add_argument("--limit", type=int, default=LIMIT, help=f"lines per input ({LIMIT})")
    paged.add_argument("--offset", type=int, default=0, help="lines skipped per input")
    paged.add_argument("--all", action="store_true", help="every line")
    m = commands.add_parser("methods", parents=[paged], help="PSI-MI terms by name or synonym")
    m.add_argument("texts", nargs="*")
    s = commands.add_parser(
        "search", parents=[paged], help="current entries by gene names, taxon, protein name"
    )
    s.add_argument("texts", nargs="*")
    s.add_argument("--taxon", help="NCBI taxon ID or name: its whole subtree")
    kind = s.add_mutually_exclusive_group()
    kind.add_argument("--human", action="store_const", const="h", dest="kind")
    kind.add_argument("--viral", action="store_const", const="v", dest="kind")
    s.add_argument("--reviewed", action="store_true", help="Swiss-Prot only")
    t = commands.add_parser("taxon", parents=[paged], help="taxa by name: rank, lineage")
    t.add_argument("texts", nargs="+")
    t.add_argument("--taxon", help="only the taxa under it (NCBI taxon ID or name)")
    o = commands.add_parser(
        "closest", parents=[paged], help="the current entries of a taxon by identity"
    )
    o.add_argument("sequences", nargs="+", help="a sequence, or <accession>[:<start>-<stop>]")
    o.add_argument("--taxon", required=True, help="NCBI taxon ID or name: its whole subtree")
    o.add_argument(
        "--min-identity", type=float, default=0.0, help="only entries at this %% or more"
    )
    q = commands.add_parser("seq", help="sequences, or subsequences between coordinates")
    q.add_argument("locations", nargs="+", help="<accession>[:<start>-<stop>]")
    a = commands.add_parser("map", help="the occurrences the write computes for mappings")
    a.add_argument("interactor", help="<accession>[:<start>-<stop>]")
    a.add_argument("sequences", nargs="+", help="extra end residues in lowercase")
    u = commands.add_parser(
        "used", parents=[paged], help="viral interactors of live descriptions under a taxon"
    )
    u.add_argument("taxon", help="NCBI taxon ID or name: its whole subtree")
    u.add_argument("names", nargs="*", help="generic names")
    u.add_argument("--exclude", type=int, metavar="PMID", help="leave out its descriptions")
    x = commands.add_parser("sql", parents=[paged], help="free read-only SQL, a page of its rows")
    x.add_argument("query")
    args = parser.parse_args()
    with connect(readonly=True) as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '30s'")
        if args.command == "publication":
            print(publication(cur, args.run_id, args.pmid))
        elif args.command == "entry":
            print(entry(cur, args.accession))
        elif args.command == "names":
            print(names(cur, args.accession))
        elif args.command == "curation-names":
            print(names(cur, args.accession, exclude=args.pmid))
        elif args.command == "row":
            print(rows(cur, args.stable_ids))
        elif args.command == "seq":
            print(seq(cur, args.locations))
        elif args.command == "map":
            print(map_(cur, args.interactor, args.sequences))
        else:
            page = Page(args.offset, None if args.all else args.limit)
            if args.command == "methods":
                print(methods(cur, args.texts, page))
            elif args.command == "search":
                print(search(cur, args.texts, args.taxon, args.kind, args.reviewed, page))
            elif args.command == "taxon":
                print(taxa(cur, args.texts, args.taxon, page))
            elif args.command == "closest":
                print(closest(cur, args.sequences, args.taxon, args.min_identity, page))
            elif args.command == "used":
                print(used(cur, args.taxon, args.names, args.exclude, page))
            else:
                print(sql(cur, args.query, page))
