"""Add and revise descriptions, so that every written row satisfies the invariants.

Guard functions for the regular curation route (`docs/database.md` §2), not a surface for
database corrections, which go outside this route:

- `add_description`: a new interaction on a publication, with a new `CW` stable ID, version 1.
- `revise_description`: a new version of an existing stable ID that fixes it (the publication
  never changes). It keeps the protein snapshots of the description, even obsolete ones.
- `update_snapshots`: a new version of an existing stable ID that only moves it to the current
  protein snapshots (UniProt upgrade job, never mixed with fixes).
- `mark_curated`: end of a curation pass, the publication `curated` with its note.
- `curate_publication`: a curation pass, all the descriptions found at once, then
  `mark_curated`.

They take each interaction as an `Interaction` (accessions, coordinates, names, mapping
sequences). Everything the invariants derive is computed here, never passed by the caller:
snapshots, human names (D7), human coordinates (D4), mapping occurrences (D9). The
remaining invariants are checked against the database before writing, and any violation raises
`InvalidDescription` with every problem found. Nothing is committed: the caller owns the
transaction and commits or rolls back (dry run).

    with connect() as conn, conn.cursor() as cur:
        stable_id = add_description(cur, run_id, pmid, Interaction(...))
        conn.rollback()  # or conn.commit(), once the user approved the write
"""

import json
import re
import secrets
from collections import defaultdict
from dataclasses import dataclass, field, replace
from typing import Any, cast

from Bio import Align
from Bio.Align import substitution_matrices

MIN_IDENTITY = 96.0  # C4
AMINO_ACIDS = re.compile(r"[ACDEFGHIKLMNPQRSTVWYUOXBZJ]+")


class InvalidDescription(ValueError):
    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class Interaction:
    """What a curator decides for one description.

    `accession2` is viral in vh, human in hh. `start2`/`stop2` default to the full protein; a
    mature protein of a polyprotein gets its coordinates. `name2` is the generic name of a viral
    interactor; it is ignored in hh, where it is the gene name. Mappings are the domain sequences
    as described by the publication (C4: never adapted to UniProt).
    """

    method: str  # PSI-MI ID, e.g. "MI:0007"
    accession1: str
    accession2: str
    name2: str = ""
    start2: int | None = None
    stop2: int | None = None
    mappings1: tuple[str, ...] = field(default=())
    mappings2: tuple[str, ...] = field(default=())


@dataclass(frozen=True)
class Snapshot:
    id: int
    accession: str
    type: str
    gene: str
    taxon: int
    sequences: dict[str, str]

    @property
    def length(self) -> int:
        return len(self.sequences[self.accession])


def _aligner() -> Any:  # Biopython is not fully typed
    # The whole mapping is aligned (global), the protein may overhang at both ends for free.
    aligner = Align.PairwiseAligner(mode="global")
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")  # type: ignore
    aligner.open_gap_score = -10
    aligner.extend_gap_score = -0.5
    aligner.end_deletion_score = 0  # protein residues outside the mapping
    return aligner


ALIGNER: Any = _aligner()


def map_sequence(sequence: str, snapshot: Snapshot, start: int, stop: int) -> dict[str, Any]:
    """Mapping JSON for one sequence: its occurrences on each isoform of the interactor.

    Positions on the canonical isoform are relative to the region [start, stop], positions on
    other isoforms to the whole isoform (as checked by D9). On each isoform, every exact
    occurrence is reported; without any, the best alignment is kept if it reaches
    `MIN_IDENTITY`. Identity is the number of identical residues over the alignment length
    (mapping plus the protein residues facing a gap in it).
    """
    regions = {
        isoform: seq[start - 1 : stop] if isoform == snapshot.accession else seq
        for isoform, seq in snapshot.sequences.items()
    }
    isoforms: list[dict[str, Any]] = []
    for isoform, region in sorted(regions.items()):
        occurrences: list[dict[str, Any]] = []
        position = region.find(sequence)
        while position != -1:
            occurrences.append(
                {"start": position + 1, "stop": position + len(sequence), "identity": 100}
            )
            position = region.find(sequence, position + 1)
        if not occurrences:
            alignment: Any = ALIGNER.align(region, sequence)[0]
            counts: Any = alignment.counts()
            columns = len(sequence) + counts.internal_deletions
            identity: float = round(100 * counts.identities / columns, 5)
            if identity >= MIN_IDENTITY:
                blocks = alignment.aligned[0]  # aligned blocks on the region
                start_, stop_ = int(blocks[0][0]) + 1, int(blocks[-1][1])
                occurrences.append({"start": start_, "stop": stop_, "identity": identity})
        if occurrences:
            isoforms.append({"accession": isoform, "occurrences": occurrences})
    return {"sequence": sequence, "isoforms": isoforms}


def _snapshot(cur: Any, accession: str, snapshot_id: int | None = None) -> Snapshot | None:
    """A snapshot of an accession, or None; raise if the data is inconsistent.

    The current one (C5), or the given `snapshot_id`, which may be obsolete (fixes keep the
    snapshots of the description).
    """
    if snapshot_id is None:
        cur.execute(
            """
            SELECT p.id, p.accession, p.type, p.name, p.ncbi_taxon_id, p.sequences::text
            FROM proteins AS p
            JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
            WHERE p.accession = %s
            """,
            (accession,),
        )
    else:
        cur.execute(
            """
            SELECT id, accession, type, name, ncbi_taxon_id, sequences::text
            FROM proteins WHERE id = %s AND accession = %s
            """,
            (snapshot_id, accession),
        )
    rows = cur.fetchall()
    if not rows:
        return None
    if len(rows) > 1:
        ids = ", ".join(str(r[0]) for r in rows)
        raise InvalidDescription([f"{accession} has {len(rows)} current snapshots ({ids})"])
    id_, accession, type_, gene, taxon, sequences = rows[0]
    parsed: Any = json.loads(sequences)
    raw = cast(dict[str, Any], parsed) if isinstance(parsed, dict) else {}
    isoforms = {k: v for k, v in raw.items() if isinstance(v, str) and v}
    problems: list[str] = []
    if type_ not in ("h", "v"):
        problems.append(f"{accession} (snapshot {id_}) has type {type_!r}")
    if accession not in isoforms:
        problems.append(f"{accession} (snapshot {id_}) has no canonical sequence")
    elif len(isoforms) != len(raw):
        problems.append(f"{accession} (snapshot {id_}) has an empty or invalid isoform sequence")
    if type_ == "h" and not (gene or "").strip():
        problems.append(f"{accession} (snapshot {id_}) is human without a gene name (D7)")
    if problems:
        raise InvalidDescription(problems)
    return Snapshot(id_, accession, type_, gene or "", taxon, isoforms)


def _build(
    cur: Any,
    association_id: int,
    run_type: str,
    item: Interaction,
    stable_id: str | None,
    kept: tuple[tuple[str, int], tuple[str, int]] | None = None,
) -> dict[str, Any]:
    """The row to write for an interaction; raise `InvalidDescription` on any violation.

    `stable_id` is the description being revised (excluded from the D5 and D6 comparisons).
    `kept` is its (accession, snapshot ID) on each side: a side that keeps its accession keeps
    that snapshot, even obsolete; otherwise a side uses the current snapshot of its accession.
    """
    problems: list[str] = []
    cur.execute("SELECT id FROM methods WHERE psimi_id = %s", (item.method,))
    methods = cur.fetchall()
    method = methods[0] if len(methods) == 1 else None
    if not methods:
        problems.append(f"unknown method {item.method}")
    elif len(methods) > 1:
        problems.append(f"method {item.method} has {len(methods)} rows in `methods`")

    pinned = [
        kept[side][1] if kept and kept[side][0] == accession else None
        for side, accession in enumerate((item.accession1, item.accession2))
    ]
    p1 = _snapshot(cur, item.accession1, pinned[0])
    p2 = _snapshot(cur, item.accession2, pinned[1])
    expected2 = "v" if run_type == "vh" else "h"
    for side, accession, snapshot, expected in (
        (1, item.accession1, p1, "h"),
        (2, item.accession2, p2, expected2),
    ):
        if snapshot is None:
            problems.append(f"protein {side}: {accession} has no current snapshot (D2)")
            continue
        if snapshot.type != expected:  # D1
            problems.append(
                f"protein {side}: {accession} is type {snapshot.type!r}, "
                f"expected {expected!r} in a {run_type} run (D1)"
            )
        cur.execute("SELECT 1 FROM taxon WHERE ncbi_taxon_id = %s", (snapshot.taxon,))
        if cur.fetchone() is None:
            problems.append(
                f"protein {side}: taxon {snapshot.taxon} of {accession} "
                "is missing from the taxonomy (R3)"
            )
    if p1 is None or p2 is None or problems:
        raise InvalidDescription(problems)

    start2 = 1 if item.start2 is None else item.start2
    stop2 = p2.length if item.stop2 is None else item.stop2
    if run_type == "hh":
        if (start2, stop2) != (1, p2.length):  # D4
            problems.append(
                f"protein 2: {start2}-{stop2}, but a human interactor is 1-{p2.length} (D4)"
            )
        name2 = p2.gene
    else:
        if not 1 <= start2 <= stop2 <= p2.length:  # D3
            problems.append(f"protein 2: {start2}-{stop2} is outside 1-{p2.length} (D3)")
        name2 = item.name2.strip()
        if not name2:
            problems.append("protein 2: the generic name is empty (D6)")
    if problems:
        raise InvalidDescription(problems)

    # D9: mappings are computed here, and must reach the identity threshold.
    mappings: list[list[dict[str, Any]]] = []
    for side, snapshot, sequences, start, stop in (
        (1, p1, item.mappings1, 1, p1.length),
        (2, p2, item.mappings2, start2, stop2),
    ):
        if len(set(sequences)) != len(sequences):
            problems.append(f"protein {side}: duplicate mapping sequences")
        computed: list[dict[str, Any]] = []
        for sequence in sequences:
            if not AMINO_ACIDS.fullmatch(sequence):
                problems.append(
                    f"protein {side}: mapping {sequence[:20]}… is not an uppercase "
                    "amino acid sequence"
                )
                continue
            mapping = map_sequence(sequence, snapshot, start, stop)
            if not mapping["isoforms"]:
                problems.append(
                    f"protein {side}: mapping {sequence[:20]}… "
                    f"({len(sequence)} aa) is below {MIN_IDENTITY:g} % identity "
                    f"on every isoform of {snapshot.accession}[{start}-{stop}] (D9)"
                )
            computed.append(mapping)
        mappings.append(computed)

    # D5: no other live description of the same publication, method and interactors.
    cur.execute(
        """
        SELECT d.stable_id FROM descriptions AS d
        JOIN proteins AS p1 ON p1.id = d.protein1_id
        JOIN proteins AS p2 ON p2.id = d.protein2_id
        WHERE d.deleted_at IS NULL AND d.association_id = %s AND d.method_id = %s
          AND p1.accession = %s AND p2.accession = %s AND d.start2 = %s AND d.stop2 = %s
          AND d.stable_id IS DISTINCT FROM %s
        """,
        (
            association_id,
            method[0] if method else None,
            p1.accession,
            p2.accession,
            start2,
            stop2,
            stable_id,
        ),
    )
    if duplicates := [r[0] for r in cur.fetchall()]:
        problems.append(
            f"same publication, method and interactors as live {', '.join(duplicates)} "
            "(D5): add mappings to that description instead"
        )

    # D6: a viral interactor keeps the generic name it already has (C2).
    if run_type == "vh":
        cur.execute(
            """
            SELECT DISTINCT d.name2 FROM descriptions AS d
            JOIN proteins AS p2 ON p2.id = d.protein2_id
            JOIN associations AS a ON a.id = d.association_id
            JOIN runs AS r ON r.id = a.run_id
            WHERE d.deleted_at IS NULL AND r.type = 'vh' AND p2.accession = %s
              AND d.start2 = %s AND d.stop2 = %s AND d.stable_id IS DISTINCT FROM %s
            """,
            (p2.accession, start2, stop2, stable_id),
        )
        names = sorted(r[0] for r in cur.fetchall())
        if names and names != [name2]:
            problems.append(
                f"protein 2: {p2.accession}[{start2}-{stop2}] is already named "
                f"{' | '.join(names)}, not {name2!r} (D6)"
            )

    if problems:
        raise InvalidDescription(problems)
    row = {
        "association_id": association_id,
        "method_id": method[0] if method else None,
        "protein1_id": p1.id,
        "name1": p1.gene,  # D7
        "start1": 1,  # D4
        "stop1": p1.length,
        "mapping1": json.dumps(mappings[0]),
        "protein2_id": p2.id,
        "name2": name2,
        "start2": start2,
        "stop2": stop2,
        "mapping2": json.dumps(mappings[1]),
    }
    return row


@dataclass(frozen=True)
class _Association:
    """A publication in one run (internal: the API names it by run ID and PMID)."""

    id: int
    run_id: int
    pmid: int
    run_type: str
    state: str

    def __str__(self) -> str:
        return f"publication {self.pmid} in run {self.run_id}"


ASSOCIATION = """
    SELECT a.id, a.run_id, a.pmid, r.type, a.state
    FROM associations AS a JOIN runs AS r ON r.id = a.run_id
"""


def _one_association(rows: list[tuple[Any, ...]], what: str) -> _Association:
    if not rows:
        raise InvalidDescription([f"{what} does not exist"])
    if len(rows) > 1:
        ids = ", ".join(str(r[0]) for r in rows)
        raise InvalidDescription([f"{what} has {len(rows)} associations ({ids})"])
    association = _Association(*rows[0])
    if association.run_type not in ("vh", "hh"):
        raise InvalidDescription([f"run {association.run_id} has type {association.run_type!r}"])
    return association


def _association(cur: Any, run_id: int, pmid: int) -> _Association:
    """A publication in a run. It can also be in runs of the other type, which are not read."""
    cur.execute(ASSOCIATION + "WHERE a.run_id = %s AND a.pmid = %s", (run_id, pmid))
    return _one_association(cur.fetchall(), f"publication {pmid} in run {run_id}")


STABLE_ID = re.compile(r"(EY|CW)[0-9A-F]{8}|EYUW[0-9A-F]{6}")  # V7

# All versions of a stable ID: (id, stable_id, version, association_id, created_at, deleted_at).
VERSION_ROWS = """
    SELECT id, stable_id, version, association_id, created_at, deleted_at FROM descriptions
    WHERE stable_id = %s ORDER BY version
"""


def _version_problems(rows: list[tuple[Any, ...]]) -> list[str]:
    """Versioning problems (V2 to V7) of the stable IDs of `rows`, all their versions included."""
    by_stable_id: dict[str, list[tuple[Any, ...]]] = defaultdict(list)
    for row in rows:
        by_stable_id[row[1]].append(row)
    problems: list[str] = []
    for stable_id, versions in sorted(by_stable_id.items()):
        numbers = [v[2] for v in versions]
        live = [v[2] for v in versions if v[5] is None]
        if not STABLE_ID.fullmatch(stable_id.strip()):
            problems.append(f"{stable_id!r}: malformed stable ID (V7)")
        if numbers != list(range(1, len(numbers) + 1)):
            problems.append(f"{stable_id}: versions {numbers}, not 1 to {len(numbers)} (V2)")
        if len(live) > 1:
            problems.append(f"{stable_id}: versions {live} are all live (V3)")
        elif live and live[0] != numbers[-1]:
            problems.append(f"{stable_id}: live version {live[0]} is not the last one (V3)")
        for version, following in zip(versions, versions[1:], strict=False):
            if version[5] is not None and version[5] > following[4]:
                problems.append(
                    f"{stable_id}: version {version[2]} deleted after version {following[2]} "
                    "was created (V4)"
                )
        for version in versions:
            if version[5] is not None and version[5] < version[4]:
                problems.append(f"{stable_id}: version {version[2]} deleted before created (V5)")
        if len({v[3] for v in versions}) > 1:
            problems.append(f"{stable_id}: versions in several publications (V6)")
    return problems


def _check_versions(cur: Any, stable_id: str, lock: bool) -> list[Any]:
    """All versions of a stable ID, locked if `lock`; raise if their versioning is broken.

    A revision is built on them (next version, live row), so it must not add to a mess. Other
    descriptions are not checked: detecting and fixing problems is not the guards' concern.
    """
    cur.execute(VERSION_ROWS + (" FOR UPDATE" if lock else ""), (stable_id,))
    rows = cur.fetchall()
    if problems := _version_problems(rows):
        raise InvalidDescription(problems)
    return rows


def _state_problems(association: _Association) -> list[str]:
    """A publication still `pending` or `discarded` has no descriptions: reconsider its state.

    `selected`: curation in progress, descriptions are added over time. `curated`: curation is
    done, but its descriptions can still be revised or completed.
    """
    if association.state in ("selected", "curated"):
        return []
    return [f"{association} is {association.state}: reconsider its state first"]


def _insert(cur: Any, stable_id: str, version: int, row: dict[str, Any]) -> None:
    columns = ["stable_id", "version", *row]
    cur.execute(
        f"INSERT INTO descriptions ({', '.join(columns)}, created_at) "
        f"VALUES ({', '.join(['%s'] * len(columns))}, now())",
        (stable_id, version, *row.values()),
    )


def new_stable_id(cur: Any) -> str:
    """A `CW` stable ID unused by any row, live or deleted (V7, collision check of §2)."""
    while True:
        candidate = "CW" + secrets.token_hex(4).upper()
        cur.execute("SELECT 1 FROM descriptions WHERE stable_id = %s", (candidate,))
        if cur.fetchone() is None:
            return candidate


def _vh_association(cur: Any, run_id: int, pmid: int) -> _Association:
    """A publication in a vh run, `selected` or `curated`, where descriptions can be added."""
    association = _association(cur, run_id, pmid)
    problems = _state_problems(association)
    if association.run_type != "vh":
        problems.append(
            f"run {run_id} is a {association.run_type} run: new descriptions go to a vh run"
        )
    if problems:
        raise InvalidDescription(problems)
    return association


def _add(cur: Any, association: _Association, item: Interaction) -> str:
    row = _build(cur, association.id, "vh", item, None)
    stable_id = new_stable_id(cur)
    _insert(cur, stable_id, 1, row)
    return stable_id


def add_description(cur: Any, run_id: int, pmid: int, item: Interaction) -> str:
    """Insert a new description on a publication of a vh run; return its new `CW` stable ID.

    The publication must be `selected` or `curated` in that run. It may also be in an hh run,
    which is left untouched.
    """
    return _add(cur, _vh_association(cur, run_id, pmid), item)


CLAUDE_HEADER = re.compile(r"\[(\d{4}-\d{2}-\d{2}) Claude\] ([A-Z]+): (.+)")
PASS_LINE = re.compile(r"- Pass (\d{4}-\d{2}-\d{2}): \S")
CURATOR_BLOCK = "--- Curator note (before Claude) ---"
DESCRIPTION_COUNT = re.compile(r"\b(\d+) descriptions?\b")


def _note_problems(old: str, note: str, today: str, descriptions: int) -> list[str]:
    """Problems of a CURATED note against the template of `docs/curation-rules.md` §6.

    `old` is the note before this pass: its pass history and its curator block are kept, and a
    note not written by Claude becomes the curator block, verbatim.
    """
    problems: list[str] = []
    body, _, block = note.partition(f"\n{CURATOR_BLOCK}\n")
    lines = body.split("\n")
    header = CLAUDE_HEADER.fullmatch(lines[0])
    if header is None or header[2] != "CURATED":
        problems.append(f"note header is not `[{today} Claude] CURATED: <summary>`")
    else:
        if header[1] != today:
            problems.append(f"note header is dated {header[1]}, not today ({today})")
        count = DESCRIPTION_COUNT.search(header[3])
        if count is None or int(count[1]) != descriptions:
            problems.append(f"note header must give the count: {descriptions} descriptions")
    passes = [line for line in lines if PASS_LINE.match(line)]
    if not passes or not passes[-1].startswith(f"- Pass {today}:"):
        problems.append(f"note must end its pass history with `- Pass {today}: <outcome>`")

    old = old.strip()
    if CLAUDE_HEADER.match(old):
        old_body, _, old_block = old.partition(f"\n{CURATOR_BLOCK}\n")
        old_passes = [line for line in old_body.split("\n") if PASS_LINE.match(line)]
        if passes[: len(old_passes)] != old_passes:
            problems.append("note must keep the previous `Pass` lines, unchanged and first")
    else:
        old_block = old
    if block != old_block:
        problems.append(
            f"note must end with `{CURATOR_BLOCK}` and the previous curator note, verbatim"
            if old_block
            else f"note has a `{CURATOR_BLOCK}` block but there was no curator note"
        )
    return problems


def _live_count(cur: Any, association: _Association) -> int:
    """Live descriptions of a publication: stable IDs, even if one has several live rows."""
    cur.execute(
        "SELECT count(DISTINCT stable_id) FROM descriptions "
        "WHERE association_id = %s AND deleted_at IS NULL",
        (association.id,),
    )
    return cur.fetchone()[0]


def _curated_note_problems(
    cur: Any, association: _Association, note: str, descriptions: int
) -> list[str]:
    cur.execute(
        "SELECT coalesce(annotation, ''), current_date::text FROM associations WHERE id = %s",
        (association.id,),
    )
    old_note, today = cur.fetchone()
    return _note_problems(old_note, note, today, descriptions)


def _mark_curated(cur: Any, association: _Association, note: str) -> None:
    descriptions = _live_count(cur, association)
    if problems := _curated_note_problems(cur, association, note, descriptions):
        raise InvalidDescription(problems)
    cur.execute(
        "UPDATE associations SET state = 'curated', annotation = %s, ai_pass_at = now(), "
        "updated_at = now() WHERE id = %s",
        (note, association.id),
    )


def mark_curated(cur: Any, run_id: int, pmid: int, note: str) -> None:
    """End a curation pass: mark the publication `curated` in a vh run, with its note.

    For a pass that adds no description, e.g. a publication already curated and reviewed again,
    or one with no interaction meeting the criteria. The publication must be `selected` or
    `curated`. Its note is replaced by `note`, checked against the template
    (`docs/curation-rules.md` §6) with the count of its live descriptions, and `ai_pass_at` is
    set to now.
    """
    _mark_curated(cur, _vh_association(cur, run_id, pmid), note)


def curate_publication(
    cur: Any, run_id: int, pmid: int, items: list[Interaction], note: str
) -> list[str]:
    """One curation pass: add all the descriptions found, then `mark_curated`.

    All or nothing: on any problem, nothing is written and `InvalidDescription` lists every
    problem, prefixed by the number of the description. Returns the new stable IDs, in the order
    of `items`.
    """
    association = _vh_association(cur, run_id, pmid)
    expected = _live_count(cur, association) + len(items)
    problems: list[str] = []
    stable_ids: list[str] = []
    with cur.connection.transaction():  # savepoint: rolled back if anything fails
        for number, item in enumerate(items, start=1):
            try:
                stable_ids.append(_add(cur, association, item))
            except InvalidDescription as e:
                problems += [f"description {number}: {p}" for p in e.problems]
        if problems:
            problems += _curated_note_problems(cur, association, note, expected)
            raise InvalidDescription(problems)
        _mark_curated(cur, association, note)
    return stable_ids


def current(cur: Any, stable_id: str) -> Interaction:
    """Interaction of the live version of a stable ID, to derive a revision.

    Accessions are those of the snapshots it uses, which may be obsolete: `revise_description`
    keeps those snapshots, unless the caller changes the accession.
    """
    live_id = _live_row(cur, stable_id, lock=False)[0]
    cur.execute(
        """
        SELECT m.psimi_id, p1.accession, p2.accession, d.name2, d.start2,
               d.stop2, d.mapping1::text, d.mapping2::text
        FROM descriptions AS d
        JOIN methods AS m ON m.id = d.method_id
        JOIN proteins AS p1 ON p1.id = d.protein1_id
        JOIN proteins AS p2 ON p2.id = d.protein2_id
        WHERE d.id = %s
        """,
        (live_id,),
    )
    row = cur.fetchone()
    if row is None:
        raise InvalidDescription([f"{stable_id}: method or protein of row {live_id} is missing"])
    method, accession1, accession2, name2, start2, stop2, m1, m2 = row
    return Interaction(
        method=method,
        accession1=accession1,
        accession2=accession2,
        name2=name2,
        start2=start2,
        stop2=stop2,
        mappings1=_mapping_sequences(stable_id, 1, m1),
        mappings2=_mapping_sequences(stable_id, 2, m2),
    )


def _mapping_sequences(stable_id: str, side: int, text: str) -> tuple[str, ...]:
    mappings: Any = json.loads(text)
    sequences: list[str] = []
    items = cast(list[Any], mappings) if isinstance(mappings, list) else [None]
    for mapping in items:
        fields = cast(dict[str, Any], mapping) if isinstance(mapping, dict) else {}
        sequence = fields.get("sequence")
        if not isinstance(sequence, str):
            raise InvalidDescription([f"{stable_id}: mapping{side} is not a list of mappings"])
        sequences.append(sequence)
    return tuple(sequences)


def _live_row(cur: Any, stable_id: str, lock: bool) -> tuple[Any, ...]:
    """The live row of a stable ID, once all its versions are checked (V2 to V7)."""
    rows = _check_versions(cur, stable_id, lock)
    if not rows:
        raise InvalidDescription([f"{stable_id} does not exist"])
    live = [r for r in rows if r[5] is None]
    if not live:
        raise InvalidDescription([f"{stable_id} has no live version: it was removed"])
    return live[0]


# Accessions and snapshot IDs of a description row, and its viral coordinates.
PROTEINS = """
    SELECT p1.accession, p1.id, p2.accession, p2.id, d.start2, d.stop2
    FROM descriptions AS d
    JOIN proteins AS p1 ON p1.id = d.protein1_id
    JOIN proteins AS p2 ON p2.id = d.protein2_id
    WHERE d.id = %s
"""


def _revisable(cur: Any, stable_id: str) -> tuple[tuple[Any, ...], _Association]:
    """The live row of a stable ID, locked, and its publication, which must accept revisions."""
    live = _live_row(cur, stable_id, lock=True)
    cur.execute(ASSOCIATION + "WHERE a.id = %s", (live[3],))
    association = _one_association(cur.fetchall(), f"association {live[3]}")
    if problems := _state_problems(association):
        raise InvalidDescription(problems)
    return live, association


def _replace(cur: Any, stable_id: str, live: tuple[Any, ...], row: dict[str, Any]) -> int:
    """Write `row` as the next version of a stable ID; refuse it if it changes nothing."""
    live_id, _, version = live[:3]
    columns = list(row)
    cur.execute(
        f"SELECT {', '.join(columns)} FROM descriptions WHERE id = %s",
        (live_id,),
    )
    old = dict(zip(columns, cur.fetchone(), strict=True))
    for key in ("mapping1", "mapping2"):  # compare JSON by content
        old[key] = json.loads(old[key]) if isinstance(old[key], str) else old[key]
    new = {**row, "mapping1": json.loads(row["mapping1"]), "mapping2": json.loads(row["mapping2"])}
    if old == new:
        raise InvalidDescription([f"the revision of {stable_id} changes nothing"])

    cur.execute("UPDATE descriptions SET deleted_at = now() WHERE id = %s", (live_id,))
    _insert(cur, stable_id, version + 1, row)
    return version + 1


def revise_description(cur: Any, stable_id: str, item: Interaction) -> int:
    """Fix the live version of a stable ID by a new version; return the new version number.

    A fix never moves to another snapshot: a side that keeps its accession keeps the snapshot
    of the live row, even obsolete, and its derived values (human name and coordinates, mapping
    occurrences) are computed on it. A side whose accession changes takes the current snapshot of
    the new accession. Moving to current snapshots is `update_snapshots` alone.

    The publication stays the same (V6). The live row is deleted and the new row created at the same
    instant (V4, V5). A revision identical to the live row is refused: no throwaway version.
    """
    live, association = _revisable(cur, stable_id)
    cur.execute(PROTEINS, (live[0],))
    accession1, id1, accession2, id2, _, _ = cur.fetchone()
    kept = ((accession1, id1), (accession2, id2))
    row = _build(cur, association.id, association.run_type, item, stable_id, kept)
    return _replace(cur, stable_id, live, row)


def update_snapshots(cur: Any, stable_id: str) -> int:
    """Move the live version of a stable ID to the current snapshots; return the new version.

    The UniProt upgrade job, and nothing else: same method, accessions, viral coordinates and
    generic name, same mapping sequences. Only what derives from the snapshots follows: human
    names and full-length coordinates, mapping occurrences. Refused, with every problem found,
    when the description is already current, when an accession has no current snapshot (deleted
    from UniProt: another entry is a curation decision), when the sequence of a viral interactor
    changed between its coordinates (a curation decision), or when the result breaks an
    invariant (e.g. a mapping no longer found, D9).
    """
    live, association = _revisable(cur, stable_id)
    cur.execute(PROTEINS, (live[0],))
    accession1, id1, accession2, id2, start2, stop2 = cur.fetchone()
    problems: list[str] = []
    moved = False
    for side, accession, old_id in ((1, accession1, id1), (2, accession2, id2)):
        snapshot = _snapshot(cur, accession)
        if snapshot is None:
            problems.append(
                f"protein {side}: {accession} has no current snapshot: choosing another entry "
                "is a curation decision"
            )
            continue
        if snapshot.id == old_id:
            continue
        moved = True
        if side == 2 and association.run_type == "vh":
            old = _snapshot(cur, accession, old_id)
            assert old is not None  # foreign key
            before = old.sequences[accession][start2 - 1 : stop2]
            after = snapshot.sequences[accession][start2 - 1 : stop2]
            if before != after:
                problems.append(
                    f"protein 2: the sequence of {accession}[{start2}-{stop2}] changed: "
                    "new coordinates are a curation decision"
                )
    if not problems and not moved:
        problems.append(f"{stable_id} is already on the current snapshots")
    if problems:
        raise InvalidDescription(problems)

    item = current(cur, stable_id)
    if association.run_type == "hh":  # human interactor 2: full length, derived
        item = replace(item, start2=None, stop2=None)
    row = _build(cur, association.id, association.run_type, item, stable_id)
    return _replace(cur, stable_id, live, row)
