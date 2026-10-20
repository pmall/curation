"""Write descriptions and publication states (`docs/tools.md`).

Four functions, one per kind of write: `add_descriptions`, `revise_descriptions`,
`update_publications`, `move_publications`; `write_batch` runs the four on a curation batch.
Each writes its lists in one transaction:

1. every row is applied in its own savepoint; a row with a problem is not written, and its
   problems are reported with its number;
2. every invariant is checked on the whole database as the transaction sees it (`check.py`);
3. the transaction is committed only with `commit=True`, no row problem and no error. Otherwise
   it is rolled back: a dry run is the same code as a commit.

Rows are checked only for what they build on: the publication, the snapshots, the method, the
coordinates, the mappings, the note. What involves other descriptions (duplicates, generic
names) is left to the full check, on the result of the whole list: a rename carried by several
descriptions passes through inconsistent states and is valid at the end.

A description note carries no date (its version has `created_at`); a publication note keeps the
notes of its passes and moves, the newest first.
"""

import json
import re
import secrets
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast

import psycopg

from drakkar import check
from drakkar.align import MIN_IDENTITY, best_identity, map_sequence, read_written, written


class InvalidRow(ValueError):
    def __init__(self, *problems: str) -> None:
        super().__init__("; ".join(problems))
        self.problems = list(problems)


@dataclass(frozen=True)
class Description:
    """What a curator decides for one description.

    `accession2` is viral in vh, human in hh. `start2`/`stop2` default to the full protein; a
    mature protein of a polyprotein gets its coordinates. `name2` is the generic name of a viral
    interactor (in hh, the gene name, derived). Human names and coordinates are derived from the
    snapshots. Mappings are the domain sequences as used in the publication
    (`curation-rules.md` §3), their extra end residues in lowercase (`drakkar.align`); their
    occurrences are computed. `below_threshold` lists the mapping sequences accepted below
    `MIN_IDENTITY`, explained in the note; they are stored with their best occurrences.
    """

    method: str  # PSI-MI ID, e.g. "MI:0007"
    accession1: str
    accession2: str
    name2: str = ""
    start2: int | None = None
    stop2: int | None = None
    mappings1: tuple[str, ...] = ()
    mappings2: tuple[str, ...] = ()
    below_threshold: tuple[str, ...] = ()


@dataclass(frozen=True)
class NewDescription:
    """A description to add to a publication of a vh run, with its `CREATED` note."""

    run_id: int
    pmid: int
    description: Description
    note: str = ""


@dataclass(frozen=True)
class Revision:
    """A decision on the live `version` of a description.

    `revise`: a new version holding `description`, with its note (`REVISED`, `FIXED` or
    `UPDATED`). `remove`: no successor, the `REMOVED` line added to the note of the live version.
    With `into`, the removed description is a duplicate merged into that survivor: as it is, or
    as `description` when it was decided to become the survivor, it has the same publication,
    method and interactors, and the survivor holds all its mapping sequences.
    """

    stable_id: str
    version: int
    run_id: int
    pmid: int
    action: Literal["revise", "remove"]
    description: Description | None = None
    into: str = ""
    note: str = ""


@dataclass(frozen=True)
class PublicationUpdate:
    """The state of a publication (`selected` or `curated`) and the note of a pass."""

    run_id: int
    pmid: int
    state: Literal["selected", "curated"]
    note: str


@dataclass
class Outcome:
    written: list[str]  # stable IDs, `run_id/pmid` for publications, `run/pmid → run` for moves
    problems: list[tuple[int, str]]  # (row number, why) for each problem of a row not written
    results: list[check.Result]  # the full check on the result
    committed: bool

    @property
    def errors(self) -> list[check.Result]:
        return check.errors(self.results)

    @property
    def ok(self) -> bool:
        return not self.problems and not self.errors


# --- The transaction ----------------------------------------------------------------------------


Applied = tuple[list[str], list[tuple[int, str]]]  # what was written, the problems of the rows


def _apply_rows[T](
    cur: Any,
    rows: Sequence[T],
    apply: Callable[[Any, T], str],
    first: int = 1,
    order: Callable[[T], int] = lambda _: 0,
) -> Applied:
    """Apply each row in its own savepoint; rows are numbered from `first` in their problems."""
    written: list[str] = []
    problems: list[tuple[int, str]] = []
    for number, row in sorted(enumerate(rows, first), key=lambda n_row: order(n_row[1])):
        try:
            with cur.connection.transaction():
                written.append(apply(cur, row))
        except InvalidRow as e:
            problems += [(number, p) for p in e.problems]
    return written, problems


def _write(conn: psycopg.Connection, commit: bool, apply: Callable[[Any], Applied]) -> Outcome:
    """Apply the rows in one transaction, check everything, commit or roll back."""
    if conn.info.transaction_status != psycopg.pq.TransactionStatus.IDLE:
        raise RuntimeError("the connection has a transaction in progress")
    with conn.transaction() as tx:
        cur = conn.cursor()
        written, problems = apply(cur)
        results = check.run_checks(cur)
        committed = commit and not problems and not check.errors(results)
        if not committed:
            raise psycopg.Rollback(tx)
    return Outcome(written, sorted(problems, key=lambda p: p[0]), results, committed)


# --- Shared checks ------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Snapshot:
    id: int
    accession: str
    type: str
    gene: str
    sequences: dict[str, str]

    @property
    def length(self) -> int:
        return len(self.sequences[self.accession])


def _snapshot(cur: Any, accession: str, snapshot_id: int | None = None) -> _Snapshot:
    """The current snapshot of an accession, or the given one (a revision keeps its own)."""
    if snapshot_id is None:
        cur.execute(
            """
            SELECT p.id, p.accession, p.type, p.name, p.sequences::text FROM proteins AS p
            JOIN proteins_versions AS v ON v.accession = p.accession AND v.version = p.version
            WHERE p.accession = %s
            """,
            (accession,),
        )
    else:
        cur.execute(
            "SELECT id, accession, type, name, sequences::text FROM proteins WHERE id = %s",
            (snapshot_id,),
        )
    rows = cur.fetchall()
    if not rows:
        raise InvalidRow(f"{accession} has no current snapshot")
    if len(rows) > 1:
        raise InvalidRow(f"{accession} has {len(rows)} current snapshots")
    id_, accession, type_, gene, text = rows[0]
    raw: Any = json.loads(text)
    sequences = {k: v for k, v in cast(dict[str, Any], raw).items() if isinstance(v, str) and v}
    if accession not in sequences or len(sequences) != len(raw):
        raise InvalidRow(f"{accession} (snapshot {id_}) has a missing or empty sequence")
    if type_ == "h" and not (gene or "").strip():
        raise InvalidRow(f"{accession} (snapshot {id_}) is human without a gene name")
    return _Snapshot(id_, accession, type_, gene or "", sequences)


@dataclass(frozen=True)
class _Association:
    id: int
    run_type: str
    state: str


def _association(cur: Any, run_id: int, pmid: int) -> _Association:
    """A publication in a run, `selected` or `curated`: where descriptions are written."""
    cur.execute(
        "SELECT a.id, r.type, a.state FROM associations AS a JOIN runs AS r ON r.id = a.run_id "
        "WHERE a.run_id = %s AND a.pmid = %s",
        (run_id, pmid),
    )
    row = cur.fetchone()
    if row is None:
        raise InvalidRow(f"publication {pmid} is not in run {run_id}")
    association = _Association(*row)
    if association.state not in ("selected", "curated"):
        raise InvalidRow(f"publication {pmid} of run {run_id} is {association.state}")
    return association


def _build(
    cur: Any,
    association: _Association,
    item: Description,
    kept: tuple[tuple[str, int], tuple[str, int]] | None = None,
) -> dict[str, Any]:
    """The columns of a description; raise `InvalidRow` with every problem found.

    `kept` is the (accession, snapshot ID) of each side of a revised description: a side that
    keeps its accession keeps its snapshot, even obsolete; otherwise the current snapshot.
    """
    problems: list[str] = []
    cur.execute("SELECT id FROM methods WHERE psimi_id = %s", (item.method,))
    method = cur.fetchone()
    if method is None:
        problems.append(f"unknown method {item.method}")
    snapshots: list[_Snapshot] = []
    expected = ("h", "v" if association.run_type == "vh" else "h")
    for side, accession in enumerate((item.accession1, item.accession2)):
        pinned = kept[side][1] if kept and kept[side][0] == accession else None
        try:
            snapshot = _snapshot(cur, accession, pinned)
        except InvalidRow as e:
            problems += [f"protein {side + 1}: {p}" for p in e.problems]
            continue
        if snapshot.type != expected[side]:
            problems.append(
                f"protein {side + 1}: {accession} is {'human' if snapshot.type == 'h' else 'viral'}"
            )
        snapshots.append(snapshot)
    if problems:
        raise InvalidRow(*problems)
    p1, p2 = snapshots

    start2 = 1 if item.start2 is None else item.start2
    stop2 = p2.length if item.stop2 is None else item.stop2
    if association.run_type == "hh":
        name2 = p2.gene
        if (start2, stop2) != (1, p2.length):
            problems.append(f"protein 2: a human interactor is 1-{p2.length}, not {start2}-{stop2}")
    else:
        name2 = item.name2.strip()
        if not name2:
            problems.append("protein 2: the generic name is empty")
        if not 1 <= start2 <= stop2 <= p2.length:
            problems.append(f"protein 2: {start2}-{stop2} is outside 1-{p2.length}")
    if problems:
        raise InvalidRow(*problems)

    below = {b.upper() for b in item.below_threshold}
    if unknown := below - {m.upper() for m in item.mappings1 + item.mappings2}:
        problems.append(f"below_threshold lists sequences that are not mappings: {sorted(unknown)}")
    mappings: list[list[dict[str, Any]]] = []
    for side, snapshot, sequences, start, stop in (
        (1, p1, item.mappings1, 1, p1.length),
        (2, p2, item.mappings2, start2, stop2),
    ):
        if len({s.upper() for s in sequences}) != len(sequences):
            problems.append(f"protein {side}: duplicate mapping sequences")
        computed: list[dict[str, Any]] = []
        for text in sequences:
            try:
                sequence, nter, cter = read_written(text)
            except ValueError as e:
                problems.append(f"protein {side}: {e}")
                continue
            if not check.AMINO_ACIDS.fullmatch(sequence):
                problems.append(
                    f"protein {side}: mapping {sequence[:20]}… is not an amino acid sequence"
                )
                continue
            mapping = map_sequence(
                sequence, snapshot.sequences, snapshot.accession, start, stop, nter, cter
            )
            if not mapping["isoforms"]:
                problems.append(
                    f"protein {side}: mapping {sequence[:20]}… ({len(sequence)} aa) aligns "
                    f"nowhere on {snapshot.accession}[{start}-{stop}]"
                )
            elif best_identity(mapping) < MIN_IDENTITY and sequence not in below:
                problems.append(
                    f"protein {side}: mapping {sequence[:20]}… ({len(sequence)} aa) is below "
                    f"{MIN_IDENTITY:g} % on every isoform of {snapshot.accession}[{start}-{stop}]: "
                    "explain it in the note and list it in below_threshold"
                )
            computed.append(mapping)
        mappings.append(computed)
    if problems:
        raise InvalidRow(*problems)
    return {
        "association_id": association.id,
        "method_id": method[0],  # type: ignore[index]
        "protein1_id": p1.id,
        "name1": p1.gene,
        "start1": 1,
        "stop1": p1.length,
        "mapping1": json.dumps(mappings[0]),
        "protein2_id": p2.id,
        "name2": name2,
        "start2": start2,
        "stop2": stop2,
        "mapping2": json.dumps(mappings[1]),
    }


def _insert(cur: Any, stable_id: str, version: int, row: dict[str, Any], note: str) -> None:
    cur.execute(
        """
        INSERT INTO descriptions (stable_id, version, association_id, method_id,
            protein1_id, name1, start1, stop1, mapping1,
            protein2_id, name2, start2, stop2, mapping2, annotation)
        VALUES (%(stable_id)s, %(version)s, %(association_id)s, %(method_id)s,
            %(protein1_id)s, %(name1)s, %(start1)s, %(stop1)s, %(mapping1)s,
            %(protein2_id)s, %(name2)s, %(start2)s, %(stop2)s, %(mapping2)s, %(annotation)s)
        """,
        {**row, "stable_id": stable_id, "version": version, "annotation": note},
    )


# --- Adding -------------------------------------------------------------------------------------


def _new_stable_id(cur: Any) -> str:
    """A `CW` stable ID unused by any row, live or deleted."""
    while True:
        candidate = "CW" + secrets.token_hex(4).upper()
        cur.execute("SELECT 1 FROM descriptions WHERE stable_id = %s", (candidate,))
        if cur.fetchone() is None:
            return candidate


def _add(cur: Any, item: NewDescription) -> str:
    association = _association(cur, item.run_id, item.pmid)
    if association.run_type != "vh":
        raise InvalidRow(f"run {item.run_id} is an hh run: new descriptions go to a vh run")
    note = item.note.strip()
    row = _build(cur, association, item.description)
    stable_id = _new_stable_id(cur)
    _insert(cur, stable_id, 1, row, note)
    return stable_id


def add_descriptions(
    conn: psycopg.Connection, items: Sequence[NewDescription], *, commit: bool = False
) -> Outcome:
    """Add new descriptions, each with a new `CW` stable ID, version 1."""
    return _write(conn, commit, lambda cur: _apply_rows(cur, items, _add))


# --- Revising -----------------------------------------------------------------------------------


def _live(cur: Any, revision: Revision) -> tuple[int, int, _Association]:
    """The live row of a revision's stable ID, locked: its row ID, version and publication."""
    cur.execute(
        "SELECT id, version, association_id FROM descriptions "
        "WHERE stable_id = %s AND deleted_at IS NULL FOR UPDATE",
        (revision.stable_id,),
    )
    row = cur.fetchone()
    if row is None:
        raise InvalidRow(f"{revision.stable_id} has no live version")
    id_, version, association_id = row
    if version != revision.version:
        raise InvalidRow(
            f"{revision.stable_id}: decided on version {revision.version}, "
            f"but the live version is {version}"
        )
    association = _association(cur, revision.run_id, revision.pmid)
    if association_id != association.id:
        raise InvalidRow(
            f"{revision.stable_id} is not a description of publication {revision.pmid} "
            f"in run {revision.run_id}"
        )
    return id_, version, association


# The live version of a stable ID: what a revision keeps, and what makes it a duplicate.
LIVE_DESCRIPTION = """
    SELECT d.association_id, d.method_id, p1.accession, p1.id, p2.accession, p2.id,
           d.start2, d.stop2, d.mapping1::text, d.mapping2::text
    FROM descriptions AS d
    JOIN proteins AS p1 ON p1.id = d.protein1_id
    JOIN proteins AS p2 ON p2.id = d.protein2_id
    WHERE d.stable_id = %s AND d.deleted_at IS NULL
"""

# The columns `_build` gives.
COLUMNS = """
    SELECT association_id, method_id, protein1_id, name1, start1, stop1, mapping1,
           protein2_id, name2, start2, stop2, mapping2
    FROM descriptions WHERE id = %s
"""


def _sequences(mappings: str) -> set[str]:
    return {m["sequence"] for m in json.loads(mappings)}


def _check_merge(cur: Any, revision: Revision, removed: tuple[Any, ...]) -> None:
    """The removed description (publication, method, interactors, mappings) is in its survivor."""
    cur.execute(LIVE_DESCRIPTION, (revision.into,))
    survivor = cur.fetchone()
    if survivor is None:
        raise InvalidRow(f"{revision.into}, the survivor, has no live version")
    association_id, method_id, accession1, _, accession2, _, start2, stop2, m1, m2 = survivor
    if removed[:6] != (association_id, method_id, accession1, accession2, start2, stop2):
        raise InvalidRow(
            f"{revision.stable_id} and {revision.into} differ in publication, method or "
            "interactors: not duplicates"
        )
    for side, mine, theirs in ((1, removed[6], m1), (2, removed[7], m2)):
        if missing := mine - _sequences(theirs):
            raise InvalidRow(
                f"{revision.into} lacks the mapping sequences of {revision.stable_id} "
                f"on side {side}: {sorted(missing)}"
            )


def _revise(cur: Any, revision: Revision) -> str:
    live_id, version, association = _live(cur, revision)
    cur.execute(LIVE_DESCRIPTION, (revision.stable_id,))
    _, method_id, a1, id1, a2, id2, start2, stop2, mappings1, mappings2 = cur.fetchone()
    kept = ((a1, id1), (a2, id2))
    item = revision.description

    if revision.action == "remove":
        note = revision.note.strip()
        if not note:
            raise InvalidRow("the note must hold the REMOVED decision")
        if revision.into:
            # The removed description, as it is or as it was decided to be, is its survivor.
            if item is None:
                removed = (association.id, method_id, a1, a2, start2, stop2)
                removed += (_sequences(mappings1), _sequences(mappings2))
            else:
                row = _build(cur, association, item, kept)
                removed = (association.id, row["method_id"], item.accession1, item.accession2)
                removed += (row["start2"], row["stop2"])
                removed += (_sequences(row["mapping1"]), _sequences(row["mapping2"]))
            _check_merge(cur, revision, removed)
        elif item is not None:
            raise InvalidRow("a removal without `into` takes no description")
        # The live version is deleted, its note gets the REMOVED line.
        cur.execute(
            "UPDATE descriptions SET deleted_at = now(), "
            "annotation = concat_ws(E'\\n', nullif(annotation, ''), %s::text) WHERE id = %s",
            (note, live_id),
        )
        return revision.stable_id

    if item is None:
        raise InvalidRow(f"{revision.stable_id}: a revision needs its description")
    note = revision.note.strip()
    row = _build(cur, association, item, kept)
    cur.execute(COLUMNS, (live_id,))
    old = dict(zip(row, cur.fetchone(), strict=True))  # same order; JSON columns come parsed
    new = {**row, "mapping1": json.loads(row["mapping1"]), "mapping2": json.loads(row["mapping2"])}
    if old == new:
        raise InvalidRow(f"the revision of {revision.stable_id} changes nothing")
    cur.execute("UPDATE descriptions SET deleted_at = now() WHERE id = %s", (live_id,))
    _insert(cur, revision.stable_id, version + 1, row, note)
    return revision.stable_id


def live_revisions(cur: Any, run_id: int, pmid: int) -> list[Revision]:
    """The live descriptions of a publication, each as a `revise` row to edit (empty note).

    Accessions are those of the snapshots used, even obsolete: a revision keeps them unless the
    accession changes. `below_threshold` lists the mappings stored below `MIN_IDENTITY`.
    """
    cur.execute(
        """
        SELECT d.stable_id, d.version, m.psimi_id, p1.accession, p2.accession, d.name2, d.start2,
               d.stop2, d.mapping1::text, d.mapping2::text, r.type
        FROM descriptions AS d
        JOIN associations AS a ON a.id = d.association_id
        JOIN runs AS r ON r.id = a.run_id
        JOIN methods AS m ON m.id = d.method_id
        JOIN proteins AS p1 ON p1.id = d.protein1_id
        JOIN proteins AS p2 ON p2.id = d.protein2_id
        WHERE a.run_id = %s AND a.pmid = %s AND d.deleted_at IS NULL
        ORDER BY d.stable_id
        """,
        (run_id, pmid),
    )
    revisions: list[Revision] = []
    for stable_id, version, method, a1, a2, name2, start2, stop2, m1, m2, run_type in cur:
        mappings = [cast(list[dict[str, Any]], json.loads(m)) for m in (m1, m2)]
        below = tuple(
            written(m) for side in mappings for m in side if best_identity(m) < MIN_IDENTITY
        )
        hh = run_type == "hh"
        description = Description(
            method=method,
            accession1=a1,
            accession2=a2,
            name2="" if hh else name2,
            start2=None if hh else start2,
            stop2=None if hh else stop2,
            mappings1=tuple(written(m) for m in mappings[0]),
            mappings2=tuple(written(m) for m in mappings[1]),
            below_threshold=below,
        )
        revisions.append(Revision(stable_id, version, run_id, pmid, "revise", description))
    return revisions


def revise_descriptions(
    conn: psycopg.Connection, revisions: Sequence[Revision], *, commit: bool = False
) -> Outcome:
    """Revise or remove live descriptions; a stable ID appears once.

    Revisions are applied before removals, so that a duplicate is compared with its survivor
    as revised.
    """
    _once(revisions)
    return _write(conn, commit, lambda cur: _apply_rows(cur, revisions, _revise, order=_removal))


def _once(revisions: Sequence[Revision]) -> None:
    """Raise `ValueError` for a stable ID given twice."""
    seen: dict[str, int] = {}
    for number, revision in enumerate(revisions, 1):
        if revision.stable_id in seen:
            raise ValueError(
                f"rows {seen[revision.stable_id]} and {number}: {revision.stable_id} twice"
            )
        seen[revision.stable_id] = number


def _removal(revision: Revision) -> bool:
    return revision.action == "remove"


# --- Publications -------------------------------------------------------------------------------

# A new note goes first in the note of a publication, the previous notes after a line `---`.
NEW_NOTE = "concat_ws(E'\\n---\\n', nullif(%s::text, ''), nullif(annotation, ''))"


def _publication(cur: Any, update: PublicationUpdate) -> str:
    association = _association(cur, update.run_id, update.pmid)
    if association.run_type != "vh":
        raise InvalidRow(f"run {update.run_id} is an hh run: hh curation is frozen")
    if update.state not in ("selected", "curated"):
        raise InvalidRow(f"state {update.state!r} is not selected or curated")
    cur.execute(
        f"UPDATE associations SET state = %s, annotation = {NEW_NOTE}, ai_pass_at = now(), "
        "updated_at = now() WHERE id = %s",
        (update.state, update.note.strip(), association.id),
    )
    return f"{update.run_id}/{update.pmid}"


def update_publications(
    conn: psycopg.Connection, updates: Sequence[PublicationUpdate], *, commit: bool = False
) -> Outcome:
    """Set the state of publications of vh runs at the end of a pass (`ai_pass_at`), the note of
    the pass first in their notes."""
    return _write(conn, commit, lambda cur: _apply_rows(cur, updates, _publication))


# --- Moving to a special run --------------------------------------------------------------------

SPECIAL_RUN = re.compile(r"special-(\d+)")
SPECIAL_INFO = (
    "Publications Claude could not curate fully, moved from their runs of the PubMed query."
)


@dataclass(frozen=True)
class Move:
    """A publication Claude could not curate fully, in the run it leaves."""

    association_id: int
    pmid: int
    run: str


def _special_run(cur: Any, new: bool) -> tuple[int, str]:
    """The open special run, the one with the highest number; a new one when asked or when none."""
    cur.execute("SELECT id, name FROM runs WHERE type = 'vh' AND name ~ '^special-[0-9]+$'")
    runs = sorted(
        (int(cast(re.Match[str], SPECIAL_RUN.fullmatch(name))[1]), run_id, name)
        for run_id, name in cur.fetchall()
    )
    if runs and not new:
        return runs[-1][1], runs[-1][2]
    name = f"special-{runs[-1][0] + 1 if runs else 1}"
    cur.execute(
        "INSERT INTO runs (type, name, populated, info) VALUES ('vh', %s, true, %s) RETURNING id",
        (name, SPECIAL_INFO),
    )
    return cur.fetchone()[0], name


def _move(cur: Any, move: Move, target_id: int, target: str) -> str:
    cur.execute(
        "SELECT 1 FROM associations WHERE run_id = %s AND pmid = %s", (target_id, move.pmid)
    )
    if cur.fetchone() is not None:
        raise InvalidRow(f"publication {move.pmid} is already in run {target}")
    cur.execute("SELECT current_date::text")
    note = f"Moved {cur.fetchone()[0]}: from run {move.run}"
    cur.execute(
        f"UPDATE associations SET run_id = %s, annotation = {NEW_NOTE}, updated_at = now() "
        "WHERE id = %s",
        (target_id, note, move.association_id),
    )
    return f"{move.run}/{move.pmid} → {target}"


def move_publications(
    conn: psycopg.Connection,
    publications: Sequence[tuple[int, int]],
    *,
    new_run: bool = False,
    commit: bool = False,
) -> tuple[list[Move], Outcome]:
    """Move the publications given as (run_id, pmid) that are `selected` with a pass date in a vh
    run of the PubMed query to the open special run (a new one with `new_run`), each with a
    `Moved` note first in its note. The others are left where they are.

    Raises `ValueError` for a publication that is not in its run.
    """
    with conn.transaction(), conn.cursor() as cur:
        moves, missing = _movable(cur, publications)
    if missing:
        raise ValueError(f"publications not in their run: {', '.join(missing)}")
    if not moves:
        return moves, Outcome([], [], [], False)
    return moves, _write(conn, commit, lambda cur: _apply_moves(cur, moves, new_run))


def _movable(cur: Any, publications: Sequence[tuple[int, int]]) -> tuple[list[Move], list[str]]:
    """The publications given as (run_id, pmid) that a move takes, and those not in their run."""
    cur.execute(
        "SELECT given.run_id, given.pmid, a.id, r.name, r.type, a.state, a.ai_pass_at "
        "FROM unnest(%s::int[], %s::bigint[]) AS given (run_id, pmid) "
        "LEFT JOIN associations AS a ON a.run_id = given.run_id AND a.pmid = given.pmid "
        "LEFT JOIN runs AS r ON r.id = a.run_id "
        "ORDER BY given.run_id, given.pmid",
        ([run_id for run_id, _ in publications], [pmid for _, pmid in publications]),
    )
    rows = cur.fetchall()
    missing = [
        f"{run_id}/{pmid}" for run_id, pmid, association_id, *_ in rows if association_id is None
    ]
    moves = sorted(
        {
            Move(association_id, pmid, run)
            for _, pmid, association_id, run, run_type, state, ai_pass_at in rows
            if run_type == "vh"
            and not SPECIAL_RUN.fullmatch(run)
            and state == "selected"
            and ai_pass_at is not None
        },
        key=lambda move: (move.run, move.pmid),
    )
    return moves, missing


def _apply_moves(cur: Any, moves: Sequence[Move], new_run: bool, first: int = 1) -> Applied:
    target_id, target = _special_run(cur, new_run)
    return _apply_rows(cur, moves, lambda c, move: _move(c, move, target_id, target), first)


# --- A curation batch ---------------------------------------------------------------------------


def write_batch(
    conn: psycopg.Connection,
    revisions: Sequence[Revision],
    additions: Sequence[NewDescription],
    updates: Sequence[PublicationUpdate],
    *,
    new_run: bool = False,
    commit: bool = False,
) -> tuple[list[Move], Outcome]:
    """Write a curation batch in one transaction, in this order: the revisions and removals, the
    new descriptions, the publication updates, then the move of the updated publications left
    `selected` to the special run, as `move_publications` does. Every invariant is checked once,
    on the result, so a row can rely on an earlier one (an addition on a rename).

    Rows are numbered across the three lists, in that order, then the moves.
    """
    _once(revisions)
    moves: list[Move] = []

    def apply(cur: Any) -> Applied:
        stages = [
            _apply_rows(cur, revisions, _revise, order=_removal),
            _apply_rows(cur, additions, _add, len(revisions) + 1),
            _apply_rows(cur, updates, _publication, len(revisions) + len(additions) + 1),
        ]
        # A publication not in its run is already refused by its update.
        moves.extend(_movable(cur, [(u.run_id, u.pmid) for u in updates])[0])
        if moves:
            first = len(revisions) + len(additions) + len(updates) + 1
            stages.append(_apply_moves(cur, moves, new_run, first))
        return [w for s in stages for w in s[0]], [p for s in stages for p in s[1]]

    return moves, _write(conn, commit, apply)
