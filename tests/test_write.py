"""Writes: one transaction per list, checked on the whole database, committed only on demand."""

from dataclasses import replace

import pytest

from drakkar.write import (
    Description,
    NewDescription,
    PublicationUpdate,
    Revision,
    add_descriptions,
    live_revisions,
    revise_descriptions,
    update_publications,
    write_batch,
)

SARS = (1, 22046132)  # Q6VA95 `N` carried by EY73D2C965 and EYF737084C
RABIES = (69, 38566321)
SELECTED = (12, 25031347)


def live(conn, run_id, pmid) -> dict[str, Revision]:
    rows = {r.stable_id: r for r in live_revisions(conn.cursor(), run_id, pmid)}
    conn.rollback()
    return rows


def count(conn) -> int:
    result = conn.execute("SELECT count(*) FROM descriptions").fetchone()[0]
    conn.rollback()
    return result


def renamed(revision: Revision, name2: str, note: str = "") -> Revision:
    assert revision.description is not None
    return replace(revision, description=replace(revision.description, name2=name2), note=note)


# --- Adding -------------------------------------------------------------------------------------


@pytest.fixture
def new(conn) -> NewDescription:
    """NEDD4 with P25223 `P`, mapped by the first 20 residues of P25223."""
    sequence = conn.execute(
        "SELECT p.sequences->>p.accession FROM proteins AS p JOIN proteins_versions AS v "
        "ON v.accession = p.accession AND v.version = p.version WHERE p.accession = 'P25223'"
    ).fetchone()[0]
    conn.rollback()
    return NewDescription(
        *SELECTED,
        Description("MI:0007", "P46934", "P25223", "P", mappings2=(sequence[:20],)),
        "CREATED: anti-tag co-IP (MI:0007), Fig. 2B",
    )


def test_add_dry_run_writes_nothing(conn, new):
    before = count(conn)
    outcome = add_descriptions(conn, [new])
    assert outcome.ok and not outcome.committed and len(outcome.written) == 1
    assert count(conn) == before


def test_add_commits(conn, new):
    outcome = add_descriptions(conn, [new], commit=True)
    assert outcome.ok and outcome.committed
    [stable_id] = outcome.written
    assert stable_id.startswith("CW")
    row = conn.execute(
        "SELECT version, name1, start1, stop1, name2, start2, stop2, mapping2, annotation "
        "FROM descriptions WHERE stable_id = %s",
        (stable_id,),
    ).fetchone()
    version, name1, start1, stop1, name2, start2, stop2, mapping2, note = row
    assert (version, name1, start1, name2, start2) == (1, "NEDD4", 1, "P", 1)
    assert stop1 > 1 and stop2 > 1
    assert mapping2[0]["isoforms"][0]["occurrences"][0] == {"start": 1, "stop": 20, "identity": 100}
    assert note == "CREATED: anti-tag co-IP (MI:0007), Fig. 2B"


def test_add_refuses_a_bad_row_and_writes_none(conn, new):
    bad = replace(new, description=replace(new.description, accession2="NOTANACC"))
    before = count(conn)
    outcome = add_descriptions(conn, [new, bad], commit=True)
    assert not outcome.committed
    assert [number for number, _ in outcome.problems] == [2]
    assert count(conn) == before


def test_add_duplicate_is_caught_by_the_full_check(conn, new):
    outcome = add_descriptions(conn, [new, new], commit=True)
    assert not outcome.problems  # each row is valid on its own
    assert [r.invariant.id for r in outcome.errors] == ["D5"]
    assert not outcome.committed


def test_add_to_an_hh_run_is_refused(conn, new):
    outcome = add_descriptions(conn, [replace(new, run_id=31, pmid=15471871)])
    assert "hh run" in outcome.problems[0][1]


def test_mapping_below_threshold_needs_to_be_listed(conn, new):
    low = replace(new, description=replace(new.description, mappings2=("WWWWWWWWWWWWWWWWWWWW",)))
    assert "below_threshold" in add_descriptions(conn, [low]).problems[0][1]
    listed = replace(
        low, description=replace(low.description, below_threshold=("WWWWWWWWWWWWWWWWWWWW",))
    )
    assert add_descriptions(conn, [listed]).ok


# --- Revising -----------------------------------------------------------------------------------


def test_rename_an_interactor_carried_by_two_descriptions(conn):
    rows = live(conn, *SARS)
    note = "REVISED: name2 N → orf6, Drakkar name of the protein"
    revisions = [renamed(rows[s], "orf6", note) for s in ("EY73D2C965", "EYF737084C")]
    outcome = revise_descriptions(conn, revisions, commit=True)
    assert outcome.ok and outcome.committed
    names = conn.execute(
        "SELECT stable_id, version, name2 FROM descriptions WHERE deleted_at IS NULL "
        "AND stable_id IN ('EY73D2C965', 'EYF737084C') ORDER BY 1"
    ).fetchall()
    assert names == [("EY73D2C965", 2, "orf6"), ("EYF737084C", 2, "orf6")]


def test_rename_one_of_two_breaks_one_name_per_interactor(conn):
    rows = live(conn, *SARS)
    outcome = revise_descriptions(conn, [renamed(rows["EY73D2C965"], "orf6")], commit=True)
    assert not outcome.problems
    assert [r.invariant.id for r in outcome.errors] == ["D6"]
    assert not outcome.committed


def test_revision_on_a_stale_version_is_refused(conn):
    revision = renamed(live(conn, *SARS)["EY73D2C965"], "orf6")
    outcome = revise_descriptions(conn, [replace(revision, version=revision.version + 1)])
    assert "live version is" in outcome.problems[0][1]


def test_revision_that_changes_nothing_is_refused(conn):
    revision = live(conn, *SARS)["EY73D2C965"]
    assert "changes nothing" in revise_descriptions(conn, [revision]).problems[0][1]


def test_revision_of_another_publication_is_refused(conn):
    revision = renamed(live(conn, *SARS)["EY73D2C965"], "orf6")
    outcome = revise_descriptions(conn, [replace(revision, run_id=69, pmid=38566321)])
    assert "not a description of publication" in outcome.problems[0][1]


def test_stable_id_twice_is_refused(conn):
    revision = renamed(live(conn, *SARS)["EY73D2C965"], "orf6")
    with pytest.raises(ValueError, match="twice"):
        revise_descriptions(conn, [revision, revision])


def test_merge_a_description_decided_to_be_a_duplicate(conn):
    # EYC9AE3284 (NEDD4, A4UHQ0 M) is decided to be NEDD4 with P25223 P: EY10BAD696.
    rows = live(conn, *RABIES)
    removed = rows["EYC9AE3284"]
    assert removed.description is not None
    decided = replace(removed.description, accession2="P25223", name2="P", start2=1, stop2=202)
    merge = replace(
        removed,
        action="remove",
        into="EY10BAD696",
        description=decided,
        note="REMOVED: duplicate of EY10BAD696, the protein tested is P",
    )
    outcome = revise_descriptions(conn, [merge], commit=True)
    assert outcome.ok and outcome.committed
    assert "EYC9AE3284" not in live(conn, *RABIES)


def test_merge_of_different_descriptions_is_refused(conn):
    removed = live(conn, *RABIES)["EYC9AE3284"]
    merge = replace(
        removed,
        action="remove",
        into="EY10BAD696",
        description=None,
        note="REMOVED: duplicate",
    )
    assert "not duplicates" in revise_descriptions(conn, [merge]).problems[0][1]


def test_removal_needs_its_note(conn):
    removed = replace(live(conn, *RABIES)["EYC9AE3284"], action="remove", description=None)
    assert "REMOVED" in revise_descriptions(conn, [removed]).problems[0][1]


# --- Publications -------------------------------------------------------------------------------


def test_publication_curated(conn):
    note = "CURATED: no description, a review of earlier screens\n- Full text: PMC1234567 (cc by)"
    update = PublicationUpdate(*SELECTED, "curated", note)
    assert update_publications(conn, [update], commit=True).committed
    state, ai_pass_at = conn.execute(
        "SELECT state, ai_pass_at IS NOT NULL FROM associations "
        "WHERE run_id = 12 AND pmid = 25031347"
    ).fetchone()
    assert (state, ai_pass_at) == ("curated", True)


def test_publication_note_goes_first(conn):
    """SELECTED has no note yet; then each note goes first, the previous ones after `---`, its
    header dated by the write."""
    first = PublicationUpdate(*SELECTED, "selected", "SELECTED: no full text, closed")
    assert update_publications(conn, [first], commit=True).committed
    dated = f"SELECTED {today(conn)}: no full text, closed"
    assert note_of(conn, SELECTED[1]) == dated
    note = "CURATED: co-IP of NS1 with TRIM25\n- Full text: PDF provided by the user"
    assert update_publications(conn, [replace(first, state="curated", note=note)], commit=True).ok
    assert note_of(conn, SELECTED[1]) == (
        f"CURATED {today(conn)}: co-IP of NS1 with TRIM25\n- Full text: PDF provided by the user"
        f"\n---\n{dated}"
    )


def test_publication_note_starts_with_its_state(conn):
    for note in ("SELECTED: a relevant file missing", "co-IP of NS1 with TRIM25"):
        outcome = update_publications(conn, [PublicationUpdate(*SELECTED, "curated", note)])
        assert "the note must start with its state, CURATED:" in outcome.problems[0][1]


def today(conn) -> str:
    result = conn.execute("SELECT current_date::text").fetchone()[0]
    conn.rollback()
    return result


def note_of(conn, pmid) -> str:
    result = conn.execute("SELECT annotation FROM associations WHERE pmid = %s", (pmid,))
    note = result.fetchone()[0]
    conn.rollback()
    return note


# --- Moving to a special run --------------------------------------------------------------------


NOT_ACCESSIBLE = "SELECTED: no full text, closed — not open access anywhere"


def left_selected(run_id: int = SELECTED[0]) -> PublicationUpdate:
    """SELECTED left `selected` by a pass: what the batch moves."""
    return PublicationUpdate(run_id, SELECTED[1], "selected", NOT_ACCESSIBLE)


def run_of(conn, pmid) -> tuple[int, str, str]:
    result = conn.execute(
        "SELECT r.id, r.name, a.annotation FROM associations AS a "
        "JOIN runs AS r ON r.id = a.run_id WHERE a.pmid = %s",
        (pmid,),
    ).fetchone()
    conn.rollback()
    return result


def test_move_takes_the_descriptions(conn, new):
    [stable_id] = add_descriptions(conn, [new], commit=True).written
    assert write_batch(conn, [], [], [left_selected()], commit=True)[1].committed
    run_id, name, moved = run_of(conn, SELECTED[1])
    day = today(conn)
    selected = NOT_ACCESSIBLE.replace("SELECTED:", f"SELECTED {day}:")
    assert name == "special-1" and moved == f"Moved {day}: from run 32\n---\n{selected}"
    assert stable_id in live(conn, run_id, SELECTED[1])
    curated = "CURATED: co-IP of NS1 with TRIM25\n- Full text: PDF provided by the user"
    update = PublicationUpdate(run_id, SELECTED[1], "curated", curated)
    assert update_publications(conn, [update], commit=True).committed
    dated = curated.replace("CURATED:", f"CURATED {day}:")
    assert note_of(conn, SELECTED[1]) == f"{dated}\n---\n{moved}"


def test_move_to_a_new_special_run(conn):
    conn.execute("INSERT INTO runs (type, name) VALUES ('vh', 'special-1')")
    conn.commit()
    assert write_batch(conn, [], [], [left_selected()], new_run=True, commit=True)[1].committed
    assert run_of(conn, SELECTED[1])[1] == "special-2"


def test_move_leaves_the_others(conn):
    curated = PublicationUpdate(*SARS, "curated", "CURATED: co-IP of SARS-CoV N")
    assert write_batch(conn, [], [], [curated])[0] == []
    assert write_batch(conn, [], [], [left_selected()], commit=True)[1].committed
    run_id = run_of(conn, SELECTED[1])[0]
    assert write_batch(conn, [], [], [left_selected(run_id)])[0] == []  # already in a special run


def test_open_transaction_is_refused(conn, new):
    conn.execute("SELECT 1")
    with pytest.raises(RuntimeError):
        add_descriptions(conn, [new])


def test_extra_end_residues_in_lowercase_are_left_out_of_the_occurrences(conn, new):
    [sequence] = new.description.mappings2
    tagged = replace(new, description=replace(new.description, mappings2=("gst" + sequence,)))
    outcome = add_descriptions(conn, [tagged], commit=True)
    assert outcome.ok
    [mapping] = conn.execute(
        "SELECT mapping2 FROM descriptions WHERE stable_id = %s", outcome.written
    ).fetchone()[0]
    assert mapping["sequence"] == "GST" + sequence and mapping["nter"] == "GST"
    assert mapping["isoforms"][0]["occurrences"][0] == {"start": 1, "stop": 20, "identity": 100}
    row = {r.stable_id: r for r in live_revisions(conn.cursor(), *SELECTED)}[outcome.written[0]]
    assert row.description is not None and row.description.mappings2 == ("gst" + sequence,)


def test_the_same_sequence_with_other_extra_residues_is_a_duplicate(conn, new):
    [sequence] = new.description.mappings2
    twice = (sequence, sequence[0].lower() + sequence[1:])
    duplicated = replace(new, description=replace(new.description, mappings2=twice))
    assert "duplicate" in add_descriptions(conn, [duplicated]).problems[0][1]


# --- A curation batch ---------------------------------------------------------------------------


def batch(conn) -> tuple[list[Revision], list[NewDescription], list[PublicationUpdate]]:
    """SARS's `N` renamed `orf6` with a new `orf6` description, which holds only after the
    renames; SELECTED left `selected`, which the batch then moves."""
    rows = live(conn, *SARS)
    note = "REVISED: name2 N → orf6, Drakkar name of the protein"
    revisions = [renamed(rows[s], "orf6", note) for s in ("EY73D2C965", "EYF737084C")]
    added = NewDescription(
        *SARS,
        Description("MI:0007", "P46934", "Q6VA95", "orf6"),
        "CREATED: anti-tag co-IP (MI:0007), Fig. 2B",
    )
    return revisions, [added], [left_selected()]


def test_batch_writes_everything_in_one_transaction(conn):
    revisions, additions, updates = batch(conn)
    assert [r.invariant.id for r in add_descriptions(conn, additions).errors] == ["D6"]  # alone
    before = count(conn)
    moves, outcome = write_batch(conn, revisions, additions, updates)  # a dry run
    assert outcome.ok and not outcome.committed and [m.pmid for m in moves] == [SELECTED[1]]
    assert count(conn) == before and run_of(conn, SELECTED[1])[1] == "32"
    moves, outcome = write_batch(conn, revisions, additions, updates, commit=True)
    assert outcome.committed and count(conn) == before + 3
    names = {r.description.name2 for r in live(conn, *SARS).values() if r.description}
    assert "orf6" in names and "N" not in names
    _, name, note = run_of(conn, SELECTED[1])
    assert name == "special-1" and note.startswith(f"Moved {today(conn)}: from run 32\n---\n")


def test_batch_numbers_rows_across_its_lists(conn):
    revisions, additions, updates = batch(conn)
    bad = replace(additions[0], description=replace(additions[0].description, accession2="X"))
    _, outcome = write_batch(conn, revisions, [bad], updates, commit=True)
    assert [number for number, _ in outcome.problems] == [3] and not outcome.committed
