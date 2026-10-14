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
        "[DATE Claude] CREATED: anti-tag co-IP (MI:0007), Fig. 2B",
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
    assert note.startswith("[") and "CREATED" in note and "DATE" not in note


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


def test_add_checks_the_note(conn, new):
    outcome = add_descriptions(conn, [replace(new, note="anti-tag co-IP")])
    assert "note" in outcome.problems[0][1]


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
    note = "[DATE Claude] REVISED: name2 N → orf6, Drakkar name of the protein"
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
        note="[DATE Claude] REMOVED: duplicate of EY10BAD696, the protein tested is P",
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
        note="[DATE Claude] REMOVED: duplicate",
    )
    assert "not duplicates" in revise_descriptions(conn, [merge]).problems[0][1]


def test_removal_needs_its_note(conn):
    removed = replace(live(conn, *RABIES)["EYC9AE3284"], action="remove", description=None)
    assert "REMOVED" in revise_descriptions(conn, [removed]).problems[0][1]


# --- Publications -------------------------------------------------------------------------------


def today(conn) -> str:
    result = conn.execute("SELECT current_date::text").fetchone()[0]
    conn.rollback()
    return result


def test_publication_curated(conn):
    note = f"[DATE Claude] CURATED: from PMC1234567, no description\n- Pass {today(conn)}: curated"
    outcome = update_publications(
        conn, [PublicationUpdate(*SELECTED, "curated", note)], commit=True
    )
    assert outcome.ok and outcome.committed
    state, ai_pass_at = conn.execute(
        "SELECT state, ai_pass_at FROM associations WHERE run_id = 12 AND pmid = 25031347"
    ).fetchone()
    assert state == "curated" and ai_pass_at is not None


def test_publication_keeps_the_curator_note(conn):
    note = f"[DATE Claude] CURATED: from PMC1234567\n- Pass {today(conn)}: re-curated"
    update = PublicationUpdate(56, 34799561, "curated", note)
    assert "curator note" in update_publications(conn, [update]).problems[0][1]
    kept = PublicationUpdate(
        56,
        34799561,
        "curated",
        note + "\n--- Curator note (before Claude) ---\nDone. Pierre to upload",
    )
    assert update_publications(conn, [kept]).ok


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
