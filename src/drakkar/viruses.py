"""Map the viral interactors of one or more virus families to the viral proteins reference.

The reference is `docs/viruses/`: one file per family, one table of targets per NCBI species, each
target a protein with one reference sequence (a UniProt entry and region, `docs/viruses.md` §4).

`review <family>...` writes, per family, a worksheet for the review of the `map-viral-family` skill
(`skills/map-viral-family/SKILL.md`), without writing to the database: every live vh viral
interactor of the family's species (snapshot, start, stop, generic name) with its UniProt name,
the UniProt chains at its region, and the target of its species whose sequence matches it best
(MMseqs2 against the family's targets only; a local alignment for short sequences). A hit is a
`quick` match only when it is the same protein beyond doubt (high identity, both sequences
covered); the name is checked by hand in every case.

`apply <changes.tsv>` writes the approved revisions of a review: a new version of each
description with only `name2`, `start2`, `stop2` (and the `mapping2` occurrences, relative to the
coordinates) changed, and its note. Dry run unless `--commit`.
"""

import argparse
import csv
import json
import re
import shutil
import subprocess
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from Bio.Align import PairwiseAligner, substitution_matrices

from drakkar.db import connect
from drakkar.descriptions import (  # the fixes keep the snapshot of the description
    Snapshot,
    _snapshot,  # pyright: ignore[reportPrivateUsage]
    map_sequence,
)

DOCS = Path("docs/viruses")
OUTPUT = Path("data/viruses")
REF = re.compile(r"([A-Z][A-Z0-9]+) ([\d,]+)–([\d,]+)(?: \(obsolete snapshot (\d{4}_\d\d)\))?")
ROW = re.compile(r"\| `([^`]+)` +\|")
SAME_PROTEIN = 0.95  # mutual coverage of two sequences of the same protein
MIN_IDENTITY = 0.3  # below, a hit is not the same protein
MIN_COVERAGE = 0.8  # of the interactor by a hit: a fragment fits in its target, not a part of it
QUICK_IDENTITY = 0.95  # a quick match: the same protein beyond doubt, no false positive
# UniProt features that delimit a protein or a mature product.
CHAINS = ("chain", "peptide", "propeptide", "signal peptide", "transit peptide")

# Live vh viral interactors, with their descriptions and publications.
INTERACTORS = """
    WITH i AS (
        SELECT d.protein2_id, d.start2, d.stop2, d.name2, count(*) AS n,
               count(DISTINCT a.pmid) AS npub,
               string_agg(DISTINCT a.pmid::text, ' ') AS pmids,
               string_agg(d.stable_id, ' ' ORDER BY d.stable_id) AS stable_ids
        FROM descriptions AS d
        JOIN associations AS a ON a.id = d.association_id
        JOIN runs AS r ON r.id = a.run_id
        WHERE r.type = 'vh' AND d.deleted_at IS NULL
        GROUP BY d.protein2_id, d.start2, d.stop2, d.name2)
    SELECT i.protein2_id, i.start2, i.stop2, i.name2, i.n, i.npub, i.pmids, i.stable_ids,
           p.accession, p.ncbi_taxon_id,
           substr(p.sequences->>p.accession, i.start2, i.stop2 - i.start2 + 1),
           v.accession IS NOT NULL
    FROM i
    JOIN proteins AS p ON p.id = i.protein2_id
    LEFT JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
"""

# UniProt name, length and features of the interactors' snapshots (features: current ones only).
ENTRIES = """
    SELECT p.id, p.description, length(p.sequences->>p.accession), v.features
    FROM proteins AS p
    LEFT JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
    WHERE p.id = ANY(%s)
"""


@dataclass
class Reference:
    accession: str
    start: int
    stop: int
    release: str | None = None  # an obsolete snapshot; None = the current one
    sequence: str | None = None


@dataclass
class Target:
    file: str
    species: str  # NCBI species id as written in the section title, "None" when missing
    name: str
    ref: str
    # Usually one; several when the protein differs too much between strains of the species.
    references: list[Reference] = field(default_factory=lambda: list[Reference]())
    problem: str = ""


@dataclass
class Interactor:
    protein_id: int
    start: int
    stop: int
    name: str
    descriptions: int
    publications: int
    pmids: str
    stable_ids: str
    accession: str
    taxon: int
    sequence: str
    current: bool
    species: str = "None"
    uniprot_name: str = ""
    entry_length: int = 0
    chains: list[tuple[str, int, int, str]] = field(default_factory=lambda: [])
    target: Target | None = None
    identity: float = 0.0
    qcov: float = 0.0  # of the interactor by the target's region
    tcov: float = 0.0  # of the target's region by the interactor

    @property
    def quick(self) -> bool:
        return (
            self.target is not None
            and self.identity >= QUICK_IDENTITY
            and min(self.qcov, self.tcov) >= SAME_PROTEIN
        )

    @property
    def region(self) -> str:
        """Where the region stands against the UniProt chains of its entry."""
        if (self.start, self.stop) == (1, self.entry_length):
            return "whole entry"
        if any((s, e) == (self.start, self.stop) for _, s, e, _ in self.chains):
            return "a chain"
        return "not a chain"


def read_targets(files: list[str]) -> list[Target]:
    """The target rows of the given family files, with their reference parsed."""
    targets: list[Target] = []
    for name in files:
        path = DOCS / f"{name}.md"
        species = None
        for line in path.read_text().splitlines():
            if line.startswith("## "):
                m = re.search(r"NCBI (\d+|None)\)", line)
                species = m.group(1) if m else None
                continue
            m = ROW.match(line)
            if not m or species is None:
                continue
            ref = [c.strip() for c in line.split("|")][3]
            t = Target(path.name, species, m.group(1), ref)
            for part in ref.split(";"):
                r = REF.match(part.strip())
                if r:
                    start, stop = (int(r.group(n).replace(",", "")) for n in (2, 3))
                    t.references.append(Reference(r.group(1), start, stop, r.group(4)))
            if not t.references:
                t.problem = "no reference entry"
            targets.append(t)
    return targets


def load(conn: Any, targets: list[Target]) -> list[Interactor]:
    """Read the target sequences and the live viral interactors of the targets' species."""
    accs = list({r.accession for t in targets for r in t.references})
    current = dict(
        conn.execute(
            """SELECT p.accession, p.sequences->>p.accession FROM proteins_versions AS v
           JOIN proteins AS p ON p.accession = v.accession AND p.version = v.version
           WHERE v.accession = ANY(%s)""",
            (accs,),
        ).fetchall()
    )
    old = {
        (a, v): s
        for a, v, s in conn.execute(
            """SELECT accession, version, sequences->>accession FROM proteins
           WHERE accession = ANY(%s)""",
            (accs,),
        ).fetchall()
    }
    for t in targets:
        for r in t.references:
            seq = old.get((r.accession, r.release)) if r.release else current.get(r.accession)
            if seq is None:
                t.problem = (
                    f"{r.accession} not found" if r.release else f"{r.accession} not current"
                )
            elif not 1 <= r.start <= r.stop <= len(seq):
                t.problem = f"{r.accession}: region outside the entry ({len(seq)} residues)"
            else:
                r.sequence = seq[r.start - 1 : r.stop]
    interactors = [Interactor(*row) for row in conn.execute(INTERACTORS).fetchall()]
    # Species: walk the lineage of the distinct taxa once, by parent (never per row).
    node: dict[int, tuple[int | None, str]] = {}
    todo = {i.taxon for i in interactors}
    while todo:
        rows = conn.execute(
            """SELECT t.ncbi_taxon_id, pt.ncbi_taxon_id, t.node_rank FROM taxon AS t
               LEFT JOIN taxon AS pt ON pt.taxon_id = t.parent_taxon_id
               WHERE t.ncbi_taxon_id = ANY(%s)""",
            (list(todo),),
        ).fetchall()
        for taxon, parent, rank in rows:
            node[taxon] = (parent, rank)
        todo = {p for _, p, _ in rows if p is not None and p not in node}
    for i in interactors:
        tid: int | None = i.taxon
        seen: set[int] = set()
        while tid is not None and tid in node and tid not in seen:
            seen.add(tid)
            if node[tid][1] == "species":
                i.species = str(tid)
                break
            tid = node[tid][0]
    species = {t.species for t in targets}
    interactors = [i for i in interactors if i.species in species]
    entries = {
        pid: (name, length, features)
        for pid, name, length, features in conn.execute(
            ENTRIES, (list({i.protein_id for i in interactors}),)
        ).fetchall()
    }
    for i in interactors:
        name, length, features = entries[i.protein_id]
        i.uniprot_name, i.entry_length = name or "", length
        feats: list[dict[str, Any]] = features or []
        i.chains = [
            (f["type"], f["start"], f["stop"], f["description"])
            for f in feats
            if f["type"] in CHAINS and f["start"] <= i.stop and f["stop"] >= i.start
        ]
    return interactors


def place(interactors: list[Interactor], targets: list[Target], work: Path) -> None:
    """Place each interactor on the target of its species that matches it best."""
    refs = [(t, r.sequence) for t in targets for r in t.references if r.sequence]
    if not interactors or not refs:
        return
    with open(work / "q.fa", "w") as f:
        for n, i in enumerate(interactors):
            f.write(f">{n}\n{i.sequence}\n")
    with open(work / "t.fa", "w") as f:
        for n, (_, seq) in enumerate(refs):
            f.write(f">{n}\n{seq}\n")
    subprocess.run(
        [
            "mmseqs",
            "easy-search",
            work / "q.fa",
            work / "t.fa",
            work / "hits.m8",
            work / "tmp",
            "--format-output",
            "query,target,fident,qcov,tcov",
            "-e",
            "100",
            "--exhaustive-search",
            "-v",
            "1",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    hits: list[tuple[int, Target, float, float, float]] = []
    with open(work / "hits.m8") as f:
        for line in f:
            q, t, fident, qcov, tcov = line.split("\t")
            hits.append((int(q), refs[int(t)][0], float(fident), float(qcov), float(tcov)))
    # Short or variable sequences can escape the search: a local alignment on the targets of
    # their species.
    found = {q for q, *_ in hits}
    for q, i in enumerate(interactors):
        if q not in found:
            for t, seq in refs:
                if t.species == i.species:
                    hits.append((q, t, *local_alignment(i.sequence, seq)))
    # Best target: first one covering the interactor and covered by it at SAME_PROTEIN (the same
    # protein, not a joined or partial chain), then the highest identity times coverage. Same
    # species only; an interactor with no species can only go to a section with none.
    best: dict[int, tuple[tuple[bool, float], Target, float, float, float]] = {}
    for q, t, fident, qcov, tcov in hits:
        if t.species != interactors[q].species or fident < MIN_IDENTITY or qcov < MIN_COVERAGE:
            continue
        cov = min(qcov, tcov)
        key = (cov >= SAME_PROTEIN, fident * cov)
        if q not in best or key > best[q][0]:
            best[q] = (key, t, fident, qcov, tcov)
    for q, (_, t, fident, qcov, tcov) in best.items():
        i = interactors[q]
        i.target, i.identity, i.qcov, i.tcov = t, fident, qcov, tcov


def local_alignment(query: str, target: str) -> tuple[float, float, float]:
    """Identity and coverage of both sequences, from a local BLOSUM62 alignment."""
    aligner = PairwiseAligner(
        mode="local",
        substitution_matrix=substitution_matrices.load("BLOSUM62"),  # type: ignore
        open_gap_score=-10,
        extend_gap_score=-1,
    )
    alignments = aligner.align(query, target)  # type: ignore
    try:
        a = alignments[0]
    except IndexError:
        return 0.0, 0.0, 0.0
    (qs, qe), (ts, te) = (
        (a.aligned[0][0][0], a.aligned[0][-1][1]),
        (a.aligned[1][0][0], a.aligned[1][-1][1]),
    )
    same = sum(
        query[x] == target[y]
        for (q0, q1), (t0, t1) in zip(*a.aligned, strict=True)
        for x, y in zip(range(q0, q1), range(t0, t1), strict=True)
    )
    length = a.length
    return same / length, (qe - qs) / len(query), (te - ts) / len(target)


def verdict(i: Interactor) -> str:
    """same, rename, partial (the region is not the whole target: a name or region question)."""
    if i.target is None:
        return "no target"
    if min(i.qcov, i.tcov) < SAME_PROTEIN:
        return "partial"
    return "same" if i.name == i.target.name else "rename"


def write_review(family: str, targets: list[Target], interactors: list[Interactor]) -> None:
    output = OUTPUT / family
    output.mkdir(parents=True, exist_ok=True)
    interactors.sort(key=lambda i: (i.species, i.name, i.accession, i.start))
    with open(output / "interactors.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(
            [
                "species",
                "protein2_id",
                "accession",
                "current",
                "uniprot_name",
                "entry_length",
                "start",
                "stop",
                "region",
                "chains",
                "drakkar_name",
                "target",
                "target_reference",
                "verdict",
                "quick",
                "identity",
                "interactor_coverage",
                "target_coverage",
                "descriptions",
                "publications",
                "pmids",
                "stable_ids",
            ]
        )
        for i in interactors:
            t = i.target
            w.writerow(
                [
                    i.species,
                    i.protein_id,
                    i.accession,
                    i.current,
                    i.uniprot_name,
                    i.entry_length,
                    i.start,
                    i.stop,
                    i.region,
                    "; ".join(f"{k} {s}–{e} {d}".strip() for k, s, e, d in i.chains),
                    i.name,
                    t and t.name,
                    t and t.ref,
                    verdict(i),
                    i.quick,
                    round(i.identity, 3),
                    round(i.qcov, 3),
                    round(i.tcov, 3),
                    i.descriptions,
                    i.publications,
                    i.pmids,
                    i.stable_ids,
                ]
            )
    # Strains: the interactors of a species with the same name must be the same protein.
    names: dict[tuple[str, str], list[Interactor]] = defaultdict(list)
    for i in interactors:
        names[(i.species, i.name)].append(i)
    inconsistent = 0
    with open(output / "names.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(
            ["species", "drakkar_name", "interactors", "descriptions", "targets", "consistent"]
        )
        for (species, name), group in sorted(names.items()):
            hit = Counter(i.target.name if i.target else "(no target)" for i in group)
            consistent = len(hit) == 1 and all(i.quick for i in group)
            inconsistent += not consistent
            w.writerow(
                [
                    species,
                    name,
                    len(group),
                    sum(i.descriptions for i in group),
                    "; ".join(f"{k} ×{v}" for k, v in hit.most_common()),
                    consistent,
                ]
            )
    used = Counter(id(i.target) for i in interactors if i.target)
    with open(output / "targets.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["species", "target", "reference", "interactors", "problem"])
        for t in targets:
            w.writerow([t.species, t.name, t.ref, used[id(t)], t.problem])
    n: Counter[str] = Counter()
    d: Counter[str] = Counter()
    for i in interactors:
        key = f"{verdict(i)}, {'quick' if i.quick else 'not quick'}"
        n[key] += 1
        d[key] += i.descriptions
    lines = [
        f"# {family}: viral interactors against the reference",
        "",
        f"Targets: {len(targets)}, {sum(1 for t in targets if not t.problem)} readable, "
        f"{sum(1 for t in targets if used[id(t)])} used by an interactor. Species: "
        f"{len({t.species for t in targets})}.",
        "",
        "| Verdict | Interactors | Descriptions |",
        "| --- | ---: | ---: |",
        *[f"| {k} | {n[k]:,} | {d[k]:,} |" for k in sorted(n)],
        f"| **Total** | **{sum(n.values()):,}** | **{sum(d.values()):,}** |",
        "",
        f"Names of a species not on one target by quick matches: {inconsistent} of {len(names)}.",
        *[f"- Target problem: {t.name} ({t.species}): {t.problem}" for t in targets if t.problem],
    ]
    (output / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines) + "\n")


def review(families: list[str]) -> int:
    t0 = time.time()
    missing = [f for f in families if not (DOCS / f"{f}.md").exists()]
    if missing:
        raise SystemExit(f"no family file in {DOCS}: {', '.join(missing)}")
    with connect(readonly=True) as conn:
        conn.execute("SET statement_timeout = '60s'")
        for family in families:
            targets = read_targets([family])
            interactors = load(conn, targets)
            work = Path(tempfile.mkdtemp(prefix="drakkar-viruses-"))
            try:
                place(interactors, targets, work)
            finally:
                shutil.rmtree(work)
            write_review(family, targets, interactors)
    print(f"Done in {time.time() - t0:.0f} s.")
    return 0


# --- apply -------------------------------------------------------------------------------------

LIVE = """
    SELECT d.id, d.stable_id, d.version, d.protein2_id, d.start2, d.stop2, d.name2,
           d.mapping2::text, r.type
    FROM descriptions AS d
    JOIN associations AS a ON a.id = d.association_id
    JOIN runs AS r ON r.id = a.run_id
    WHERE d.stable_id = ANY(%s) AND d.deleted_at IS NULL
    FOR UPDATE OF d
"""

# Every column of a description, copied as is into its next version but the viral side.
COLUMNS = (
    "stable_id, association_id, method_id, protein1_id, name1, start1, stop1, mapping1, "
    "protein2_id, name2, start2, stop2, mapping2"
)
VIRAL = "name2, start2, stop2, mapping2"

# D5, D6 and D10 on the live vh descriptions of the given viral snapshots' accessions.
CHECKS = {
    "D5": """
        SELECT string_agg(d.stable_id, ' ') FROM descriptions AS d
        JOIN associations AS a ON a.id = d.association_id JOIN runs AS r ON r.id = a.run_id
        JOIN proteins AS p ON p.id = d.protein2_id
        WHERE d.deleted_at IS NULL AND r.type = 'vh' AND p.accession = ANY(%s)
        GROUP BY d.association_id, d.method_id, d.protein1_id, d.start1, d.stop1,
                 p.accession, d.start2, d.stop2
        HAVING count(*) > 1""",
    "D6": """
        SELECT p.accession || ' ' || d.start2 || '–' || d.stop2 || ': '
               || string_agg(DISTINCT d.name2, ' | ')
        FROM descriptions AS d
        JOIN associations AS a ON a.id = d.association_id JOIN runs AS r ON r.id = a.run_id
        JOIN proteins AS p ON p.id = d.protein2_id
        WHERE d.deleted_at IS NULL AND r.type = 'vh' AND p.accession = ANY(%s)
        GROUP BY p.accession, d.start2, d.stop2
        HAVING count(DISTINCT d.name2) > 1""",
    "D10": """
        SELECT d.protein2_id || ' ' || d.name2 || ': '
               || string_agg(DISTINCT d.start2 || '–' || d.stop2, ' | ')
        FROM descriptions AS d
        JOIN associations AS a ON a.id = d.association_id JOIN runs AS r ON r.id = a.run_id
        JOIN proteins AS p ON p.id = d.protein2_id
        WHERE d.deleted_at IS NULL AND r.type = 'vh' AND p.accession = ANY(%s)
        GROUP BY d.protein2_id, d.name2
        HAVING count(DISTINCT (d.start2, d.stop2)) > 1""",
}


@dataclass
class Change:
    """One line of a changes file: an interactor and what its descriptions become."""

    protein_id: int
    start: int
    stop: int
    name: str
    new_start: int
    new_stop: int
    new_name: str
    stable_ids: list[str]
    reason: str

    def summary(self) -> str:
        parts: list[str] = []
        if self.new_name != self.name:
            parts.append(f"name2 {self.name} → {self.new_name}")
        if (self.new_start, self.new_stop) != (self.start, self.stop):
            parts.append(f"region {self.start}–{self.stop} → {self.new_start}–{self.new_stop}")
        return ", ".join(parts)


def read_changes(path: Path) -> list[Change]:
    """The changes file of a review: a TSV with a header, one line per interactor (§ skill)."""
    changes: list[Change] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            changes.append(
                Change(
                    int(row["protein2_id"]),
                    int(row["start2"]),
                    int(row["stop2"]),
                    row["name2"],
                    int(row["new_start2"]),
                    int(row["new_stop2"]),
                    row["new_name2"],
                    row["stable_ids"].split(),
                    row["reason"].strip(),
                )
            )
    return changes


def _same_mapping(stored: Any, computed: Any) -> bool:
    """The same occurrences, identities compared to the 3rd decimal."""

    def norm(m: Any) -> Any:
        return [
            (
                x["sequence"],
                [
                    (
                        iso["accession"],
                        [
                            (o["start"], o["stop"], round(float(o["identity"]), 3))
                            for o in iso["occurrences"]
                        ],
                    )
                    for iso in sorted(x["isoforms"], key=lambda iso: iso["accession"])
                ],
            )
            for x in m
        ]

    return norm(stored) == norm(computed)


def status(mapping: str | None, new_mapping: str | None, c: Change) -> str:
    """What happened to the viral mappings of a description."""
    if not mapping or not json.loads(mapping):
        return "none"
    if (c.new_start, c.new_stop) == (c.start, c.stop):
        return "region unchanged"
    if json.loads(mapping) == json.loads(new_mapping or "[]"):
        return "recomputed, same"
    return "recomputed, changed"


def apply(path: Path, commit: bool) -> int:
    changes = read_changes(path)
    problems: list[str] = []
    applied: list[list[Any]] = []
    with connect() as conn, conn.cursor() as cursor:
        cur: Any = cursor
        cur.execute("SET statement_timeout = '60s'")
        cur.execute("SELECT now()::timestamp(0), now()::date")
        now, today = cur.fetchone()  # type: ignore
        seen: set[str] = set()
        accessions: set[str] = set()
        writes: list[tuple[int, str, int, str, str, Change]] = []
        snapshots: dict[int, Snapshot | None] = {}
        for c in changes:
            where = f"{c.protein_id} {c.start}–{c.stop} {c.name}"
            if not c.stable_ids:
                problems.append(f"{where}: no stable ID")
            if not c.summary():
                problems.append(f"{where}: changes nothing")
            if not c.reason:
                problems.append(f"{where}: no reason for the note")
            if dup := seen & set(c.stable_ids):
                problems.append(f"{where}: stable IDs in two lines: {' '.join(sorted(dup))}")
            seen |= set(c.stable_ids)
            cur.execute(LIVE, (c.stable_ids,))
            rows = cur.fetchall()
            found = {r[1] for r in rows}
            if missing := set(c.stable_ids) - found:
                problems.append(f"{where}: not live: {' '.join(sorted(missing))}")
            if c.protein_id not in snapshots:
                cur.execute("SELECT accession FROM proteins WHERE id = %s", (c.protein_id,))
                accession = cur.fetchone()
                snapshots[c.protein_id] = (
                    _snapshot(cur, accession[0], c.protein_id) if accession else None
                )
            snapshot = snapshots[c.protein_id]
            if snapshot is None:
                problems.append(f"{where}: no snapshot {c.protein_id}")
                continue
            accessions.add(snapshot.accession)
            if not 1 <= c.new_start <= c.new_stop <= snapshot.length:
                problems.append(f"{where}: new region outside the entry ({snapshot.length})")
                continue
            for id_, stable_id, version, pid, start, stop, name, mapping, run in rows:
                if run != "vh" or (pid, start, stop, name) != (
                    c.protein_id,
                    c.start,
                    c.stop,
                    c.name,
                ):
                    problems.append(
                        f"{where}: {stable_id} is {run} {pid} {start}–{stop} {name}, not the line"
                    )
                    continue
                stored: list[dict[str, Any]] = json.loads(mapping) if mapping else []
                new_mapping = mapping
                if stored and (c.new_start, c.new_stop) != (c.start, c.stop):
                    # Occurrences are relative to the coordinates: recomputed, only if our code
                    # first reproduces the stored ones.
                    sequences = [m["sequence"] for m in stored]
                    again = [map_sequence(s, snapshot, start, stop) for s in sequences]
                    if not _same_mapping(stored, again):
                        problems.append(f"{where}: {stable_id} mapping2 not reproduced")
                        continue
                    moved = [map_sequence(s, snapshot, c.new_start, c.new_stop) for s in sequences]
                    if any(not m["isoforms"] for m in moved):
                        problems.append(f"{where}: {stable_id} mapping2 not in the new region")
                        continue
                    new_mapping = json.dumps(moved, separators=(",", ":"))
                writes.append((id_, stable_id, version, new_mapping, mapping, c))
        if problems:
            print("Nothing written:\n" + "\n".join(f"- {p}" for p in problems))
            conn.rollback()
            return 1
        for id_, stable_id, version, new_mapping, mapping, c in writes:
            note = f"[{today} Claude] FIXED: {c.summary()}, {c.reason}"
            cur.execute("UPDATE descriptions SET deleted_at = %s WHERE id = %s", (now, id_))
            cur.execute(
                f"""INSERT INTO descriptions ({COLUMNS}, version, created_at, annotation)
                    SELECT {COLUMNS.replace(VIRAL, "%s, %s, %s, %s::json")}, %s, %s, %s
                    FROM descriptions WHERE id = %s""",
                (c.new_name, c.new_start, c.new_stop, new_mapping, version + 1, now, note, id_),
            )
            applied.append(
                [
                    stable_id,
                    version + 1,
                    c.protein_id,
                    c.summary(),
                    status(mapping, new_mapping, c),
                    note,
                ]
            )
        for invariant, query in CHECKS.items():
            cur.execute(query, (list(accessions),))
            problems += [f"{invariant}: {r[0]}" for r in cur.fetchall()]
        if problems:
            print("Rolled back, invariants broken:\n" + "\n".join(f"- {p}" for p in problems))
            conn.rollback()
            return 1
        out = path.with_name("applied.tsv" if commit else "dry-run.tsv")
        with open(out, "w", newline="") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(["stable_id", "version", "protein2_id", "change", "mapping2", "note"])
            w.writerows(applied)
        if commit:
            conn.commit()
        else:
            conn.rollback()
        print(
            f"{'Committed' if commit else 'Dry run, rolled back'}: {len(applied)} descriptions "
            f"from {len(changes)} lines, "
            f"mapping2: {dict(Counter(a[4] for a in applied))}. D5, D6, D10 hold. {out}"
        )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map the viral interactors of virus families to docs/viruses/."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("review", help="worksheet per family in data/viruses/<family>/")
    r.add_argument("families", nargs="+", help="family file names, e.g. retroviridae")
    a = sub.add_parser("apply", help="write the approved changes of a review")
    a.add_argument("changes", type=Path, help="e.g. data/viruses/retroviridae/changes.tsv")
    a.add_argument("--commit", action="store_true", help="commit (default: dry run)")
    args = parser.parse_args()
    if args.command == "review":
        raise SystemExit(review(args.families))
    raise SystemExit(apply(args.changes, args.commit))
