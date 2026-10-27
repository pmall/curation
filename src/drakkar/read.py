"""Read what a curation decision needs from Drakkar, on its current snapshots (read-only).

uv run drakkar-read methods <text>...             PSI-MI terms by name or synonym
uv run drakkar-read taxon <text>...               taxa by name, with their lineage
uv run drakkar-read entry <accession>...          an entry: lineage, isoforms, names, chains,
                                                  regions, generic names
uv run drakkar-read search <text>... [--taxon <ID>]
                                                  entries by accession, gene or protein name
uv run drakkar-read closest <sequence>... --taxon <ID>
                                                  the entries of a taxon closest to sequences
uv run drakkar-read seq <accession>[:<start>-<stop>]...
                                                  sequences and subsequences
uv run drakkar-read names <taxon ID>...           generic names used under each taxon
uv run drakkar-read sql <query> --limit <n>       free read-only SQL, refused beyond n rows

Each takes many inputs. `entry` prints a block per entry; the others print tab-separated lines
under a `#` header, each starting with the input it answers, the best first. `--limit <n>`
bounds the lines per input (20); a list that is cut ends with how many there are. `sql` is never
cut: its `--limit` is required, and a query returning more rows is refused. An accession is
taken as publications write it (`written_accession`, `written_accessions`) and names its
current entries (`current_entries`). A taxon is given by its NCBI ID, and written `<ID> <name>`;
a lineage `<ID> <name> < …` up to the family; a stretch of a protein
`<accession>:<start>-<stop>`, then `obsolete` on an obsolete snapshot. An input that cannot be
read gets its line, with why.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, cast

import psycopg
import pyopal

from drakkar.align import UNSCORED
from drakkar.check import AMINO_ACIDS
from drakkar.db import connect

LIMIT = 20  # lines per input by default
CELL = 200  # characters shown of an `sql` cell
# The database search of `closest`: Smith-Waterman on every sequence, BLAST's protein scoring.
# Its alphabet lacks U, O and J, aligned as X (`align.py`).
SEARCH: Any = pyopal.Aligner("BLOSUM62", gap_open=11, gap_extend=1)  # pyopal is not typed
# The features `entry` prints, by their UniProt type: the parts of the protein a mature
# protein's coordinates can come from (`curation-rules.md` §4, tier `annotation`), and the
# regions of interest.
FEATURES = {
    "chain": "chain",
    "peptide": "peptide",
    "propeptide": "propeptide",
    "region of interest": "region",
}
# An accession as publications write it: UniProt's pattern of an entry's accession, then an
# isoform's number (`P04637-2`) or a sequence version (`P04637.2`); in a UniProt ID, between the
# bars (`sp|P04637|P53_HUMAN`).
ACCESSION = re.compile(
    r"([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})(-\d+)?(?:\.\d+)?"
)
UNIPROT_ID = re.compile(r"(?:sp|tr)\|([^|]+)\|[^|]*", re.IGNORECASE)
LOCATION = re.compile(r"([A-Z0-9]+)(-\d+)?(?::(\d+)-(\d+))?")  # P26662-2:810-1026


@dataclass(frozen=True)
class Page:
    """At most `limit` lines per input, the best first; a list that is cut ends with how many
    there are, and the limit that cut it."""

    limit: int = LIMIT

    def cut[T](self, items: list[T]) -> list[T]:
        return items[: self.limit]

    def lines(self, label: str, lines: list[str], total: int | None = None) -> list[str]:
        """An input's lines, each after its label, cut to the page; `lines` may already be the
        page, of `total` lines."""
        total = len(lines) if total is None else total
        if not total:
            return [f"{label}\t(none)"]
        shown = [f"{label}\t{line}" for line in self.cut(lines)]
        if len(shown) < total:
            shown.append(f"{label}\t… {len(shown)} of {total} shown, cut by --limit {self.limit}")
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


def _bare(text: str) -> str:
    """A text without case or punctuation: `Bio-layer` is `biolayer`."""
    return re.sub(r"[\W_]+", "", text.casefold())


def _term_rank(text: str, names: list[str]) -> int:
    """How closely a text matches the names of a term, case and punctuation aside: 0 a name is
    the text, 1 a name starts with it, 2 a name contains it, 3 a name contains each of its
    words, 4 none."""
    wanted, words = _bare(text), [w for w in map(_bare, text.split()) if w]
    bare = [_bare(n) for n in names]
    if not wanted:
        return 4
    if wanted in bare:
        return 0
    if any(n.startswith(wanted) for n in bare):
        return 1
    if any(wanted in n for n in bare):
        return 2
    return 3 if any(all(w in n for w in words) for n in bare) else 4


def database(reviewed: bool) -> str:
    return "SP" if reviewed else "TR"


# --- Accessions as publications write them -----------------------------------------------------


def written_accession(text: str) -> tuple[str, str] | None:
    """(entry accession, isoform accession) of an accession as publications write it: `P04637`,
    `p04637`, `P04637-2` (the isoform), `P04637.2`, `sp|P04637|P53_HUMAN`; None for any other
    text."""
    text = text.strip()
    if match := UNIPROT_ID.fullmatch(text):
        text = match.group(1)
    match = ACCESSION.fullmatch(text.upper())
    if match is None:
        return None
    accession, isoform = match.groups()
    return accession, accession + (isoform or "")


def written_accessions(text: str) -> list[str] | None:
    """The accessions an input holds, each as written: one, or a group (`P09913; O14879`,
    `Q15646;`, `P09913,O14879`); None when it is not made of accessions only."""
    parts = [p for p in re.split(r"[;,\s]+", text) if p]
    return parts if parts and all(written_accession(p) for p in parts) else None


def current_entries(cur: Any, accession: str) -> list[str]:
    """The current entries an accession names: its own when it is current, else the entries
    that hold it as an old accession, one after a merge, several after a split."""
    cur.execute(
        """
        SELECT accession FROM proteins_versions
        WHERE accession = %(accession)s OR secondary_accessions @> ARRAY[%(accession)s]::varchar[]
        ORDER BY accession
        """,
        {"accession": accession},
    )
    found = [r[0] for r in cur.fetchall()]
    return [accession] if accession in found else found


def methods(cur: Any, texts: list[str], page: Page = DEFAULT) -> str:
    """The PSI-MI terms whose name or a synonym holds each word of the text, case and punctuation
    aside: the closest names first, then the detection methods, then the most used."""
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
        found = [m for m in terms if _term_rank(text, [m[1], *m[2]]) < 4]
        found.sort(key=lambda m: (_term_rank(text, [m[1], *m[2]]), not m[3], -m[4], m[0]))
        shown: list[str] = []
        for psimi_id, name, synonyms, detection, count in found:
            also = [s for s in synonyms if _term_rank(text, [s]) < 4]
            if also and _term_rank(text, [name]) == 4:
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


def entries(cur: Any, texts: list[str]) -> str:
    """Each entry the texts name, a group of accessions one by one."""
    return "\n\n".join(
        entry(cur, accession) for text in texts for accession in written_accessions(text) or [text]
    )


def _snapshots(cur: Any, accession: str) -> list[tuple[Any, ...]]:
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
    return cur.fetchall()


def entry(cur: Any, text: str) -> str:
    """The block of each current entry an accession names, as publications write it
    (`current_entries`; an isoform's names its entry); never an obsolete one."""
    found = written_accession(text)
    if found is None:
        return f"# {text}: not an accession"
    accession, isoform = found
    named = current_entries(cur, accession)
    if not named:
        return f"# {text}: no current entry has this accession, current or old"
    blocks: list[str] = []
    for current in named:
        note = (
            f"# {accession} is a secondary accession of {current}\n"
            if current != accession
            else f"# {text} is an isoform of {accession}\n"
            if isoform != accession
            else ""
        )
        blocks.append(note + _entry(cur, current, _snapshots(cur, current)))
    return "\n\n".join(blocks)


def _entry(cur: Any, accession: str, snapshots: list[tuple[Any, ...]]) -> str:
    """A current entry's block, from its snapshots."""
    latest = next(s for s in snapshots if s[7])
    id_, version, type_, gene, description, taxon, sequences, _ = latest
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
        f"Snapshot {id_} ({version}), current; length {len(isoforms.get(accession, ''))}",
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
        parts = [f for f in json.loads(features) if f.get("type") in FEATURES]
        if parts:
            lines += ["", "Chains, peptides and regions:"]
            lines += [
                f"- {f['start']}-{f['stop']} {FEATURES[f['type']]}: {f.get('description', '')}"
                for f in sorted(parts, key=lambda f: (f["start"], -f["stop"]))
            ]
    if type_ == "v":
        lines += _generic_names(cur, [s[0] for s in snapshots], id_)
    return "\n".join(lines)


def _generic_names(cur: Any, snapshot_ids: list[int], latest: int) -> list[str]:
    """The generic names of the live descriptions of an entry's snapshots, each with its span
    and its live descriptions, by snapshot: one span per name and one name per span on each
    (`curation-rules.md` §1, names; invariants D6 and D10)."""
    cur.execute(
        """
        SELECT protein2_id, name2, start2, stop2, count(*) AS descriptions
        FROM descriptions
        WHERE protein2_id = ANY(%s) AND deleted_at IS NULL
        GROUP BY protein2_id, name2, start2, stop2
        ORDER BY protein2_id, start2, stop2, name2
        """,
        (snapshot_ids,),
    )
    by_snapshot: dict[int, list[str]] = defaultdict(list)
    for snapshot, name2, start, stop, count in cur.fetchall():
        by_snapshot[snapshot].append(f"- {start}-{stop} {name2} ({count})")
    if not by_snapshot:
        return ["", "Generic names (live descriptions): none"]
    lines: list[str] = []
    for snapshot in sorted(by_snapshot, key=lambda s: (s != latest, s)):
        which = "" if snapshot == latest else f", on obsolete snapshot {snapshot}"
        lines += ["", f"Generic names (live descriptions){which}:", *by_snapshot[snapshot]]
    return lines


# An entry as `search` and `closest` show it, and the columns of its line (`_described`).
ENTRY = """
    SELECT p.accession, v.reviewed, p.name, p.description, p.ncbi_taxon_id, v.names,
           length(p.sequences->>p.accession), v.secondary_accessions
    FROM proteins_versions AS v
    JOIN proteins AS p ON p.accession = v.accession AND p.version = v.version
"""
DESCRIBED = "accession\tother_accessions\tdb\tgene\tprotein\ttaxon\tlength"


def _described(row: tuple[Any, ...], names: dict[int, str]) -> str:
    """An entry's line: the accession to write, its other accessions (its old ones, `-` when
    none), Swiss-Prot or TrEMBL, gene name, protein name, taxon, length."""
    accession, is_reviewed, gene, description, taxon_id, _, length, others = row[:8]
    taxon_name = names.get(taxon_id, "not in the NCBI taxonomy")
    return (
        f"{accession}\t{','.join(others) or '-'}\t{database(is_reviewed)}\t{gene}\t"
        f"{description}\t{taxon_id} {taxon_name}\t{length}"
    )


def search(cur: Any, texts: list[str], taxon: int | None = None, page: Page = DEFAULT) -> str:
    """The current entries each text names, under the taxon when given, Swiss-Prot first, each
    with its other accessions (its old ones). An accession as publications write it (an old
    one, an isoform's, `sp|P04637|P53_HUMAN`; a group `P09913; O14879` one by one) gives its
    current entries (`current_entries`), or, when it names none, the entries with a gene name
    that is the text (`B3GAT1`). Any other text gives the entries whose `search` text
    (accession, gene names, taxon, protein name) contains it, case aside, the closest names
    first."""
    taxa = None if taxon is None else subtree(cur, taxon)
    under = "(%(taxa)s::int[] IS NULL OR p.ncbi_taxon_id = ANY(%(taxa)s))"
    found: dict[str, list[tuple[Any, ...]]] = {}
    for label in (a for text in texts for a in written_accessions(text) or [text]):
        accession = written_accession(label)
        named = current_entries(cur, accession[0]) if accession else []
        where = "p.accession = ANY(%(named)s)" if named else "v.search ILIKE %(like)s"
        cur.execute(
            f"{ENTRY} WHERE {where} AND {under}",
            {"named": named, "like": _like(label), "taxa": taxa},
        )
        rows: list[tuple[Any, ...]] = cur.fetchall()
        if accession and not named:  # a gene name with an accession's shape, whole
            rows = [r for r in rows if _rank(label, r[5]) == 0]
        rows.sort(key=lambda r: (not r[1], _rank(label, [r[2], r[3], *r[5]]), r[0]))
        found[label] = rows
    names = taxon_names(cur, {r[4] for rows in found.values() for r in page.cut(rows)})
    lines = [f"#text\t{DESCRIBED}"]
    for text, rows in found.items():
        lines += page.lines(text, [_described(r, names) for r in page.cut(rows)], len(rows))
    return "\n".join(lines)


def label_of(text: str) -> str:
    """An input as its line shows it: whitespace as one space, cut at 20 characters."""
    text = " ".join(text.split())
    return text if len(text) <= 20 else f"{text[:20]}…({len(text)} characters)"


def spaced(text: str) -> str | None:
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
        if why := spaced(text):
            unread[label_of(text)] = why
        elif any(c.isdigit() for c in text):  # an accession, never a sequence
            try:
                queries[text] = sequence_of(cur, text)
            except ValueError as e:
                unread[text] = str(e)
        elif AMINO_ACIDS.fullmatch(text.upper()):
            queries[text if len(text) <= 20 else f"{text[:20]}…({len(text)} aa)"] = text.upper()
        else:
            unread[label_of(text)] = "neither an accession nor an amino acid sequence"
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
    """The current entries of the taxon closest to each sequence, as `search` shows them, with
    the identity, the coverage and the region aligned: every isoform is aligned
    (Smith-Waterman), each entry ranked by the score of its best isoform, then Swiss-Prot
    first."""
    queries, unread = _queries(cur, sequences)
    cur.execute(
        """
        SELECT p.accession, v.reviewed, p.name, p.description, p.ncbi_taxon_id, v.names,
               length(p.sequences->>p.accession), v.secondary_accessions, p.sequences::text
        FROM proteins_versions AS v
        JOIN proteins AS p ON p.accession = v.accession AND v.version = p.version
        WHERE p.ncbi_taxon_id = ANY(%s)
        ORDER BY p.accession
        """,
        (subtree(cur, taxon),),
    )
    entries: list[tuple[Any, ...]] = []
    isoforms: list[tuple[int, str, str]] = []  # entry index, isoform accession, sequence
    for row in cur.fetchall():
        for isoform, sequence in sorted(cast(dict[str, str], json.loads(row[8])).items()):
            isoforms.append((len(entries), isoform, sequence.translate(UNSCORED)))
        entries.append(row[:8])
    targets = pyopal.Database([s for _, _, s in isoforms], alphabet=SEARCH.alphabet)
    names = taxon_names(cur, {e[4] for e in entries})
    lines = [f"#sequence\t{DESCRIBED}\tidentity\tcoverage\tregion"]
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
        rows = [
            f"{_described(entries[e], names)}"
            f"\t{_hit(alignment, entries[e][0], isoforms[best[e][1]][1])}"
            for e, alignment in zip(shown, aligned, strict=True)
        ]
        lines += page.lines(label, rows, len(ranked))
    lines += [f"{label}\t{why}" for label, why in unread.items()]
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
    snapshot (an obsolete one marked: its generic name stays reusable, its entry does not)."""
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


def sql(cur: Any, query: str, limit: int) -> str:
    """The rows of a free query, tab-separated under a `#` header of column names, each cell cut
    at `CELL` characters; refused when it returns more than `limit` rows, so that no result is
    ever cut. A query is run through a cursor that fetches on the server; a statement no cursor
    takes (EXPLAIN, SHOW) is run as is."""
    query = query.strip().rstrip(";")
    try:
        cur.execute("SAVEPOINT lookup")
        try:
            cur.execute(f"DECLARE lookup NO SCROLL CURSOR FOR {query}")
        except psycopg.Error:
            cur.execute("ROLLBACK TO SAVEPOINT lookup")
            cur.execute(query)
            if cur.description is None:
                return ""
            columns = [c.name for c in cur.description]
            rows = cur.fetchmany(limit + 1)
        else:
            cur.execute(f"FETCH {limit + 1} FROM lookup")
            columns = [c.name for c in cur.description]
            rows = cur.fetchall()
    except psycopg.Error as e:
        sys.exit(f"sql: {e}".strip())
    if len(rows) > limit:
        sys.exit(f"sql: more than {limit} rows, none printed: narrow the query or raise --limit")
    shown = ["\t".join(_cell(v) for v in row) for row in rows]
    return "\n".join(["#" + "\t".join(columns), *shown])


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
    c = commands.add_parser("closest", parents=[limit], help="entries closest to sequences")
    c.add_argument("sequences", nargs="+", help="a sequence, or <accession>[:<start>-<stop>]")
    c.add_argument("--taxon", type=int, required=True, help="NCBI taxon ID: its whole subtree")
    q = commands.add_parser("seq", help="sequences, or subsequences between coordinates")
    q.add_argument("locations", nargs="+", help="<accession>[:<start>-<stop>]")
    n = commands.add_parser("names", parents=[limit], help="generic names used under each taxon")
    n.add_argument("taxa", nargs="+", type=int, help="NCBI taxon ID: its whole subtree")
    x = commands.add_parser("sql", help="free read-only SQL")
    x.add_argument("query")
    x.add_argument("--limit", type=int, required=True, help="rows: refused beyond")
    args = parser.parse_args()
    with connect(readonly=True) as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '30s'")
        if args.command == "entry":
            print(entries(cur, args.accessions))
        elif args.command == "seq":
            print(seq(cur, args.locations))
        elif args.command == "sql":
            print(sql(cur, args.query, args.limit))
        else:
            page = Page(args.limit)
            if args.command == "methods":
                print(methods(cur, args.texts, page))
            elif args.command == "taxon":
                print(taxa(cur, args.texts, page))
            elif args.command == "search":
                print(search(cur, args.texts, args.taxon, page))
            elif args.command == "closest":
                print(closest(cur, args.sequences, args.taxon, page))
            else:
                print(names(cur, args.taxa, page))
