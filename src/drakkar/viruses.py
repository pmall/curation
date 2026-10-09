"""Compare the live viral interactors of Drakkar with the viral proteins reference, without writing.

The reference is `docs/viruses/`: one table of targets per NCBI species, each target a protein with
one reference sequence (a UniProt entry and region, `docs/viruses.md` §4). Every live vh viral
interactor (snapshot, start, stop, generic name) is placed on the target of its species whose
sequence matches it best (MMseqs2), and its name is compared with the target's. The report is a
Markdown summary plus TSV files: one line per interactor, and the targets that cannot be read.
"""

import argparse
import csv
import re
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from Bio.Align import PairwiseAligner, substitution_matrices

from drakkar.db import connect

DOCS = Path("docs/viruses")
REF = re.compile(r"([A-Z][A-Z0-9]+) ([\d,]+)–([\d,]+)(?: \(obsolete snapshot (\d{4}_\d\d)\))?")
ROW = re.compile(r"\| `([^`]+)` +\|")
SAME_PROTEIN = 0.95  # mutual coverage of two sequences of the same protein
MIN_IDENTITY = 0.3  # below, a hit is not the same protein
MIN_COVERAGE = 0.8  # of the interactor by a hit: a fragment fits in its target, not a part of it

# Live vh viral interactors, with the number of descriptions and publications using them.
INTERACTORS = """
    WITH i AS (
        SELECT d.protein2_id, d.start2, d.stop2, d.name2, count(*) AS n,
               count(DISTINCT a.pmid) AS npub, min(d.stable_id) AS example
        FROM descriptions AS d
        JOIN associations AS a ON a.id = d.association_id
        JOIN runs AS r ON r.id = a.run_id
        WHERE r.type = 'vh' AND d.deleted_at IS NULL
        GROUP BY d.protein2_id, d.start2, d.stop2, d.name2)
    SELECT i.protein2_id, i.start2, i.stop2, i.name2, i.n, i.npub, i.example,
           p.accession, p.ncbi_taxon_id,
           substr(p.sequences->>p.accession, i.start2, i.stop2 - i.start2 + 1),
           v.accession IS NOT NULL
    FROM i
    JOIN proteins AS p ON p.id = i.protein2_id
    LEFT JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
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
    example: str
    accession: str
    taxon: int
    sequence: str
    current: bool
    species: str = "None"
    target: Target | None = None
    identity: float = 0.0
    coverage: float = 0.0  # of the interactor by the target's region, and conversely: the smallest


def read_targets() -> list[Target]:
    """The target rows of every family file, with their reference parsed."""
    targets: list[Target] = []
    for path in sorted(DOCS.glob("*.md")):
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
    """Read the target sequences and the live viral interactors, with their species."""
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
    return interactors


def place(interactors: list[Interactor], targets: list[Target], work: Path) -> None:
    """Place each interactor on the target of its species that matches it best."""
    refs = [(t, r.sequence) for t in targets for r in t.references if r.sequence]
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
    best: dict[int, tuple[tuple[bool, float], Target, float, float]] = {}
    for q, t, fident, qcov, tcov in hits:
        if t.species != interactors[q].species or fident < MIN_IDENTITY or qcov < MIN_COVERAGE:
            continue
        cov = min(qcov, tcov)
        key = (cov >= SAME_PROTEIN, fident * cov)
        if q not in best or key > best[q][0]:
            best[q] = (key, t, fident, cov)
    for q, (_, t, fident, cov) in best.items():
        interactors[q].target, interactors[q].identity, interactors[q].coverage = t, fident, cov


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
    if i.coverage < SAME_PROTEIN:
        return "partial"
    return "same" if i.name == i.target.name else "rename"


def run(output: Path) -> int:
    t0 = time.time()
    output.mkdir(parents=True, exist_ok=True)
    targets = read_targets()
    with connect(readonly=True) as conn:
        conn.execute("SET statement_timeout = '60s'")
        interactors = load(conn, targets)
    work = Path(tempfile.mkdtemp(prefix="drakkar-viruses-"))
    try:
        place(interactors, targets, work)
    finally:
        shutil.rmtree(work)
    with open(output / "interactors.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(
            [
                "species",
                "protein2_id",
                "accession",
                "current",
                "start",
                "stop",
                "drakkar_name",
                "target",
                "target_reference",
                "file",
                "verdict",
                "identity",
                "coverage",
                "descriptions",
                "publications",
                "example_stable_id",
            ]
        )
        for i in sorted(interactors, key=lambda i: (i.species, i.name, i.accession, i.start)):
            t = i.target
            w.writerow(
                [
                    i.species,
                    i.protein_id,
                    i.accession,
                    i.current,
                    i.start,
                    i.stop,
                    i.name,
                    t and t.name,
                    t and t.ref,
                    t and t.file,
                    verdict(i),
                    round(i.identity, 3),
                    round(i.coverage, 3),
                    i.descriptions,
                    i.publications,
                    i.example,
                ]
            )
    used = Counter(id(i.target) for i in interactors if i.target)
    with open(output / "targets.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["file", "species", "target", "reference", "interactors", "problem"])
        for t in targets:
            w.writerow([t.file, t.species, t.name, t.ref, used[id(t)], t.problem])
    n: Counter[str] = Counter()
    d: Counter[str] = Counter()
    for i in interactors:
        n[verdict(i)] += 1
        d[verdict(i)] += i.descriptions
    problems = Counter(t.problem for t in targets if t.problem)
    readable = sum(1 for t in targets if not t.problem)
    in_use = sum(1 for t in targets if used[id(t)])
    lines = [
        "# Viral interactors against the reference",
        "",
        f"Targets: {len(targets)} in `docs/viruses/`, {readable} readable, {in_use} used by an "
        "interactor.",
        "",
        "| Verdict | Interactors | Descriptions |",
        "| --- | ---: | ---: |",
        *[f"| {v} | {n[v]:,} | {d[v]:,} |" for v in ("same", "rename", "partial", "no target")],
        f"| **Total** | **{sum(n.values()):,}** | **{sum(d.values()):,}** |",
        "",
        *[f"- Targets with {p}: {c}" for p, c in problems.items()],
        "",
        f"Done in {time.time() - t0:.0f} s.",
    ]
    (output / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare the viral interactors with docs/viruses/."
    )
    parser.add_argument("output", type=Path, help="e.g. data/2026_03/reports/viruses")
    args = parser.parse_args()
    raise SystemExit(run(args.output))
